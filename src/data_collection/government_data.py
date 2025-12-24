"""
Government Data Loader Module
Loads and manages government cyber crime statistics data from CSV/Excel files.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import random

# Indonesian provinces for data generation
PROVINCES = [
    'DKI Jakarta', 'Jawa Barat', 'Jawa Tengah', 'Jawa Timur', 'Banten',
    'DI Yogyakarta', 'Sumatera Utara', 'Sumatera Barat', 'Sumatera Selatan',
    'Riau', 'Kepulauan Riau', 'Lampung', 'Kalimantan Timur', 'Kalimantan Selatan',
    'Kalimantan Barat', 'Sulawesi Selatan', 'Sulawesi Utara', 'Bali',
    'Nusa Tenggara Barat', 'Nusa Tenggara Timur', 'Papua', 'Papua Barat',
    'Maluku', 'Maluku Utara', 'Gorontalo', 'Sulawesi Tengah', 'Sulawesi Tenggara',
    'Bengkulu', 'Jambi', 'Aceh', 'Kalimantan Tengah', 'Kalimantan Utara',
    'Sulawesi Barat', 'Bangka Belitung'
]

# Attack types based on Indonesian cyber crime patterns
ATTACK_TYPES = [
    'Phishing', 'Ransomware', 'DDoS', 'Data Breach', 'Malware',
    'Social Engineering', 'SQL Injection', 'Man-in-the-Middle',
    'Credential Stuffing', 'Business Email Compromise', 'Cryptojacking',
    'Zero-Day Exploit', 'Insider Threat', 'Website Defacement'
]

# Target sectors
SECTORS = [
    'Perbankan', 'E-Commerce', 'Pemerintahan', 'Kesehatan', 'Pendidikan',
    'Telekomunikasi', 'Energi', 'Transportasi', 'Fintech', 'Media',
    'UMKM', 'Manufaktur', 'Ritel', 'Asuransi'
]

# Severity levels
SEVERITY_LEVELS = ['Low', 'Medium', 'High', 'Critical']


class GovernmentDataLoader:
    """Loads and manages government cyber crime statistics."""
    
    def __init__(self, data_path: str = None):
        self.data_path = Path(data_path) if data_path else None
        self.data = None
    
    def load_csv(self, filepath: str) -> pd.DataFrame:
        """Load data from CSV file."""
        self.data = pd.read_csv(filepath)
        return self.data
    
    def load_excel(self, filepath: str, sheet_name: str = 0) -> pd.DataFrame:
        """Load data from Excel file."""
        self.data = pd.read_excel(filepath, sheet_name=sheet_name)
        return self.data
    
    def get_data(self) -> pd.DataFrame:
        """Return loaded data."""
        return self.data


def generate_sample_government_data(
    n_records: int = 1500,
    start_date: str = '2020-01-01',
    end_date: str = '2024-12-31',
    output_path: str = None
) -> pd.DataFrame:
    """
    Generate realistic sample government cyber crime data.
    
    Args:
        n_records: Number of records to generate
        start_date: Start date for data range
        end_date: End date for data range
        output_path: Path to save CSV file
        
    Returns:
        DataFrame with generated data
    """
    random.seed(42)
    np.random.seed(42)
    
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    date_range = (end - start).days
    
    # Generate random dates with increasing trend (more attacks over time)
    dates = []
    for _ in range(n_records):
        # Weighted towards recent dates to simulate increasing cyber crime
        weight = np.random.beta(2, 1.5)
        day_offset = int(weight * date_range)
        dates.append(start + timedelta(days=day_offset))
    
    # Province distribution (weighted towards major provinces)
    province_weights = [0.20, 0.15, 0.10, 0.12, 0.08] + [0.35/(len(PROVINCES)-5)] * (len(PROVINCES)-5)
    provinces = random.choices(PROVINCES, weights=province_weights, k=n_records)
    
    # Attack type distribution (some more common than others)
    attack_weights = [0.18, 0.12, 0.10, 0.15, 0.12, 0.08, 0.05, 0.04, 0.04, 0.05, 0.02, 0.02, 0.02, 0.01]
    attack_types = random.choices(ATTACK_TYPES, weights=attack_weights, k=n_records)
    
    # Sector distribution
    sectors = random.choices(SECTORS, k=n_records)
    
    # Severity based on attack type (some attacks more severe)
    severity_map = {
        'Ransomware': [0.05, 0.15, 0.40, 0.40],
        'Data Breach': [0.05, 0.20, 0.45, 0.30],
        'Zero-Day Exploit': [0.05, 0.10, 0.35, 0.50],
        'DDoS': [0.10, 0.40, 0.35, 0.15],
        'Phishing': [0.30, 0.45, 0.20, 0.05],
    }
    default_severity_weights = [0.20, 0.40, 0.30, 0.10]
    
    severities = []
    for attack in attack_types:
        weights = severity_map.get(attack, default_severity_weights)
        severities.append(random.choices(SEVERITY_LEVELS, weights=weights, k=1)[0])
    
    # Victims count based on severity
    victims = []
    for severity in severities:
        if severity == 'Critical':
            victims.append(np.random.randint(1000, 100000))
        elif severity == 'High':
            victims.append(np.random.randint(100, 10000))
        elif severity == 'Medium':
            victims.append(np.random.randint(10, 1000))
        else:
            victims.append(np.random.randint(1, 100))
    
    # Financial loss (IDR)
    financial_loss = []
    for v, severity in zip(victims, severities):
        base_loss = v * np.random.randint(100000, 10000000)
        if severity == 'Critical':
            base_loss *= 10
        elif severity == 'High':
            base_loss *= 5
        financial_loss.append(int(base_loss))
    
    # Create DataFrame
    df = pd.DataFrame({
        'incident_id': [f'INC-{str(i).zfill(6)}' for i in range(1, n_records + 1)],
        'date': dates,
        'province': provinces,
        'attack_type': attack_types,
        'sector': sectors,
        'severity': severities,
        'victims_count': victims,
        'financial_loss_idr': financial_loss,
        'is_resolved': np.random.choice([True, False], size=n_records, p=[0.7, 0.3]),
        'response_time_hours': np.random.exponential(48, n_records).astype(int),
        'source': random.choices(['BSSN', 'Kominfo', 'Kepolisian', 'Laporan Publik'], k=n_records)
    })
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # Add some missing values for realistic data (5% missing)
    missing_mask = np.random.random(n_records) < 0.05
    df.loc[missing_mask, 'financial_loss_idr'] = np.nan
    
    missing_mask2 = np.random.random(n_records) < 0.03
    df.loc[missing_mask2, 'response_time_hours'] = np.nan
    
    # Add some duplicates for testing (2% duplicates)
    n_duplicates = int(n_records * 0.02)
    duplicate_indices = random.sample(range(n_records), n_duplicates)
    duplicates = df.iloc[duplicate_indices].copy()
    df = pd.concat([df, duplicates], ignore_index=True)
    
    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    if output_path:
        df.to_csv(output_path, index=False)
        print(f"Generated {len(df)} records and saved to {output_path}")
    
    return df


if __name__ == '__main__':
    # Generate sample data
    output_file = Path(__file__).parent.parent.parent / 'data' / 'raw' / 'sample_government_data.csv'
    df = generate_sample_government_data(output_path=str(output_file))
    print(df.head())
    print(f"\nData shape: {df.shape}")
    print(f"\nColumns: {df.columns.tolist()}")
