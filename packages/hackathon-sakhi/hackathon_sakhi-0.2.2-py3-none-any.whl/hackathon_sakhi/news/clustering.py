"""Article clustering by location and category."""

import logging
from typing import List
from collections import defaultdict

from .models import Article, ArticleCluster


class ArticleClusterer:
    """Clusters articles by location and category."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def cluster_articles(self, articles: List[Article]) -> List[ArticleCluster]:
        """Cluster articles by location and category."""
        # Group by location and category
        groups = defaultdict(list)
        
        for article in articles:
            key = (article.location or "Unknown", article.category or "general")
            groups[key].append(article)
        
        # Create clusters
        clusters = []
        for (location, category), group_articles in groups.items():
            cluster = ArticleCluster(
                cluster_title=f"{category.title()} incidents in {location}",
                location=location,
                category=category,
                incident_count=len(group_articles),
                articles=group_articles
            )
            clusters.append(cluster)
        
        # Sort by incident count
        clusters.sort(key=lambda x: x.incident_count, reverse=True)
        
        return clusters
