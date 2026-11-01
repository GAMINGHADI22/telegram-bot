import os
import glob
import time
import html
import json
import asyncio
import requests
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8954438065:AAFsDQAd4B7n3q948z8we44eQfLkQ_t0_uk")

STATS_FILE = "stats.json"
BOT_START_TIME = time.time()

FAST_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "concurrent_fragment_downloads": 16,
    "retries": 5,
    "fragment_retries": 5,
    "socket_timeout": 15,
    "http_headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    }
}

def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"total_downloads": 0, "users": []}

def save_stats(stats):
    try:
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f)
    except Exception:
        pass

def increment_downloads(user_id):
    stats = load_stats()
    stats["total_downloads"] = stats.get("total_downloads", 0) + 1
    if "users" not in stats:
        stats["users"] = []
    if user_id not in stats["users"]:
        stats["users"].append(user_id)
    save_stats(stats)

def format_number(num):
    if not num:
        return "N/A"
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    if num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)

def format_duration(seconds):
    if not seconds:
        return "N/A"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def file_size_mb(path):
    if os.path.exists(path):
        return round(os.path.getsize(path) / (1024 * 1024), 2)
    return 0.0

def fetch_tikwm_data(url):
    try:
        api = "https://www.tikwm.com/api/?url=" + requests.utils.quote(url, safe='')
        res = requests.get(api, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        data = res.json()
        if data.get("code") == 0 and "data" in data:
            return data["data"]
    except Exception as e:
        print(f"TikWM fetch error: {e}")
    return None

def is_supported_url(url):
    valid_domains = ["youtube.com", "youtu.be", "tiktok.com", "instagram.com", "instagr.am", "facebook.com", "fb.watch", "fb.com"]
    return any(domain in url.lower() for domain in valid_domains)

def get_platform_badge(url):
    url_lower = url.lower()
    if "tiktok.com" in url_lower:
        return "🎵 <b>TIKTOK</b>"
    elif "youtube.com" in url_lower or "youtu.be" in url_lower:
        if "shorts" in url_lower:
            return "⚡ <b>YOUTUBE SHORTS</b>"
        return "🎥 <b>YOUTUBE</b>"
    elif "instagram.com" in url_lower or "instagr.am" in url_lower:
        return "📸 <b>INSTAGRAM</b>"
    elif "facebook.com" in url_lower or "fb.watch" in url_lower or "fb.com" in url_lower:
        return "📘 <b>FACEBOOK</b>"
    return "🎬 <b>MEDIA</b>"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "✨ <b>──────────────────────────────</b> ✨\n"
        "👑 <b>ADMIN RAHMAN ULTRA DOWNLOADER</b> 👑\n"
        "✨ <b>──────────────────────────────</b> ✨\n\n"
        "💎 <b>Welcome to the Ultimate Media Downloader!</b>\n\n"
        "🎬 <b>Supported Platforms:</b>\n"
        "  • 🎥 <b>YouTube</b> — Videos, Shorts, MP3\n"
        "  • 🎵 <b>TikTok</b> — No-Watermark Video & Photo Albums\n"
        "  • 📸 <b>Instagram</b> — Reels, Posts & IGTV\n"
        "  • 📘 <b>Facebook</b> — Public Videos & Reels\n"
        "  • 🎧 <b>Audio Extractor</b> — High Quality 320k MP3\n\n"
        "💡 <b>Quick Commands:</b>\n"
        "  • /help — How to use\n"
        "  • /stats — Live bot statistics\n"
        "  • /about — Bot Information\n\n"
        "💜 <i>Send any media link below to begin!</i> 👇"
    )
    await update.message.reply_text(welcome_text, parse_mode="HTML")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 <b>ADMIN RAHMAN DOWNLOADER HELP</b>\n"
        "✨ <b>──────────────────────────────</b> ✨\n\n"
        "💡 <b>How to use:</b>\n"
        " 1. Copy any video or photo link from YouTube, TikTok, Instagram, or Facebook.\n"
        " 2. Paste the link into this chat.\n"
        " 3. Click your desired quality button (1080p, 720p, MP3, etc.).\n"
        " 4. Receive your media file instantly!\n\n"
        "🎬 <b>Supported Sites:</b>\n"
        " • <b>YouTube:</b> Videos, Shorts, Audio Extraction\n"
        " • <b>TikTok:</b> Videos (No Watermark), Photo Slideshows, Music\n"
        " • <b>Instagram:</b> Reels, Posts & IGTV Videos\n"
        " • <b>Facebook:</b> Public Videos & Reels\n\n"
        "❓ <b>Commands:</b> /start, /help, /stats, /about"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = load_stats()
    uptime_sec = int(time.time() - BOT_START_TIME)
    h, remainder = divmod(uptime_sec, 3600)
    m, s = divmod(remainder, 60)
    
    text = (
        "📊 <b>BOT SYSTEM STATISTICS</b>\n"
        "✨ <b>──────────────────────────────</b> ✨\n\n"
        f"💾 <b>Total Downloads Served:</b> <code>{stats.get('total_downloads', 0)}</code>\n"
        f"👥 <b>Total Unique Users:</b> <code>{len(stats.get('users', []))}</code>\n"
        f"⏱ <b>System Uptime:</b> <code>{h}h {m}m {s}s</code>\n"
        f"⚡ <b>Server Engine:</b> <b>100% Online & Fast</b>\n\n"
        "💜 <i>ADMIN RAHMAN BOT SYSTEM</i>"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def about_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "👑 <b>ABOUT ADMIN RAHMAN BOT</b>\n"
        "✨ <b>──────────────────────────────</b> ✨\n\n"
        "🚀 <b>Version:</b> <code>v3.5 Ultra Max</code>\n"
        "⚡ <b>Engine:</b> <code>Python Telegram API + TikWM + YT-DLP</code>\n"
        "👤 <b>Developer:</b> <b>ADMIN RAHMAN</b>\n"
        "🛡 <b>Features:</b> High-Speed Multi-Platform Media Downloader\n\n"
        "💜 <i>Thank you for using our bot!</i>"
    )
    await update.message.reply_text(about_text, parse_mode="HTML")

async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not is_supported_url(url):
        await update.message.reply_text(
            "❌ <b>Unsupported Link!</b>\n\nPlease send a valid URL from <b>YouTube, TikTok, Instagram, or Facebook</b>.",
            parse_mode="HTML"
        )
        return

    context.user_data["url"] = url
    context.user_data["tikwm_data"] = None

    status_msg = await update.message.reply_text("⚡ <code>Analyzing link... Please wait</code>", parse_mode="HTML")

    is_tiktok = "tiktok.com" in url.lower()
    badge = get_platform_badge(url)

    # TIKTOK PATH
    if is_tiktok:
        tik_data = await asyncio.to_thread(fetch_tikwm_data, url)
        if tik_data:
            context.user_data["tikwm_data"] = tik_data
            images = tik_data.get("images", [])
            raw_title = tik_data.get("title", "TikTok Content")
            title = html.escape(raw_title)
            duration = tik_data.get("duration", 0)
            cover = tik_data.get("cover")
            author = html.escape(tik_data.get("author", {}).get("nickname", "TikTok User"))
            views = format_number(tik_data.get("play_count"))
            likes = format_number(tik_data.get("digg_count"))

            context.user_data["title"] = raw_title

            if images:
                # TikTok Photo Album
                buttons = [
                    [InlineKeyboardButton("📸 Download HD Photo Album", callback_data="photo")],
                    [InlineKeyboardButton("🎧 Background Music (MP3)", callback_data="mp3")],
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ]
                caption = (
                    f"╭━━━━━━━〔 {badge} 〕━━━━━━━╮\n\n"
                    f"📌 <b>Title:</b> <code>{title[:50]}</code>\n"
                    f"👤 <b>Author:</b> <b>{author}</b>\n"
                    f"🖼 <b>Photos Count:</b> <b>{len(images)} HD Images</b>\n\n"
                    "╰─────────────────────────────────────╯\n"
                    "👇 <b>Choose an action below:</b>"
                )
                await status_msg.delete()
                if cover:
                    await update.message.reply_photo(photo=cover, caption=caption, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))
                else:
                    await update.message.reply_text(caption, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))
                return
            else:
                # TikTok Video
                buttons = [
                    [InlineKeyboardButton("🔥 HD Video (No Watermark)", callback_data="tiktok_video")],
                    [InlineKeyboardButton("🎧 Original MP3 Audio", callback_data="mp3")],
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ]
                caption = (
                    f"╭━━━━━━━〔 {badge} 〕━━━━━━━╮\n\n"
                    f"📌 <b>Title:</b> <code>{title[:50]}</code>\n"
                    f"👤 <b>Author:</b> <b>{author}</b>\n"
                    f"📊 <b>Stats:</b> 👁 <b>{views}</b> views • ❤️ <b>{likes}</b> likes\n"
                    f"⏱ <b>Duration:</b> <code>{format_duration(duration)}</code>\n\n"
                    "╰──────────────────────────────────╯\n"
                    "👇 <b>Select download format:</b>"
                )
                await status_msg.delete()
                if cover:
                    await update.message.reply_photo(photo=cover, caption=caption, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))
                else:
                    await update.message.reply_text(caption, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))
                return

    # GENERAL PATH (YouTube, Instagram, Facebook, Fallback)
    try:
        def extract_info():
            with yt_dlp.YoutubeDL({**FAST_OPTS, "extract_flat": False}) as ydl:
                return ydl.extract_info(url, download=False)
        
        data = await asyncio.to_thread(extract_info)

        raw_title = data.get("title", "Media Content")
        title = html.escape(raw_title)
        duration = data.get("duration", 0)
        thumbnail = data.get("thumbnail")
        uploader = html.escape(data.get("uploader", data.get("extractor", "Creator")))
        views = format_number(data.get("view_count"))

        context.user_data["title"] = raw_title

        buttons = [
            [
                InlineKeyboardButton("💜 1080p Ultra HD", callback_data="1080"),
                InlineKeyboardButton("⚡ 720p HD", callback_data="720")
            ],
            [
                InlineKeyboardButton("🔮 360p Fast", callback_data="360"),
                InlineKeyboardButton("🎧 MP3 Audio 320k", callback_data="mp3")
            ],
            [
                InlineKeyboardButton("❌ Close", callback_data="close")
            ]
        ]

        caption = (
            f"╭━━━━━━━〔 {badge} 〕━━━━━━━╮\n\n"
            f"📌 <b>Title:</b> <code>{title[:50]}</code>\n"
            f"👤 <b>Creator:</b> <b>{uploader}</b>\n"
            f"📊 <b>Stats:</b> 👁 <b>{views}</b> views • ⏱ <code>{format_duration(duration)}</code>\n\n"
            "╰──────────────────────────────────╯\n"
            "👇 <b>Choose video/audio quality:</b>"
        )

        await status_msg.delete()

        if thumbnail:
            await update.message.reply_photo(
                photo=thumbnail,
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await update.message.reply_text(
                caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Fetch Failed!</b>\n\nError: <code>{html.escape(str(e)[:120])}</code>", parse_mode="HTML")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    choice = q.data
    user_id = q.from_user.id

    if choice == "close":
        try:
            await q.message.delete()
        except Exception:
            pass
        return

    url = context.user_data.get("url")
    raw_title = context.user_data.get("title", "Media File")
    title = html.escape(raw_title)
    tik_data = context.user_data.get("tikwm_data")

    # PHOTO ALBUM
    if choice == "photo":
        status_msg = await q.message.reply_text("⚡ <code>Fetching HD Photo Album...</code>", parse_mode="HTML")
        try:
            images = []
            if tik_data:
                images = tik_data.get("images", [])
            if not images and url:
                td = await asyncio.to_thread(fetch_tikwm_data, url)
                if td:
                    images = td.get("images", [])

            if not images:
                await status_msg.edit_text("❌ <b>No photos found for this post!</b>", parse_mode="HTML")
                return

            await status_msg.edit_text(f"📥 <code>Uploading {len(images)} HD photos...</code>", parse_mode="HTML")

            chunks = [images[i:i + 10] for i in range(0, len(images[:20]), 10)]
            for chunk in chunks:
                media = [InputMediaPhoto(media=img_url) for img_url in chunk]
                await q.message.reply_media_group(media=media)

            increment_downloads(user_id)

            await status_msg.edit_text(
                "✨ <b>──────────────────────────────</b> ✨\n"
                "✅ <b>PHOTO ALBUM DELIVERED!</b>\n"
                "✨ <b>──────────────────────────────</b> ✨\n\n"
                f"📸 <b>Total Images:</b> <code>{len(images)}</code> Photos\n"
                "💜 <i>Powered by ADMIN RAHMAN BOT</i>",
                parse_mode="HTML"
            )
            return

        except Exception as e:
            await status_msg.edit_text(f"❌ <b>Photo Download Failed:</b> <code>{html.escape(str(e)[:120])}</code>", parse_mode="HTML")
            return

    # TIKTOK DIRECT VIDEO
    if choice == "tiktok_video" or ("tiktok.com" in (url or "") and tik_data and choice != "mp3"):
        status_msg = await q.message.reply_text("🚀 <code>Downloading Watermark-Free HD Video...</code>", parse_mode="HTML")
        start_t = time.time()
        try:
            os.makedirs("downloads", exist_ok=True)
            video_url = tik_data.get("play") or tik_data.get("wmplay") if tik_data else None
            
            if not video_url and url:
                tik_data = await asyncio.to_thread(fetch_tikwm_data, url)
                if tik_data:
                    video_url = tik_data.get("play") or tik_data.get("wmplay")

            if video_url:
                out_path = os.path.join("downloads", f"tiktok_{int(time.time())}.mp4")
                
                resp = await asyncio.to_thread(requests.get, video_url, stream=True, timeout=25)
                with open(out_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=16384):
                        if chunk:
                            f.write(chunk)
                
                await status_msg.edit_text("📤 <code>Uploading to Telegram...</code>", parse_mode="HTML")
                size = file_size_mb(out_path)
                elapsed = round(time.time() - start_t, 1)

                with open(out_path, "rb") as f:
                    await q.message.reply_video(
                        video=f,
                        caption=(
                            "✨ <b>──────────────────────────────</b> ✨\n"
                            "✅ <b>DOWNLOAD COMPLETE!</b>\n"
                            "✨ <b>──────────────────────────────</b> ✨\n\n"
                            f"🎬 <b>Title:</b> <code>{title[:35]}</code>\n"
                            "📺 <b>Quality:</b> <b>No-Watermark HD</b>\n"
                            f"💾 <b>Size:</b> <code>{size} MB</code>  │  ⚡ <b>Speed:</b> <code>{elapsed}s</code>\n\n"
                            "💜 <i>Powered by ADMIN RAHMAN BOT</i>"
                        ),
                        parse_mode="HTML"
                    )
                increment_downloads(user_id)
                try:
                    os.remove(out_path)
                except Exception:
                    pass
                await status_msg.delete()
                return
        except Exception as e:
            print(f"Direct TikTok failed, falling back to yt_dlp: {e}")

    # GENERAL DOWNLOAD
    quality_name = {
        "1080": "1080p Ultra HD",
        "720": "720p HD",
        "360": "360p Fast",
        "mp3": "MP3 Audio (320k)",
        "tiktok_video": "HD Video"
    }.get(choice, "HD Video")

    status_msg = await q.message.reply_text(f"⚡ <code>Downloading {quality_name}... Please wait</code>", parse_mode="HTML")
    start_t = time.time()

    try:
        os.makedirs("downloads", exist_ok=True)
        for old in glob.glob("downloads/*"):
            try:
                os.remove(old)
            except Exception:
                pass

        base_opts = {
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "noplaylist": True,
            **FAST_OPTS
        }

        is_tiktok = "tiktok.com" in (url or "")

        # TIKTOK DIRECT AUDIO
        if choice == "mp3" and is_tiktok and tik_data and tik_data.get("music"):
            try:
                music_url = tik_data.get("music")
                out_path = os.path.join("downloads", f"audio_{int(time.time())}.mp3")
                resp = await asyncio.to_thread(requests.get, music_url, stream=True, timeout=25)
                with open(out_path, "wb") as f:
                    for chunk in resp.iter_content(16384):
                        f.write(chunk)
                
                size = file_size_mb(out_path)
                elapsed = round(time.time() - start_t, 1)

                with open(out_path, "rb") as f:
                    await q.message.reply_audio(
                        audio=f,
                        caption=(
                            "✨ <b>──────────────────────────────</b> ✨\n"
                            "🎧 <b>AUDIO EXTRACTION COMPLETE!</b>\n"
                            "✨ <b>──────────────────────────────</b> ✨\n\n"
                            f"🎵 <b>Track:</b> <code>{title[:35]}</code>\n"
                            f"💾 <b>Size:</b> <code>{size} MB</code>  │  ⚡ <b>Speed:</b> <code>{elapsed}s</code>\n\n"
                            "💜 <i>Powered by ADMIN RAHMAN BOT</i>"
                        ),
                        parse_mode="HTML"
                    )
                increment_downloads(user_id)
                try:
                    os.remove(out_path)
                except Exception:
                    pass
                await status_msg.delete()
                return
            except Exception as ex:
                print(f"Direct audio failed, falling back to yt_dlp: {ex}")

        # YT_DLP DOWNLOAD
        if choice == "mp3":
            ydl_opts = {
                **base_opts,
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                }],
            }
        elif is_tiktok:
            ydl_opts = {**base_opts, "format": "best/bestvideo+bestaudio"}
        elif choice == "1080":
            ydl_opts = {**base_opts, "format": "bestvideo[height<=1080]+bestaudio/best"}
        elif choice == "720":
            ydl_opts = {**base_opts, "format": "bestvideo[height<=720]+bestaudio/best"}
        else:
            ydl_opts = {**base_opts, "format": "bestvideo[height<=360]+bestaudio/best"}

        def download_media():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        file = await asyncio.to_thread(download_media)

        await status_msg.edit_text("📤 <code>Uploading file to Telegram...</code>", parse_mode="HTML")

        elapsed = round(time.time() - start_t, 1)

        if choice == "mp3":
            base, _ = os.path.splitext(file)
            mp3_file = base + ".mp3"
            if os.path.exists(mp3_file):
                file = mp3_file
            
            size = file_size_mb(file)

            with open(file, "rb") as f:
                await q.message.reply_audio(
                    audio=f,
                    caption=(
                        "✨ <b>──────────────────────────────</b> ✨\n"
                        "🎧 <b>AUDIO EXTRACTION COMPLETE!</b>\n"
                        "✨ <b>──────────────────────────────</b> ✨\n\n"
                        f"🎵 <b>Track:</b> <code>{title[:35]}</code>\n"
                        f"💾 <b>Size:</b> <code>{size} MB</code>  │  ⚡ <b>Speed:</b> <code>{elapsed}s</code>\n\n"
                        "💜 <i>Powered by ADMIN RAHMAN BOT</i>"
                    ),
                    parse_mode="HTML"
                )
        else:
            size = file_size_mb(file)

            with open(file, "rb") as f:
                await q.message.reply_video(
                    video=f,
                    caption=(
                        "✨ <b>──────────────────────────────</b> ✨\n"
                        "✅ <b>DOWNLOAD COMPLETE!</b>\n"
                        "✨ <b>──────────────────────────────</b> ✨\n\n"
                        f"🎬 <b>Title:</b> <code>{title[:35]}</code>\n"
                        f"📺 <b>Quality:</b> <b>{quality_name}</b>\n"
                        f"💾 <b>Size:</b> <code>{size} MB</code>  │  ⚡ <b>Speed:</b> <code>{elapsed}s</code>\n\n"
                        "💜 <i>Powered by ADMIN RAHMAN BOT</i>"
                    ),
                    parse_mode="HTML"
                )

        increment_downloads(user_id)

        for fpath in glob.glob("downloads/*"):
            try:
                os.remove(fpath)
            except Exception:
                pass

        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Download Failed!</b>\n\nError: <code>{html.escape(str(e)[:180])}</code>", parse_mode="HTML")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("about", about_cmd))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, link_handler))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("⚡ ADMIN RAHMAN ULTRA MAX DOWNLOADER RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()