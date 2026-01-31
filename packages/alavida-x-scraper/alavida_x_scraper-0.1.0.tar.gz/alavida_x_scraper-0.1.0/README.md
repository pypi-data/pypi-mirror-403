# Alavida X Scraper SDK (Python)

Install:

```bash
pip install alavida-x-scraper
```

Usage:

```python
from alavida_x_scraper import XScraperClient

client = XScraperClient(
    base_url="https://your-host.com/api",
    token="YOUR_CLERK_API_KEY",
)

result = client.scraping.scrape_tweets_from_a_twitter_user(
    user_name="elonmusk",
    max_tweets=5,
    query_type="Latest",
    replies_filter="exclude",
)
```
