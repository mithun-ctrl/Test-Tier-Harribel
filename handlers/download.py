import aiohttp
class downloadHandler:
    async def download_image(url):
        """Download image from URL"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
        return None

    async def download_poster(poster_url):
        """Download movie poster from URL"""
        if poster_url and poster_url != 'N/A':
            async with aiohttp.ClientSession() as session:
                async with session.get(poster_url) as response:
                    if response.status == 200:
                        return await response.read()
        return None