from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pyrogram import Client
from pyrogram.types import Message, CallbackQuery
import json
import secrets
import os
from plugins.logs import Logger

class WebhookHandler:
    def __init__(self, bot: Client, logger: Logger):
        """Initialize webhook handler with bot instance and logger"""
        self.app = FastAPI(title="Movie Caption Bot")
        self.bot = bot
        self.logger = logger
        
        # Configure webhook settings
        self.port = int(os.getenv("PORT", 8000))  # Ensure PORT is set in environment
        self.railway_url = "https://captionbot.up.railway.app"
        self.secret_token = "b9e22537af1d9b9687541b850d68a2413f2c45af708b7ab3ff53d7380375ca23"
        self.webhook_path = f"/webhook/{self.secret_token}"
        self.webhook_url = f"{self.railway_url}{self.webhook_path}"
        
        # Setup routes
        self.setup_routes()
        
    def setup_routes(self):
        """Setup FastAPI routes"""
        @self.app.get("/")
        async def root():
            return {"status": "alive", "message": "Bot is running"}
            
        @self.app.post(self.webhook_path)
        async def webhook_handler(request: Request):
            return await self.handle_webhook(request)
            
        @self.app.on_event("startup")
        async def startup_event():
            await self.on_startup()
            
        @self.app.on_event("shutdown")
        async def shutdown_event():
            await self.on_shutdown()
            
    async def on_startup(self):
        """Handle startup events"""
        try:
            # Instead of set_webhook, we'll log the startup
            print(f"Bot started successfully!")
            print(f"Webhook URL: {self.webhook_url}")
            
            await self.logger.log_message(
                action="Bot Startup",
                user_id=0,
                username="System",
                chat_id=int(os.getenv('LOG_CHANNEL', 0)),  # Ensure LOG_CHANNEL is set
                error="Bot started with webhook configuration"
            )
        except Exception as e:
            print(f"Startup error: {str(e)}")
            await self.logger.log_message(
                action="Startup Error",
                user_id=0,
                username="System",
                chat_id=int(os.getenv('LOG_CHANNEL', 0)),
                error=str(e)
            )
            
    async def on_shutdown(self):
        """Handle shutdown events"""
        try:
            # Remove webhook-specific method calls
            print("Bot shutdown process initiated")
        except Exception as e:
            print(f"Shutdown error: {str(e)}")
            
    async def handle_webhook(self, request: Request):
        """Process incoming webhook updates"""
        try:
            # Verify secret token if needed
            if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != self.secret_token:
                return JSONResponse(status_code=403, content={"error": "Unauthorized"})
            
            data = await request.json()
            update = json.loads(json.dumps(data))
            
            async with self.bot:
                if "message" in update:
                    message = Message._parse(self.bot, update["message"])
                    await self.handle_message(message)
                elif "callback_query" in update:
                    callback_query = CallbackQuery._parse(self.bot, update["callback_query"])
                    await self.handle_callback(callback_query)
            
            return JSONResponse(status_code=200, content={"status": "success"})
        except Exception as e:
            print(f"Webhook error: {str(e)}")
            await self.logger.log_message(
                action="Webhook Error",
                user_id=0,
                username="System",
                chat_id=int(os.getenv('LOG_CHANNEL', 0)),
                error=str(e)
            )
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            )
            
    async def handle_message(self, message: Message):
        """Route messages to appropriate handlers"""
        from main import start_command, caption_command, series_command, default_response
        
        try:
            if message.command:
                command = message.command[0].lower()
                if command == "start":              
                    await start_command(self.bot, message)
                elif command in ["captionm", "cm"]:
                    await caption_command(self.bot, message)
                elif command in ["captions", "cs"]:
                    await series_command(self.bot, message)
                else:
                    await default_response(self.bot, message)
            else:
                await default_response(self.bot, message)
                
        except Exception as e:
            print(f"Message handling error: {str(e)}")
            await message.reply_text("An error occurred while processing your request.")
            await self.logger.log_message(
                action="Message Handler Error",
                user_id=message.from_user.id if message.from_user else 0,
                username=message.from_user.username if message.from_user else "Unknown",
                chat_id=message.chat.id,
                error=str(e)
            )
            
    async def handle_callback(self, callback_query: CallbackQuery):
        """Route callback queries to appropriate handlers"""
        from main import process_title_selection, callback_query as handle_menu_callback
        
        try:
            if callback_query.data.startswith("title_"):
                imdb_id = callback_query.data.split("_")[1]
                await process_title_selection(callback_query, imdb_id)
            else:
                await handle_menu_callback(self.bot, callback_query)
                
        except Exception as e:
            print(f"Callback handling error: {str(e)}")
            await callback_query.answer("An error occurred. Please try again.")
            await self.logger.log_message(
                action="Callback Handler Error",
                user_id=callback_query.from_user.id,
                username=callback_query.from_user.username,
                chat_id=callback_query.message.chat.id,
                error=str(e)
            )
