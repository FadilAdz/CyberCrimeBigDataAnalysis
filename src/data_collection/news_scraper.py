"""
News Scraper Module
Scrapes cyber crime news from Indonesian news portals.
For demonstration, generates simulated news data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path

# News sources
NEWS_SOURCES = [
    'kompas.com', 'detik.com', 'cnnindonesia.com', 
    'tribunnews.com', 'liputan6.com', 'tempo.co',
    'republika.co.id', 'merdeka.com'
]

# Sample news titles related to cyber crime
NEWS_TEMPLATES = [
    "Serangan {attack_type} Menargetkan {sector} di {province}",
    "BSSN Ungkap Lonjakan Kasus {attack_type} Sepanjang {year}",
    "Kerugian Akibat {attack_type} Capai Rp {amount} Miliar",
    "{sector} Indonesia Jadi Target Utama {attack_type}",
    "Waspada! Modus Baru {attack_type} Melalui {method}",
    "Polri Tangkap Pelaku {attack_type} yang Rugikan Korban Rp {amount} Juta",
    "Kominfo Blokir {num} Situs Terkait {attack_type}",
    "Tips Lindungi Data dari {attack_type} Menurut Pakar Keamanan",
    "Kasus {attack_type} di {province} Meningkat {percent}%",
    "{company_type} Kehilangan Data Jutaan Pengguna Akibat {attack_type}",
]

ATTACK_TYPES = [
    'Phishing', 'Ransomware', 'DDoS', 'Kebocoran Data', 'Malware',
    'Social Engineering', 'Hacking', 'Penipuan Online', 'Skimming'
]

SECTORS = [
    'Perbankan', 'E-Commerce', 'Pemerintahan', 'Fintech', 'Kesehatan',
    'Pendidikan', 'Telekomunikasi', 'Startup', 'UMKM'
]

PROVINCES = [
    'Jakarta', 'Jawa Barat', 'Jawa Timur', 'Surabaya', 'Bandung',
    'Semarang', 'Yogyakarta', 'Bali', 'Medan', 'Makassar'
]

METHODS = [
    'WhatsApp', 'Email', 'SMS', 'Link Palsu', 'Aplikasi Berbahaya',
    'Media Sosial', 'Website Palsu', 'QR Code'
]


class NewsScraper:
    """Scrapes and manages news data from Indonesian portals."""
    
    def __init__(self, sources: list = None):
        self.sources = sources or NEWS_SOURCES
        self.news_data = None
    
    def generate_simulated_news(
        self,
        n_articles: int = 500,
        start_date: str = '2020-01-01',
        end_date: str = '2024-12-31'
    ) -> pd.DataFrame:
        """
        Generate simulated news data for demonstration.
        In production, this would be replaced with actual web scraping.
        """
        random.seed(42)
        np.random.seed(42)
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        date_range = (end - start).days
        
        articles = []
        
        for i in range(n_articles):
            # Random date with trend towards recent
            weight = np.random.beta(2, 1.5)
            day_offset = int(weight * date_range)
            pub_date = start + timedelta(days=day_offset)
            
            # Generate title
            template = random.choice(NEWS_TEMPLATES)
            attack_type = random.choice(ATTACK_TYPES)
            sector = random.choice(SECTORS)
            province = random.choice(PROVINCES)
            
            title = template.format(
                attack_type=attack_type,
                sector=sector,
                province=province,
                year=pub_date.year,
                amount=random.randint(1, 500),
                method=random.choice(METHODS),
                num=random.randint(10, 1000),
                percent=random.randint(10, 200),
                company_type=sector
            )
            
            # Generate content summary
            content = f"""
            Laporan terbaru menunjukkan adanya kasus {attack_type} yang menargetkan 
            sektor {sector} di wilayah {province}. Menurut sumber dari 
            {random.choice(['BSSN', 'Kominfo', 'Kepolisian'])}, insiden ini 
            terjadi pada {pub_date.strftime('%d %B %Y')}. Para ahli keamanan siber 
            menyarankan masyarakat untuk meningkatkan kewaspadaan terhadap ancaman 
            serupa. Kerugian diperkirakan mencapai ratusan juta hingga miliaran rupiah.
            """.strip()
            
            articles.append({
                'article_id': f'NEWS-{str(i+1).zfill(6)}',
                'title': title,
                'content': content,
                'source': random.choice(self.sources),
                'published_date': pub_date,
                'attack_type_mentioned': attack_type,
                'sector_mentioned': sector,
                'province_mentioned': province,
                'sentiment': random.choices(
                    ['negative', 'neutral', 'positive'],
                    weights=[0.6, 0.35, 0.05],
                    k=1
                )[0],
                'word_count': len(content.split()),
                'scraped_at': datetime.now()
            })
        
        self.news_data = pd.DataFrame(articles)
        return self.news_data
    
    def save_news_data(self, output_path: str):
        """Save news data to CSV."""
        if self.news_data is not None:
            self.news_data.to_csv(output_path, index=False)
            print(f"Saved {len(self.news_data)} articles to {output_path}")
    
    def get_news_data(self) -> pd.DataFrame:
        """Return collected news data."""
        return self.news_data
    
    def extract_attack_mentions(self) -> pd.DataFrame:
        """Extract attack type mentions from news articles."""
        if self.news_data is None:
            return pd.DataFrame()
        
        attack_counts = self.news_data.groupby([
            'attack_type_mentioned', 
            pd.Grouper(key='published_date', freq='M')
        ]).size().reset_index(name='mention_count')
        
        return attack_counts


if __name__ == '__main__':
    # Generate simulated news data
    scraper = NewsScraper()
    news_df = scraper.generate_simulated_news(n_articles=500)
    
    output_file = Path(__file__).parent.parent.parent / 'data' / 'external' / 'news_data.csv'
    scraper.save_news_data(str(output_file))
    
    print(news_df.head())
    print(f"\nData shape: {news_df.shape}")
