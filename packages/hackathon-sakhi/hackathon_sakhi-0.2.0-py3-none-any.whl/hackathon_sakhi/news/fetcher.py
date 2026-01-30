"""Article fetcher from RSS feeds."""

import logging
from typing import List, Dict
import feedparser

from .models import Article


class ArticleFetcher:
    """Fetches articles from RSS feeds."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def fetch_rss(self, url: str) -> List[Article]:
        """Fetch articles from a single RSS feed."""
        try:
            feed = feedparser.parse(url)
            articles = []
            
            for entry in feed.entries:
                article = Article(
                    title=entry.title,
                    summary=entry.get("summary", ""),
                    published=entry.get("published", ""),
                    url=entry.link,
                    source=feed.feed.get("title", "Unknown")
                )
                articles.append(article)
            
            return articles
        except Exception as e:
            self.logger.error(f"Error fetching RSS from {url}: {str(e)}")
            return []
    
    def fetch_all(self, sources: Dict[str, List[str]]) -> List[Article]:
        """Fetch articles from all RSS sources."""
        all_articles = []
        for urls in sources.values():
            for url in urls:
                articles = self.fetch_rss(url)
                all_articles.extend(articles)
        return all_articles
