"""
Merge all scraped news data into a unified dataset.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

def merge_scraped_data():
    """Merge all scraped news files into one unified dataset."""
    
    data_dir = Path(__file__).parent.parent.parent / 'data' / 'external'
    
    # Find all scraped news files
    scraped_files = list(data_dir.glob('scraped*.csv'))
    scraped_files.extend(list(data_dir.glob('*_news*.csv')))
    
    print(f"Found {len(scraped_files)} scraped files:")
    for f in scraped_files:
        print(f"  - {f.name}")
    
    # Load and merge
    all_dfs = []
    for f in scraped_files:
        try:
            df = pd.read_csv(f)
            print(f"  Loaded {len(df)} records from {f.name}")
            all_dfs.append(df)
        except Exception as e:
            print(f"  Error loading {f.name}: {e}")
    
    if not all_dfs:
        print("No data found!")
        return None
    
    # Combine all
    merged_df = pd.concat(all_dfs, ignore_index=True)
    print(f"\nTotal before dedup: {len(merged_df)}")
    
    # Remove duplicates
    if 'url' in merged_df.columns:
        merged_df = merged_df.drop_duplicates(subset=['url'])
    if 'title' in merged_df.columns:
        merged_df = merged_df.drop_duplicates(subset=['title'])
    
    print(f"After dedup: {len(merged_df)}")
    
    # Clean dates
    if 'date' in merged_df.columns:
        merged_df['date'] = pd.to_datetime(merged_df['date'], errors='coerce')
    
    # Sort by date
    merged_df = merged_df.sort_values('date', ascending=False).reset_index(drop=True)
    
    # Save merged file
    output_path = data_dir / 'merged_news_data.csv'
    merged_df.to_csv(output_path, index=False)
    
    print(f"\n✅ Merged data saved to: {output_path}")
    print(f"   Total articles: {len(merged_df)}")
    if 'source' in merged_df.columns:
        print(f"   Sources: {merged_df['source'].value_counts().to_dict()}")
    
    return merged_df


if __name__ == '__main__':
    merge_scraped_data()
