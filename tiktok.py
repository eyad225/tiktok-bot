import logging
import os
import re
import requests

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
user_mode = {}

# -------- تنظيف الرابط --------
def clean_url(url):
    match = re.search(r"(https?://[^\s]+)", url)
    return match.group(1) if match else url


# -------- TikTok بدون علامة (3 APIs) --------
def download_tiktok(url):

    # -------- 1. TikWM --------
    try:
        api = f"https://www.tikwm.com/api/?url={url}"
        r = requests.get(api, timeout=10).json()

        video_url = r["data"]["play"]
        video = requests.get(video_url, timeout=10).content

        with open("tiktok.mp4", "wb") as f:
            f.write(video)

        return "tiktok.mp4"
    except:
        pass

    # -------- 2. SnapTik --------
    try:
        api = f"https://snaptik.app/abc2.php?url={url}"
        r = requests.get(api, timeout=10).text

        video_url = re.search(r'href="(https://[^"]+mp4)"', r)
        if video_url:
            video = requests.get(video_url.group(1), timeout=10).content

            with open("tiktok.mp4", "wb") as f:
                f.write(video)

            return "tiktok.mp4"
    except:
        pass

    # -------- 3. TikMate --------
    try:
        api = f"https://api.tikmate.app/api/lookup?url={url}"
        r = requests.get(api, timeout=10).json()

        video_url = f"https://tikmate.app/download/{r['token']}/{r['id']}.mp4"
        video = requests.get(video_url, timeout=10).content

        with open("tiktok.mp4", "wb") as f:
            f.write(video)

        return "tiktok.mp4"
    except:
        pass

    return None


# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    users.add(update.effective_user.id)

    text = f"""
👋 أهلاً بيك يا {name} 

🎬 بوت تحميل TikTok
━━━━━━━━━━━━━━━

⚡ المميزات:
• تحميل بدون علامة مائية 🔥  
• نظام قوي (3 مصادر)  
• سرعة عالية  

━━━━━━━━━━━━━━━
💙 برعاية إياد
"""

    keyboard = [
        [InlineKeyboardButton("🎬 فيديو", callback_data="video"),
         InlineKeyboardButton("🎧 صوت", callback_data="audio")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")]
    ]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# -------- الأزرار --------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_id = q.from_user.id

    if q.data == "video":
        user_mode[user_id] = "video"
        await q.edit_message_text("📎 ابعت رابط TikTok")

    elif q.data == "audio":
        user_mode[user_id] = "audio"
        await q.edit_message_text("📎 ابعت رابط TikTok")

    elif q.data == "stats":
        await q.edit_message_text(f"👥 المستخدمين: {len(users)}")


# -------- استقبال الرابط --------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = clean_url(update.message.text)

    msg = await update.message.reply_text("⏳ جاري التحميل...")

    try:
        file = download_tiktok(url)

        if not file:
            raise Exception("Download failed")

        await msg.edit_text("📤 جاري الإرسال...")

        with open(file, "rb") as f:
            if user_mode.get(user_id) == "audio":
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
