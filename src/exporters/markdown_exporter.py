"""
Markdown Exporter
Exports articles to markdown files with frontmatter
"""
import frontmatter
from pathlib import Path
from datetime import datetime
from slugify import slugify
from typing import Dict

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MarkdownExporter:
    """Export articles to markdown files"""
    
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or settings.EXPORT_BASE_PATH
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def export_article(self, article: Dict) -> Path:
        """
        Export a single article to markdown file
        
        Args:
            article: Article dictionary
            
        Returns:
            Path to the created file
        """
        try:
            # Check content length
            content_text = article.get("full_content") or article.get("summary", "")
            if len(content_text) < 800:
                logger.warning(
                    f"Article '{article.get('title')}' has less than 800 characters ({len(content_text)}), skipping export"
                )
                return None
            
            # Build file path
            file_path = self._build_file_path(article)
            
            # Create markdown with frontmatter
            content = self._create_markdown_content(article)
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(content))
            
            logger.info(f"Exported article to: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error exporting article {article.get('title')}: {e}")
            raise
    
    def export_articles(self, articles: list[Dict]) -> list[Path]:
        """
        Export multiple articles
        
        Args:
            articles: List of article dictionaries
            
        Returns:if path:  # Only add if file was actually created
                    
            List of paths to created files
        """
        exported_paths = []
        
        for article in articles:
            try:
                path = self.export_article(article)
                exported_paths.append(path)
            except Exception as e:
                logger.warning(f"Failed to export article: {e}")
                continue
        
        logger.info(f"Exported {len(exported_paths)} articles")
        return exported_paths
    
    def _build_file_path(self, article: Dict) -> Path:
        """
        Build file path following pattern:
        data/{domain}/{year}/{month}/{date}_{article_name}.md
        """
        # Extract date components
        published_date = article.get("published_date", "")
        try:
            dt = datetime.strptime(published_date, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            dt = datetime.now()
        
        year = dt.strftime("%Y")
        month = dt.strftime("%m")
        date = dt.strftime("%Y-%m-%d")
        
        # Sanitize domain
        domain = article.get("domain", "unknown")
        domain = slugify(domain)
        
        # Sanitize article name
        title = article.get("title", "untitled")
        article_slug = slugify(title, max_length=100)
        
        # Build path
        file_name = f"{date}_{article_slug}.md"
        file_path = (
            self.base_path / 
            domain / 
            year / 
            month / 
            file_name
        )
        
        return file_path
    
    def _create_markdown_content(self, article: Dict) -> frontmatter.Post:
        """Create markdown post with frontmatter"""
        # Determine content
        content = article.get("full_content") or article.get("summary", "")
        
        # Create post
        post = frontmatter.Post(content)
        
        # Add metadata
        post['title'] = article.get("title", "")
        post['url'] = article.get("url", "")
        post['author'] = article.get("author", "")
        post['published_date'] = article.get("published_date", "")
        post['feed_name'] = article.get("feed_name", "")
        post['feed_url'] = article.get("feed_url", "")
        post['domain'] = article.get("domain", "")
        post['extracted_at'] = article.get("extracted_at", "")
        
        if article.get("summary"):
            post['summary'] = article.get("summary")
        
        return post
