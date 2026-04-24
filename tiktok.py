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

# تخزين المنصة لكل مستخدم
user_platform = {}

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
        f"👋 أهلاً بيك يا {name} 🛡️\n\n"
        "🎬 بوت تحميل الفيديوهات\n"
        "━━━━━━━━━━━━━━━\n"
        "⚡ يدعم:\n"
        "• TikTok\n"
        "• YouTube\n"
        "• Instagram\n\n"
        "📌 اختار المنصة الأول 👇\n"
        "وبعدها ابعت رابط الفيديو\n\n"
        "💙 برعاية إياد",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# اختيار المنصة
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    platform = query.data

    user_platform[user_id] = platform

    await query.message.reply_text(
        f"📥 ابعت رابط الفيديو من {platform.upper()} الآن"
    )


# استقبال الرابط
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    platform = user_platform.get(user_id)

    if not platform:
        await update.message.reply_text("❌ اختار المنصة الأول")
        return

    url = clean_url(update.message.text)

    await update.message.reply_text("⏳ جاري التحميل...")

    file_path = download_video(url)

    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "rb") as video:
                await update.message.reply_video(video)

            os.remove(file_path)

        except Exception as e:
            print(e)
            await update.message.reply_text("❌ خطأ أثناء الإرسال")

    else:
        await update.message.reply_text("❌ فشل التحميل")


# تشغيل البوت
def main():
    if not TOKEN:
        raise ValueError("TOKEN is missing!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
