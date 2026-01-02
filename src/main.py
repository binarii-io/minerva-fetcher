"""
Minerva RSS - Main Pipeline
Extract articles from RSS feeds and export to markdown
"""
from datetime import datetime
from src.config import settings
from src.services import RSSFetcher, GSheetService, ArticleProcessor
from src.services.supabase_service import SupabaseService
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main pipeline execution"""
    try:
        # Validate settings
        logger.info("Starting Minerva RSS Pipeline")
        settings.validate()
        
        # Initialize services
        logger.info("Initializing services...")
        gsheet_service = GSheetService()
        supabase_service = SupabaseService()
        rss_fetcher = RSSFetcher()
        processor = ArticleProcessor()
        
        # Step 1: Get RSS feeds configuration
        logger.info("Step 1: Fetching RSS feeds configuration from Google Sheet...")
        rss_feeds = gsheet_service.get_rss_feeds_from_csv()
        logger.info(f"Found {len(rss_feeds)} RSS feeds to process")
        
        if not rss_feeds:
            logger.warning("No RSS feeds found. Exiting.")
            return
        
        # Step 2: Fetch articles from RSS feeds
        logger.info("Step 2: Fetching articles from RSS feeds...")
        fetched_articles = rss_fetcher.fetch_feeds(rss_feeds)
        logger.info(f"Fetched {len(fetched_articles)} total articles")
        
        if not fetched_articles:
            logger.warning("No articles fetched. Exiting.")
            return
        
        # Step 3: Get existing articles from Google Sheet
        logger.info("Step 3: Retrieving existing articles from Google Sheet...")
        existing_articles_gsheet = gsheet_service.get_existing_articles()
        processor.load_existing_articles(existing_articles_gsheet)

        # Step 4: Compare and filter new articles for Google Sheets
        logger.info("Step 4: Comparing articles to identify new ones for Google Sheets...")
        new_articles_for_gsheet, duplicate_articles = processor.filter_new_articles(fetched_articles)
        logger.info(f"Found {len(new_articles_for_gsheet)} new articles for Google Sheets, {len(duplicate_articles)} duplicates")

        # Step 4b: Get existing articles from Supabase
        logger.info("Step 4b: Retrieving existing articles from Supabase...")
        existing_articles_supabase = supabase_service.get_existing_articles()
        existing_supabase_urls = {article.get("url", "").strip() for article in existing_articles_supabase if article.get("url")}
        logger.info(f"Found {len(existing_supabase_urls)} existing articles in Supabase")

        # Step 4c: Filter new articles for Supabase
        new_articles_for_supabase = [
            article for article in fetched_articles
            if article.get("url", "").strip() not in existing_supabase_urls
        ]
        logger.info(f"Found {len(new_articles_for_supabase)} new articles for Supabase")

        if not new_articles_for_gsheet and not new_articles_for_supabase:
            logger.info("No new articles to process. Exiting.")
            return
        
        # Step 5: Add new articles to Google Sheet (only new ones for GSheet)
        if new_articles_for_gsheet:
            logger.info("Step 5a: Adding new articles to Google Sheet...")
            storage_articles_gsheet = processor.prepare_for_storage(new_articles_for_gsheet)
            gsheet_service.add_articles(storage_articles_gsheet)
            logger.info(f"Added {len(storage_articles_gsheet)} articles to Google Sheet")
        else:
            logger.info("Step 5a: No new articles to add to Google Sheet")
            storage_articles_gsheet = []

        # Step 5b: Add new articles to Supabase (only new ones for Supabase)
        if new_articles_for_supabase:
            logger.info("Step 5b: Adding new articles to Supabase...")
            storage_articles_supabase = []
            for article in new_articles_for_supabase:
                storage_article = {
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "summary": article.get("summary", ""),
                    "author": article.get("author", ""),
                    "published_date": article.get("published_date", ""),
                    "feed_name": article.get("feed_name", ""),
                    "domain": article.get("domain", ""),
                    "extracted_at": article.get("extracted_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    "has_full_content": bool(article.get("full_content", "")),
                }
                storage_articles_supabase.append(storage_article)

            supabase_service.add_articles(storage_articles_supabase)
            logger.info(f"Added {len(storage_articles_supabase)} articles to Supabase")
        else:
            logger.info("Step 5b: No new articles to add to Supabase")
            storage_articles_supabase = []
        
        # Summary
        logger.info("=" * 60)
        logger.info("Pipeline completed successfully!")
        logger.info(f"Total articles fetched: {len(fetched_articles)}")
        logger.info(f"New articles for Google Sheet: {len(new_articles_for_gsheet)}")
        logger.info(f"New articles for Supabase: {len(new_articles_for_supabase)}")
        logger.info(f"Articles added to Google Sheet: {len(storage_articles_gsheet)}")
        logger.info(f"Articles added to Supabase: {len(storage_articles_supabase)}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
