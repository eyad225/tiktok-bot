import logging
import os
import re
import requests
import yt_dlp

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN")

logging.basicConfig(level=logging.INFO)

users = set()
user_platform = {}
user_mode = {}

# -------- تنظيف الرابط --------
def clean_url(url):
    match = re.search(r"(https?://[^\s]+)", url)
    return match.group(1) if match else url


# -------- TikTok بدون علامة --------
def download_tiktok(url):
    try:
        api = f"https://www.tikwm.com/api/?url={url}"
        r = requests.get(api).json()

        video_url = r["data"]["play"]
        video = requests.get(video_url).content

        file_name = "tiktok.mp4"
        with open(file_name, "wb") as f:
            f.write(video)

        return file_name
    except:
        return None


# -------- yt-dlp تحميل (محسن) --------
def download_ytdlp(url, audio=False):

    # تحويل روابط youtu.be
    if "youtu.be" in url:
        url = url.replace("youtu.be/", "youtube.com/watch?v=")

    ydl_opts = {
        "outtmpl": "%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
    }

    if not audio:
        ydl_opts["format"] = "bestvideo+bestaudio/best"
        ydl_opts["merge_output_format"] = "mp4"
    else:
        ydl_opts["format"] = "bestaudio"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file = ydl.prepare_filename(info)

        if not audio:
            if not file.endswith(".mp4"):
                file = file.rsplit(".", 1)[0] + ".mp4"
        else:
            file = file.rsplit(".", 1)[0] + ".mp3"

        return file


# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    users.add(update.effective_user.id)

    text = f"""
👋 أهلاً بيك يا {name} 🛡

🎬 بوت تحميل الفيديوهات
━━━━━━━━━━━━━━━

⚡ يدعم:
• TikTok بدون علامة  
• YouTube فيديو + صوت  
• Instagram  

━━━━━━━━━━━━━━━
💙 برعاية إياد
"""

    keyboard = [
        [InlineKeyboardButton("🎵 TikTok", callback_data="tiktok"),
         InlineKeyboardButton("▶️ YouTube", callback_data="youtube")],
        [InlineKeyboardButton("📸 Instagram", callback_data="instagram")],
        [InlineKeyboardButton("🎧 تحميل صوت", callback_data="audio")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")]
    ]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# -------- الأزرار --------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_id = q.from_user.id

    if q.data in ["tiktok", "youtube", "instagram"]:
        user_platform[user_id] = q.data

        keyboard = [
            [InlineKeyboardButton("🎬 فيديو", callback_data="video"),
             InlineKeyboardButton("🎧 صوت", callback_data="audio_mode")]
        ]

        await q.edit_message_text("🎯 اختر النوع:")
        await q.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

    elif q.data == "video":
        user_mode[user_id] = "video"
        await q.edit_message_text("📎 ابعت الرابط")

    elif q.data == "audio_mode":
        user_mode[user_id] = "audio"
        await q.edit_message_text("📎 ابعت الرابط")

    elif q.data == "stats":
        await q.edit_message_text(f"👥 المستخدمين: {len(users)}")


# -------- استقبال الرابط --------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = clean_url(update.message.text)

    msg = await update.message.reply_text("⏳ جاري التحميل...")

    try:
        # TikTok
        if user_platform.get(user_id) == "tiktok":
            file = download_tiktok(url)

        # باقي المنصات
        else:
            file = download_ytdlp(url, audio=(user_mode.get(user_id) == "audio"))

        if not file:
            raise Exception("Download failed")

        await msg.edit_text("📤 جاري الإرسال...")

        with open(file, "rb") as f:
            if file.endswith(".mp3"):
                await update.message.reply_audio(f)
            else:
                await update.message.reply_video(f)

        os.remove(file)

    except Exception as e:
        print(e)
        await msg.edit_text("❌ حصل خطأ أثناء التحميل")


# -------- MAIN --------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.run_polling()


if __name__ == "__main__":
    main()
