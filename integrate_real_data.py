"""
Data Integration Script
Integrates real data from FinalExamBdata repository and cleans it for dashboard.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def clean_date(date_str):
    """Parse various date formats."""
    if pd.isna(date_str):
        return None
    
    date_str = str(date_str).strip()
    
    # Try different formats
    formats = [
        '%Y-%m-%d',
        '%Y-%m',
        '%d %B %Y',
        '%d %b %Y',
    ]
    
    # Handle Indonesian month names
    indo_months = {
        'Januari': 'January', 'Februari': 'February', 'Maret': 'March',
        'April': 'April', 'Mei': 'May', 'Juni': 'June',
        'Juli': 'July', 'Agustus': 'August', 'September': 'September',
        'Oktober': 'October', 'November': 'November', 'Desember': 'December',
        'Jan': 'Jan', 'Feb': 'Feb', 'Mar': 'Mar', 'Apr': 'Apr',
        'Des': 'Dec'
    }
    
    for indo, eng in indo_months.items():
        date_str = date_str.replace(indo, eng)
    
    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except:
            continue
    
    try:
        return pd.to_datetime(date_str)
    except:
        return None


def clean_unified_data():
    """Clean and prepare the unified data from FinalExamBdata."""
    
    data_path = project_root / 'FinalExamBdata' / 'data_unified_20251223_0605.csv'
    
    if not data_path.exists():
        print(f"Error: {data_path} not found!")
        return None
    
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    print(f"Original shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    # ===== CLEANING STEPS =====
    
    # 1. Parse dates
    df['date'] = df['date'].apply(clean_date)
    
    # 2. Filter out invalid dates (future dates or invalid)
    df = df[df['date'].notna()]
    df = df[df['date'] <= datetime.now()]
    df = df[df['date'] >= '2020-01-01']
    
    print(f"After date filtering: {df.shape}")
    
    # 3. Handle Unknown values
    # Replace 'Unknown' sector with most common sector
    valid_sectors = df[df['sector'] != 'Unknown']['sector'].value_counts()
    if len(valid_sectors) > 0:
        # Keep Unknown but mark it
        pass  # We'll keep Unknown as a category
    
    # Replace 'Unknown' attack_type with info from news if possible
    df['attack_type'] = df['attack_type'].replace('Unknown', np.nan)
    df['attack_type'] = df['attack_type'].fillna('Other')
    
    # 4. Normalize attack types
    attack_type_map = {
        'Scam/Fraud': 'Scam',
        'Scam': 'Scam',
        'APT': 'APT',
        'Brute Force': 'Brute Force',
        'Cryptojacking': 'Cryptojacking',
        'Data Breach': 'Data Breach',
        'DDoS': 'DDoS',
        'Malware': 'Malware',
        'Phishing': 'Phishing',
        'Ransomware': 'Ransomware',
        'Social Engineering': 'Social Engineering',
        'SQL Injection': 'SQL Injection',
        'Zero-Day Exploit': 'Zero-Day Exploit',
    }
    df['attack_type'] = df['attack_type'].map(lambda x: attack_type_map.get(x, x))
    
    # 5. Normalize province names
    province_map = {
        'Lainnya': 'Other',
        'Unknown': 'Unknown',
    }
    df['province'] = df['province'].map(lambda x: province_map.get(x, x))
    
    # 6. Handle severity - map to standard values
    severity_map = {
        'Low': 'Low',
        'Medium': 'Medium', 
        'High': 'High',
        'Critical': 'Critical'
    }
    df['severity'] = df['severity'].map(lambda x: severity_map.get(x, 'Medium'))
    
    # 7. Handle incident_count - fill with 1 for news items
    df['incident_count'] = df['incident_count'].fillna(1).astype(int)
    
    # 8. Remove duplicates
    initial_count = len(df)
    df = df.drop_duplicates(subset=['date', 'attack_type', 'sector', 'province'], keep='first')
    duplicates_removed = initial_count - len(df)
    print(f"Removed {duplicates_removed} duplicates")
    
    # 9. Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # 10. Add date features
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['quarter'] = df['date'].dt.quarter
    
    # 11. Create unique incident_id
    df['incident_id'] = [f'INC-{str(i).zfill(6)}' for i in range(1, len(df) + 1)]
    
    # 12. Reorder columns
    columns_order = [
        'incident_id', 'date', 'province', 'attack_type', 'sector',
        'severity', 'incident_count', 'source_type', 'source',
        'year', 'month', 'quarter'
    ]
    available_cols = [c for c in columns_order if c in df.columns]
    df = df[available_cols]
    
    print(f"\nFinal shape: {df.shape}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"\nAttack types distribution:\n{df['attack_type'].value_counts()}")
    print(f"\nProvince distribution:\n{df['province'].value_counts().head(10)}")
    print(f"\nSeverity distribution:\n{df['severity'].value_counts()}")
    
    return df


def integrate_bssn_data():
    """Also load original BSSN data for additional context."""
    bssn_path = project_root / 'FinalExamBdata' / 'bssn_data_20251222_0746.csv'
    
    if bssn_path.exists():
        df = pd.read_csv(bssn_path)
        print(f"\nBSSN Data: {len(df)} records")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        return df
    return None


def main():
    print("=" * 60)
    print("Data Integration from FinalExamBdata")
    print("=" * 60)
    
    # Clean unified data
    df_clean = clean_unified_data()
    
    if df_clean is not None:
        # Save to processed folder
        output_path = project_root / 'data' / 'processed' / 'cleaned_government_data.csv'
        df_clean.to_csv(output_path, index=False)
        print(f"\n✅ Saved cleaned data to {output_path}")
        
        # Also save a copy to raw for reference
        raw_output = project_root / 'data' / 'raw' / 'real_data_integrated.csv'
        df_clean.to_csv(raw_output, index=False)
        print(f"✅ Saved copy to {raw_output}")
        
        return df_clean
    
    return None


if __name__ == '__main__':
    main()
