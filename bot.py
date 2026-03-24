const TelegramBot = require('node-telegram-bot-api');
const { exec } = require('child_process');
const fs = require('fs');

const token = "YOUR_BOT_TOKEN"; // এখানে BotFather token বসাও
const bot = new TelegramBot(token, { polling: true });

// 🔹 Start message
bot.onText(/\/start/, (msg) => {
  bot.sendMessage(msg.chat.id, "📥 Send any TikTok or YouTube link\n🎬 Choose quality (720p / 1080p)\n🎵 Or download audio (MP3)");
});

// 🔹 Message handler
bot.on('message', (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text;

  if (!text) return;

  // Link check
  if (text.includes("tiktok.com") || text.includes("youtube.com") || text.includes("youtu.be")) {

    bot.sendMessage(chatId, "👇 Choose option:", {
      reply_markup: {
        inline_keyboard: [
          [{ text: "🎬 Download 720p", callback_data: `720|${text}` }],
          [{ text: "🎬 Download 1080p", callback_data: `1080|${text}` }],
          [{ text: "🎵 Extract Audio (MP3)", callback_data: `mp3|${text}` }]
        ]
      }
    });

  }
});

// 🔹 Button click handle
bot.on('callback_query', async (query) => {
  const chatId = query.message.chat.id;
  const [type, url] = query.data.split("|");

  const fileName = `file_${Date.now()}`;

  bot.sendMessage(chatId, "⏳ Downloading your file...");

  let command = "";

  if (type === "720") {
    command = `yt-dlp -f "best[height<=720]" -o "${fileName}.mp4" ${url}`;
  } 
  else if (type === "1080") {
    command = `yt-dlp -f "best[height<=1080]" -o "${fileName}.mp4" ${url}`;
  } 
  else if (type === "mp3") {
    command = `yt-dlp -x --audio-format mp3 -o "${fileName}.mp3" ${url}`;
  }

  exec(command, async (err) => {
    if (err) {
      bot.sendMessage(chatId, "❌ Download failed!");
      return;
    }

    try {
      if (type === "mp3") {
        await bot.sendAudio(chatId, `${fileName}.mp3`);
        fs.unlinkSync(`${fileName}.mp3`);
      } else {
        await bot.sendVideo(chatId, `${fileName}.mp4`);
        fs.unlinkSync(`${fileName}.mp4`);
      }
    } catch (e) {
      bot.sendMessage(chatId, "❌ Sending failed!");
    }
  });
});
