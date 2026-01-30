import re
import aiohttp
import asyncio

# Filter constants accessible to the user
class Filters:
    # Duration: 3 - 20 Minutes (Medium)
    medium_today = "EgYIAhABGAU="
    medium_this_week = "EgQIAxGF"
    medium_this_month = "EgYIBBABGAU="
    medium_this_year = "EgYIBRABGAU="

    # Duration: Over 20 Minutes (Long)
    long_today = "EgYIAhABGAI="
    long_this_week = "EgQIAxAB"
    long_this_month = "EgYIBBABGAI="
    long_this_year = "EgYIBRABGAI="


class YouTubeSearch:
    def __init__(self):
        """
        Initialize the YouTubeSearch client.
        The client is stateless; parameters are passed to the search method.
        """
        self.base_url = "https://www.youtube.com/results"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    async def _fetch_source(self, query: str, sp: str = None):
        params = {"search_query": query.replace(" ", "+")}
        if sp:
            params["sp"] = sp

        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params, headers=self.headers) as response:
                return await response.text()

    async def search(self, query: str, sp: str = None, limit: int = 15):
        """
        Asynchronously fetches and parses search results for the given query.
        
        Args:
            query (str): The search query.
            sp (str, optional): The filter string (use Filters class). Defaults to None.
            limit (int, optional): Max number of results. Defaults to 15.

        Returns:
            list: A list of dictionaries containing video details.
        """
        source = await self._fetch_source(query, sp)

        # Regex to capture distinct JSON fields for ID, Title, Duration, and Views.
        pattern = (
            r'\"videoRenderer\":\{'
            r'.+?\"videoId\":\"(?P<id>\S{11})\"'
            r'.+?\"title\":\{\"runs\":\[\{\"text\":\"(?P<title>.+?)\"\}\]'
            r'.+?\"lengthText\":\{.*?\"simpleText\":\"(?P<duration>.+?)\"\}'
            r'.+?\"viewCountText\":\{\"simpleText\":\"(?P<views>.+?)\"\}'
        )

        matches = re.finditer(pattern, source)
        
        results = []
        for match in matches:
            if len(results) >= limit:
                break
            
            data = match.groupdict()
            results.append({
                "id": data["id"],
                "title": data["title"],
                "duration": data["duration"],
                "views": data["views"],
                "url_suffix": f"/watch?v={data['id']}"
            })

        return results

# --- Usage Example (Async) ---
# import asyncio
# async def main():
#     yt = YouTubeSearch()
#     
#     # Search 1: Long videos about LangGraph
#     print("Searching LangGraph...")
#     videos1 = await yt.search("LangGraph", sp=Filters.long_this_week, limit=5)
#     print(f"Found {len(videos1)} videos")
#
#     # Search 2: Short Python tutorials (reusing the same instance)
#     print("Searching Python...")
#     videos2 = await yt.search("Python", sp=Filters.medium_today, limit=3)
#     print(f"Found {len(videos2)} videos")
#
# asyncio.run(main())
