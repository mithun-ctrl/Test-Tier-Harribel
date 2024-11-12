import time
import datetime
import os
import git
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode

class Stats:
    def __init__(self, client):
        self.client = client
        self.start_time = time.time()
        self.repo = self._get_repo()
        
    def _get_repo(self):
        """Get git repo information if available"""
        try:
            return git.Repo(search_parent_directories=True)
        except:
            return None
            
    def _get_last_commit_info(self):
        """Get the last commit date and time ago"""
        if not self.repo:
            return "N/A", "N/A"
            
        try:
            last_commit = self.repo.head.commit
            last_commit_date = datetime.datetime.fromtimestamp(last_commit.committed_date)
            time_ago = datetime.datetime.now() - last_commit_date
            
            # Format time ago in a human-readable way
            if time_ago.days > 0:
                time_ago_str = f"{time_ago.days} days ago"
            elif time_ago.seconds >= 3600:
                hours = time_ago.seconds // 3600
                time_ago_str = f"{hours} hours ago"
            elif time_ago.seconds >= 60:
                minutes = time_ago.seconds // 60
                time_ago_str = f"{minutes} minutes ago"
            else:
                time_ago_str = f"{time_ago.seconds} seconds ago"
                
            return last_commit_date.strftime("%Y-%m-%d %H:%M:%S"), time_ago_str
        except:
            return "N/A", "N/A"
            
    def _get_uptime(self):
        """Get bot uptime"""
        uptime = int(time.time() - self.start_time)
        days = uptime // (24 * 3600)
        uptime = uptime % (24 * 3600)
        hours = uptime // 3600
        uptime %= 3600
        minutes = uptime // 60
        uptime %= 60
        seconds = uptime
        
        if days > 0:
            return f"{days}d, {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
            
    async def _get_total_users(self):
        """Get total number of users who have started the bot"""
        try:
            # You might want to implement this based on your user tracking mechanism
            # This is just a placeholder that counts messages in the log channel
            messages = []
            async for message in self.client.get_chat_history(os.getenv('LOG_CHANNEL')):
                if "Start Command" in message.text:
                    messages.append(message)
            return len(set(msg.text.split('User ID: ')[1].split('\n')[0] for msg in messages))
        except:
            return 0

    async def handle_stats_command(self, message: Message):
        """Handle the /stats command"""
        # Send loading message
        loading_msg = await message.reply_text("Fetching stats... ⌛")
        
        try:
            # Gather all stats
            last_commit_date, time_ago = self._get_last_commit_info()
            uptime = self._get_uptime()
            total_users = await self._get_total_users()
            
            # Create stats message
            stats_text = f"""
📊 **Bot Statistics**

🔄 **Last Commit:** {last_commit_date}
⏰ **Time Since Commit:** {time_ago}
⚡ **Bot Uptime:** {uptime}
👥 **Total Users:** {total_users}

_Stats last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_
"""
            
            # Create keyboard with refresh button
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh Stats", callback_data="refresh_stats")],
                [InlineKeyboardButton("🏠 Back to Home", callback_data="home")]
            ])
            
            # Edit loading message with stats
            await loading_msg.edit_text(
                stats_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            await loading_msg.edit_text(f"Error fetching stats: {str(e)}")
            
    async def refresh_stats(self, callback_query):
        """Handle refresh stats button press"""
        try:
            # Show loading state
            await callback_query.answer("Refreshing stats...")
            
            # Gather fresh stats
            last_commit_date, time_ago = self._get_last_commit_info()
            uptime = self._get_uptime()
            total_users = await self._get_total_users()
            
            # Update stats message
            stats_text = f"""
📊 **Bot Statistics**

🔄 **Last Commit:** {last_commit_date}
⏰ **Time Since Commit:** {time_ago}
⚡ **Bot Uptime:** {uptime}
👥 **Total Users:** {total_users}

_Stats last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_
"""
            
            # Keep the same keyboard
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh Stats", callback_data="refresh_stats")],
                [InlineKeyboardButton("🏠 Back to Home", callback_data="home")]
            ])
            
            # Update the message
            await callback_query.message.edit_text(
                stats_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            await callback_query.answer(f"Error refreshing stats: {str(e)}", show_alert=True)