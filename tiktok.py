import logging
import os
import re
import requests
import yt_dlp
import random

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
user_mode = {}
user_quality = {}

# ---------------- تنظيف الرابط ----------------
def clean_url(url):
    match = re.search(r"(https?://[^\s]+)", url)
    return match.group(1) if match else url


# ---------------- جلب دعاء من الإنترنت ----------------
def get_duaa():
    try:
        url = "https://api.aladhan.com/v1/adhkar"
        res = requests.get(url, timeout=10).json()

        if res.get("data"):
            all_duas = []

            for category in res["data"]:
                for item in res["data"][category]:
                    all_duas.append(item.get("text"))

            return random.choice(all_duas)

    except:
        pass

    return "اللهم ارزقنا الخير كله 🤲"


# ---------------- TikTok بدون علامة ----------------
def download_tiktok(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        api = f"https://tikwm.com/api/?url={url}"
        r = requests.get(api, headers=headers, timeout=10).json()
        if r.get("data") and r["data"].get("play"):
            data = requests.get(r["data"]["play"], headers=headers).content
            with open("tiktok.mp4", "wb") as f:
                f.write(data)
            return "tiktok.mp4"
    except:
        pass

    try:
        api = f"https://api.tiklydown.eu.org/api/download?url={url}"
        r = requests.get(api, headers=headers, timeout=10).json()
        if r.get("video"):
            data = requests.get(r["video"], headers=headers).content
            with open("tiktok.mp4", "wb") as f:
                f.write(data)
            return "tiktok.mp4"
    except:
        pass

    try:
        api = f"https://ttdownloader.com/req/?url={url}"
        r = requests.get(api, headers=headers, timeout=10)
        links = re.findall(r'href="(https://[^"]+)"', r.text)
        if links:
            data = requests.get(links[0], headers=headers).content
            with open("tiktok.mp4", "wb") as f:
                f.write(data)
            return "tiktok.mp4"
    except:
        pass

    try:
        ydl_opts = {
            "format": "best",
            "outtmpl": "tiktok.%(ext)s",
            "quiet": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except:
        pass

    return None


# ---------------- فيديو ----------------
def download_video(url, quality="best"):
    if quality == "360":
        fmt = "best[height<=360]"
    elif quality == "720":
        fmt = "best[height<=720]"
    elif quality == "1080":
        fmt = "best[height<=1080]"
    else:
        fmt = "best"

    ydl_opts = {
        "format": fmt,
        "outtmpl": "%(title)s.%(ext)s",
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except:
        return None


# ---------------- صوت ----------------
def download_audio(url):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "%(title)s.%(ext)s",
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            filename = os.path.splitext(filename)[0] + ".mp3"
        return filename
    except:
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
        [
            InlineKeyboardButton("📿 أدعية", callback_data="duaa"),
        ],
        [
            InlineKeyboardButton("ℹ️ معلومات", callback_data="about"),
            InlineKeyboardButton("🧑‍💻 المطور", callback_data="dev"),
        ],
    ]

    await update.message.reply_text(
        f"👋 أهلاً بيك يا {name} 🛡\n\n"
        "🎬 بوت تحميل الفيديوهات\n"
        "━━━━━━━━━━━━━━━\n"
        "⚡ يدعم:\n"
        "• TikTok (بدون علامة 🔥)\n"
        "• YouTube\n"
        "• Instagram\n\n"
        "📌 اختار من تحت 👇\n\n"
        "💙 برعاية إياد",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ---------------- أزرار إضافية ----------------
async def extra_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "duaa":
        doa = get_duaa()
        keyboard = [
            [InlineKeyboardButton("🔄 دعاء آخر", callback_data="duaa")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
        ]

        await query.edit_message_text(
            f"📿 دعاء:\n\n{doa}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "about":
        await query.edit_message_text("🤖 بوت تحميل فيديوهات احترافي")

    elif query.data == "dev":
        await query.edit_message_text("🧑‍💻 المطور: إياد 💙")

    elif query.data == "back":
        return await start(update, context)


# ---------------- اختيار المنصة ----------------
async def choose_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_platform[query.from_user.id] = query.data

    keyboard = [
        [InlineKeyboardButton("🎬 فيديو", callback_data="video")],
        [InlineKeyboardButton("🎧 صوت", callback_data="audio")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")],
    ]

    await query.edit_message_text(
        f"✅ اخترت {query.data.upper()}\n\n🎯 اختر النوع:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ---------------- اختيار النوع ----------------
async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "back":
        return await start(update, context)

    user_mode[user_id] = query.data

    if query.data == "video":
        keyboard = [
            [
                InlineKeyboardButton("360p", callback_data="360"),
                InlineKeyboardButton("720p", callback_data="720"),
                InlineKeyboardButton("1080p", callback_data="1080"),
            ],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back")],
        ]

        await query.edit_message_text(
            "🎥 اختر الجودة:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        await query.edit_message_text("📎 ابعت الرابط الآن")


# ---------------- اختيار الجودة ----------------
async def choose_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "back":
        return await start(update, context)

    user_quality[user_id] = query.data
    await query.edit_message_text("📎 ابعت الرابط الآن")


# ---------------- HANDLE ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_platform or user_id not in user_mode:
        await update.message.reply_text("❗ ابدأ بـ /start الأول")
        return

    url = clean_url(update.message.text)
    platform = user_platform[user_id]
    mode = user_mode[user_id]
    quality = user_quality.get(user_id, "best")

    msg = await update.message.reply_text("⏳ جاري التحميل...")

    try:
        if platform == "tiktok" and mode == "video":
            file_path = download_tiktok(url)
        elif mode == "audio":
            file_path = download_audio(url)
        else:
            file_path = download_video(url, quality)

        if file_path and os.path.exists(file_path):
            await msg.edit_text("📤 جاري الإرسال...")

            with open(file_path, "rb") as f:
                if mode == "audio":
                    await update.message.reply_audio(f)
                else:
                    await update.message.reply_video(f)

            os.remove(file_path)
        else:
            await msg.edit_text("❌ فشل التحميل")

    except Exception as e:
        print(e)
        await msg.edit_text("❌ حصل خطأ")


# ---------------- MAIN ----------------
def main():
    if not TOKEN:
        raise ValueError("TOKEN missing!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(extra_buttons, pattern="^(duaa|about|dev|back)$"))
    app.add_handler(CallbackQueryHandler(choose_platform, pattern="^(tiktok|youtube|instagram)$"))
    app.add_handler(CallbackQueryHandler(choose_mode, pattern="^(video|audio|back)$"))
    app.add_handler(CallbackQueryHandler(choose_quality, pattern="^(360|720|1080|back)$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🤖 Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
