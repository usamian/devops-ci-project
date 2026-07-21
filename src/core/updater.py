"""
Atlas AI — Data Updater Module
Handles automatic updates from GOV.UK with change detection.
"""

import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.core.config import AtlasConfig


class DataUpdater:
    """
    Smart data updater with change detection.
    Only updates when content has actually changed.
    """
    
    def __init__(self):
        self.data_dir = AtlasConfig.DATA_DIR / "gov_uk_docs"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.data_dir / "update_metadata.json"
        self.content_hashes_file = self.data_dir / "content_hashes.json"
    
    def get_last_update(self) -> Optional[datetime]:
        """Get the timestamp of the last successful update."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
                    if 'last_update' in metadata:
                        return datetime.fromisoformat(metadata['last_update'])
            except Exception:
                pass
        return None
    
    def get_content_hashes(self) -> Dict[str, str]:
        """Get hashes of all cached content."""
        if self.content_hashes_file.exists():
            try:
                with open(self.content_hashes_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def has_content_changed(self, url: str, new_content: str, old_hashes: Dict[str, str]) -> bool:
        """Check if content has changed by comparing hashes."""
        new_hash = self.compute_hash(new_content)
        old_hash = old_hashes.get(url)
        return old_hash is None or old_hash != new_hash
    
    def save_metadata(self, pages_updated: int, pages_unchanged: int, total_pages: int):
        """Save update metadata."""
        metadata = {
            'last_update': datetime.utcnow().isoformat(),
            'pages_updated': pages_updated,
            'pages_unchanged': pages_unchanged,
            'total_pages': total_pages,
            'version': '2.0'
        }
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def save_content_hashes(self, hashes: Dict[str, str]):
        """Save content hashes."""
        with open(self.content_hashes_file, 'w') as f:
            json.dump(hashes, f, indent=2)
    
    def check_for_updates(self, scraper) -> Dict[str, Any]:
        """
        Check for updates without actually updating.
        Returns info about what would be updated.
        """
        old_hashes = self.get_content_hashes()
        changes = []
        
        for category, urls in scraper.TARGET_PAGES.items():
            for url in urls:
                try:
                    page = scraper.scrape_page(url, force_refresh=False)
                    if page:
                        content = page.content
                        new_hash = self.compute_hash(content)
                        old_hash = old_hashes.get(url)
                        
                        if old_hash is None or old_hash != new_hash:
                            changes.append({
                                'url': url,
                                'title': page.title,
                                'category': category,
                                'status': 'new' if old_hash is None else 'changed'
                            })
                except Exception as e:
                    changes.append({
                        'url': url,
                        'title': f'Error: {str(e)}',
                        'category': category,
                        'status': 'error'
                    })
        
        return {
            'changes': changes,
            'total_changes': len(changes),
            'last_update': self.get_last_update().isoformat() if self.get_last_update() else None
        }
    
    def update_data(self, scraper) -> Dict[str, Any]:
        """
        Perform smart update - only update changed content.
        Returns update statistics.
        """
        start_time = time.time()
        old_hashes = self.get_content_hashes()
        new_hashes = {}
        
        pages_updated = 0
        pages_unchanged = 0
        pages_error = 0
        updated_pages = []
        
        for category, urls in scraper.TARGET_PAGES.items():
            for url in urls:
                try:
                    # Scrape the page
                    page = scraper.scrape_page(url, force_refresh=True)
                    if page:
                        content = page.content
                        new_hash = self.compute_hash(content)
                        old_hash = old_hashes.get(url)
                        
                        # Check if content changed
                        if old_hash is None or old_hash != new_hash:
                            # Content changed - save it
                            new_hashes[url] = new_hash
                            pages_updated += 1
                            updated_pages.append({
                                'url': url,
                                'title': page.title,
                                'category': category,
                                'status': 'updated'
                            })
                        else:
                            # Content unchanged - keep old hash
                            new_hashes[url] = old_hash
                            pages_unchanged += 1
                    else:
                        pages_error += 1
                        
                except Exception as e:
                    pages_error += 1
        
        # Save metadata and hashes
        self.save_metadata(pages_updated, pages_unchanged, pages_updated + pages_unchanged)
        self.save_content_hashes(new_hashes)
        
        elapsed = time.time() - start_time
        
        return {
            'status': 'success',
            'pages_updated': pages_updated,
            'pages_unchanged': pages_unchanged,
            'pages_error': pages_error,
            'total_pages': pages_updated + pages_unchanged + pages_error,
            'updated_pages': updated_pages,
            'elapsed_seconds': round(elapsed, 2),
            'last_update': datetime.utcnow().isoformat()
        }


# Global updater instance
updater = DataUpdater()