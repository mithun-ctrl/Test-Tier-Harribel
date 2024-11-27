from ..config import omdb_api
import aiohttp


class tmdbHelpers:
    
    async def get_imdb_rating(imdb_id):
        """ Fetch IMDb rating using OMDB API """
        try:
            if not imdb_id:
                return 'N/A'
                
            url = f"http://www.omdbapi.com/?i={imdb_id}&apikey={omdb_api}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        rating = data.get('imdbRating')
                        return rating if rating and rating != 'N/A' else '0'
                    return '0'
        except Exception as e:
            print(f"Error fetching IMDb rating: {str(e)}")
            return '0'