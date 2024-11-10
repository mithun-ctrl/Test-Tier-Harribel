from dotenv import load_dotenv
import os
load_dotenv()

main_channel = os.getenv("MAIN_CHANNEL")
support_channel = os.getenv("SUPPORT_CHANNEL")

START_TEXT = """Welcome to Movie Caption Bot! 🎬

I can help you create beautiful captions for movies with automatic poster fetching."""

ABOUT_TEXT = (
    "🤖 ᴄᴀᴘᴛɪᴏɴ ᴍᴀᴋᴇʀ\n\n"
    "📝 ℑ𝔫𝔣𝔬𝔯𝔪𝔞𝔱𝔦𝔬𝔫:\n"
    "├ ɴᴀᴍᴇ:  ᴛɪᴇʀ ʜᴀʀʀɪʙᴇʟ‌\n"
    "├ ʀᴀɴᴋ: ᴇsᴘᴀᴅᴀ ɴᴏ.𝟹\n"
    "├ ʟᴀɴɢᴜᴀɢᴇ: [ᴘʏᴛʜᴏɴ](https://www.python.org)\n"
    "├ ʟɪʙʀᴀʀʏ: [ᴘʏʀᴏɢʀᴀᴍ](https://pytba.readthedocs.io/en/latest/)\n"
    "└ ᴄʀᴇᴀᴛᴏʀ: [ᴍɪᴛʜᴜɴ](https://t.me/mithun_naam_toh_suna_hoga)\n")

HELP_TEXT = """🔍 **Available Commands:**

• /start - Start the bot
• /caption [movie name] - Get movie poster with caption

**How to use:**
1. Just send /caption followed by movie name
2. Wait for the bot to fetch details
3. Get your poster with formatted caption!"""

SUPPORT_TEXT = f"""**Join Our Channels:**

• @{main_channel} - Main Channel
• @{support_channel} - Support Channel

Join us for updates and support!"""