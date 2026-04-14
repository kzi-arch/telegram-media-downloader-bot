import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import yt_dlp

# Load .env file
load_dotenv()

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Ambil token
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("Error: TELEGRAM_BOT_TOKEN tidak ditemukan! Set di file .env atau environment variable.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bot siap!\n\n"
        "Kirim link video, foto, atau audio dari:\n"
        "YouTube, Instagram, TikTok, Twitter/X, Facebook, dll.\n\n"
        "Saya akan download dan kirim balik ke kamu."
    )

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("⚠️ Kirim link yang valid (harus mulai dengan http atau https)")
        return

    wait_msg = await update.message.reply_text("⏳ Sedang mendownload... Mohon tunggu sebentar.")

    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best[height<=720]',
            'outtmpl': '%(title)s.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'ignoreerrors': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
            # Tambahan untuk Instagram (mengurangi warning metadata)
            # 'cookiesfrombrowser': 'firefox',   # Ganti 'firefox' atau 'edge' kalau kamu pakai browser lain
            # 'cookiefile': 'cookies.txt',    # Alternatif: pakai file cookies.txt
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if not os.path.exists(filename):
            await wait_msg.edit_text("❌ Gagal mendownload file. Coba link lain.")
            return

        ext = filename.lower().split('.')[-1]
        caption = f"✅ Berhasil!\nJudul: {info.get('title', 'Unknown')}\nDari: {info.get('extractor_key', 'Unknown')}"

        # Kirim sesuai tipe file
        if ext in ['mp4', 'mkv', 'webm', 'mov']:
            await update.message.reply_video(video=open(filename, 'rb'), caption=caption, supports_streaming=True)
        elif ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
            await update.message.reply_photo(photo=open(filename, 'rb'), caption=caption)
        elif ext in ['mp3', 'm4a', 'wav', 'ogg']:
            await update.message.reply_audio(audio=open(filename, 'rb'), caption=caption)
        else:
            await update.message.reply_document(document=open(filename, 'rb'), caption=caption)

        await wait_msg.delete()  # hapus pesan "sedang mendownload"

        # Hapus file setelah dikirim (hemat storage)
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        logger.error(f"Error download {url}: {e}")
        await wait_msg.edit_text(f"❌ Gagal: {str(e)[:200]}\nCoba lagi atau gunakan link lain.")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))

    print("🤖 Bot sedang berjalan...")
    application.run_polling()

if __name__ == '__main__':
    main()