
# py-youtube-search

A lightweight, asynchronous Python library to search YouTube videos programmatically without an API key. 
It scrapes search results using `aiohttp` and `re`, making it fast, robust, and perfect for high-performance applications.

## Features

- **Async Support**: Fully asynchronous using `aiohttp` for non-blocking execution.
- **No API Key Required**: Search YouTube directly without setting up Google Cloud projects.
- **Advanced Filtering**: Built-in support for duration (Medium 3-20m, Long >20m) and upload date filters.
- **Rich Data Extraction**: Extracts Video ID, Title, Duration, and View Count using optimized regex.

## Installation

```bash
pip install py-youtube-search
```

## Quick Start

### 1. Basic Async Search
Fetch the top results for any keyword asynchronously.

```python
import asyncio
from py_youtube_search import YouTubeSearch

async def main():
    # 1. Initialize the search (no network call yet)
    yt = YouTubeSearch("Python async tutorials", limit=5)
    
    # 2. Await the search results
    videos = await yt.search()

    for v in videos:
        print(f"Title: {v['title']}")
        print(f"Duration: {v['duration']}")
        print(f"Views: {v['views']}")
        print(f"Link: https://www.youtube.com/watch?v={v['id']}\n")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Advanced Search with Filters
Search for specific content, like long-form videos (>20m) uploaded this week.

```python
import asyncio
from py_youtube_search import YouTubeSearch, Filters

async def main():
    # Use the Filters class for readable constants
    yt = YouTubeSearch("LangGraph", sp=Filters.long_this_week, limit=3)
    
    videos = await yt.search()

    for v in videos:
        print(f"🎥 {v['title']} | ⏱ {v['duration']} | 👁 {v['views']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Available Filters

Pass these constants into the `sp` parameter of `YouTubeSearch`.

### Duration: Medium (3 - 20 Minutes)
| Filter Attribute | Description |
| :--- | :--- |
| `Filters.medium_today` | Uploaded **Today** |
| `Filters.medium_this_week` | Uploaded **This Week** |
| `Filters.medium_this_month` | Uploaded **This Month** |
| `Filters.medium_this_year` | Uploaded **This Year** |

### Duration: Long (Over 20 Minutes)
| Filter Attribute | Description |
| :--- | :--- |
| `Filters.long_today` | Uploaded **Today** |
| `Filters.long_this_week` | Uploaded **This Week** |
| `Filters.long_this_month` | Uploaded **This Month** |
| `Filters.long_this_year` | Uploaded **This Year** |

## Data Structure

The `.search()` method returns a list of dictionaries:

```json
[
  {
    "id": "lDoYisPfcck",
    "title": "Hack the planet! LangGraph AI HackBot Dev & Q/A",
    "duration": "1:05:23",
    "views": "1.2K views",
    "url_suffix": "/watch?v=lDoYisPfcck"
  }
]
```

## Dependencies
- `aiohttp` (for async requests)

## License
MIT License. See LICENSE file for details.
