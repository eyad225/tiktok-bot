import logging
import os
import re
import requests
import json
import subprocess

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand
)
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

user_mode = {}
cache = {}
downloads_count = 0


# -------- USERS --------
def load_users():
    if os.path.exists("users.json"):
        with open("users.json") as f:
            return set(json.load(f))
    return set()

def save_users():
    with open("users.json", "w") as f:
        json.dump(list(users), f)

users = load_users()


# -------- API STATS --------
api_stats = {
    "api1": {"success": 0, "fail": 0},
    "api2": {"success": 0, "fail": 0},
    "api3": {"success": 0, "fail": 0},
}

def load_api_stats():
    global api_stats
    if os.path.exists("api_stats.json"):
        with open("api_stats.json") as f:
            api_stats = json.load(f)

def save_api_stats():
    with open("api_stats.json", "w") as f:
        json.dump(api_stats, f)

load_api_stats()


# -------- KEYBOARD --------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 فيديو", callback_data="video"),
         InlineKeyboardButton("🎧 صوت", callback_data="audio")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")]
    ])


# -------- HELPERS --------
def sanitize_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name[:80]

def clean_url(url):
    match = re.search(r"(https?://[^\s]+)", url)
    return match.group(1) if match else url

def get_sorted_apis(apis):
    return sorted(
        apis,
        key=lambda x: api_stats[x[0]]["success"] - api_stats[x[0]]["fail"],
        reverse=True
    )


# -------- DOWNLOAD --------
def download_tiktok(url):

    if url in cache and os.path.exists(cache[url]):
        return cache[url]

    def api1():
        r = requests.get(f"https://www.tikwm.com/api/?url={url}", timeout=10).json()
        return r["data"]["play"], r["data"].get("title", "tiktok_video")

    def api2():
        html = requests.get(f"https://snaptik.app/abc2.php?url={url}", timeout=10).text
        video_url = re.search(r'href="(https://[^"]+mp4)"', html).group(1)
        return video_url, "tiktok_video"

    def api3():
        r = requests.get(f"https://api.tikmate.app/api/lookup?url={url}", timeout=10).json()
        video_url = f"https://tikmate.app/download/{r['token']}/{r['id']}.mp4"
        return video_url, "tiktok_video"

    apis = [("api1", api1), ("api2", api2), ("api3", api3)]
    sorted_apis = get_sorted_apis(apis)

    for _ in range(2):
        for name, api in sorted_apis:
            try:
                video_url, title = api()

                title = sanitize_filename(title)
                file_name = f"{title}.mp4"

                video = requests.get(video_url, timeout=10).content

                with open(file_name, "wb") as f:
                    f.write(video)

                cache[url] = file_name

                api_stats[name]["success"] += 1
                save_api_stats()

                return file_name

            except:
                api_stats[name]["fail"] += 1
                save_api_stats()

    return None


# -------- AUDIO --------
def convert_to_mp3(video_file):
    audio_file = video_file.replace(".mp4", ".mp3")

    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_file,
            "-vn",
            "-acodec", "libmp3lame",
            "-ab", "192k",
            audio_file
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if not os.path.exists(audio_file):
            raise Exception()

        return audio_file

    except:
        return None


# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name

    users.add(update.effective_user.id)
    save_users()

    text = f"""
👋 أهلاً بيك يا {name} 

🎬 بوت تحميل TikTok
━━━━━━━━━━━━━━━

🔥 بدون علامة مائية  
📂 اسم الفيديو الحقيقي  
🎧 الصوت بنفس الاسم  
🧠 ذكاء اختيار السيرفر  

━━━━━━━━━━━━━━━
💙 برعاية إياد
"""

    await update.message.reply_text(text, reply_markup=main_menu())


# -------- BUTTONS --------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_id = q.from_user.id

    if q.data == "video":
        user_mode[user_id] = "video"
        await q.message.reply_text("📎 ابعت رابط TikTok", reply_markup=main_menu())

    elif q.data == "audio":
        user_mode[user_id] = "audio"
        await q.message.reply_text("📎 ابعت رابط TikTok", reply_markup=main_menu())

    elif q.data == "stats":
        await q.message.reply_text(
            f"📊 الإحصائيات\n\n👥 المستخدمين: {len(users)}\n📥 التحميلات: {downloads_count}",
            reply_markup=main_menu()
        )


# -------- HANDLE --------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global downloads_count

    user_id = update.effective_user.id
    url = clean_url(update.message.text)

    msg = await update.message.reply_text("⏳ جاري التحميل...")

    try:
        video_file = download_tiktok(url)

        if not video_file:
            raise Exception()

        downloads_count += 1

        if user_mode.get(user_id) == "audio":

            await msg.edit_text("🎧 جاري استخراج الصوت...")
            audio_file = convert_to_mp3(video_file)

            if not audio_file:
                await msg.edit_text("❌ مشكلة في الصوت")
                return

            await msg.edit_text("📤 جاري إرسال الصوت...")

            with open(audio_file, "rb") as f:
                await update.message.reply_audio(
                    audio=f,
                    title=os.path.basename(audio_file)
                )

            os.remove(audio_file)

        else:
            await msg.edit_text("📤 جاري إرسال الفيديو...")

            with open(video_file, "rb") as f:
                await update.message.reply_video(f)

        os.remove(video_file)

        await msg.edit_text("✅ تم التحميل بنجاح")

        await update.message.reply_text("اختار تاني 👇", reply_markup=main_menu())

    except:
        await msg.edit_text("❌ حصل خطأ أثناء التحميل")


# -------- COMMANDS --------
async def set_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "تشغيل البوت"),
        BotCommand("stats", "إحصائيات"),
    ])


# -------- MAIN --------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.post_init = set_commands

    app.run_polling()


if __name__ == "__main__":
    main()
