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


# -------- تحميل المستخدمين --------
def load_users():
    if os.path.exists("users.json"):
        with open("users.json") as f:
            return set(json.load(f))
    return set()

def save_users():
    with open("users.json", "w") as f:
        json.dump(list(users), f)

users = load_users()


# -------- تنظيف الرابط --------
def clean_url(url):
    match = re.search(r"(https?://[^\s]+)", url)
    return match.group(1) if match else url


# -------- تحميل TikTok --------
def download_tiktok(url):

    if url in cache and os.path.exists(cache[url]):
        return cache[url]

    apis = []

    apis.append(lambda: requests.get(
        f"https://www.tikwm.com/api/?url={url}", timeout=10
    ).json()["data"]["play"])

    apis.append(lambda: re.search(
        r'href="(https://[^"]+mp4)"',
        requests.get(f"https://snaptik.app/abc2.php?url={url}", timeout=10).text
    ).group(1))

    def tikmate():
        r = requests.get(
            f"https://api.tikmate.app/api/lookup?url={url}", timeout=10
        ).json()
        return f"https://tikmate.app/download/{r['token']}/{r['id']}.mp4"

    apis.append(tikmate)

    for _ in range(2):
        for api in apis:
            try:
                video_url = api()
                video = requests.get(video_url, timeout=10).content

                file_name = f"{hash(url)}.mp4"
                with open(file_name, "wb") as f:
                    f.write(video)

                cache[url] = file_name
                return file_name

            except:
                continue

    return None


# -------- تحويل إلى MP3 بنفس الاسم --------
def convert_to_mp3(video_file):
    audio_file = video_file.replace(".mp4", ".mp3")

    subprocess.run([
        "ffmpeg", "-i", video_file,
        "-vn", "-ab", "192k",
        audio_file
    ])

    return audio_file


# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name

    users.add(update.effective_user.id)
    save_users()

    text = f"""
👋 أهلاً بيك يا {name} 🛡

🎬 بوت تحميل TikTok
━━━━━━━━━━━━━━━

⚡ المميزات:
• بدون علامة مائية 🔥  
• الصوت بنفس اسم الفيديو 🎧  
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


# -------- CANCEL --------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_mode.pop(update.effective_user.id, None)
    await update.message.reply_text("❌ تم إلغاء العملية")


# -------- STATS --------
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"""
📊 إحصائيات البوت:

👥 المستخدمين: {len(users)}
📥 التحميلات: {downloads_count}

💙 برعاية إياد
""")


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
        await q.edit_message_text(f"""
📊 إحصائيات البوت:

👥 المستخدمين: {len(users)}
📥 التحميلات: {downloads_count}
""")


# -------- استقبال الرابط --------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global downloads_count

    user_id = update.effective_user.id
    url = clean_url(update.message.text)

    msg = await update.message.reply_text("⏳ جاري التحميل...")

    try:
        video_file = download_tiktok(url)

        if not video_file:
            raise Exception("fail")

        downloads_count += 1

        await msg.edit_text("📤 جاري المعالجة...")

        # لو صوت
        if user_mode.get(user_id) == "audio":
            audio_file = convert_to_mp3(video_file)

            await msg.edit_text("📤 جاري إرسال الصوت...")

            with open(audio_file, "rb") as f:
                await update.message.reply_audio(f)

            os.remove(audio_file)

        else:
            await msg.edit_text("📤 جاري إرسال الفيديو...")

            with open(video_file, "rb") as f:
                await update.message.reply_video(f)

        os.remove(video_file)

        await msg.edit_text("✅ تم التحميل بنجاح 🎉")

    except Exception as e:
        print(e)
        await msg.edit_text("❌ حصل خطأ أثناء التحميل")


# -------- أوامر البوت --------
async def set_commands(app):
    commands = [
        BotCommand("start", "تشغيل البوت"),
        BotCommand("cancel", "إلغاء العملية"),
        BotCommand("stats", "إحصائيات البوت"),
    ]
    await app.bot.set_my_commands(commands)


# -------- MAIN --------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("stats", stats))

    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.post_init = set_commands

    app.run_polling()


if __name__ == "__main__":
    main()
