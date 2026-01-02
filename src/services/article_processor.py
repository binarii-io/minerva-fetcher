"""
Article Processor Service
Compares and processes articles
"""
from typing import List, Dict, Tuple
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ArticleProcessor:
    """Service to process and compare articles"""
    
    def __init__(self):
        self.existing_urls = set()
    
    def load_existing_articles(self, existing_articles: List[Dict]):
        """
        Load existing articles URLs for comparison
        
        Args:
            existing_articles: List of existing article dictionaries
        """
        self.existing_urls = {
            article.get("url", "").strip() 
            for article in existing_articles 
            if article.get("url")
        }
        logger.info(f"Loaded {len(self.existing_urls)} existing article URLs")
    
    def filter_new_articles(self, fetched_articles: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter articles into new and existing
        
        Args:
            fetched_articles: List of fetched article dictionaries
            
        Returns:
            Tuple of (new_articles, existing_articles)
        """
        new_articles = []
        existing_articles = []
        
        for article in fetched_articles:
            url = article.get("url", "").strip()
            
            if url in self.existing_urls:
                existing_articles.append(article)
            else:
                new_articles.append(article)
        
        logger.info(f"Found {len(new_articles)} new articles and {len(existing_articles)} existing articles")
        
        return new_articles, existing_articles
    
    def filter_extractable_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Filter articles that should be extracted (extract_articles=true)
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Filtered list of articles to extract
        """
        extractable = [
            article for article in articles 
            if article.get("extract_articles") is True
        ]
        
        logger.info(f"Filtered {len(extractable)} articles for extraction")
        return extractable
    
    def prepare_for_export(self, articles: List[Dict]) -> List[Dict]:
        """
        Prepare articles for export with metadata
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Articles with additional metadata
        """
        prepared = []
        
        for article in articles:
            # Add extraction timestamp
            article["extracted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Ensure all required fields
            article.setdefault("title", "Untitled")
            article.setdefault("author", "Unknown")
            article.setdefault("domain", "")
            article.setdefault("feed_name", "Unknown")
            
            prepared.append(article)
        
        return prepared
    
    def prepare_for_storage(self, articles: List[Dict]) -> List[Dict]:
        """
        Prepare articles for Google Sheet storage
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Articles formatted for sheet storage
        """
        storage_ready = []
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for article in articles:
            # Create simplified version for sheet
            storage_article = {
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "summary": article.get("summary", "")[:500],  # Limit summary length
                "author": article.get("author", ""),
                "published_date": article.get("published_date", ""),
                "feed_name": article.get("feed_name", ""),
                "feed_url": article.get("feed_url", ""),
                "domain": article.get("domain", ""),
                "extracted_at": article.get("extracted_at", current_time),
                "has_full_content": "Yes" if article.get("full_content") else "No",
            }
            
            storage_ready.append(storage_article)
        
        return storage_ready
