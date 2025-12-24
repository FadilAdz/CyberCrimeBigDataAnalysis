"""
Utility functions for the Big Data Analysis project.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any


# Indonesia province coordinates for mapping
PROVINCE_COORDINATES = {
    'DKI Jakarta': {'lat': -6.2088, 'lon': 106.8456},
    'Jawa Barat': {'lat': -6.9175, 'lon': 107.6191},
    'Jawa Tengah': {'lat': -7.1510, 'lon': 110.1403},
    'Jawa Timur': {'lat': -7.5361, 'lon': 112.2384},
    'Banten': {'lat': -6.4058, 'lon': 106.0640},
    'DI Yogyakarta': {'lat': -7.7956, 'lon': 110.3695},
    'Sumatera Utara': {'lat': 3.5852, 'lon': 98.6619},
    'Sumatera Barat': {'lat': -0.9471, 'lon': 100.4172},
    'Sumatera Selatan': {'lat': -3.3194, 'lon': 104.9147},
    'Riau': {'lat': 0.5071, 'lon': 101.4478},
    'Kepulauan Riau': {'lat': 1.0456, 'lon': 104.0305},
    'Lampung': {'lat': -5.4500, 'lon': 105.2667},
    'Kalimantan Timur': {'lat': -0.5022, 'lon': 117.1536},
    'Kalimantan Selatan': {'lat': -3.0926, 'lon': 115.2838},
    'Kalimantan Barat': {'lat': -0.0263, 'lon': 109.3425},
    'Sulawesi Selatan': {'lat': -5.1355, 'lon': 119.4233},
    'Sulawesi Utara': {'lat': 1.4748, 'lon': 124.8421},
    'Bali': {'lat': -8.3405, 'lon': 115.0920},
    'Nusa Tenggara Barat': {'lat': -8.6529, 'lon': 117.3616},
    'Nusa Tenggara Timur': {'lat': -8.6574, 'lon': 121.0794},
    'Papua': {'lat': -4.2699, 'lon': 138.0804},
    'Papua Barat': {'lat': -1.3361, 'lon': 133.1747},
    'Maluku': {'lat': -3.2385, 'lon': 130.1453},
    'Maluku Utara': {'lat': 1.5709, 'lon': 127.8088},
    'Gorontalo': {'lat': 0.6999, 'lon': 122.4467},
    'Sulawesi Tengah': {'lat': -1.4300, 'lon': 121.4456},
    'Sulawesi Tenggara': {'lat': -4.1448, 'lon': 122.1746},
    'Bengkulu': {'lat': -3.7928, 'lon': 102.2608},
    'Jambi': {'lat': -1.6101, 'lon': 103.6131},
    'Aceh': {'lat': 4.6951, 'lon': 96.7494},
    'Kalimantan Tengah': {'lat': -1.6815, 'lon': 113.3824},
    'Kalimantan Utara': {'lat': 3.0731, 'lon': 116.0413},
    'Sulawesi Barat': {'lat': -2.8441, 'lon': 119.2321},
    'Bangka Belitung': {'lat': -2.7411, 'lon': 106.4406}
}


def get_province_coordinates(province: str) -> Dict[str, float]:
    """Get coordinates for a province."""
    return PROVINCE_COORDINATES.get(province, {'lat': -2.5, 'lon': 118.0})


def format_currency_idr(amount: float) -> str:
    """Format number as Indonesian Rupiah."""
    if amount >= 1_000_000_000_000:
        return f"Rp {amount/1_000_000_000_000:.1f}T"
    elif amount >= 1_000_000_000:
        return f"Rp {amount/1_000_000_000:.1f}M"
    elif amount >= 1_000_000:
        return f"Rp {amount/1_000_000:.1f}Jt"
    else:
        return f"Rp {amount:,.0f}"


def get_severity_color(severity: str) -> str:
    """Get color for severity level."""
    colors = {
        'Critical': '#dc2626',
        'High': '#f97316',
        'Medium': '#eab308',
        'Low': '#22c55e'
    }
    return colors.get(severity, '#6b7280')


def get_attack_icon(attack_type: str) -> str:
    """Get emoji icon for attack type."""
    icons = {
        'Phishing': '🎣',
        'Ransomware': '🔒',
        'DDoS': '🌊',
        'Data Breach': '📊',
        'Malware': '🦠',
        'Social Engineering': '🎭',
        'SQL Injection': '💉',
        'Man-in-the-Middle': '👤',
        'Credential Stuffing': '🔑',
        'Business Email Compromise': '📧',
        'Cryptojacking': '⛏️',
        'Zero-Day Exploit': '🆕',
        'Insider Threat': '👥',
        'Website Defacement': '🖼️'
    }
    return icons.get(attack_type, '⚠️')


def calculate_trend(values: pd.Series, periods: int = 3) -> str:
    """Calculate trend direction from recent values."""
    if len(values) < periods:
        return 'stable'
    
    recent = values.tail(periods)
    pct_change = (recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0] * 100
    
    if pct_change > 10:
        return 'increasing'
    elif pct_change < -10:
        return 'decreasing'
    else:
        return 'stable'


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


def load_processed_data() -> pd.DataFrame:
    """Load cleaned data if available, otherwise raw data."""
    root = get_project_root()
    processed_path = root / 'data' / 'processed' / 'cleaned_government_data.csv'
    raw_path = root / 'data' / 'raw' / 'sample_government_data.csv'
    
    if processed_path.exists():
        return pd.read_csv(processed_path)
    elif raw_path.exists():
        return pd.read_csv(raw_path)
    else:
        return pd.DataFrame()
