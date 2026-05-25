import os
import sys
from fastapi import FastAPI, Request
from telegram import Update

# Tambahkan folder root ke sys.path agar media_downloader_bot.py bisa diimpor dari folder api/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from media_downloader_bot import build_app

app = FastAPI()
bot_app = build_app()
_is_initialized = False

async def init_bot():
    global _is_initialized
    if not _is_initialized:
        await bot_app.initialize()
        _is_initialized = True

# Menangkap semua request (POST) dari Webhook Telegram
@app.post("/{full_path:path}")
async def webhook(request: Request):
    await init_bot()
    update_dict = await request.json()
    update = Update.de_json(update_dict, bot_app.bot)
    
    # Proses update via Application python-telegram-bot
    await bot_app.process_update(update)
    return {"status": "ok"}

# Pengecekan status saat diakses melalui browser
@app.get("/{full_path:path}")
def index():
    return {"status": "Telegram Media Downloader Bot is running on Vercel Serverless!"}