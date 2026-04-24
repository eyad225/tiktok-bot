import logging
import os
import re
import asyncio
import time
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import yt_dlp

TOKEN = os.getenv("TOKEN")

logging.basicConfig(level=logging.INFO)

# 📊 تخزين المستخدمين
users = set()

# 🛡️ حماية سبام (كل مستخدم له وقت)
last_request = defaultdict(float)

# تنظيف الرابط
def clean_url(url):
    match = re.search(r"(https://www\.tiktok\.com/@[\w\.-]+/video/\d+)", url)
    return match.group(1) if match else url

# تحميل الفيديو (محسن)
def download_video(url):
    ydl_opts = {
        "outtmpl": "video_%(id)s.%(ext)s",
        "format": "mp4",
        "quiet": True,
        "noplaylist": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0"
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# 🎨 قائمة احترافية
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 تحميل فيديو", callback_data="download")],
        [InlineKeyboardButton("📊 عدد المستخدمين", callback_data="stats")]
    ])

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users.add(user_id)

    await update.message.reply_text(
        "👋 أهلاً بيك في بوت تحميل الفيديوهات 🎬\n\n"
        "برعاية ( إياد ) 💙\n\n"
        "📥 تحميل بدون علامة مائية\n"
        "⚡ سرعة عالية\n\n"
        "اضغط وابدأ 👇",
        reply_markup=main_menu()
    )

# الأزرار
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "download":
        await query.message.reply_text("📎 ابعت لينك TikTok")

    elif query.data == "stats":
        await query.message.reply_text(f"👥 عدد المستخدمين: {len(users)}")

# استقبال اللينك
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # 🛡️ حماية سبام (كل 10 ثواني)
    if time.time() - last_request[user_id] < 10:
        await update.message.reply_text("⏳ استنى شوية قبل ما تبعت تاني")
        return

    last_request[user_id] = time.time()

    if "tiktok.com" not in text:
        await update.message.reply_text("❌ ابعت لينك TikTok صحيح")
        return

    msg = await update.message.reply_text("⏳ جاري التحميل...")

    try:
        url = clean_url(text)

        loop = asyncio.get_running_loop()
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

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
