from datetime import datetime
import pytz
import psutil
import time
import os
import git
import platform
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

class Stats:
    def __init__(self, client):
        self.start_time = time.time()
        self.client = client
        self.repo = git.Repo(search_parent_directories=True)
        self.ist_tz = pytz.timezone('Asia/Kolkata')
        
    def get_readable_time(self, seconds: int) -> str:
        """Convert seconds into human readable format"""
        result = ""
        time_dict = {
            "days": seconds // (24 * 3600),
            "hours": (seconds % (24 * 3600)) // 3600,
            "minutes": (seconds % 3600) // 60,
            "seconds": seconds % 60
        }
        
        for unit, value in time_dict.items():
            if value > 0:
                result += f"{value} {unit} " if value > 1 else f"{value} {unit[:-1]} "
                
        return result.strip() or "0 seconds"

    def get_ist_time(self, timestamp):
        """Convert timestamp to IST datetime"""
        utc_dt = datetime.fromtimestamp(timestamp).replace(tzinfo=pytz.UTC)
        ist_dt = utc_dt.astimezone(self.ist_tz)
        return ist_dt
    
    def get_size(self, bytes_value):
        """Get size in readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0

    async def get_bot_users(self):
        """Get total number of bot users"""
        try:
            # You should implement this based on how you store user data
            # This is just a placeholder
            return "Coming soon"
        except Exception as e:
            return "Error counting users"

    async def get_stats(self) -> str:
        """Get all stats in formatted string"""
        try:
            # System Info
            cpu_usage = psutil.cpu_percent()
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Bot Info
            bot_uptime = self.get_readable_time(int(time.time() - self.start_time))
            python_version = platform.python_version()
            pyrogram_version = "2.0.106"  # Update this based on your pyrogram version
            
            # Git Info
            last_commit = self.repo.head.commit
            commit_date = self.get_ist_time(last_commit.committed_date)
            time_since_commit = self.get_readable_time(int(time.time() - last_commit.committed_date))
            
            # Current Time in IST
            current_time = self.get_ist_time(time.time())
            
            # Get total users
            total_users = await self.get_bot_users()
            
            # Format stats message
            stats_text = f"""
╭─❰ 𝗕𝗢𝗧 𝗦𝗧𝗔𝗧𝗜𝗦𝗧𝗜𝗖𝗦 ❱
├・ **Server Time:** `{current_time.strftime('%I:%M:%S %p IST')}`
├・ **Date:** `{current_time.strftime('%d %B, %Y')}`
├・ **Bot Uptime:** `{bot_uptime}`
├・ **Total Users:** `{total_users}`
│
├─❰ 𝗟𝗔𝗦𝗧 𝗨𝗣𝗗𝗔𝗧𝗘 ❱
├・ **Last Commit:** 
├  `{commit_date.strftime('%d %B, %Y')}`
├  `{commit_date.strftime('%I:%M:%S %p IST')}`
├・ **Time Since Update:**
├  `{time_since_commit}`
│
├─❰ 𝗦𝗬𝗦𝗧𝗘𝗠 𝗦𝗧𝗔𝗧𝗦 ❱
├・ **CPU Usage:** `{cpu_usage}%`
├・ **RAM Usage:** `{ram.percent}%`
├・ **Storage Used:** `{disk.percent}%`
├・ **Total Memory:** `{self.get_size(ram.total)}`
├・ **Used Memory:** `{self.get_size(ram.used)}`
├・ **Total Storage:** `{self.get_size(disk.total)}`
│
├─❰ 𝗦𝗢𝗙𝗧𝗪𝗔𝗥𝗘 𝗜𝗡𝗙𝗢 ❱
├・ **Python:** `{python_version}`
├・ **Pyrogram:** `{pyrogram_version}`
├・ **Bot Memory:** `{self.get_size(psutil.Process().memory_info().rss)}`
│
├─❰ 𝗖𝗢𝗠𝗠𝗜𝗧 𝗗𝗘𝗧𝗔𝗜𝗟𝗦 ❱
├・ **Last Commit Message:**
╰ `{last_commit.message.strip()}`

**⌚️ Last Updated:** `{current_time.strftime('%I:%M:%S %p IST')}`
"""
            return stats_text
            
        except Exception as e:
            return f"❌ Error getting stats: {str(e)}"

    async def handle_stats_command(self, message: Message):
        """Handle the /stats command"""
        try:
            # Send "Getting stats..." message with loading animation
            loading_text = "Getting Statistics"
            status_message = await message.reply_text(loading_text)
            
            # Animate loading message
            for _ in range(3):
                for dots in ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]:
                    await status_message.edit_text(f"{loading_text} {dots}")
                    await asyncio.sleep(0.3)
            
            # Get formatted stats
            stats_text = await self.get_stats()
            
            # Create keyboard
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("♻️ Refresh", callback_data="refresh_stats"),
                    InlineKeyboardButton("🏠 Home", callback_data="home")
                ]
            ])
            
            # Edit message with stats
            await status_message.edit_text(
                text=stats_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            await message.reply_text("❌ Error fetching stats. Please try again later.")
            print(f"Stats command error: {str(e)}")

    async def refresh_stats(self, callback_query):
        """Refresh stats for callback query"""
        try:
            # Get new stats
            stats_text = await self.get_stats()
            
            # Update keyboard
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("♻️ Refresh", callback_data="refresh_stats"),
                    InlineKeyboardButton("🏠 Home", callback_data="home")
                ]
            ])
            
            # Edit message with new stats
            await callback_query.message.edit_text(
                text=stats_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
            await callback_query.answer("Statistics refreshed!")
            
        except Exception as e:
            print(f"Error refreshing stats: {str(e)}")
            await callback_query.answer("Error refreshing stats!", show_alert=True)