"""Article processor for filtering and categorization."""

import re
import logging
from typing import Optional

from .models import Article


class ArticleProcessor:
    """Processes and filters articles for women safety relevance."""
    
    SAFETY_KEYWORDS = [
        "women", "woman", "girl", "female", "lady",
        "rape", "assault", "harassment", "molest", "abuse",
        "murder", "killed", "attack", "violence", "crime",
        "safety", "security", "stalking", "kidnap", "abduct",
        "domestic violence", "dowry", "acid attack", "eve teasing"
    ]
    
    INDIAN_CITIES = [
        "delhi", "mumbai", "bangalore", "bengaluru", "chennai",
        "kolkata", "hyderabad", "pune", "ahmedabad", "jaipur",
        "lucknow", "kanpur", "nagpur", "indore", "thane",
        "bhopal", "visakhapatnam", "patna", "vadodara", "ghaziabad",
        "ludhiana", "agra", "nashik", "faridabad", "meerut",
        "rajkot", "varanasi", "srinagar", "aurangabad", "dhanbad",
        "amritsar", "allahabad", "ranchi", "howrah", "coimbatore",
        "jabalpur", "gwalior", "vijayawada", "jodhpur", "madurai",
        "raipur", "kota", "chandigarh", "guwahati", "solapur",
        "noida", "gurugram", "gurgaon"
    ]
    
    CATEGORIES = {
        "assault": ["rape", "assault", "molest", "attack", "violence"],
        "harassment": ["harassment", "stalking", "eve teasing", "abuse"],
        "kidnapping": ["kidnap", "abduct", "missing"],
        "murder": ["murder", "killed", "death", "body found"],
        "domestic": ["domestic violence", "dowry", "husband", "in-laws"],
        "policy": ["law", "court", "police", "investigation", "arrest"]
    }
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def is_safety_related(self, article: Article) -> bool:
        """Check if article is related to women safety."""
        text = f"{article.title} {article.summary}".lower()
        return any(keyword in text for keyword in self.SAFETY_KEYWORDS)
    
    def extract_location(self, article: Article, filter_location: Optional[str] = None) -> Optional[Article]:
        """Extract location from article and optionally filter by location."""
        text = f"{article.title} {article.summary}".lower()
        
        for city in self.INDIAN_CITIES:
            if city in text:
                article.location = city.title()
                break
        
        if not article.location:
            article.location = "Unknown"
        
        # Filter by location if specified
        if filter_location:
            if filter_location.lower() not in article.location.lower():
                return None
        
        return article
    
    def determine_category(self, article: Article) -> str:
        """Determine the category of the article."""
        text = f"{article.title} {article.summary}".lower()
        
        for category, keywords in self.CATEGORIES.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return "general"
