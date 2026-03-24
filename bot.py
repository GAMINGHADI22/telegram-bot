import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

TOKEN = os.getenv("TOKEN")

# TikTok no watermark
def download_tiktok(url):
    api = f"https://tikwm.com/api/?url={url}"
    res = requests.get(api).json()

    if res.get("data"):
        video_url = res["data"]["play"]
        title = res["data"]["title"]
        file = "tiktok.mp4"

        video = requests.get(video_url).content
        with open(file, "wb") as f:
            f.write(video)

        return file, title
    return None, None


# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send TikTok / YouTube link 📥")


# Message
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    keyboard = [
        [InlineKeyboardButton("🎬 720p", callback_data=f"720|{url}")],
        [InlineKeyboardButton("🎬 1080p", callback_data=f"1080|{url}")],
        [InlineKeyboardButton("🎵 Audio", callback_data=f"audio|{url}")]
    ]

    await update.message.reply_text("Choose quality 👇", reply_markup=InlineKeyboardMarkup(keyboard))


# Button click
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    mode, url = query.data.split("|")
    msg = await query.message.reply_text("Starting... ⏳")

    try:
        # TikTok
        if "tiktok.com" in url:
            file, title = download_tiktok(url)
            if file:
                await msg.edit_text("Uploading... 📤")
                await query.message.reply_video(video=open(file, "rb"), caption=title)
                os.remove(file)
            return

        # Progress hook
        def progress_hook(d):
            if d['status'] == 'downloading':
                try:
                    percent = d.get('_percent_str', '')
                    context.bot.edit_message_text(
                        chat_id=msg.chat_id,
                        message_id=msg.message_id,
                        text=f"Downloading... {percent}"
                    )
                except:
                    pass

        # Format select
        if mode == "720":
            fmt = "bestvideo[height<=720]+bestaudio/best[height<=720]"
        elif mode == "1080":
            fmt = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
        else:
            fmt = "bestaudio"

        ydl_opts = {
            'outtmpl': 'file.%(ext)s',
            'format': fmt,
            'progress_hooks': [progress_hook],
        }

        # Audio convert
        if mode == "audio":
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "Downloaded")

        await msg.edit_text("Uploading... 📤")

        for file in os.listdir():
            if file.startswith("file"):
                if mode == "audio":
                    await query.message.reply_audio(audio=open(file, "rb"), title=title)
                else:
                    await query.message.reply_video(video=open(file, "rb"), caption=title)
                os.remove(file)

    except Exception as e:
        await msg.edit_text("Failed 😢")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(button_click))

print("🚀 Bot Running...")
app.run_polling()
