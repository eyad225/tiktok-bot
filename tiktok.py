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

user_platform = {}

# ---------------- تنظيف الرابط ----------------
def clean_url(url):
    match = re.search(r"(https?://[^\s]+)", url)
    return match.group(1) if match else url


# ---------------- تحميل TikTok بدون علامة ----------------
def download_tiktok(url):
    try:
        api = f"https://tikwm.com/api/?url={url}"
        res = requests.get(api).json()

        video_url = res["data"]["play"]

        video_data = requests.get(video_url).content

        with open("tiktok.mp4", "wb") as f:
            f.write(video_data)

        return "tiktok.mp4"

    except Exception as e:
        print("TikTok ERROR:", e)
        return None


# ---------------- تحميل باقي المنصات ----------------
def download_video(url):
    ydl_opts = {
        "format": "best",
        "outtmpl": "video.%(ext)s",
        "quiet": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        print("YTDLP ERROR:", e)
        return None


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name

    keyboard = [
        [
            InlineKeyboardButton("🎵 TikTok", callback_data="tiktok"),
            InlineKeyboardButton("▶️ YouTube", callback_data="youtube"),
        ],
        [
            InlineKeyboardButton("📸 Instagram", callback_data="instagram"),
        ],
    ]

    await update.message.reply_text(
        f"👋 أهلاً بيك يا {name} 🛡\n\n"
        "🎬 بوت تحميل الفيديوهات\n"
        "━━━━━━━━━━━━━━━\n"
        "⚡ يدعم:\n"
        "• TikTok (بدون علامة مائية)\n"
        "• YouTube\n"
        "• Instagram\n\n"
        "📌 اختار المنصة الأول 👇\n"
        "وبعدها ابعت الرابط\n\n"
        "💙 برعاية إياد",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ---------------- اختيار المنصة ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_platform[query.from_user.id] = query.data

    await query.edit_message_text(
        f"✅ اخترت {query.data.upper()}\n\n📎 ابعت الرابط الآن"
    )


# ---------------- استقبال الرابط ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_platform:
        await update.message.reply_text("❗ اختار المنصة الأول من /start")
        return

    url = clean_url(update.message.text)
    platform = user_platform[user_id]

    msg = await update.message.reply_text("⏳ جاري التحميل...")

    try:
        if platform == "tiktok":
            file_path = download_tiktok(url)
        else:
            file_path = download_video(url)

        if file_path and os.path.exists(file_path):

            await msg.edit_text("📤 جاري الإرسال...")

            with open(file_path, "rb") as video:
                await update.message.reply_video(video)

            os.remove(file_path)

        else:
            await msg.edit_text("❌ فشل التحميل")

    except Exception as e:
        print(e)
        await msg.edit_text("❌ حصل خطأ")


# ---------------- MAIN ----------------
def main():
    if not TOKEN:
        raise ValueError("TOKEN is missing!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🤖 Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
