"""
Focused Cyber Crime News Scraper
Only scrapes cybercrime-related news from trusted international and local sources.

International Sources:
- The Hacker News (thehackernews.com)
- BleepingComputer
- SecurityWeek
- KrebsOnSecurity

Local Sources:
- Detik Inet (cyber section)
- CNN Indonesia Tech
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import random
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
]


def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }


def delay():
    time.sleep(random.uniform(1.5, 3))


def safe_request(url: str, retries: int = 2) -> Optional[requests.Response]:
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=get_headers(), timeout=20)
            resp.raise_for_status()
            return resp
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(2)
    return None


# ============== THE HACKER NEWS ==============

def scrape_hacker_news(max_articles: int = 25) -> List[Dict]:
    """Scrape The Hacker News - top cybersecurity news source."""
    articles = []
    url = "https://feeds.feedburner.com/TheHackersNews"
    
    logger.info("Scraping The Hacker News RSS...")
    
    try:
        resp = safe_request(url)
        if not resp:
            return articles
        
        root = ET.fromstring(resp.content)
        
        for item in root.findall('.//item')[:max_articles]:
            title = item.find('title')
            link = item.find('link')
            desc = item.find('description')
            pubdate = item.find('pubDate')
            
            if title is None or link is None:
                continue
            
            # Parse date
            date = None
            if pubdate is not None and pubdate.text:
                try:
                    date = pd.to_datetime(pubdate.text).to_pydatetime()
                except:
                    pass
            
            # Clean description (remove HTML)
            content = ''
            if desc is not None and desc.text:
                content = BeautifulSoup(desc.text, 'html.parser').get_text()
            
            articles.append({
                'title': title.text,
                'url': link.text,
                'source': 'The Hacker News',
                'date': date,
                'content': content[:3000],
                'scraped_at': datetime.now(),
                'category': 'Cyber Security'
            })
            
    except Exception as e:
        logger.error(f"Error scraping The Hacker News: {e}")
    
    logger.info(f"  ✓ The Hacker News: {len(articles)} articles")
    return articles


# ============== BLEEPING COMPUTER ==============

def scrape_bleeping_computer(max_articles: int = 20) -> List[Dict]:
    """Scrape BleepingComputer - cybersecurity and tech news."""
    articles = []
    url = "https://www.bleepingcomputer.com/feed/"
    
    logger.info("Scraping BleepingComputer RSS...")
    
    try:
        resp = safe_request(url)
        if not resp:
            return articles
        
        root = ET.fromstring(resp.content)
        
        for item in root.findall('.//item')[:max_articles]:
            title = item.find('title')
            link = item.find('link')
            desc = item.find('description')
            pubdate = item.find('pubDate')
            
            if title is None or link is None:
                continue
            
            # Filter: only security related
            title_text = title.text or ''
            security_keywords = ['hack', 'malware', 'ransomware', 'phishing', 'breach', 
                               'vulnerability', 'exploit', 'cyber', 'attack', 'security',
                               'data leak', 'threat', 'botnet', 'trojan', 'apt']
            
            if not any(kw in title_text.lower() for kw in security_keywords):
                continue
            
            date = None
            if pubdate is not None and pubdate.text:
                try:
                    date = pd.to_datetime(pubdate.text).to_pydatetime()
                except:
                    pass
            
            content = ''
            if desc is not None and desc.text:
                content = BeautifulSoup(desc.text, 'html.parser').get_text()
            
            articles.append({
                'title': title_text,
                'url': link.text,
                'source': 'BleepingComputer',
                'date': date,
                'content': content[:3000],
                'scraped_at': datetime.now(),
                'category': 'Cyber Security'
            })
            
    except Exception as e:
        logger.error(f"Error scraping BleepingComputer: {e}")
    
    logger.info(f"  ✓ BleepingComputer: {len(articles)} articles")
    return articles


# ============== SECURITY WEEK ==============

def scrape_security_week(max_articles: int = 20) -> List[Dict]:
    """Scrape SecurityWeek - enterprise security news."""
    articles = []
    url = "https://feeds.feedburner.com/securityweek"
    
    logger.info("Scraping SecurityWeek RSS...")
    
    try:
        resp = safe_request(url)
        if not resp:
            return articles
        
        root = ET.fromstring(resp.content)
        
        for item in root.findall('.//item')[:max_articles]:
            title = item.find('title')
            link = item.find('link')
            desc = item.find('description')
            pubdate = item.find('pubDate')
            
            if title is None or link is None:
                continue
            
            date = None
            if pubdate is not None and pubdate.text:
                try:
                    date = pd.to_datetime(pubdate.text).to_pydatetime()
                except:
                    pass
            
            content = ''
            if desc is not None and desc.text:
                content = BeautifulSoup(desc.text, 'html.parser').get_text()
            
            articles.append({
                'title': title.text,
                'url': link.text,
                'source': 'SecurityWeek',
                'date': date,
                'content': content[:3000],
                'scraped_at': datetime.now(),
                'category': 'Cyber Security'
            })
            
    except Exception as e:
        logger.error(f"Error scraping SecurityWeek: {e}")
    
    logger.info(f"  ✓ SecurityWeek: {len(articles)} articles")
    return articles


# ============== DARK READING ==============

def scrape_dark_reading(max_articles: int = 20) -> List[Dict]:
    """Scrape Dark Reading - cybersecurity insights."""
    articles = []
    url = "https://www.darkreading.com/rss.xml"
    
    logger.info("Scraping Dark Reading RSS...")
    
    try:
        resp = safe_request(url)
        if not resp:
            return articles
        
        root = ET.fromstring(resp.content)
        
        for item in root.findall('.//item')[:max_articles]:
            title = item.find('title')
            link = item.find('link')
            desc = item.find('description')
            pubdate = item.find('pubDate')
            
            if title is None or link is None:
                continue
            
            date = None
            if pubdate is not None and pubdate.text:
                try:
                    date = pd.to_datetime(pubdate.text).to_pydatetime()
                except:
                    pass
            
            content = ''
            if desc is not None and desc.text:
                content = BeautifulSoup(desc.text, 'html.parser').get_text()
            
            articles.append({
                'title': title.text,
                'url': link.text,
                'source': 'Dark Reading',
                'date': date,
                'content': content[:3000],
                'scraped_at': datetime.now(),
                'category': 'Cyber Security'
            })
            
    except Exception as e:
        logger.error(f"Error scraping Dark Reading: {e}")
    
    logger.info(f"  ✓ Dark Reading: {len(articles)} articles")
    return articles


# ============== THREATPOST ==============

def scrape_threatpost(max_articles: int = 15) -> List[Dict]:
    """Scrape Threatpost - security news and analysis."""
    articles = []
    
    # Try main page scraping
    url = "https://threatpost.com/"
    
    logger.info("Scraping Threatpost...")
    
    try:
        resp = safe_request(url)
        if not resp:
            return articles
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Find article links
        article_links = soup.select('article a, .c-card__title a, h2 a, h3 a')
        
        seen_urls = set()
        for link in article_links:
            if len(articles) >= max_articles:
                break
            
            href = link.get('href', '')
            if not href or href in seen_urls:
                continue
            
            if 'threatpost.com' not in href:
                continue
            
            seen_urls.add(href)
            title = link.get_text(strip=True)
            
            if not title or len(title) < 10:
                continue
            
            articles.append({
                'title': title,
                'url': href,
                'source': 'Threatpost',
                'date': datetime.now(),  # Will be updated if we scrape article
                'content': '',
                'scraped_at': datetime.now(),
                'category': 'Cyber Security'
            })
            
    except Exception as e:
        logger.error(f"Error scraping Threatpost: {e}")
    
    logger.info(f"  ✓ Threatpost: {len(articles)} articles")
    return articles


# ============== DETIK INET CYBER ==============

def scrape_detik_cyber(max_articles: int = 15) -> List[Dict]:
    """Scrape Detik Inet - Indonesian cybersecurity news."""
    articles = []
    
    search_urls = [
        "https://www.detik.com/search/searchall?query=serangan+siber&sortby=time",
        "https://www.detik.com/search/searchall?query=ransomware&sortby=time",
        "https://www.detik.com/search/searchall?query=hacker&sortby=time",
        "https://www.detik.com/search/searchall?query=kebocoran+data&sortby=time",
    ]
    
    logger.info("Scraping Detik Cyber news...")
    scraped_urls = set()
    
    for search_url in search_urls:
        if len(articles) >= max_articles:
            break
            
        try:
            resp = safe_request(search_url)
            if not resp:
                continue
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            article_divs = soup.select('article h2 a, .media__title a')
            
            for link in article_divs[:5]:
                if len(articles) >= max_articles:
                    break
                
                href = link.get('href', '')
                if not href or href in scraped_urls:
                    continue
                
                if 'detik.com' not in href:
                    continue
                
                scraped_urls.add(href)
                delay()
                
                # Get article content
                article_resp = safe_request(href)
                if not article_resp:
                    continue
                
                article_soup = BeautifulSoup(article_resp.text, 'html.parser')
                
                title_elem = article_soup.select_one('h1.detail__title, h1')
                date_elem = article_soup.select_one('.detail__date')
                content_elems = article_soup.select('div.detail__body-text p')
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                content = ' '.join([p.get_text(strip=True) for p in content_elems])
                
                date = None
                if date_elem:
                    try:
                        date = pd.to_datetime(date_elem.get_text(strip=True)).to_pydatetime()
                    except:
                        pass
                
                articles.append({
                    'title': title,
                    'url': href,
                    'source': 'Detik Inet',
                    'date': date,
                    'content': content[:3000],
                    'scraped_at': datetime.now(),
                    'category': 'Cyber Security Indonesia'
                })
                logger.info(f"  ✓ {title[:50]}...")
                
        except Exception as e:
            logger.error(f"Error scraping Detik: {e}")
    
    logger.info(f"  ✓ Detik Cyber: {len(articles)} articles")
    return articles


# ============== MAIN ORCHESTRATOR ==============

def run_cybercrime_focused_scraper() -> pd.DataFrame:
    """Run focused cybercrime news scraper from international sources."""
    all_articles = []
    
    print("=" * 70)
    print("🔒 Focused Cyber Crime News Scraper")
    print("=" * 70)
    print("Sources: The Hacker News, BleepingComputer, SecurityWeek,")
    print("         Dark Reading, Threatpost, Detik Inet")
    print("=" * 70)
    
    # International sources
    print("\n🌍 International Sources:")
    all_articles.extend(scrape_hacker_news(25))
    all_articles.extend(scrape_bleeping_computer(20))
    all_articles.extend(scrape_security_week(20))
    all_articles.extend(scrape_dark_reading(15))
    all_articles.extend(scrape_threatpost(10))
    
    # Indonesian source
    print("\n🇮🇩 Indonesian Sources:")
    all_articles.extend(scrape_detik_cyber(15))
    
    # Create DataFrame
    df = pd.DataFrame(all_articles)
    
    if len(df) > 0:
        # Remove duplicates
        df = df.drop_duplicates(subset=['url'])
        df = df.drop_duplicates(subset=['title'])
        
        # Sort by date
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.sort_values('date', ascending=False, na_position='last')
        
        df = df.reset_index(drop=True)
    
    print("\n" + "=" * 70)
    print("📊 SCRAPING COMPLETE")
    print(f"   Total articles: {len(df)}")
    if len(df) > 0:
        print(f"   Sources: {df['source'].value_counts().to_dict()}")
    print("=" * 70)
    
    return df


def save_results(df: pd.DataFrame) -> str:
    """Save results to CSV."""
    output_dir = Path(__file__).parent.parent.parent / 'data' / 'external'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / 'cybercrime_news.csv'
    df.to_csv(output_path, index=False)
    
    # Also update merged file
    merged_path = output_dir / 'merged_news_data.csv'
    df.to_csv(merged_path, index=False)
    
    logger.info(f"Saved {len(df)} articles to {output_path}")
    return str(output_path)


if __name__ == '__main__':
    print("\n🚀 Starting focused cybercrime news scraper...\n")
    
    df = run_cybercrime_focused_scraper()
    
    if len(df) > 0:
        output_path = save_results(df)
        print(f"\n✅ Data saved to: {output_path}")
        
        print("\n📰 Latest Cyber Security News:")
        for _, row in df.head(15).iterrows():
            source = row['source']
            title = row['title'][:60] if len(str(row['title'])) > 60 else row['title']
            print(f"  - [{source}] {title}...")
    else:
        print("\n❌ No articles scraped.")
