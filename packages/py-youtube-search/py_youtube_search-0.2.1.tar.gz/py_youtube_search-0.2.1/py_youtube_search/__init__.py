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
    def __init__(self, keywords: str, sp: str = None, limit: int = 15):
        """
        Initialize the search parameters.
        Note: No network request happens here. Call .search() to fetch data.
        """
        self.keywords = keywords.replace(" ", "+")
        self.sp = sp
        self.limit = limit
        self.source = None
        self.base_url = "https://www.youtube.com/results"

    async def _fetch_source(self):
        params = {"search_query": self.keywords}
        if self.sp:
            params["sp"] = self.sp

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params, headers=headers) as response:
                return await response.text()

    async def search(self):
        """
        Asynchronously fetches and parses the search results.
        Returns a list of videos.
        """
        if not self.source:
            self.source = await self._fetch_source()

        # Regex to capture distinct JSON fields for ID, Title, Duration, and Views.
        pattern = (
            r'\"videoRenderer\":\{'
            r'.+?\"videoId\":\"(?P<id>\S{11})\"'
            r'.+?\"title\":\{\"runs\":\[\{\"text\":\"(?P<title>.+?)\"\}\]'
            r'.+?\"lengthText\":\{.*?\"simpleText\":\"(?P<duration>.+?)\"\}'
            r'.+?\"viewCountText\":\{\"simpleText\":\"(?P<views>.+?)\"\}'
        )

        matches = re.finditer(pattern, self.source)
        
        results = []
        for match in matches:
            if len(results) >= self.limit:
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
#     yt = YouTubeSearch("LangGraph", sp=Filters.long_this_week)
#     videos = await yt.search()
#     print(videos)
# asyncio.run(main())
