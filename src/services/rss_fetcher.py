"""
RSS Feed Fetcher Service
Retrieves and parses RSS feeds, extracts full article content
"""
import feedparser
import requests
from readability import Document
from bs4 import BeautifulSoup
import html2text
from typing import List, Dict, Optional
from datetime import datetime
import time
from urllib.parse import urlparse

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RSSFetcher:
    """Service to fetch and parse RSS feeds"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings.USER_AGENT})
        
        # Configure html2text converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.ignore_emphasis = False
        self.html_converter.body_width = 0  # Don't wrap lines
    
    def fetch_feeds(self, feed_urls: List[Dict]) -> List[Dict]:
        """
        Fetch articles from multiple RSS feeds
        
        Args:
            feed_urls: List of dicts with keys: url, name, description, extract_articles
            
        Returns:
            List of article dictionaries
        """
        all_articles = []
        
        for feed_config in feed_urls:
            feed_url = feed_config.get("url")
            feed_name = feed_config.get("name", "Unknown")
            extract_articles = feed_config.get("extract_articles", "false").lower() == "true"
            
            logger.info(f"Fetching RSS feed: {feed_name} ({feed_url})")
            
            try:
                articles = self._parse_feed(feed_url, feed_name, extract_articles, feed_url)
                all_articles.extend(articles)
                logger.info(f"Retrieved {len(articles)} articles from {feed_name}")
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching feed {feed_name}: {e}")
                continue
        
        return all_articles
    
    def _parse_feed(self, feed_url: str, feed_name: str, extract_full: bool, rss_feed_url: str = "") -> List[Dict]:
        """Parse a single RSS feed"""
        feed = feedparser.parse(feed_url)
        articles = []
        
        for entry in feed.entries:
            try:
                article = self._parse_entry(entry, feed_name, extract_full, rss_feed_url)
                if article:
                    articles.append(article)
            except Exception as e:
                logger.warning(f"Error parsing entry: {e}")
                continue
        
        return articles
    
    def _parse_entry(self, entry, feed_name: str, extract_full: bool, rss_feed_url: str = "") -> Optional[Dict]:
        """Parse a single RSS entry"""
        # Extract basic info
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        
        if not title or not link:
            return None
        
        # Parse date
        published_date = self._parse_date(entry)
        
        # Extract summary
        summary = entry.get("summary", "") or entry.get("description", "")
        summary_clean = self._clean_html(summary)
        
        # Extract author
        author = entry.get("author", "") or entry.get("creator", "")
        
        # Extract full content if needed
        full_content = None
        if extract_full:
            full_content = self._extract_full_content(link)
        
        # Extract domain
        domain = urlparse(link).netloc
        # Remove www. prefix if present
        if domain.startswith("www."):
            domain = domain[4:]
        
        return {
            "title": title,
            "url": link,
            "summary": summary_clean,
            "full_content": full_content,
            "author": author,
            "published_date": published_date,
            "feed_name": feed_name,
            "feed_url": rss_feed_url,
            "domain": domain,
            "extract_articles": extract_full,
        }
    
    def _extract_full_content(self, url: str) -> Optional[str]:
        """Extract full article content using readability and convert to markdown"""
        try:
            response = self.session.get(url, timeout=settings.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Use readability to extract main content
            doc = Document(response.text)
            html_content = doc.summary()
            
            # Convert HTML to markdown (keeps structure, images, links)
            markdown_content = self.html_converter.handle(html_content)
            
            return markdown_content.strip()
            
        except Exception as e:
            logger.warning(f"Could not extract full content from {url}: {e}")
            return None
    
    def _clean_html(self, html: str) -> str:
        """Clean HTML content to plain text"""
        if not html:
            return ""
        
        soup = BeautifulSoup(html, "lxml")
        
        # Remove script and style tags
        for tag in soup(["script", "style"]):
            tag.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _parse_date(self, entry) -> str:
        """Parse and format entry date"""
        # Try different date fields
        date_fields = ["published_parsed", "updated_parsed", "created_parsed"]
        
        for field in date_fields:
            if field in entry and entry[field]:
                try:
                    time_struct = entry[field]
                    dt = datetime(*time_struct[:6])
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    continue
        
        # Fallback to current date
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
