# Telegram Media Downloader Bot

Bot Telegram berbasis Python untuk mengunduh media (video/audio/foto) dari berbagai platform seperti YouTube, Instagram, TikTok, X (Twitter), dan Facebook menggunakan kekuatan `yt-dlp`.

## Fitur Utama
- **Multi-Platform:** Mendukung pengunduhan dari ratusan situs populer.
- **Vercel & Serverless Ready:** Menggunakan direktori `/tmp` untuk penyimpanan sementara file dengan penamaan UUID untuk mencegah tabrakan data (Concurrency Race Condition).
- **Non-Blocking Download:** Menggunakan `asyncio.to_thread` sehingga bot tidak *freeze* atau tertahan saat ada beberapa user yang mengunduh file secara bersamaan.
- **Auto-Limit 50MB:** Memiliki batasan ukuran file 50MB di level scraping agar sesuai dengan standar API gratis Telegram. Membantu menghindari error dan pemborosan RAM (OOM) di Vercel.
- **Dukungan Cookies Cerdas:** Akan mendeteksi file `cookies.txt` secara otomatis jika diletakkan di root direktori. Sangat berguna untuk mengunduh konten privat dari Instagram atau Facebook.

## Persyaratan Sistem
- Python 3.9 atau yang lebih baru.
- uv (Opsional, direkomendasikan untuk manajemen dependensi super cepat).
- Token Bot Telegram (Dapatkan dari @BotFather di aplikasi Telegram).

## Instalasi & Menjalankan secara Lokal

1. **Clone repositori ini:**
   ```bash
   git clone <URL_REPO_ANDA>
   cd Bot_Downloader
   ```

2. **Atur Environment Variables:**
   Buat file bernama `.env` di root direktori dan tambahkan token bot Anda:
   ```env
   TELEGRAM_BOT_TOKEN=masukkan_token_bot_anda_di_sini
   ```

3. **Instal dependensi:**
   Jika menggunakan `uv` (Direkomendasikan):
   ```bash
   uv sync
   ```
   Atau jika menggunakan `pip` bawaan:
   ```bash
   pip install python-telegram-bot[job-queue] python-dotenv yt-dlp
   ```

4. **Jalankan Bot:**
   ```bash
   python media_downloader_bot.py
   ```
   Bot akan melakukan *polling* dan mencetak log di terminal. Silakan kirimkan link video ke bot Anda di Telegram!

## Penggunaan `cookies.txt` (Opsional)
Beberapa platform memblokir permintaan tak dikenal atau mewajibkan login (seperti Instagram). Untuk mengatasi hal ini:
1. Ekspor cookies dari browser web PC Anda. Anda bisa menggunakan ekstensi browser seperti *Get cookies.txt LOCALLY* (Chrome/Edge/Firefox).
2. Simpan file hasil ekspor tersebut dengan nama persis `cookies.txt` di folder root bot (bersebelahan dengan `media_downloader_bot.py`).
3. Jalankan bot. Konfigurasi `yt-dlp` akan otomatis membaca file tersebut dan masuk (login) layaknya browser PC Anda.

## Catatan untuk Deployment Vercel (Serverless)
Bot ini telah direfaktor untuk mendukung skema *Serverless*. Fungsi utama telah dibungkus ke dalam `build_app()`. 
Karena platform seperti Vercel tidak mengizinkan skrip berjalan terus-menerus (`run_polling()`), Anda perlu menambahkan *Endpoint Webhook* terpisah (misalnya di folder `api/`) yang berfungsi untuk meneruskan request (POST) dari server Telegram ke fungsi `build_app()` bot ini.
