import os
from dotenv import load_dotenv
from pyrogram import Client

# Load environment variables
load_dotenv()

# Get environment variables
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
log_channel = int(os.getenv('LOG_CHANNEL'))
rapidapi_key = os.getenv("RAPID_API")
PORT = int(os.getenv("PORT", 8000))

# Initialize the bot
espada = Client("movie_caption_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)