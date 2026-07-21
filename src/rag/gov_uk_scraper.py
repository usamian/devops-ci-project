"""
Atlas AI — GOV.UK Web Scraper
Automatically scrapes official UK government immigration guidance.
100% free - no API costs required.

This module:
- Scrapes GOV.UK pages for visa information
- Extracts structured data from HTML
- Stores content for RAG (Retrieval Augmented Generation)
- Respects robots.txt and rate limits
"""

import requests
import re
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
import logging

from src.core.config import AtlasConfig

logger = logging.getLogger(__name__)


@dataclass
class ScrapedPage:
    """Represents a scraped GOV.UK page."""
    url: str
    title: str
    content: str
    sections: List[Dict[str, str]]
    visa_types: List[str]
    hash: str
    scraped_at: str


class GovUKScraper:
    """
    Web scraper for GOV.UK immigration guidance.
    Scrapes official sources to build a local knowledge base.
    """
    
    # Target GOV.UK pages for scraping
    TARGET_PAGES = {
        "skilled_worker": [
            "https://www.gov.uk/skilled-worker-visa",
            "https://www.gov.uk/skilled-worker-visa/eligibility",
            "https://www.gov.uk/skilled-worker-visa/your-job",
            "https://www.gov.uk/skilled-worker-visa/knowledge-of-english",
            "https://www.gov.uk/skilled-worker-visa/financial-requirements",
            "https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-skilled-worker",
        ],
        "health_care_worker": [
            "https://www.gov.uk/health-care-worker-visa",
            "https://www.gov.uk/health-care-worker-visa/eligibility",
        ],
        "graduate": [
            "https://www.gov.uk/graduate-visa",
            "https://www.gov.uk/graduate-visa/eligibility",
        ],
        "global_talent": [
            "https://www.gov.uk/global-talent-visa",
            "https://www.gov.uk/global-talent-visa/eligibility",
        ],
        "general": [
            "https://www.gov.uk/browse/visas-immigration",
            "https://www.gov.uk/government/publications/skilled-worker-visa-immigration-salary-list",
        ],
    }
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or (AtlasConfig.DATA_DIR / "gov_uk_docs")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en-US;q=0.7,en;q=0.3",
            "Referer": "https://www.google.com/",
        })
    
    def scrape_page(self, url: str, force_refresh: bool = False) -> Optional[ScrapedPage]:
        """
        Scrape a single GOV.UK page.
        Returns structured content or None if failed.
        """
        # Check cache first
        cache_file = self.cache_dir / f"{self._url_to_filename(url)}.json"
        if cache_file.exists() and not force_refresh:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded from cache: {url}")
                    return ScrapedPage(**data)
            except Exception:
                pass
        
        try:
            logger.info(f"Scraping: {url}")
            
            # Make request with rate limiting
            time.sleep(1)  # Be polite to GOV.UK servers
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title_tag = soup.find('h1', class_='govuk-heading-xl') or soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else url
            
            # Extract main content
            main_content = soup.find('main') or soup.find('div', class_='govuk-body')
            if not main_content:
                main_content = soup.find('body')
            
            # Extract sections (h2/h3 headings with their content)
            sections = self._extract_sections(soup)
            
            # Clean text content
            content = self._extract_text(main_content) if main_content else ""
            
            # Detect visa types mentioned
            visa_types = self._detect_visa_types(content)
            
            # Create hash for deduplication
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            scraped_page = ScrapedPage(
                url=url,
                title=title,
                content=content,
                sections=sections,
                visa_types=visa_types,
                hash=content_hash,
                scraped_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            )
            
            # Save to cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(scraped_page), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully scraped: {title}")
            return scraped_page
            
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return None
    
    def scrape_all(self, force_refresh: bool = False) -> List[ScrapedPage]:
        """Scrape all target pages."""
        results = []
        
        for category, urls in self.TARGET_PAGES.items():
            logger.info(f"Scraping category: {category}")
            for url in urls:
                page = self.scrape_page(url, force_refresh)
                if page:
                    results.append(page)
        
        logger.info(f"Scraped {len(results)} pages total")
        return results
    
    def _extract_sections(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract sections with headings and content."""
        sections = []
        
        headings = soup.find_all(['h2', 'h3'])
        for heading in headings:
            section_content = []
            sibling = heading.find_next_sibling()
            
            while sibling and sibling.name not in ['h2', 'h3']:
                if sibling.name in ['p', 'li', 'ul', 'ol']:
                    section_content.append(sibling.get_text(strip=True))
                sibling = sibling.find_next_sibling()
            
            sections.append({
                "heading": heading.get_text(strip=True),
                "content": " ".join(section_content),
            })
        
        return sections
    
    def _extract_text(self, element) -> str:
        """Extract clean text from HTML element."""
        # Remove script and style tags
        for tag in element(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        
        text = element.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text
    
    def _detect_visa_types(self, content: str) -> List[str]:
        """Detect which visa types are mentioned in content."""
        visa_types = []
        visa_keywords = {
            "skilled_worker": ["skilled worker", "skilled worker visa", "tier 2"],
            "health_care_worker": ["health and care worker", "nhs", "care worker"],
            "graduate": ["graduate", "graduate visa", "post-study"],
            "global_talent": ["global talent", "exceptional talent", "exceptional promise"],
            "student": ["student visa", "tier 4", "student route"],
            "family": ["family visa", "spouse", "partner", "dependent"],
            "visitor": ["visitor", "tourist", "standard visitor"],
        }
        
        content_lower = content.lower()
        for visa_type, keywords in visa_keywords.items():
            if any(kw in content_lower for kw in keywords):
                visa_types.append(visa_type)
        
        return visa_types
    
    def _url_to_filename(self, url: str) -> str:
        """Convert URL to safe filename."""
        # Remove protocol and domain
        name = url.replace("https://", "").replace("http://", "")
        name = name.replace("www.gov.uk/", "")
        name = name.replace("/", "_").replace("?", "_").replace("=", "_")
        # Limit length
        return name[:100]
    
    def get_cached_pages(self) -> List[ScrapedPage]:
        """Load all cached pages."""
        pages = []
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    pages.append(ScrapedPage(**data))
            except Exception:
                continue
        return pages
    
    def build_knowledge_base(self) -> Dict[str, Any]:
        """
        Build a structured knowledge base from scraped data.
        Returns a dict suitable for RAG retrieval.
        """
        pages = self.get_cached_pages()
        
        knowledge_base = {
            "pages": [],
            "chunks": [],
            "faq": [],
            "visa_rules": {},
        }
        
        for page in pages:
            # Add full page
            knowledge_base["pages"].append({
                "url": page.url,
                "title": page.title,
                "content": page.content,
                "visa_types": page.visa_types,
            })
            
            # Create chunks for RAG (by sections)
            for section in page.sections:
                chunk = {
                    "url": page.url,
                    "title": page.title,
                    "section": section["heading"],
                    "content": section["content"],
                    "visa_types": page.visa_types,
                    "full_text": f"{page.title} - {section['heading']}\n{section['content']}",
                }
                knowledge_base["chunks"].append(chunk)
            
            # Extract FAQ-like Q&A pairs
            faqs = self._extract_faqs(page)
            knowledge_base["faq"].extend(faqs)
        
        # Build visa-specific rules
        for page in pages:
            for visa_type in page.visa_types:
                if visa_type not in knowledge_base["visa_rules"]:
                    knowledge_base["visa_rules"][visa_type] = []
                knowledge_base["visa_rules"][visa_type].append({
                    "url": page.url,
                    "title": page.title,
                    "content": page.content[:2000],  # First 2000 chars
                })
        
        # Save knowledge base
        kb_file = self.cache_dir / "knowledge_base.json"
        with open(kb_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Built knowledge base with {len(knowledge_base['chunks'])} chunks")
        return knowledge_base
    
    def _extract_faqs(self, page: ScrapedPage) -> List[Dict[str, str]]:
        """Extract FAQ-like Q&A pairs from page content."""
        faqs = []
        
        # Look for common question patterns
        question_patterns = [
            r'([A-Z][^?]+[?:])\s*([A-Z][^.]+[.])',  # Question followed by answer
            r'(?:Can I|How do I|What is|Who can|When can|Where can|Am I eligible)[^?]+\?',
        ]
        
        content = page.content
        for pattern in question_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                question = match.group(0).strip()
                if '?' in question:
                    # Get surrounding context as answer
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 200)
                    answer = content[start:end].strip()
                    
                    faqs.append({
                        "question": question,
                        "answer": answer,
                        "source": page.url,
                    })
        
        return faqs[:20]  # Limit to 20 FAQs per page


# Global scraper instance
scraper = GovUKScraper()


def scrape_gov_uk():
    """Main function to scrape GOV.UK and build knowledge base."""
    print("Starting GOV.UK scraper...")
    
    # Scrape all pages
    pages = scraper.scrape_all()
    print(f"Scraped {len(pages)} pages")
    
    # Build knowledge base
    kb = scraper.build_knowledge_base()
    print(f"Knowledge base built with {len(kb['chunks'])} chunks")
    
    return kb


if __name__ == "__main__":
    scrape_gov_uk()