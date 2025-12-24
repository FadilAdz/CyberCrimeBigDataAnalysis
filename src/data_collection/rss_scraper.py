"""
Alternative News Scraper - API and RSS Based
Uses RSS feeds and direct API endpoints to scrape Indonesian news.

No Selenium required - works with requests only.
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
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional
import logging
from urllib.parse import urljoin, quote_plus

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]


KEYWORDS = [
    'kejahatan siber',
    'serangan siber',
    'kebocoran data',
    'ransomware',
    'phishing',
    'hacker',
    'cyber crime',
    'data breach',
    'malware',
    'penipuan online',
    'BSSN',
    'PDN diretas',
]


def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
    }


def delay():
    time.sleep(random.uniform(1, 3))


def safe_request(url: str, retries: int = 3) -> Optional[requests.Response]:
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=get_headers(), timeout=30)
            resp.raise_for_status()
            return resp
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return None


def parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    
    months = {
        'januari': 1, 'februari': 2, 'maret': 3, 'april': 4, 'mei': 5, 'juni': 6,
        'juli': 7, 'agustus': 8, 'september': 9, 'oktober': 10, 'november': 11, 'desember': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mei': 5, 'jun': 6,
        'jul': 7, 'agu': 8, 'sep': 9, 'okt': 10, 'nov': 11, 'des': 12
    }
    
    try:
        return pd.to_datetime(date_str).to_pydatetime()
    except:
        pass
    
    match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date_str, re.I)
    if match:
        try:
            d, m, y = match.groups()
            return datetime(int(y), months.get(m.lower(), 1), int(d))
        except:
            pass
    return None


# ============== DETIK RSS SCRAPER ==============

def scrape_detik_rss() -> List[Dict]:
    """Scrape Detik via RSS feeds."""
    articles = []
    
    # Detik RSS feeds that may contain cyber crime news
    rss_urls = [
        'https://rss.detik.com/index.php/inet',
        'https://rss.detik.com/index.php/detiknews',
        'https://rss.detik.com/index.php/finance',
    ]
    
    logger.info("Scraping Detik RSS feeds...")
    
    for rss_url in rss_urls:
        try:
            resp = safe_request(rss_url)
            if not resp:
                continue
            
            # Parse RSS XML
            root = ET.fromstring(resp.content)
            
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                desc_elem = item.find('description')
                pubdate_elem = item.find('pubDate')
                
                if title_elem is None or link_elem is None:
                    continue
                
                title = title_elem.text or ''
                
                # Filter for cyber crime related
                cyber_keywords = ['siber', 'hacker', 'ransomware', 'phishing', 'malware', 
                                 'kebocoran', 'data', 'cyber', 'peretasan', 'hacking', 
                                 'penipuan online', 'kejahatan digital', 'BSSN', 'PDN']
                
                if not any(kw.lower() in title.lower() for kw in cyber_keywords):
                    continue
                
                articles.append({
                    'title': title,
                    'url': link_elem.text or '',
                    'source': 'Detik.com',
                    'date': parse_date(pubdate_elem.text if pubdate_elem is not None else None),
                    'content': desc_elem.text if desc_elem is not None else '',
                    'scraped_at': datetime.now()
                })
                
        except Exception as e:
            logger.error(f"Error parsing Detik RSS: {e}")
    
    logger.info(f"  ✓ Detik RSS: {len(articles)} articles")
    return articles


# ============== KOMPAS RSS SCRAPER ==============

def scrape_kompas_rss() -> List[Dict]:
    """Scrape Kompas via RSS feeds."""
    articles = []
    
    rss_urls = [
        'https://rss.kompas.com/tekno',
        'https://rss.kompas.com/nasional',
        'https://rss.kompas.com/sains',
    ]
    
    logger.info("Scraping Kompas RSS feeds...")
    
    for rss_url in rss_urls:
        try:
            resp = safe_request(rss_url)
            if not resp:
                continue
            
            root = ET.fromstring(resp.content)
            
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                desc_elem = item.find('description')
                pubdate_elem = item.find('pubDate')
                
                if title_elem is None or link_elem is None:
                    continue
                
                title = title_elem.text or ''
                
                cyber_keywords = ['siber', 'hacker', 'ransomware', 'phishing', 'malware', 
                                 'kebocoran', 'data breach', 'cyber', 'peretasan', 
                                 'penipuan', 'BSSN', 'PDN']
                
                if not any(kw.lower() in title.lower() for kw in cyber_keywords):
                    continue
                
                articles.append({
                    'title': title,
                    'url': link_elem.text or '',
                    'source': 'Kompas.com',
                    'date': parse_date(pubdate_elem.text if pubdate_elem is not None else None),
                    'content': desc_elem.text if desc_elem is not None else '',
                    'scraped_at': datetime.now()
                })
                
        except Exception as e:
            logger.error(f"Error parsing Kompas RSS: {e}")
    
    logger.info(f"  ✓ Kompas RSS: {len(articles)} articles")
    return articles


# ============== TEMPO RSS SCRAPER ==============

def scrape_tempo_rss() -> List[Dict]:
    """Scrape Tempo via RSS feeds."""
    articles = []
    
    rss_urls = [
        'https://rss.tempo.co/teco/nasional',
        'https://rss.tempo.co/teco/tekno',
        'https://rss.tempo.co/teco/bisnis',
    ]
    
    logger.info("Scraping Tempo RSS feeds...")
    
    for rss_url in rss_urls:
        try:
            resp = safe_request(rss_url)
            if not resp:
                continue
            
            root = ET.fromstring(resp.content)
            
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                desc_elem = item.find('description')
                pubdate_elem = item.find('pubDate')
                
                if title_elem is None or link_elem is None:
                    continue
                
                title = title_elem.text or ''
                
                cyber_keywords = ['siber', 'hacker', 'ransomware', 'phishing', 'malware', 
                                 'kebocoran', 'data', 'cyber', 'peretasan', 
                                 'BSSN', 'PDN', 'digital']
                
                if not any(kw.lower() in title.lower() for kw in cyber_keywords):
                    continue
                
                articles.append({
                    'title': title,
                    'url': link_elem.text or '',
                    'source': 'Tempo.co',
                    'date': parse_date(pubdate_elem.text if pubdate_elem is not None else None),
                    'content': desc_elem.text if desc_elem is not None else '',
                    'scraped_at': datetime.now()
                })
                
        except Exception as e:
            logger.error(f"Error parsing Tempo RSS: {e}")
    
    logger.info(f"  ✓ Tempo RSS: {len(articles)} articles")
    return articles


# ============== CNN RSS SCRAPER ==============

def scrape_cnn_rss() -> List[Dict]:
    """Scrape CNN Indonesia via RSS feeds."""
    articles = []
    
    rss_urls = [
        'https://www.cnnindonesia.com/teknologi/rss',
        'https://www.cnnindonesia.com/nasional/rss',
    ]
    
    logger.info("Scraping CNN Indonesia RSS feeds...")
    
    for rss_url in rss_urls:
        try:
            resp = safe_request(rss_url)
            if not resp:
                continue
            
            root = ET.fromstring(resp.content)
            
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                desc_elem = item.find('description')
                pubdate_elem = item.find('pubDate')
                
                if title_elem is None or link_elem is None:
                    continue
                
                title = title_elem.text or ''
                
                cyber_keywords = ['siber', 'hacker', 'ransomware', 'phishing', 'malware', 
                                 'kebocoran', 'data', 'cyber', 'peretasan', 
                                 'BSSN', 'PDN', 'serangan']
                
                if not any(kw.lower() in title.lower() for kw in cyber_keywords):
                    continue
                
                articles.append({
                    'title': title,
                    'url': link_elem.text or '',
                    'source': 'CNN Indonesia',
                    'date': parse_date(pubdate_elem.text if pubdate_elem is not None else None),
                    'content': desc_elem.text if desc_elem is not None else '',
                    'scraped_at': datetime.now()
                })
                
        except Exception as e:
            logger.error(f"Error parsing CNN RSS: {e}")
    
    logger.info(f"  ✓ CNN Indonesia RSS: {len(articles)} articles")
    return articles


# ============== DETIK SEARCH SCRAPER ==============

def scrape_detik_search(keywords: List[str], max_per_keyword: int = 10) -> List[Dict]:
    """Scrape Detik search results with direct HTML parsing."""
    articles = []
    scraped_urls = set()
    
    logger.info("Scraping Detik search...")
    
    for keyword in keywords:
        url = f"https://www.detik.com/search/searchall?query={quote_plus(keyword)}&sortby=time"
        
        resp = safe_request(url)
        if not resp:
            continue
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Find article elements
        article_divs = soup.select('article, .list-content__item, .media')
        
        count = 0
        for article in article_divs:
            if count >= max_per_keyword:
                break
            
            link = article.select_one('a')
            if not link:
                continue
            
            href = link.get('href', '')
            if not href or href in scraped_urls:
                continue
            
            if 'detik.com' not in href:
                continue
            
            scraped_urls.add(href)
            
            # Get article details
            delay()
            article_resp = safe_request(href)
            if not article_resp:
                continue
            
            article_soup = BeautifulSoup(article_resp.text, 'html.parser')
            
            title_elem = article_soup.select_one('h1.detail__title, h1')
            date_elem = article_soup.select_one('.detail__date, time')
            content_elems = article_soup.select('div.detail__body-text p')
            
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            content = ' '.join([p.get_text(strip=True) for p in content_elems])
            
            if len(content) < 100:
                continue
            
            articles.append({
                'title': title,
                'url': href,
                'source': 'Detik.com',
                'date': parse_date(date_elem.get_text(strip=True) if date_elem else None),
                'content': content[:5000],
                'scraped_at': datetime.now()
            })
            count += 1
            logger.info(f"  ✓ {title[:50]}...")
    
    logger.info(f"  ✓ Detik Search: {len(articles)} articles")
    return articles


# ============== LIPUTAN6 RSS SCRAPER ==============

def scrape_liputan6_rss() -> List[Dict]:
    """Scrape Liputan6 via RSS."""
    articles = []
    
    rss_urls = [
        'https://www.liputan6.com/feed/rss',
        'https://www.liputan6.com/tekno/feed/rss',
    ]
    
    logger.info("Scraping Liputan6 RSS feeds...")
    
    for rss_url in rss_urls:
        try:
            resp = safe_request(rss_url)
            if not resp:
                continue
            
            root = ET.fromstring(resp.content)
            
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                desc_elem = item.find('description')
                pubdate_elem = item.find('pubDate')
                
                if title_elem is None or link_elem is None:
                    continue
                
                title = title_elem.text or ''
                
                cyber_keywords = ['siber', 'hacker', 'ransomware', 'phishing', 'malware', 
                                 'kebocoran', 'data', 'cyber', 'peretasan', 
                                 'BSSN', 'PDN', 'penipuan']
                
                if not any(kw.lower() in title.lower() for kw in cyber_keywords):
                    continue
                
                articles.append({
                    'title': title,
                    'url': link_elem.text or '',
                    'source': 'Liputan6.com',
                    'date': parse_date(pubdate_elem.text if pubdate_elem is not None else None),
                    'content': desc_elem.text if desc_elem is not None else '',
                    'scraped_at': datetime.now()
                })
                
        except Exception as e:
            logger.error(f"Error parsing Liputan6 RSS: {e}")
    
    logger.info(f"  ✓ Liputan6 RSS: {len(articles)} articles")
    return articles


# ============== MAIN ORCHESTRATOR ==============

def run_full_scraper(target_articles: int = 100) -> pd.DataFrame:
    """Run all scrapers and collect articles."""
    all_articles = []
    
    print("=" * 70)
    print("🕷️ Indonesian Cyber Crime News Scraper (RSS + API)")
    print("=" * 70)
    print(f"Target: {target_articles} articles")
    print("=" * 70)
    
    # 1. RSS Feeds (fastest and most reliable)
    print("\n📡 Phase 1: RSS Feeds")
    all_articles.extend(scrape_detik_rss())
    all_articles.extend(scrape_kompas_rss())
    all_articles.extend(scrape_tempo_rss())
    all_articles.extend(scrape_cnn_rss())
    all_articles.extend(scrape_liputan6_rss())
    
    print(f"\nRSS Phase Complete: {len(all_articles)} articles")
    
    # 2. Direct Search (for more articles)
    if len(all_articles) < target_articles:
        print("\n🔍 Phase 2: Direct Search Scraping")
        search_articles = scrape_detik_search(KEYWORDS[:5], max_per_keyword=5)
        all_articles.extend(search_articles)
    
    # Create DataFrame
    df = pd.DataFrame(all_articles)
    
    if len(df) > 0:
        # Remove duplicates
        df = df.drop_duplicates(subset=['url'])
        df = df.drop_duplicates(subset=['title'])
        
        # Filter date range
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df[df['date'].notna()]
        df = df[(df['date'] >= '2023-01-01') & (df['date'] <= '2025-12-31')]
        
        # Sort
        df = df.sort_values('date', ascending=False).reset_index(drop=True)
        
        # Clean content (remove HTML tags)
        df['content'] = df['content'].apply(lambda x: BeautifulSoup(str(x), 'html.parser').get_text() if x else '')
    
    print("\n" + "=" * 70)
    print("📊 SCRAPING COMPLETE")
    print(f"   Total articles: {len(df)}")
    if len(df) > 0:
        print(f"   Sources: {df['source'].value_counts().to_dict()}")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print("=" * 70)
    
    return df


def save_results(df: pd.DataFrame) -> str:
    """Save results to CSV."""
    output_dir = Path(__file__).parent.parent.parent / 'data' / 'external'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    output_path = output_dir / f'scraped_news_rss_{timestamp}.csv'
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} articles to {output_path}")
    
    return str(output_path)


if __name__ == '__main__':
    print("\n🚀 Starting RSS + API news scraper...\n")
    
    df = run_full_scraper(target_articles=100)
    
    if len(df) > 0:
        output_path = save_results(df)
        print(f"\n✅ Data saved to: {output_path}")
        
        print("\n📰 Sample articles:")
        for _, row in df.head(10).iterrows():
            source = row['source']
            title = row['title'][:55] if len(row['title']) > 55 else row['title']
            print(f"  - [{source}] {title}...")
    else:
        print("\n❌ No articles scraped.")
