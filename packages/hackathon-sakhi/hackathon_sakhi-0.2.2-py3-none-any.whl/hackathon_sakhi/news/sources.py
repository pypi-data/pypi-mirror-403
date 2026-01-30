"""RSS feed sources for Indian news."""

from abc import ABC, abstractmethod
from typing import Dict, List


class RSSSourcesInterface(ABC):
    """Abstract interface for RSS sources."""
    
    @abstractmethod
    def get_sources(self) -> Dict[str, List[str]]:
        """Get RSS feed sources."""
        pass


class IndianNewsSources(RSSSourcesInterface):
    """Indian news sources for women safety."""
    
    def get_sources(self) -> Dict[str, List[str]]:
        return {
            "national_crime": [
                "https://indianexpress.com/section/india/feed/",
                "https://www.news18.com/rss/india.xml",
                "https://zeenews.india.com/rss/india-national-news.xml"
            ],
            "delhi": [
                "https://www.thehindu.com/news/cities/delhi/feeder/default.rss",
                "https://indianexpress.com/section/cities/delhi/feed/"
            ],
            "mumbai": [
                "https://www.thehindu.com/news/cities/mumbai/feeder/default.rss",
                "https://indianexpress.com/section/cities/mumbai/feed/"
            ],
            "bangalore": [
                "https://www.thehindu.com/news/cities/bangalore/feeder/default.rss",
                "https://indianexpress.com/section/cities/bangalore/feed/"
            ],
            "chennai": [
                "https://www.thehindu.com/news/cities/chennai/feeder/default.rss"
            ],
            "women_rights": [
                "https://www.thehindu.com/society/feeder/default.rss"
            ],
            "law_and_policy": [
                "https://www.barandbench.com/feed"
            ]
        }
