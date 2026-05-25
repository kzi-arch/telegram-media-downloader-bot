import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import yt_dlp
import signal
import sys
import asyncio
import tempfile
import uuid

# Load .env
load_dotenv()

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN tidak ditemukan di .env!")

# === PERBAIKAN UTAMA: Bersihkan proxy environment ===
def clean_proxy_env():
    for key in list(os.environ.keys()):
        if key.upper() in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY'):
            logger.info(f"Menghapus variabel proxy: {key} = {os.environ[key]}")
            del os.environ[key]

clean_proxy_env()   # Jalankan sebelum bot mulai

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bot siap!\n\n"
        "Kirim link video dari YouTube, Instagram, TikTok, X/Twitter, Facebook, dll.\n"
        "Saya akan download (max ~720p) dan kirim balik."
    )

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("⚠️ Kirim link yang valid (http/https)")
        return

    wait_msg = await update.message.reply_text("⏳ Sedang mendownload... Mohon tunggu.")

    try:
        def _download():
            # Buat UUID agar aman jika ada 2 user mendownload file yang sama secara bersamaan
            unique_id = uuid.uuid4().hex
            temp_dir = tempfile.gettempdir()
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best[height<=720]/best',
                # Gunakan folder temp sistem (Vercel hanya mengizinkan modifikasi file di /tmp)
                'outtmpl': os.path.join(temp_dir, f'{unique_id}_%(id)s.%(ext)s'),
                'noplaylist': True,
                'quiet': True,
                'ignoreerrors': False,
                'max_filesize': 50 * 1024 * 1024, # Batas 50MB dari API Telegram standard
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                },
                'impersonate': 'chrome-99',
                # Vercel tidak punya instalasi Chrome lokal, cookiesfrombrowser akan menyebabkan crash
                # Jika butuh authentikasi, aktifkan 'cookiefile' dan sertakan cookies.txt di dalam repositori
            }
            
            # Gunakan cookies.txt otomatis jika file tersedia di root repositori
            if os.path.exists('cookies.txt'):
                ydl_opts['cookiefile'] = 'cookies.txt'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    raise ValueError("Tidak bisa extract info dari link ini")
                return ydl.prepare_filename(info), info

        # Jalankan yt-dlp di thread terpisah agar bot tidak freeze (Non-blocking)
        filename, info = await asyncio.to_thread(_download)

        if not os.path.exists(filename):
            await wait_msg.edit_text("❌ File tidak ditemukan setelah download.")
            return

        ext = filename.lower().rsplit('.', 1)[-1]
        title = info.get('title', 'Unknown')
        extractor = info.get('extractor_key', 'Unknown')

        caption = f"✅ Berhasil!\nJudul: {title}\nDari: {extractor}"

        # Kirim file sesuai tipe
        with open(filename, 'rb') as f:
            if ext in ['mp4', 'mkv', 'webm', 'mov']:
                await update.message.reply_video(video=f, caption=caption, supports_streaming=True)
            elif ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                await update.message.reply_photo(photo=f, caption=caption)
            elif ext in ['mp3', 'm4a', 'wav', 'ogg']:
                await update.message.reply_audio(audio=f, caption=caption)
            else:
                await update.message.reply_document(document=f, caption=caption)

        await wait_msg.delete()

        # Hapus file setelah dikirim
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        logger.error(f"Error download {url}: {type(e).__name__} - {e}", exc_info=True)
        error_text = str(e)[:250]
        if "facebook" in error_text.lower() and "cannot parse data" in error_text.lower():
            await wait_msg.edit_text("❌ Gagal download dari Facebook.\n"
                                    "Link ini mungkin privat atau Facebook baru-baru ini berubah.\n"
                                    "Coba update yt-dlp ke nightly atau gunakan link lain.")
        elif "File is larger than max-filesize" in error_text or "max_filesize" in error_text:
            await wait_msg.edit_text("❌ Gagal: Ukuran video melebihi batas 50MB (Limit Telegram).")
        else:
            await wait_msg.edit_text(f"❌ Gagal: {error_text}\nCoba link lain.")

def signal_handler(sig, frame):
    print("\n🛑 Menutup bot secara graceful...")
    # Bisa tambahkan cleanup lain kalau perlu
    sys.exit(0)

def build_app():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    return application

def main():
    # Daftarkan signal handler (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    application = build_app()

    print("🤖 Bot sedang berjalan... Tekan Ctrl+C untuk berhenti dengan benar.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()