import logging
import os
import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import yt_dlp

TOKEN = "8582326537:AAEIqaGuU24vekRPFqZnHSV9mS6CczJu_xw"

logging.basicConfig(level=logging.INFO)

# تنظيف الرابط
def clean_url(url):
    match = re.search(r"(https://www\.tiktok\.com/@[\w\.-]+/video/\d+)", url)
    return match.group(1) if match else url

# تحميل الفيديو
def download_video(url):
    ydl_opts = {
        "outtmpl": "video_%(id)s.%(ext)s",
        "format": "mp4",
        "quiet": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0"
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# زرار القائمة
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 تحميل فيديو", callback_data="download")]
    ])

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بيك في بوت تحميل الفيديوهات 🎬\n\n"
        "برعاية ( إياد ) 💙\n\n"
        "📥 تقدر تحمّل فيديوهات TikTok بدون علامة مائية\n"
        "⚡ بسرعة عالية وبجودة ممتازة\n\n"
        "اضغط على الزرار وابدأ 👇",
        reply_markup=main_menu()
    )

# التعامل مع الأزرار
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "download":
        await query.message.reply_text("📎 ابعت لينك TikTok")

# استقبال اللينك
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "tiktok.com" not in text:
        await update.message.reply_text("❌ ابعت لينك TikTok صحيح")
        return

    msg = await update.message.reply_text("⏳ جاري التحميل...")

    try:
        url = clean_url(text)
        loop = asyncio.get_event_loop()
        file = await loop.run_in_executor(None, download_video, url)

        if not os.path.exists(file):
            await msg.edit_text("❌ فشل التحميل")
            return

        with open(file, "rb") as video:
            await update.message.reply_video(video=video)

        os.remove(file)

        await update.message.reply_text(
            "✅ تم التحميل بنجاح",
            reply_markup=main_menu()
        )

        await msg.delete()

    except Exception as e:
        print(e)
        await msg.edit_text("⚠️ حصل خطأ")

# تشغيل البوت
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("🤖 Bot running...")
app.run_polling()