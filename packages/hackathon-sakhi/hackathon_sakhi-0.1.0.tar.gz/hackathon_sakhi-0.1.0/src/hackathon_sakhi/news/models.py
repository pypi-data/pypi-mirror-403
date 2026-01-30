"""Data models for news articles."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Article:
    """Data class for news article."""
    title: str
    summary: str
    published: str
    url: str
    source: str
    location: Optional[str] = None
    category: Optional[str] = None


@dataclass
class ArticleCluster:
    """Data class for clustered articles."""
    cluster_title: str
    location: str
    category: str
    incident_count: int
    articles: List[Article] = field(default_factory=list)
