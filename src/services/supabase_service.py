"""
Supabase Service
Handles reading and writing to Supabase PostgreSQL Database
"""
from supabase import create_client, Client
from typing import List, Dict, Optional
from datetime import datetime

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SupabaseService:
    """Service to interact with Supabase PostgreSQL Database"""

    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize()

    def _initialize(self):
        """Initialize Supabase client"""
        try:
            self.client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_SERVICE_KEY
            )
            logger.info("Successfully connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
            raise

    def get_existing_articles(self) -> List[Dict]:
        """
        Get the 1000 most recent existing articles from Supabase

        Returns:
            List of article dictionaries sorted by most recent first
        """
        try:
            response = self.client.table(settings.SUPABASE_TABLE_NAME).select("*").order("published_date", desc=True).limit(1000).execute()
            articles = response.data if response.data else []
            logger.info(f"Retrieved {len(articles)} recent articles from Supabase")
            return articles

        except Exception as e:
            logger.error(f"Error fetching existing articles from Supabase: {e}")
            return []

    def add_articles(self, articles: List[Dict]):
        """
        Add new articles to Supabase, ignoring duplicates

        Args:
            articles: List of article dictionaries to add
        """
        if not articles:
            logger.info("No articles to add to Supabase")
            return

        try:
            added_count = 0
            skipped_count = 0
            for article in articles:
                # Prepare article data for Supabase (only fields that exist in the table)
                article_data = {
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'summary': article.get('summary', ''),
                    'author': article.get('author', ''),
                    'published_date': article.get('published_date', ''),
                    'feed_name': article.get('feed_name', ''),
                    'domain': article.get('domain', ''),
                    'extracted_at': article.get('extracted_at', ''),
                    'has_full_content': article.get('has_full_content', False),
                }

                try:
                    response = self.client.table(settings.SUPABASE_TABLE_NAME).insert(article_data).execute()
                    if response.data:
                        added_count += 1
                except Exception as e:
                    # Ignore duplicate key errors (article already exists)
                    if "duplicate key" in str(e).lower() or "23505" in str(e):
                        skipped_count += 1
                    else:
                        raise

            logger.info(f"Added {added_count} articles to Supabase, skipped {skipped_count} duplicates")

        except Exception as e:
            logger.error(f"Error adding articles to Supabase: {e}")
            raise

    def update_article(self, url: str, updates: Dict):
        """
        Update an existing article in Supabase

        Args:
            url: Article URL to identify the record
            updates: Dictionary of fields to update
        """
        try:
            # Check if article exists
            response = self.client.table(settings.SUPABASE_TABLE_NAME).select("*").eq("url", url).execute()

            if response.data:
                # Add updated timestamp
                updates['updated_at'] = datetime.utcnow().isoformat()
                self.client.table(settings.SUPABASE_TABLE_NAME).update(updates).eq("url", url).execute()
                logger.info(f"Updated article in Supabase: {url}")
            else:
                logger.warning(f"Article not found in Supabase for update: {url}")

        except Exception as e:
            logger.error(f"Error updating article in Supabase: {e}")

    def get_article_by_url(self, url: str) -> Optional[Dict]:
        """
        Get a specific article by URL

        Args:
            url: Article URL

        Returns:
            Article dictionary or None if not found
        """
        try:
            response = self.client.table(settings.SUPABASE_TABLE_NAME).select("*").eq("url", url).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]

            return None

        except Exception as e:
            logger.error(f"Error fetching article from Supabase: {e}")
            return None

    def delete_article(self, url: str):
        """
        Delete an article from Supabase

        Args:
            url: Article URL to identify the record
        """
        try:
            # Check if article exists
            response = self.client.table(settings.SUPABASE_TABLE_NAME).select("*").eq("url", url).execute()

            if response.data:
                self.client.table(settings.SUPABASE_TABLE_NAME).delete().eq("url", url).execute()
                logger.info(f"Deleted article from Supabase: {url}")
            else:
                logger.warning(f"Article not found in Supabase for deletion: {url}")

        except Exception as e:
            logger.error(f"Error deleting article from Supabase: {e}")
