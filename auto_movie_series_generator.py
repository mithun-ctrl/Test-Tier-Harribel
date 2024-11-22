import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from typing import Dict, Optional
import aiohttp
from io import BytesIO
from config import target_channel

TARGET_CHANNEL_ID = target_channel

class MovieAutoGenerator:
    def __init__(self, client: Client, search_titles_func, get_title_details_func, format_caption_func):
        # Dependency injection for core functions
        self.client = client
        self.search_titles = search_titles_func
        self.get_title_details = get_title_details_func
        self.format_caption = format_caption_func
        
        # State variables
        self.generation_task: Optional[asyncio.Task] = None
        self.current_condition: Optional[Dict] = None
        self.is_running = False

    async def set_movie_condition(self, message: Message, year: str, max_posts: int = 10, genre: Optional[str] = None):
        """
        Set movie generation conditions
        """
        try:
            # Validate year
            try:
                int(year)  # Ensure it's a valid year
            except ValueError:
                await message.reply_text("Please provide a valid year.")
                return False

            # Store condition
            self.current_condition = {
                "year": year,
                "max_posts": max_posts,
                "genre": genre,
                "target_chat": TARGET_CHANNEL_ID  # Use the global TARGET_CHANNEL_ID
            }

            response = f"Movie auto-generation condition set:\n" \
                       f"Year: {year}\n" \
                       f"Max Posts: {max_posts}\n" \
                       f"Genre: {genre or 'Any'}\n" \
                       f"Target Chat: {TARGET_CHANNEL_ID}"
            
            await message.reply_text(response)
            return True

        except Exception as e:
            await message.reply_text(f"Error setting condition: {str(e)}")
            print(f"Set condition error: {str(e)}")
            return False

    async def start_movie_post_generation(self):
        """
        Background task to generate movie posts based on set conditions
        """
        if not self.current_condition or self.is_running:
            return

        try:
            self.is_running = True
            condition = self.current_condition
            year = condition['year']
            max_posts = condition['max_posts']
            genre = condition.get('genre')
            target_chat = condition['target_chat']

            # Search movies with the specified year and optional genre
            search_query = f"{year} {genre if genre else ''}"
            results = await self.search_titles(search_query)

            # Filter results to match exact year and optional genre
            filtered_results = [
                movie for movie in results 
                if movie['Year'] == year and 
                (not genre or genre.lower() in movie.get('Genre', '').lower())
            ]

            # Limit to max posts
            filtered_results = filtered_results[:max_posts]

            # Process and send each movie
            for movie in filtered_results:
                if not self.is_running:
                    break
                
                await self.process_and_send_movie_post(movie, target_chat)
                
                # Add a delay between posts to avoid flooding
                await asyncio.sleep(5)  # 5 seconds between posts

        except Exception as e:
            print(f"Movie post generation error: {str(e)}")
        finally:
            self.is_running = False

    async def process_and_send_movie_post(self, movie, target_chat):
        """
        Process a single movie and send its post
        """
        try:
            # Fetch detailed movie information
            imdb_id = movie['imdbID']
            title_data = await self.get_title_details(imdb_id)

            if not title_data:
                return

            # Prepare caption
            caption = self.format_caption(
                title_data.get('Title', 'N/A'),
                title_data.get('Year', 'N/A'),
                title_data.get('Language', 'N/A'),
                title_data.get('Language', 'N/A'),
                title_data.get('Genre', 'N/A'),
                title_data.get('imdbRating', 'N/A'),
                title_data.get('Runtime', 'N/A'),
                title_data.get('Rated', 'U/A'),
                title_data.get('Plot', 'N/A')
            )

            # Handle poster
            poster_url = title_data.get('Poster')
            if poster_url and poster_url != 'N/A':
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(poster_url) as response:
                            if response.status == 200:
                                poster_data = await response.read()
                                poster_stream = BytesIO(poster_data)
                                poster_stream.name = f"poster_{imdb_id}.jpg"
                                
                                # Send post with poster
                                await self.client.send_photo(
                                    chat_id=target_chat,
                                    photo=poster_stream,
                                    caption=caption,
                                    parse_mode="markdown"
                                )
                                return
                except Exception as poster_error:
                    print(f"Poster download error: {str(poster_error)}")
            
            # Fallback to text-only if no poster
            await self.client.send_message(
                chat_id=target_chat,
                text=caption,
                parse_mode="markdown"
            )

        except Exception as e:
            print(f"Movie post send error: {str(e)}")

    async def stop_movie_post_generation(self, message: Message):
        """
        Stop the ongoing movie post generation
        """
        if not self.is_running:
            await message.reply_text("Auto movie generation is not currently running.")
            return

        self.is_running = False
        
        if self.generation_task and not self.generation_task.done():
            self.generation_task.cancel()
        
        self.current_condition = None
        await message.reply_text("Auto movie generation stopped.")

    def register_handlers(self):
        """
        Register command handlers for the client
        """
        @self.client.on_message(filters.command(["setautogen"]))
        async def handle_set_auto_gen(client, message):
            """
            Handle setting auto generation conditions
            Usage: /setautogen <year> [max_posts] [genre]
            """
            try:
                parts = message.text.split()
                if len(parts) < 2:
                    await message.reply_text(
                        "Invalid format. Usage:\n"
                        "/setautogen <year> [max_posts] [genre]\n"
                        "Example: /setautogen 2023 5 action"
                    )
                    return

                year = parts[1]
                max_posts = 10  # Default max posts
                genre = None

                if len(parts) > 2 and parts[2].isdigit():
                    max_posts = int(parts[2])
                
                if len(parts) > 3:
                    genre = parts[3]

                # Set condition
                success = await self.set_movie_condition(message, year, max_posts, genre)
                
                if success:
                    # Start generation task
                    self.generation_task = asyncio.create_task(self.start_movie_post_generation())
            
            except Exception as e:
                await message.reply_text(f"Error in auto generation: {str(e)}")
        @self.client.on_message(filters.command(["startautogen"]))
        async def handle_start_auto_gen(client, message):
            """
            Start auto movie generation if conditions are set
            """
            if not self.current_condition:
                await message.reply_text("Please set auto generation conditions first using /setautogen")
                return

            if self.is_running:
                await message.reply_text("Auto movie generation is already running.")
                return

            # Start generation task
            self.generation_task = asyncio.create_task(self.start_movie_post_generation())
            await message.reply_text("Auto movie generation started.")

        @self.client.on_message(filters.command(["statautogen"]))
        async def handle_stat_auto_gen(client, message):
            """
            Get status of auto movie generation
            """
            if not self.current_condition:
                await message.reply_text("No auto generation condition is set.")
                return

            status_text = "Auto Movie Generation Status:\n"
            status_text += f"Year: {self.current_condition['year']}\n"
            status_text += f"Max Posts: {self.current_condition['max_posts']}\n"
            status_text += f"Genre: {self.current_condition.get('genre', 'Any')}\n"
            status_text += f"Target Chat: {self.current_condition['target_chat']}\n"
            status_text += f"Running: {'Yes' if self.is_running else 'No'}"

            await message.reply_text(status_text)

class SeriesAutoGenerator:
    def __init__(self, client: Client, search_titles_func, get_title_details_func, format_series_caption_func):
        # Dependency injection for core functions
        self.client = client
        self.search_titles = search_titles_func
        self.get_title_details = get_title_details_func
        self.format_series_caption = format_series_caption_func
        
        # State variables
        self.generation_task: Optional[asyncio.Task] = None
        self.current_condition: Optional[Dict] = None
        self.is_running = False

    async def set_series_condition(self, message: Message, year: str, max_posts: int = 10, genre: Optional[str] = None):
        """
        Set series generation conditions
        """
        try:
            # Validate year
            try:
                int(year)  # Ensure it's a valid year
            except ValueError:
                await message.reply_text("Please provide a valid year.")
                return False

            # Store condition
            self.current_condition = {
                "year": year,
                "max_posts": max_posts,
                "genre": genre,
                "target_chat": TARGET_CHANNEL_ID  # Use the global TARGET_CHANNEL_ID
            }

            response = f"Series auto-generation condition set:\n" \
                       f"Year: {year}\n" \
                       f"Max Posts: {max_posts}\n" \
                       f"Genre: {genre or 'Any'}\n" \
                       f"Target Chat: {TARGET_CHANNEL_ID}"
            
            await message.reply_text(response)
            return True

        except Exception as e:
            await message.reply_text(f"Error setting condition: {str(e)}")
            print(f"Set condition error: {str(e)}")
            return False

    async def start_series_post_generation(self):
        """
        Background task to generate series posts based on set conditions
        """
        if not self.current_condition or self.is_running:
            return

        try:
            self.is_running = True
            condition = self.current_condition
            year = condition['year']
            max_posts = condition['max_posts']
            genre = condition.get('genre')
            target_chat = condition['target_chat']

            # Search series with the specified year and optional genre
            search_query = f"{year} {genre if genre else ''}"
            results = await self.search_titles(search_query, "series")

            # Filter results to match exact year and optional genre
            filtered_results = [
                series for series in results 
                if series['Year'] == year and 
                (not genre or genre.lower() in series.get('Genre', '').lower())
            ]

            # Limit to max posts
            filtered_results = filtered_results[:max_posts]

            # Process and send each series
            for series in filtered_results:
                if not self.is_running:
                    break
                
                await self.process_and_send_series_post(series, target_chat)
                
                # Add a delay between posts to avoid flooding
                await asyncio.sleep(5)  # 5 seconds between posts

        except Exception as e:
            print(f"Series post generation error: {str(e)}")
        finally:
            self.is_running = False

    async def process_and_send_series_post(self, series, target_chat):
        """
        Process a single series and send its post
        """
        try:
            # Fetch detailed series information
            imdb_id = series['imdbID']
            title_data = await self.get_title_details(imdb_id)

            if not title_data:
                return

            # Prepare additional message
            additional_message = f"""`[PirecyKings2] [Season Episode] {title_data.get('Title', 'N/A')} ({title_data.get('Year', 'N/A')}) @pirecykings2`

`S01 English - Hindi [480p]`

`S01 English - Hindi [720p]`

`S01 English - Hindi [1080p]`"""

            # Prepare caption
            caption = self.format_series_caption(
                title_data.get('Title', 'N/A'),
                title_data.get('Year', 'N/A'),
                title_data.get('Language', 'N/A'),
                title_data.get('Language', 'N/A'),
                title_data.get('Genre', 'N/A'),
                title_data.get('imdbRating', 'N/A'),
                title_data.get('totalSeasons', 'N/A'),
                title_data.get('Type', 'N/A'),
                title_data.get('Plot', 'N/A')
            )

            # Handle poster
            poster_url = title_data.get('Poster')
            if poster_url and poster_url != 'N/A':
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(poster_url) as response:
                            if response.status == 200:
                                poster_data = await response.read()
                                poster_stream = BytesIO(poster_data)
                                poster_stream.name = f"poster_{imdb_id}.jpg"
                                
                                # Send post with poster
                                await self.client.send_photo(
                                    chat_id=target_chat,
                                    photo=poster_stream,
                                    caption=caption,
                                    parse_mode="markdown"
                                )

                                # Send additional message
                                await self.client.send_message(
                                    chat_id=target_chat,
                                    text=additional_message,
                                    parse_mode="markdown"
                                )
                                return
                except Exception as poster_error:
                    print(f"Poster download error: {str(poster_error)}")
            
            # Fallback to text-only if no poster
            await self.client.send_message(
                chat_id=target_chat,
                text=caption,
                parse_mode="markdown"
            )

            # Send additional message
            await self.client.send_message(
                chat_id=target_chat,
                text=additional_message,
                parse_mode="markdown"
            )

        except Exception as e:
            print(f"Series post send error: {str(e)}")

    async def stop_series_post_generation(self, message: Message):
        """
        Stop the ongoing series post generation
        """
        if not self.is_running:
            await message.reply_text("Auto series generation is not currently running.")
            return

        self.is_running = False
        
        if self.generation_task and not self.generation_task.done():
            self.generation_task.cancel()
        
        self.current_condition = None
        await message.reply_text("Auto series generation stopped.")

    def register_handlers(self):
        """
        Register command handlers for the client
        """
        @self.client.on_message(filters.command(["setseriesautogen"]))
        async def handle_set_series_auto_gen(client, message):
            """
            Handle setting auto generation conditions for series
            Usage: /setseriesautogen <year> [max_posts] [genre]
            """
            try:
                parts = message.text.split()
                if len(parts) < 2:
                    await message.reply_text(
                        "Invalid format. Usage:\n"
                        "/setseriesautogen <year> [max_posts] [genre]\n"
                        "Example: /setseriesautogen 2023 5 drama"
                    )
                    return

                year = parts[1]
                max_posts = 10  # Default max posts
                genre = None

                if len(parts) > 2 and parts[2].isdigit():
                    max_posts = int(parts[2])
                
                if len(parts) > 3:
                    genre = parts[3]

                # Set condition
                success = await self.set_series_condition(message, year, max_posts, genre)
                
                if success:
                    # Start generation task
                    self.generation_task = asyncio.create_task(self.start_series_post_generation())
            
            except Exception as e:
                await message.reply_text(f"Error in series auto generation: {str(e)}")
        
        @self.client.on_message(filters.command(["startseriesautogen"]))
        async def handle_start_series_auto_gen(client, message):
            """
            Start auto series generation if conditions are set
            """
            if not self.current_condition:
                await message.reply_text("Please set auto generation conditions first using /setseriesautogen")
                return

            if self.is_running:
                await message.reply_text("Auto series generation is already running.")
                return

            # Start generation task
            self.generation_task = asyncio.create_task(self.start_series_post_generation())
            await message.reply_text("Auto series generation started.")

        @self.client.on_message(filters.command(["stopseriesautogen"]))
        async def handle_stop_series_auto_gen(client, message):
            """
            Stop auto series generation
            """
            await self.stop_series_post_generation(message)

        @self.client.on_message(filters.command(["statseriesautogen"]))
        async def handle_stat_series_auto_gen(client, message):
            """
            Get status of auto series generation
            """
            if not self.current_condition:
                await message.reply_text("No auto series generation condition is set.")
                return

            status_text = "Auto Series Generation Status:\n"
            status_text += f"Year: {self.current_condition['year']}\n"
            status_text += f"Max Posts: {self.current_condition['max_posts']}\n"
            status_text += f"Genre: {self.current_condition.get('genre', 'Any')}\n"
            status_text += f"Target Chat: {self.current_condition['target_chat']}\n"
            status_text += f"Running: {'Yes' if self.is_running else 'No'}"

            await message.reply_text(status_text)