# 📸 Instagram Reels to YouTube Shorts Bot 🤖

This bot automatically downloads your Instagram Reels and uploads them to YouTube Shorts with trending audio, thumbnails, and custom metadata — all hands-free!

---

## 🚀 Features

- Scrapes your Instagram Reels using saved cookies
- Downloads reels using `yt-dlp`
- Mixes in **muted trending audio** using `moviepy`
- Uploads to YouTube via **YouTube Data API**
- Adds title, description, thumbnail, location
- Rate-limited (every 30–35 mins) to avoid quota issues
- Fully automatable + Docker-ready

---

## 🔧 Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/YOUR_USERNAME/instagram-youtube-upload-bot.git
   cd instagram-youtube-upload-bot

2. Install dependencies
    pip install -r requirements.txt

3. Add required files
    client_secret.json (for YouTube API)

    instagram_cookies.pkl (exported cookies)

4. Run the bot
    python your_script_name.py
🔒 Auth Notes
Use save_instagram_cookies.py to store your login cookies

YouTube auth handled via token.pickle

🐳 Docker Support
Coming soon — dockerize the bot and run it in the cloud!

🙌 Credits
Built with ❤️ using selenium, yt_dlp, moviepy, Pillow, and Google API.

📜 License
MIT
