"""
Indonesian Cyber Crime News Scraper
Scrapes articles from CNN Indonesia, Detik, Kompas, Tempo.

Features:
- Random user agents for anti-detection
- Request delays to avoid blocking
- Error handling and retry logic
- Progress tracking
- Backup strategy with alternative sources
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import random
import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from urllib.parse import urljoin, quote_plus

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Random User Agents to avoid detection
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]


# Search keywords for cyber crime in Indonesian
KEYWORDS = [
    'kejahatan siber',
    'cyber crime',
    'serangan siber',
    'kebocoran data',
    'ransomware',
    'phishing',
    'hacker indonesia',
    'data breach',
    'malware',
    'penipuan online',
]


class NewsScraperConfig:
    """Configuration for news scraping."""
    MIN_DELAY = 2  # Minimum delay between requests (seconds)
    MAX_DELAY = 5  # Maximum delay between requests (seconds)
    MAX_RETRIES = 3  # Maximum retries for failed requests
    TIMEOUT = 30  # Request timeout in seconds
    TARGET_ARTICLES = 100  # Target number of articles


def get_random_headers() -> Dict[str, str]:
    """Get random headers to avoid detection."""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }


def random_delay():
    """Add random delay between requests."""
    delay = random.uniform(NewsScraperConfig.MIN_DELAY, NewsScraperConfig.MAX_DELAY)
    time.sleep(delay)


def safe_request(url: str, retries: int = NewsScraperConfig.MAX_RETRIES) -> Optional[requests.Response]:
    """Make a request with retry logic and error handling."""
    for attempt in range(retries):
        try:
            response = requests.get(
                url,
                headers=get_random_headers(),
                timeout=NewsScraperConfig.TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{retries} failed for {url}: {e}")
            if attempt < retries - 1:
                time.sleep(random.uniform(2, 5))
    return None


def parse_indonesian_date(date_str: str) -> Optional[datetime]:
    """Parse Indonesian date formats."""
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    # Indonesian month names
    months_id = {
        'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
        'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
        'september': 9, 'oktober': 10, 'november': 11, 'desember': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mei': 5, 'jun': 6,
        'jul': 7, 'agu': 8, 'sep': 9, 'okt': 10, 'nov': 11, 'des': 12
    }
    
    # Try various formats
    patterns = [
        r'(\d{1,2})\s+(\w+)\s+(\d{4})',  # 15 Januari 2024
        r'(\d{4})-(\d{2})-(\d{2})',       # 2024-01-15
        r'(\d{2})/(\d{2})/(\d{4})',       # 15/01/2024
    ]
    
    for pattern in patterns:
        match = re.search(pattern, date_str, re.IGNORECASE)
        if match:
            groups = match.groups()
            try:
                if len(groups) == 3:
                    if pattern == patterns[0]:  # Indonesian format
                        day = int(groups[0])
                        month_str = groups[1].lower()
                        year = int(groups[2])
                        month = months_id.get(month_str, 1)
                        return datetime(year, month, day)
                    elif pattern == patterns[1]:  # ISO format
                        return datetime(int(groups[0]), int(groups[1]), int(groups[2]))
                    elif pattern == patterns[2]:  # DD/MM/YYYY
                        return datetime(int(groups[2]), int(groups[1]), int(groups[0]))
            except (ValueError, KeyError):
                continue
    
    # Fallback: try pandas
    try:
        return pd.to_datetime(date_str).to_pydatetime()
    except:
        return None


# ============== CNN INDONESIA SCRAPER ==============

def scrape_cnn_indonesia(keywords: List[str], max_articles: int = 30) -> List[Dict]:
    """Scrape cyber crime articles from CNN Indonesia."""
    articles = []
    base_url = "https://www.cnnindonesia.com"
    search_url = "https://www.cnnindonesia.com/search/?query={}"
    
    logger.info("Starting CNN Indonesia scraping...")
    
    for keyword in keywords:
        if len(articles) >= max_articles:
            break
            
        logger.info(f"  Searching CNN Indonesia: '{keyword}'")
        url = search_url.format(quote_plus(keyword))
        
        response = safe_request(url)
        if not response:
            continue
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find article links
        article_links = soup.select('article a[href*="/teknologi/"], article a[href*="/nasional/"]')
        
        for link in article_links[:5]:  # Limit per keyword
            if len(articles) >= max_articles:
                break
                
            article_url = link.get('href', '')
            if not article_url.startswith('http'):
                article_url = urljoin(base_url, article_url)
            
            # Check for duplicates
            if any(a['url'] == article_url for a in articles):
                continue
            
            random_delay()
            article = scrape_cnn_article(article_url)
            if article:
                articles.append(article)
                logger.info(f"    ✓ Scraped: {article['title'][:50]}...")
    
    return articles


def scrape_cnn_article(url: str) -> Optional[Dict]:
    """Scrape single CNN Indonesia article."""
    response = safe_request(url)
    if not response:
        return None
    
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title_elem = soup.select_one('h1.title, h1')
        title = title_elem.get_text(strip=True) if title_elem else None
        
        # Extract date
        date_elem = soup.select_one('.date, time, [class*="date"]')
        date_str = date_elem.get_text(strip=True) if date_elem else None
        date = parse_indonesian_date(date_str) if date_str else None
        
        # Extract content
        content_elem = soup.select('div.detail-text p, article p, .content p')
        content = ' '.join([p.get_text(strip=True) for p in content_elem])
        
        if title and len(content) > 100:
            return {
                'title': title,
                'url': url,
                'source': 'CNN Indonesia',
                'date': date,
                'content': content[:5000],  # Limit content length
                'scraped_at': datetime.now()
            }
    except Exception as e:
        logger.error(f"Error parsing CNN article {url}: {e}")
    
    return None


# ============== DETIK SCRAPER ==============

def scrape_detik(keywords: List[str], max_articles: int = 30) -> List[Dict]:
    """Scrape cyber crime articles from Detik.com."""
    articles = []
    search_url = "https://www.detik.com/search/searchall?query={}"
    
    logger.info("Starting Detik.com scraping...")
    
    for keyword in keywords:
        if len(articles) >= max_articles:
            break
            
        logger.info(f"  Searching Detik: '{keyword}'")
        url = search_url.format(quote_plus(keyword))
        
        response = safe_request(url)
        if not response:
            continue
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find article links
        article_links = soup.select('article h2 a, .list-content__item a')
        
        for link in article_links[:5]:
            if len(articles) >= max_articles:
                break
                
            article_url = link.get('href', '')
            
            if any(a['url'] == article_url for a in articles):
                continue
            
            random_delay()
            article = scrape_detik_article(article_url)
            if article:
                articles.append(article)
                logger.info(f"    ✓ Scraped: {article['title'][:50]}...")
    
    return articles


def scrape_detik_article(url: str) -> Optional[Dict]:
    """Scrape single Detik article."""
    response = safe_request(url)
    if not response:
        return None
    
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_elem = soup.select_one('h1.detail__title, h1')
        title = title_elem.get_text(strip=True) if title_elem else None
        
        date_elem = soup.select_one('.detail__date, time')
        date_str = date_elem.get_text(strip=True) if date_elem else None
        date = parse_indonesian_date(date_str) if date_str else None
        
        content_elem = soup.select('div.detail__body-text p, article p')
        content = ' '.join([p.get_text(strip=True) for p in content_elem])
        
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


# ============== KOMPAS SCRAPER ==============

def scrape_kompas(keywords: List[str], max_articles: int = 30) -> List[Dict]:
    """Scrape cyber crime articles from Kompas.com."""
    articles = []
    search_url = "https://www.kompas.com/search?q={}"
    
    logger.info("Starting Kompas.com scraping...")
    
    for keyword in keywords:
        if len(articles) >= max_articles:
            break
            
        logger.info(f"  Searching Kompas: '{keyword}'")
        url = search_url.format(quote_plus(keyword))
        
        response = safe_request(url)
        if not response:
            continue
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        article_links = soup.select('.article__list a, .latest--indeks a')
        
        for link in article_links[:5]:
            if len(articles) >= max_articles:
                break
                
            article_url = link.get('href', '')
            
            if any(a['url'] == article_url for a in articles):
                continue
            
            random_delay()
            article = scrape_kompas_article(article_url)
            if article:
                articles.append(article)
                logger.info(f"    ✓ Scraped: {article['title'][:50]}...")
    
    return articles


def scrape_kompas_article(url: str) -> Optional[Dict]:
    """Scrape single Kompas article."""
    response = safe_request(url)
    if not response:
        return None
    
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_elem = soup.select_one('h1.read__title, h1')
        title = title_elem.get_text(strip=True) if title_elem else None
        
        date_elem = soup.select_one('.read__time, time')
        date_str = date_elem.get_text(strip=True) if date_elem else None
        date = parse_indonesian_date(date_str) if date_str else None
        
        content_elem = soup.select('div.read__content p, article p')
        content = ' '.join([p.get_text(strip=True) for p in content_elem])
        
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


# ============== TEMPO SCRAPER ==============

def scrape_tempo(keywords: List[str], max_articles: int = 30) -> List[Dict]:
    """Scrape cyber crime articles from Tempo.co."""
    articles = []
    search_url = "https://www.tempo.co/search?q={}"
    
    logger.info("Starting Tempo.co scraping...")
    
    for keyword in keywords:
        if len(articles) >= max_articles:
            break
            
        logger.info(f"  Searching Tempo: '{keyword}'")
        url = search_url.format(quote_plus(keyword))
        
        response = safe_request(url)
        if not response:
            continue
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        article_links = soup.select('.card-box a, article a')
        
        for link in article_links[:5]:
            if len(articles) >= max_articles:
                break
                
            article_url = link.get('href', '')
            if not article_url.startswith('http'):
                article_url = 'https:' + article_url if article_url.startswith('//') else article_url
            
            if any(a['url'] == article_url for a in articles):
                continue
            
            random_delay()
            article = scrape_tempo_article(article_url)
            if article:
                articles.append(article)
                logger.info(f"    ✓ Scraped: {article['title'][:50]}...")
    
    return articles


def scrape_tempo_article(url: str) -> Optional[Dict]:
    """Scrape single Tempo article."""
    response = safe_request(url)
    if not response:
        return None
    
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_elem = soup.select_one('h1.title, h1')
        title = title_elem.get_text(strip=True) if title_elem else None
        
        date_elem = soup.select_one('.date, time, .detail-date')
        date_str = date_elem.get_text(strip=True) if date_elem else None
        date = parse_indonesian_date(date_str) if date_str else None
        
        content_elem = soup.select('div.detail-konten p, article p, .content-artikel p')
        content = ' '.join([p.get_text(strip=True) for p in content_elem])
        
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


# ============== BACKUP: LIPUTAN6 SCRAPER ==============

def scrape_liputan6(keywords: List[str], max_articles: int = 20) -> List[Dict]:
    """Backup scraper for Liputan6.com."""
    articles = []
    search_url = "https://www.liputan6.com/search?q={}"
    
    logger.info("Starting Liputan6 (backup) scraping...")
    
    for keyword in keywords[:3]:  # Limit keywords for backup
        if len(articles) >= max_articles:
            break
            
        logger.info(f"  Searching Liputan6: '{keyword}'")
        url = search_url.format(quote_plus(keyword))
        
        response = safe_request(url)
        if not response:
            continue
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        article_links = soup.select('article a, .articles--rows a')
        
        for link in article_links[:5]:
            if len(articles) >= max_articles:
                break
                
            article_url = link.get('href', '')
            
            if any(a['url'] == article_url for a in articles):
                continue
            
            random_delay()
            
            try:
                response = safe_request(article_url)
                if response:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    title_elem = soup.select_one('h1.read-page--header--title, h1')
                    title = title_elem.get_text(strip=True) if title_elem else None
                    
                    date_elem = soup.select_one('.read-page--header--author__datetime, time')
                    date_str = date_elem.get_text(strip=True) if date_elem else None
                    date = parse_indonesian_date(date_str) if date_str else None
                    
                    content_elem = soup.select('div.article-content-body p')
                    content = ' '.join([p.get_text(strip=True) for p in content_elem])
                    
                    if title and len(content) > 100:
                        articles.append({
                            'title': title,
                            'url': article_url,
                            'source': 'Liputan6.com',
                            'date': date,
                            'content': content[:5000],
                            'scraped_at': datetime.now()
                        })
                        logger.info(f"    ✓ Scraped: {title[:50]}...")
            except Exception as e:
                logger.error(f"Error scraping Liputan6: {e}")
    
    return articles


# ============== MAIN SCRAPER ==============

def run_full_scraper(target_articles: int = 100) -> pd.DataFrame:
    """
    Run full scraping process from all sources.
    
    Args:
        target_articles: Target number of articles to collect
        
    Returns:
        DataFrame with all scraped articles
    """
    all_articles = []
    
    print("=" * 60)
    print("🔍 Indonesian Cyber Crime News Scraper")
    print("=" * 60)
    print(f"Target: {target_articles} articles")
    print(f"Sources: CNN Indonesia, Detik, Kompas, Tempo, Liputan6")
    print(f"Keywords: {len(KEYWORDS)} search terms")
    print("=" * 60)
    
    articles_per_source = target_articles // 4
    
    # Scrape from each source
    sources_scrapers = [
        ('CNN Indonesia', scrape_cnn_indonesia),
        ('Detik.com', scrape_detik),
        ('Kompas.com', scrape_kompas),
        ('Tempo.co', scrape_tempo),
    ]
    
    for source_name, scraper_func in sources_scrapers:
        try:
            articles = scraper_func(KEYWORDS, max_articles=articles_per_source)
            all_articles.extend(articles)
            print(f"\n✓ {source_name}: {len(articles)} articles scraped")
        except Exception as e:
            logger.error(f"Error scraping {source_name}: {e}")
            print(f"\n✗ {source_name}: Failed - {e}")
    
    # If not enough articles, use backup source
    if len(all_articles) < target_articles * 0.7:
        print("\n⚠️ Not enough articles, using backup source (Liputan6)...")
        try:
            backup_articles = scrape_liputan6(KEYWORDS, max_articles=20)
            all_articles.extend(backup_articles)
            print(f"✓ Liputan6 (backup): {len(backup_articles)} articles scraped")
        except Exception as e:
            logger.error(f"Backup scraper failed: {e}")
    
    # Create DataFrame
    df = pd.DataFrame(all_articles)
    
    # Clean and filter data
    if len(df) > 0:
        # Remove duplicates
        df = df.drop_duplicates(subset=['url'])
        
        # Filter by date (2023-2025)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df[df['date'].notna()]
            df = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2025-12-31')]
        
        # Sort by date
        df = df.sort_values('date', ascending=False).reset_index(drop=True)
    
    print("\n" + "=" * 60)
    print(f"📊 SCRAPING COMPLETE")
    print(f"   Total articles: {len(df)}")
    print(f"   Sources: {df['source'].nunique() if len(df) > 0 else 0}")
    if len(df) > 0 and 'date' in df.columns:
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print("=" * 60)
    
    return df


def save_scraped_data(df: pd.DataFrame, output_dir: str = None) -> str:
    """Save scraped data to CSV."""
    if output_dir is None:
        output_dir = Path(__file__).parent / 'data' / 'external'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    output_path = output_dir / f'scraped_news_{timestamp}.csv'
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} articles to {output_path}")
    
    return str(output_path)


if __name__ == '__main__':
    print("\n🚀 Starting news scraper...\n")
    
    # Run scraper
    df = run_full_scraper(target_articles=100)
    
    # Save results
    if len(df) > 0:
        output_path = save_scraped_data(df)
        print(f"\n✅ Data saved to: {output_path}")
        
        # Show sample
        print("\n📰 Sample articles:")
        for _, row in df.head(5).iterrows():
            print(f"  - [{row['source']}] {row['title'][:60]}...")
    else:
        print("\n❌ No articles scraped. Check your internet connection.")
