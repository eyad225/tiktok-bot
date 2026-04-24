import logging
import os
import re
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

# تخزين روابط المستخدمين
user_links = {}

# تنظيف الرابط
def clean_url(url):
    match = re.search(r"(https?://[^\s]+)", url)
    return match.group(1) if match else url


# تحميل الفيديو
def download_video(url):
    ydl_opts = {
        "outtmpl": "video.%(ext)s",
        "format": "best[ext=mp4]",
        "quiet": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        return filename
    except Exception as e:
        print("ERROR:", e)
        return None


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name

    await update.message.reply_text(
        f"👋 أهلاً بيك يا {name}\n\n"
        "🎬 بوت تحميل الفيديوهات\n"
        "برعاية ( إياد ) 💙\n\n"
        "📥 ابعت رابط الفيديو وأنا أخليك تختار المنصة 👇"
    )


# استقبال اللينك
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = clean_url(update.message.text)

    user_links[update.effective_user.id] = url

    keyboard = [
        [
            InlineKeyboardButton("🎵 TikTok", callback_data="tiktok"),
            InlineKeyboardButton("▶️ YouTube", callback_data="youtube"),
        ],
        [
            InlineKeyboardButton("📸 Instagram", callback_data="instagram")
        ],
    ]

    await update.message.reply_text(
        "اختر المنصة 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# الأزرار
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    url = user_links.get(user_id)

    if not url:
        await query.message.reply_text("❌ ابعت الرابط الأول")
        return

    await query.message.reply_text("⏳ جاري التحميل...")

    file_path = download_video(url)

    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "rb") as video:
                await query.message.reply_video(video)

            os.remove(file_path)

        except Exception as e:
            print(e)
            await query.message.reply_text("❌ خطأ في الإرسال")

    else:
        await query.message.reply_text("❌ فشل التحميل")


# تشغيل البوت
def main():
    if not TOKEN:
        raise ValueError("TOKEN is missing!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.add_handler(CallbackQueryHandler(button))

    print("🤖 Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
