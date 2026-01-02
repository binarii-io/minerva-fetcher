"""
Configuration settings for the RSS pipeline
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings"""
    
    # Base paths
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    EXPORT_BASE_PATH = BASE_DIR / os.getenv("EXPORT_BASE_PATH", "data")
    
    # Google Sheets
    RSS_FEEDS_CSV_URL = os.getenv("RSS_FEEDS_CSV_URL")
    ARTICLES_SHEET_ID = os.getenv("ARTICLES_SHEET_ID")
    ARTICLES_WORKSHEET_NAME = os.getenv("ARTICLES_WORKSHEET_NAME", "Articles")
    
    # Google Service Account
    GOOGLE_SERVICE_ACCOUNT_FILE = BASE_DIR / os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_FILE",
        "credentials/service_account.json"
    )

    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    SUPABASE_TABLE_NAME = os.getenv("SUPABASE_TABLE_NAME", "articles")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Article extraction
    REQUEST_TIMEOUT = 30
    USER_AGENT = "Mozilla/5.0 (compatible; MinervaRSS/1.0)"
    
    def validate(self):
        """Validate required settings"""
        if not self.RSS_FEEDS_CSV_URL:
            raise ValueError("RSS_FEEDS_CSV_URL is required")
        if not self.ARTICLES_SHEET_ID:
            raise ValueError("ARTICLES_SHEET_ID is required")
        if not self.GOOGLE_SERVICE_ACCOUNT_FILE.exists():
            raise ValueError(
                f"Service account file not found: {self.GOOGLE_SERVICE_ACCOUNT_FILE}"
            )
        if not self.SUPABASE_URL:
            raise ValueError("SUPABASE_URL is required")
        if not self.SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_SERVICE_KEY is required")

settings = Settings()
