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

# تخزين اختيار المستخدم
user_platform = {}

# ------------------- START -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name

    text = f"""👋 أهلاً بيك يا {user_name} 

🎬 بوت تحميل الفيديوهات
━━━━━━━━━━━━━━━
⚡ يدعم:

• TikTok
• YouTube
• Instagram

📌 اختار المنصة الأول 👇
وبعدها ابعت رابط الفيديو

💙 برعاية إياد"""

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
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ------------------- BUTTON -------------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_platform[query.from_user.id] = query.data

    await query.edit_message_text(
        f"✅ اخترت {query.data.upper()}\n\n📎 ابعت رابط الفيديو الآن"
    )

# ------------------- DOWNLOAD -------------------
def download_video(url):
    ydl_opts = {
        "format": "best",
        "outtmpl": "video.%(ext)s",
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# ------------------- HANDLE -------------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text

    if user_id not in user_platform:
        await update.message.reply_text("❗ اختار المنصة الأول من /start")
        return

    # رسالة جاري التحميل
    loading_msg = await update.message.reply_text("⏳ جاري التحميل...")

    try:
        video_path = download_video(url)

        # تعديل الرسالة بدل حذفها
        await loading_msg.edit_text("📤 جاري إرسال الفيديو...")

        # إرسال الفيديو
        await update.message.reply_video(video=open(video_path, "rb"))

        # حذف الملف بعد الإرسال
        os.remove(video_path)

    except Exception as e:
        await loading_msg.edit_text("❌ حصل خطأ أثناء التحميل")

# ------------------- MAIN -------------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.run_polling()

if __name__ == "__main__":
    main()
