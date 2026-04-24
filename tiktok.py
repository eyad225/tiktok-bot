import logging
import os
import re
import requests
import yt_dlp
import random
import time

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


# ---------------- نظام الأدعية (تحديث كل ساعة) ----------------
duaa_cache = []
duaa_index = 0
last_update = 0

def fetch_duaa(force=False):
    global duaa_cache, last_update

    # تحديث كل ساعة
    if not force and time.time() - last_update < 3600:
        return

    duaa_cache = []
    last_update = time.time()
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get("https://api.aladhan.com/v1/adhkar", headers=headers, timeout=10).json()
        if res.get("data"):
            for cat in res["data"]:
                for item in res["data"][cat]:
                    if item.get("text"):
                        duaa_cache.append(item["text"])
    except:
        pass

    try:
        res = requests.get("https://hisnmuslim.com/api/ar/husn_ar.json", headers=headers, timeout=10).json()
        for item in res:
            if item.get("ARABIC_TEXT"):
                duaa_cache.append(item["ARABIC_TEXT"])
    except:
        pass

    try:
        html = requests.get("https://www.islambook.com/dua", headers=headers, timeout=10).text
        found = re.findall(r"<p>(.*?)</p>", html)
        for d in found:
            clean = re.sub("<.*?>", "", d)
            if len(clean) > 20:
                duaa_cache.append(clean)
    except:
        pass

    if not duaa_cache:
        duaa_cache = [
            "اللهم ارزقنا الخير كله 🤲",
            "اللهم اغفر لنا وارحمنا ❤️",
            "اللهم اجعلنا من الصالحين 🤍",
        ]

    duaa_cache = list(set(duaa_cache))
    random.shuffle(duaa_cache)


def get_duaa():
    global duaa_cache, duaa_index

    fetch_duaa()  # 👈 هنا السر (يتحدث تلقائي)

    doa = duaa_cache[duaa_index]
    duaa_index = (duaa_index + 1) % len(duaa_cache)

    return doa + f"\n\n✨ {random.randint(1,99999)}"


# ---------------- TikTok بدون علامة ----------------
def download_tiktok(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(f"https://tikwm.com/api/?url={url}", headers=headers).json()
        data = requests.get(r["data"]["play"]).content
        open("tiktok.mp4", "wb").write(data)
        return "tiktok.mp4"
    except:
        pass

    try:
        r = requests.get(f"https://api.tiklydown.eu.org/api/download?url={url}").json()
        data = requests.get(r["video"]).content
        open("tiktok.mp4", "wb").write(data)
        return "tiktok.mp4"
    except:
        pass

    try:
        with yt_dlp.YoutubeDL({"format": "best"}) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except:
        return None


# ---------------- تحميل فيديو ----------------
def download_video(url, quality="best"):
    fmt = {
        "360": "best[height<=360]",
        "720": "best[height<=720]",
        "1080": "best[height<=1080]",
    }.get(quality, "best")

    with yt_dlp.YoutubeDL({"format": fmt, "outtmpl": "%(title)s.%(ext)s"}) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


# ---------------- تحميل صوت ----------------
def download_audio(url):
    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": "%(title)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name

    keyboard = [
        [InlineKeyboardButton("🎵 TikTok", callback_data="tiktok"),
         InlineKeyboardButton("▶️ YouTube", callback_data="youtube")],
        [InlineKeyboardButton("📸 Instagram", callback_data="instagram")],
        [InlineKeyboardButton("📿 أدعية", callback_data="duaa")],
        [InlineKeyboardButton("ℹ️ معلومات", callback_data="about"),
         InlineKeyboardButton("🧑‍💻 المطور", callback_data="dev")]
    ]

    await update.message.reply_text(
        f"👋 أهلاً بيك يا {name} \n\n🎬 بوت تحميل الفيديوهات\n⚡ يدعم TikTok - YouTube - Instagram\n\n📿 يوجد قسم أدعية متجدد\n\n💙 برعاية إياد",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------- أزرار إضافية ----------------
async def extra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "duaa":
        doa = get_duaa()
        kb = [
            [InlineKeyboardButton("🔄 دعاء آخر", callback_data="duaa")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
        ]
        await q.edit_message_text(f"📿 {doa}", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data == "about":
        await q.edit_message_text("🤖 بوت تحميل فيديوهات بدون علامة مائية")

    elif q.data == "dev":
        await q.edit_message_text("🧑‍💻 المطور: إياد 💙")

    elif q.data == "back":
        return await start(update, context)


# ---------------- اختيار المنصة ----------------
async def choose_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_platform[q.from_user.id] = q.data

    kb = [
        [InlineKeyboardButton("🎬 فيديو", callback_data="video")],
        [InlineKeyboardButton("🎧 صوت", callback_data="audio")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
    ]

    await q.edit_message_text("🎯 اختر النوع:", reply_markup=InlineKeyboardMarkup(kb))


# ---------------- اختيار النوع ----------------
async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_mode[q.from_user.id] = q.data

    if q.data == "video":
        kb = [
            [InlineKeyboardButton("360", callback_data="360"),
             InlineKeyboardButton("720", callback_data="720"),
             InlineKeyboardButton("1080", callback_data="1080")]
        ]
        await q.edit_message_text("🎥 اختر الجودة:", reply_markup=InlineKeyboardMarkup(kb))
    else:
        await q.edit_message_text("📎 ابعت الرابط")


# ---------------- الجودة ----------------
async def choose_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_quality[q.from_user.id] = q.data
    await q.edit_message_text("📎 ابعت الرابط")


# ---------------- التعامل مع الرابط ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = clean_url(update.message.text)

    msg = await update.message.reply_text("⏳ جاري التحميل...")

    try:
        if user_mode[user_id] == "audio":
            file = download_audio(url)
        elif user_platform[user_id] == "tiktok":
            file = download_tiktok(url)
        else:
            file = download_video(url, user_quality.get(user_id, "best"))

        await msg.edit_text("📤 جاري الإرسال...")

        with open(file, "rb") as f:
            if user_mode[user_id] == "audio":
                await update.message.reply_audio(f)
            else:
                await update.message.reply_video(f)

        os.remove(file)

    except Exception as e:
        print(e)
        await msg.edit_text("❌ حصل خطأ أثناء التحميل")


# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(extra, pattern="^(duaa|about|dev|back)$"))
    app.add_handler(CallbackQueryHandler(choose_platform, pattern="^(tiktok|youtube|instagram)$"))
    app.add_handler(CallbackQueryHandler(choose_mode, pattern="^(video|audio)$"))
    app.add_handler(CallbackQueryHandler(choose_quality, pattern="^(360|720|1080)$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.run_polling()


if __name__ == "__main__":
    main()
