"""
Advanced Indonesian Cyber Crime News Scraper with Selenium
Supports JavaScript-rendered websites for comprehensive data collection.

Features:
- Selenium WebDriver for JS-rendered content
- Multiple scraping strategies per source
- Google News as backup source
- Robust error handling and retry logic
- Anti-detection measures
"""

import os
import sys
import time
import random
import re
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import logging
from urllib.parse import urljoin, quote_plus

# Basic imports
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============== CONFIGURATION ==============

KEYWORDS = [
    'kejahatan siber indonesia',
    'serangan siber indonesia',
    'kebocoran data indonesia',
    'ransomware indonesia',
    'phishing indonesia', 
    'hacker indonesia',
    'cyber attack indonesia',
    'data breach indonesia',
    'penipuan online indonesia',
    'malware indonesia',
    'BSSN serangan siber',
    'PDN ransomware',
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]


class SeleniumScraper:
    """Base Selenium scraper with anti-detection."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.scraped_urls: Set[str] = set()
        
    def start_driver(self):
        """Initialize Chrome WebDriver with anti-detection options."""
        options = Options()
        
        if self.headless:
            options.add_argument('--headless=new')
        
        # Anti-detection options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument(f'--user-agent={random.choice(USER_AGENTS)}')
        options.add_argument('--disable-notifications')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Use webdriver-manager to auto-install ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info("Chrome WebDriver started successfully")
        
    def stop_driver(self):
        """Close WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Chrome WebDriver stopped")
    
    def random_delay(self, min_sec: float = 1, max_sec: float = 3):
        """Random delay to mimic human behavior."""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def scroll_page(self, scrolls: int = 3):
        """Scroll page to load dynamic content."""
        for i in range(scrolls):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(0.5, 1.5))
    
    def get_page_source(self, url: str, wait_time: int = 10) -> Optional[str]:
        """Get page source with wait for JavaScript rendering."""
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            self.random_delay()
            return self.driver.page_source
        except Exception as e:
            logger.error(f"Error loading {url}: {e}")
            return None


# ============== CNN INDONESIA SELENIUM SCRAPER ==============

class CNNIndonesiaScraper(SeleniumScraper):
    """Scraper for CNN Indonesia using Selenium."""
    
    BASE_URL = "https://www.cnnindonesia.com"
    SEARCH_URL = "https://www.cnnindonesia.com/search?query={}"
    
    def scrape_search_results(self, keyword: str, max_articles: int = 10) -> List[Dict]:
        """Scrape search results from CNN Indonesia."""
        articles = []
        url = self.SEARCH_URL.format(quote_plus(keyword))
        
        logger.info(f"CNN Indonesia: Searching '{keyword}'")
        
        page_source = self.get_page_source(url)
        if not page_source:
            return articles
        
        # Scroll to load more results
        self.scroll_page(2)
        page_source = self.driver.page_source
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find article links
        article_links = soup.select('article a, .list a, .media__title a')
        
        for link in article_links:
            if len(articles) >= max_articles:
                break
                
            href = link.get('href', '')
            if not href or href in self.scraped_urls:
                continue
            
            if not href.startswith('http'):
                href = urljoin(self.BASE_URL, href)
            
            # Only CNN Indonesia articles
            if 'cnnindonesia.com' not in href:
                continue
                
            self.scraped_urls.add(href)
            self.random_delay(1, 2)
            
            article = self.scrape_article(href)
            if article:
                articles.append(article)
                logger.info(f"  ✓ {article['title'][:50]}...")
        
        return articles
    
    def scrape_article(self, url: str) -> Optional[Dict]:
        """Scrape single CNN Indonesia article."""
        page_source = self.get_page_source(url)
        if not page_source:
            return None
        
        try:
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Title
            title_elem = soup.select_one('h1')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            # Date
            date_elem = soup.select_one('time, .date, [class*="date"]')
            date = self.parse_date(date_elem.get_text(strip=True) if date_elem else None)
            
            # Content
            content_elems = soup.select('div.detail-text p, article p, .content p')
            content = ' '.join([p.get_text(strip=True) for p in content_elems])
            
            if title and len(content) > 100:
                return {
                    'title': title,
                    'url': url,
                    'source': 'CNN Indonesia',
                    'date': date,
                    'content': content[:5000],
                    'scraped_at': datetime.now()
                }
        except Exception as e:
            logger.error(f"Error parsing CNN article {url}: {e}")
        
        return None
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse CNN Indonesia date format."""
        if not date_str:
            return None
        try:
            # Try various formats
            for fmt in ['%d/%m/%Y, %H:%M', '%d %b %Y %H:%M', '%Y-%m-%d']:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except:
                    continue
            return pd.to_datetime(date_str).to_pydatetime()
        except:
            return None


# ============== KOMPAS SELENIUM SCRAPER ==============

class KompasScraper(SeleniumScraper):
    """Scraper for Kompas.com using Selenium."""
    
    BASE_URL = "https://www.kompas.com"
    # Use tag-based search which works better
    TAG_URL = "https://www.kompas.com/tag/{}"
    
    def scrape_tag_results(self, tag: str, max_articles: int = 10) -> List[Dict]:
        """Scrape tag page from Kompas."""
        articles = []
        # Clean tag for URL
        tag_slug = tag.lower().replace(' ', '-').replace('indonesia', '').strip('-')
        url = self.TAG_URL.format(tag_slug)
        
        logger.info(f"Kompas: Searching tag '{tag_slug}'")
        
        page_source = self.get_page_source(url)
        if not page_source:
            return articles
        
        self.scroll_page(2)
        page_source = self.driver.page_source
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        article_links = soup.select('.article__list a, .article__title a, h2 a, h3 a')
        
        for link in article_links:
            if len(articles) >= max_articles:
                break
                
            href = link.get('href', '')
            if not href or href in self.scraped_urls:
                continue
            
            if 'kompas.com' not in href:
                continue
                
            self.scraped_urls.add(href)
            self.random_delay(1, 2)
            
            article = self.scrape_article(href)
            if article:
                articles.append(article)
                logger.info(f"  ✓ {article['title'][:50]}...")
        
        return articles
    
    def scrape_article(self, url: str) -> Optional[Dict]:
        """Scrape single Kompas article."""
        page_source = self.get_page_source(url)
        if not page_source:
            return None
        
        try:
            soup = BeautifulSoup(page_source, 'html.parser')
            
            title_elem = soup.select_one('h1.read__title, h1')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            date_elem = soup.select_one('.read__time, time')
            date = self.parse_date(date_elem.get_text(strip=True) if date_elem else None)
            
            content_elems = soup.select('div.read__content p, article p')
            content = ' '.join([p.get_text(strip=True) for p in content_elems])
            
            if title and len(content) > 100:
                return {
                    'title': title,
                    'url': url,
                    'source': 'Kompas.com',
                    'date': date,
                    'content': content[:5000],
                    'scraped_at': datetime.now()
                }
        except Exception as e:
            logger.error(f"Error parsing Kompas article {url}: {e}")
        
        return None
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return pd.to_datetime(date_str).to_pydatetime()
        except:
            return None


# ============== TEMPO SELENIUM SCRAPER ==============

class TempoScraper(SeleniumScraper):
    """Scraper for Tempo.co using Selenium."""
    
    BASE_URL = "https://www.tempo.co"
    SEARCH_URL = "https://www.tempo.co/search?q={}"
    
    def scrape_search_results(self, keyword: str, max_articles: int = 10) -> List[Dict]:
        """Scrape search results from Tempo."""
        articles = []
        url = self.SEARCH_URL.format(quote_plus(keyword))
        
        logger.info(f"Tempo: Searching '{keyword}'")
        
        page_source = self.get_page_source(url)
        if not page_source:
            return articles
        
        self.scroll_page(3)
        page_source = self.driver.page_source
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        article_links = soup.select('.card-box__heading a, article a, .title a, h2 a')
        
        for link in article_links:
            if len(articles) >= max_articles:
                break
                
            href = link.get('href', '')
            if not href or href in self.scraped_urls:
                continue
            
            if not href.startswith('http'):
                href = 'https:' + href if href.startswith('//') else urljoin(self.BASE_URL, href)
            
            if 'tempo.co' not in href:
                continue
                
            self.scraped_urls.add(href)
            self.random_delay(1, 2)
            
            article = self.scrape_article(href)
            if article:
                articles.append(article)
                logger.info(f"  ✓ {article['title'][:50]}...")
        
        return articles
    
    def scrape_article(self, url: str) -> Optional[Dict]:
        """Scrape single Tempo article."""
        page_source = self.get_page_source(url)
        if not page_source:
            return None
        
        try:
            soup = BeautifulSoup(page_source, 'html.parser')
            
            title_elem = soup.select_one('h1.title, h1')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            date_elem = soup.select_one('.date, time, .detail-date')
            date = self.parse_date(date_elem.get_text(strip=True) if date_elem else None)
            
            content_elems = soup.select('div.detail-konten p, article p, .content p')
            content = ' '.join([p.get_text(strip=True) for p in content_elems])
            
            if title and len(content) > 100:
                return {
                    'title': title,
                    'url': url,
                    'source': 'Tempo.co',
                    'date': date,
                    'content': content[:5000],
                    'scraped_at': datetime.now()
                }
        except Exception as e:
            logger.error(f"Error parsing Tempo article {url}: {e}")
        
        return None
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return pd.to_datetime(date_str).to_pydatetime()
        except:
            return None


# ============== GOOGLE NEWS SCRAPER (BACKUP) ==============

class GoogleNewsScraper(SeleniumScraper):
    """Backup scraper using Google News search."""
    
    SEARCH_URL = "https://www.google.com/search?q={}&tbm=nws&tbs=cdr:1,cd_min:1/1/2023,cd_max:12/31/2025"
    
    def scrape_search(self, keyword: str, max_articles: int = 15) -> List[Dict]:
        """Scrape Google News search results."""
        articles = []
        url = self.SEARCH_URL.format(quote_plus(keyword + " site:detik.com OR site:kompas.com OR site:tempo.co OR site:cnnindonesia.com"))
        
        logger.info(f"Google News: Searching '{keyword}'")
        
        page_source = self.get_page_source(url, wait_time=15)
        if not page_source:
            return articles
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find news result links
        news_links = soup.select('div[role="heading"] a, .SoaBEf a, a[href*="detik.com"], a[href*="kompas.com"], a[href*="tempo.co"], a[href*="cnnindonesia.com"]')
        
        for link in news_links:
            if len(articles) >= max_articles:
                break
            
            href = link.get('href', '')
            
            # Extract actual URL from Google redirect
            if '/url?q=' in href:
                import urllib.parse
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                href = parsed.get('q', [href])[0]
            
            if not href or href in self.scraped_urls:
                continue
            
            # Filter to Indonesian news sites
            if not any(site in href for site in ['detik.com', 'kompas.com', 'tempo.co', 'cnnindonesia.com', 'liputan6.com']):
                continue
            
            title = link.get_text(strip=True)
            if not title or len(title) < 10:
                continue
            
            self.scraped_urls.add(href)
            
            # Get source from URL
            if 'detik.com' in href:
                source = 'Detik.com'
            elif 'kompas.com' in href:
                source = 'Kompas.com'
            elif 'tempo.co' in href:
                source = 'Tempo.co'
            elif 'cnnindonesia.com' in href:
                source = 'CNN Indonesia'
            elif 'liputan6.com' in href:
                source = 'Liputan6.com'
            else:
                source = 'Other'
            
            articles.append({
                'title': title,
                'url': href,
                'source': source,
                'date': None,  # Will be extracted later
                'content': '',  # To be filled by article scraper
                'scraped_at': datetime.now()
            })
            logger.info(f"  ✓ Found: {title[:50]}...")
        
        return articles


# ============== DETIK SELENIUM SCRAPER ==============

class DetikScraper(SeleniumScraper):
    """Enhanced Detik scraper with Selenium."""
    
    BASE_URL = "https://www.detik.com"
    SEARCH_URL = "https://www.detik.com/search/searchall?query={}&sortby=time"
    
    def scrape_search_results(self, keyword: str, max_articles: int = 15) -> List[Dict]:
        """Scrape Detik search results."""
        articles = []
        url = self.SEARCH_URL.format(quote_plus(keyword))
        
        logger.info(f"Detik: Searching '{keyword}'")
        
        page_source = self.get_page_source(url)
        if not page_source:
            return articles
        
        self.scroll_page(3)
        page_source = self.driver.page_source
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        article_links = soup.select('article h2 a, .media__title a, h3 a')
        
        for link in article_links:
            if len(articles) >= max_articles:
                break
            
            href = link.get('href', '')
            if not href or href in self.scraped_urls:
                continue
            
            if 'detik.com' not in href:
                continue
            
            self.scraped_urls.add(href)
            self.random_delay(1, 2)
            
            article = self.scrape_article(href)
            if article:
                articles.append(article)
                logger.info(f"  ✓ {article['title'][:50]}...")
        
        return articles
    
    def scrape_article(self, url: str) -> Optional[Dict]:
        """Scrape single Detik article."""
        page_source = self.get_page_source(url)
        if not page_source:
            return None
        
        try:
            soup = BeautifulSoup(page_source, 'html.parser')
            
            title_elem = soup.select_one('h1.detail__title, h1')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            date_elem = soup.select_one('.detail__date, time')
            date = self.parse_date(date_elem.get_text(strip=True) if date_elem else None)
            
            content_elems = soup.select('div.detail__body-text p, article p')
            content = ' '.join([p.get_text(strip=True) for p in content_elems])
            
            if title and len(content) > 100:
                return {
                    'title': title,
                    'url': url,
                    'source': 'Detik.com',
                    'date': date,
                    'content': content[:5000],
                    'scraped_at': datetime.now()
                }
        except Exception as e:
            logger.error(f"Error parsing Detik article {url}: {e}")
        
        return None
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return pd.to_datetime(date_str).to_pydatetime()
        except:
            return None


# ============== MAIN SCRAPER ORCHESTRATOR ==============

def run_selenium_scraper(target_articles: int = 100) -> pd.DataFrame:
    """
    Run comprehensive Selenium-based scraping.
    
    Args:
        target_articles: Target number of articles
        
    Returns:
        DataFrame with all scraped articles
    """
    all_articles = []
    
    print("=" * 70)
    print("🕷️ Advanced Indonesian Cyber Crime News Scraper (Selenium)")
    print("=" * 70)
    print(f"Target: {target_articles} articles")
    print(f"Keywords: {len(KEYWORDS)} search terms")
    print("=" * 70)
    
    # Initialize scrapers
    scrapers = {
        'detik': DetikScraper(headless=True),
        'cnn': CNNIndonesiaScraper(headless=True),
        'kompas': KompasScraper(headless=True),
        'tempo': TempoScraper(headless=True),
        'google': GoogleNewsScraper(headless=True),
    }
    
    articles_per_source = target_articles // 4
    
    # 1. Scrape Detik
    try:
        print("\n📰 Scraping Detik.com...")
        scrapers['detik'].start_driver()
        for keyword in KEYWORDS[:5]:
            if len([a for a in all_articles if a['source'] == 'Detik.com']) >= articles_per_source:
                break
            articles = scrapers['detik'].scrape_search_results(keyword, max_articles=5)
            all_articles.extend(articles)
        scrapers['detik'].stop_driver()
        detik_count = len([a for a in all_articles if a['source'] == 'Detik.com'])
        print(f"  ✓ Detik: {detik_count} articles")
    except Exception as e:
        logger.error(f"Detik scraper error: {e}")
        scrapers['detik'].stop_driver()
    
    # 2. Scrape CNN Indonesia
    try:
        print("\n📰 Scraping CNN Indonesia...")
        scrapers['cnn'].start_driver()
        for keyword in KEYWORDS[:5]:
            if len([a for a in all_articles if a['source'] == 'CNN Indonesia']) >= articles_per_source:
                break
            articles = scrapers['cnn'].scrape_search_results(keyword, max_articles=5)
            all_articles.extend(articles)
        scrapers['cnn'].stop_driver()
        cnn_count = len([a for a in all_articles if a['source'] == 'CNN Indonesia'])
        print(f"  ✓ CNN Indonesia: {cnn_count} articles")
    except Exception as e:
        logger.error(f"CNN scraper error: {e}")
        scrapers['cnn'].stop_driver()
    
    # 3. Scrape Kompas (using tags)
    try:
        print("\n📰 Scraping Kompas.com...")
        scrapers['kompas'].start_driver()
        kompas_tags = ['siber', 'hacker', 'ransomware', 'phishing', 'kebocoran-data']
        for tag in kompas_tags:
            if len([a for a in all_articles if a['source'] == 'Kompas.com']) >= articles_per_source:
                break
            articles = scrapers['kompas'].scrape_tag_results(tag, max_articles=5)
            all_articles.extend(articles)
        scrapers['kompas'].stop_driver()
        kompas_count = len([a for a in all_articles if a['source'] == 'Kompas.com'])
        print(f"  ✓ Kompas: {kompas_count} articles")
    except Exception as e:
        logger.error(f"Kompas scraper error: {e}")
        scrapers['kompas'].stop_driver()
    
    # 4. Scrape Tempo
    try:
        print("\n📰 Scraping Tempo.co...")
        scrapers['tempo'].start_driver()
        for keyword in KEYWORDS[:5]:
            if len([a for a in all_articles if a['source'] == 'Tempo.co']) >= articles_per_source:
                break
            articles = scrapers['tempo'].scrape_search_results(keyword, max_articles=5)
            all_articles.extend(articles)
        scrapers['tempo'].stop_driver()
        tempo_count = len([a for a in all_articles if a['source'] == 'Tempo.co'])
        print(f"  ✓ Tempo: {tempo_count} articles")
    except Exception as e:
        logger.error(f"Tempo scraper error: {e}")
        scrapers['tempo'].stop_driver()
    
    # 5. Backup: Google News if not enough articles
    if len(all_articles) < target_articles * 0.5:
        try:
            print("\n🔍 Using Google News backup...")
            scrapers['google'].start_driver()
            for keyword in ['kejahatan siber', 'ransomware indonesia', 'kebocoran data', 'hacker indonesia', 'BSSN']:
                articles = scrapers['google'].scrape_search(keyword, max_articles=10)
                all_articles.extend(articles)
                if len(all_articles) >= target_articles:
                    break
            scrapers['google'].stop_driver()
            print(f"  ✓ Google News backup complete")
        except Exception as e:
            logger.error(f"Google News scraper error: {e}")
            scrapers['google'].stop_driver()
    
    # Create DataFrame
    df = pd.DataFrame(all_articles)
    
    if len(df) > 0:
        # Remove duplicates by URL
        df = df.drop_duplicates(subset=['url'])
        
        # Remove duplicates by title similarity
        df = df.drop_duplicates(subset=['title'])
        
        # Sort by date
        df = df.sort_values('scraped_at', ascending=False).reset_index(drop=True)
    
    print("\n" + "=" * 70)
    print("📊 SCRAPING COMPLETE")
    print(f"   Total articles: {len(df)}")
    if len(df) > 0:
        print(f"   Sources: {df['source'].value_counts().to_dict()}")
    print("=" * 70)
    
    return df


def save_results(df: pd.DataFrame, output_dir: str = None) -> str:
    """Save scraped results to CSV."""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent.parent / 'data' / 'external'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    output_path = output_dir / f'selenium_scraped_news_{timestamp}.csv'
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} articles to {output_path}")
    
    return str(output_path)


if __name__ == '__main__':
    print("\n🚀 Starting Selenium news scraper...\n")
    
    # Run scraper
    df = run_selenium_scraper(target_articles=100)
    
    # Save results
    if len(df) > 0:
        output_path = save_results(df)
        print(f"\n✅ Data saved to: {output_path}")
        
        # Show sample
        print("\n📰 Sample articles:")
        for _, row in df.head(10).iterrows():
            print(f"  - [{row['source']}] {row['title'][:60]}...")
    else:
        print("\n❌ No articles scraped.")
