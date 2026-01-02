"""
Google Sheets Service
Handles reading and writing to Google Sheets
"""
import gspread
from google.oauth2.service_account import Credentials
import requests
import csv
from typing import List, Dict
from io import StringIO

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GSheetService:
    """Service to interact with Google Sheets"""
    
    def __init__(self):
        self.client = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            
            creds = Credentials.from_service_account_file(
                settings.GOOGLE_SERVICE_ACCOUNT_FILE,
                scopes=scopes
            )
            
            self.client = gspread.authorize(creds)
            logger.info("Successfully authenticated with Google Sheets")
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {e}")
            raise
    
    def get_rss_feeds_from_csv(self) -> List[Dict]:
        """
        Fetch RSS feeds configuration from published Google Sheet CSV
        
        Returns:
            List of dicts with keys: url, name, description, extract_articles
        """
        try:
            response = requests.get(settings.RSS_FEEDS_CSV_URL, timeout=30)
            response.raise_for_status()
            
            # Parse CSV
            csv_data = StringIO(response.text)
            reader = csv.DictReader(csv_data)
            
            feeds = []
            for row in reader:
                if row.get("url"):  # Skip empty rows
                    feeds.append({
                        "url": row.get("url", "").strip(),
                        "name": row.get("name", "").strip(),
                        "description": row.get("description", "").strip(),
                        "extract_articles": row.get("extract_articles", "false").strip(),
                    })
            
            logger.info(f"Retrieved {len(feeds)} RSS feeds from CSV")
            return feeds
            
        except Exception as e:
            logger.error(f"Error fetching RSS feeds CSV: {e}")
            raise
    
    def get_existing_articles(self) -> List[Dict]:
        """
        Get all existing articles from Google Sheet
        
        Returns:
            List of article dictionaries
        """
        try:
            sheet = self.client.open_by_key(settings.ARTICLES_SHEET_ID)
            worksheet = sheet.worksheet(settings.ARTICLES_WORKSHEET_NAME)
            
            # Get all records as dictionaries
            records = worksheet.get_all_records()
            
            logger.info(f"Retrieved {len(records)} existing articles from sheet")
            return records
            
        except Exception as e:
            logger.error(f"Error fetching existing articles: {e}")
            return []
    
    def add_articles(self, articles: List[Dict]):
        """
        Add new articles to Google Sheet
        
        Args:
            articles: List of article dictionaries to add
        """
        if not articles:
            logger.info("No articles to add")
            return
        
        try:
            sheet = self.client.open_by_key(settings.ARTICLES_SHEET_ID)
            worksheet = sheet.worksheet(settings.ARTICLES_WORKSHEET_NAME)
            
            # Get headers
            headers = worksheet.row_values(1)
            
            # If sheet is empty, add headers
            if not headers:
                headers = [
                    "title", "url", "summary", "author", "published_date",
                    "feed_name", "domain", "extracted_at", "has_full_content", "labels", "ratings", "readers"
                ]
                worksheet.append_row(headers)
            
            # Prepare rows
            rows = []
            for article in articles:
                row = [
                    article.get("title", ""),
                    article.get("url", ""),
                    article.get("summary", ""),
                    article.get("author", ""),
                    article.get("published_date", ""),
                    article.get("feed_name", ""),
                    article.get("domain", ""),
                    article.get("extracted_at", ""),
                    "Yes" if article.get("has_full_content") else "No",
                    "",  # labels (empty by default)
                    "",  # ratings (empty by default)
                    "",  # readers (empty by default)
                ]
                rows.append(row)
            
            # Batch append
            worksheet.append_rows(rows)
            logger.info(f"Added {len(articles)} articles to Google Sheet")
            
        except Exception as e:
            logger.error(f"Error adding articles to sheet: {e}")
            raise
    
    def update_article(self, url: str, updates: Dict):
        """
        Update an existing article in the sheet
        
        Args:
            url: Article URL to identify the row
            updates: Dictionary of fields to update
        """
        try:
            sheet = self.client.open_by_key(settings.ARTICLES_SHEET_ID)
            worksheet = sheet.worksheet(settings.ARTICLES_WORKSHEET_NAME)
            
            # Find the cell with the URL
            cell = worksheet.find(url)
            
            if cell:
                # Get headers to map column names
                headers = worksheet.row_values(1)
                row_num = cell.row
                
                # Update each field
                for field, value in updates.items():
                    if field in headers:
                        col_num = headers.index(field) + 1
                        worksheet.update_cell(row_num, col_num, value)
                
                logger.info(f"Updated article: {url}")
            else:
                logger.warning(f"Article not found for update: {url}")
                
        except Exception as e:
            logger.error(f"Error updating article: {e}")
