"""
Data Cleaning Module
Handles missing values, duplicates, normalization, and outlier detection.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime


class DataCleaner:
    """Comprehensive data cleaning pipeline for cyber crime data."""
    
    def __init__(self, df: pd.DataFrame = None):
        self.df = df.copy() if df is not None else None
        self.cleaning_log = []
    
    def load_data(self, filepath: str) -> 'DataCleaner':
        """Load data from CSV file."""
        self.df = pd.read_csv(filepath)
        self._log(f"Loaded {len(self.df)} records from {filepath}")
        return self
    
    def _log(self, message: str):
        """Log cleaning operation."""
        self.cleaning_log.append({
            'timestamp': datetime.now(),
            'message': message
        })
    
    def get_cleaning_report(self) -> pd.DataFrame:
        """Get cleaning operations log."""
        return pd.DataFrame(self.cleaning_log)
    
    # ============== MISSING VALUES ==============
    
    def handle_missing_values(
        self,
        strategy: str = 'auto',
        numeric_fill: str = 'median',
        categorical_fill: str = 'mode',
        drop_threshold: float = 0.5
    ) -> 'DataCleaner':
        """
        Handle missing values using various strategies.
        
        Args:
            strategy: 'auto', 'drop', 'fill', or 'interpolate'
            numeric_fill: 'mean', 'median', or 'zero'
            categorical_fill: 'mode' or 'unknown'
            drop_threshold: Drop columns with missing > threshold
        """
        if self.df is None:
            raise ValueError("No data loaded")
        
        initial_shape = self.df.shape
        missing_before = self.df.isnull().sum().sum()
        
        # Drop columns with too many missing values
        missing_pct = self.df.isnull().sum() / len(self.df)
        cols_to_drop = missing_pct[missing_pct > drop_threshold].index.tolist()
        if cols_to_drop:
            self.df = self.df.drop(columns=cols_to_drop)
            self._log(f"Dropped columns with >{drop_threshold*100}% missing: {cols_to_drop}")
        
        if strategy == 'drop':
            self.df = self.df.dropna()
            self._log(f"Dropped rows with missing values: {initial_shape[0] - len(self.df)} rows")
        
        elif strategy in ['auto', 'fill']:
            # Fill numeric columns
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if self.df[col].isnull().any():
                    if numeric_fill == 'mean':
                        fill_value = self.df[col].mean()
                    elif numeric_fill == 'median':
                        fill_value = self.df[col].median()
                    else:
                        fill_value = 0
                    self.df[col] = self.df[col].fillna(fill_value)
            
            # Fill categorical columns
            categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns
            for col in categorical_cols:
                if self.df[col].isnull().any():
                    if categorical_fill == 'mode':
                        fill_value = self.df[col].mode().iloc[0] if len(self.df[col].mode()) > 0 else 'Unknown'
                    else:
                        fill_value = 'Unknown'
                    self.df[col] = self.df[col].fillna(fill_value)
        
        elif strategy == 'interpolate':
            self.df = self.df.interpolate(method='linear')
        
        missing_after = self.df.isnull().sum().sum()
        self._log(f"Missing values: {missing_before} -> {missing_after}")
        
        return self
    
    # ============== DUPLICATES ==============
    
    def remove_duplicates(
        self,
        subset: List[str] = None,
        keep: str = 'first'
    ) -> 'DataCleaner':
        """
        Remove duplicate records.
        
        Args:
            subset: Columns to check for duplicates
            keep: 'first', 'last', or False (remove all)
        """
        if self.df is None:
            raise ValueError("No data loaded")
        
        initial_count = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset, keep=keep)
        removed = initial_count - len(self.df)
        
        self._log(f"Removed {removed} duplicate records")
        
        return self
    
    # ============== NORMALIZATION ==============
    
    def normalize_text_columns(
        self,
        columns: List[str] = None,
        lowercase: bool = True,
        strip_whitespace: bool = True
    ) -> 'DataCleaner':
        """
        Normalize text columns.
        
        Args:
            columns: Specific columns to normalize (None = all text columns)
            lowercase: Convert to lowercase
            strip_whitespace: Remove leading/trailing whitespace
        """
        if self.df is None:
            raise ValueError("No data loaded")
        
        if columns is None:
            columns = self.df.select_dtypes(include=['object']).columns.tolist()
        
        for col in columns:
            if col in self.df.columns:
                if strip_whitespace:
                    self.df[col] = self.df[col].astype(str).str.strip()
                if lowercase:
                    self.df[col] = self.df[col].str.lower()
        
        self._log(f"Normalized text columns: {columns}")
        
        return self
    
    def normalize_province_names(self) -> 'DataCleaner':
        """Standardize Indonesian province names."""
        if 'province' not in self.df.columns:
            return self
        
        # Common variations and their standard forms
        province_mapping = {
            'jakarta': 'DKI Jakarta',
            'dki jakarta': 'DKI Jakarta',
            'jabar': 'Jawa Barat',
            'jawa barat': 'Jawa Barat',
            'jatim': 'Jawa Timur',
            'jawa timur': 'Jawa Timur',
            'jateng': 'Jawa Tengah',
            'jawa tengah': 'Jawa Tengah',
            'yogyakarta': 'DI Yogyakarta',
            'di yogyakarta': 'DI Yogyakarta',
            'diy': 'DI Yogyakarta',
            'sumut': 'Sumatera Utara',
            'sumatera utara': 'Sumatera Utara',
            'sumbar': 'Sumatera Barat',
            'sumatera barat': 'Sumatera Barat',
            'sumsel': 'Sumatera Selatan',
            'sumatera selatan': 'Sumatera Selatan',
            'kaltim': 'Kalimantan Timur',
            'kalimantan timur': 'Kalimantan Timur',
            'kalsel': 'Kalimantan Selatan',
            'kalimantan selatan': 'Kalimantan Selatan',
            'sulsel': 'Sulawesi Selatan',
            'sulawesi selatan': 'Sulawesi Selatan',
        }
        
        self.df['province'] = self.df['province'].str.lower().map(
            lambda x: province_mapping.get(x, x.title())
        )
        
        self._log("Normalized province names")
        
        return self
    
    # ============== OUTLIER DETECTION ==============
    
    def detect_outliers_iqr(
        self,
        columns: List[str] = None,
        multiplier: float = 1.5
    ) -> Dict[str, pd.DataFrame]:
        """
        Detect outliers using IQR method.
        
        Args:
            columns: Columns to check (None = all numeric)
            multiplier: IQR multiplier (1.5 = standard, 3.0 = extreme)
            
        Returns:
            Dictionary with outlier info per column
        """
        if self.df is None:
            raise ValueError("No data loaded")
        
        if columns is None:
            columns = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        outliers = {}
        
        for col in columns:
            if col not in self.df.columns:
                continue
                
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - multiplier * IQR
            upper_bound = Q3 + multiplier * IQR
            
            outlier_mask = (self.df[col] < lower_bound) | (self.df[col] > upper_bound)
            outlier_data = self.df[outlier_mask]
            
            outliers[col] = {
                'count': len(outlier_data),
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'outlier_indices': outlier_data.index.tolist()
            }
        
        total_outliers = sum(o['count'] for o in outliers.values())
        self._log(f"Detected {total_outliers} outliers across {len(columns)} columns")
        
        return outliers
    
    def handle_outliers(
        self,
        columns: List[str] = None,
        strategy: str = 'clip',
        multiplier: float = 1.5
    ) -> 'DataCleaner':
        """
        Handle outliers using specified strategy.
        
        Args:
            columns: Columns to process
            strategy: 'clip', 'remove', or 'replace_median'
            multiplier: IQR multiplier
        """
        if self.df is None:
            raise ValueError("No data loaded")
        
        if columns is None:
            columns = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in columns:
            if col not in self.df.columns:
                continue
            
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - multiplier * IQR
            upper_bound = Q3 + multiplier * IQR
            
            if strategy == 'clip':
                self.df[col] = self.df[col].clip(lower=lower_bound, upper=upper_bound)
            elif strategy == 'remove':
                mask = (self.df[col] >= lower_bound) & (self.df[col] <= upper_bound)
                self.df = self.df[mask]
            elif strategy == 'replace_median':
                median = self.df[col].median()
                outlier_mask = (self.df[col] < lower_bound) | (self.df[col] > upper_bound)
                self.df.loc[outlier_mask, col] = median
        
        self._log(f"Applied '{strategy}' strategy to outliers in {columns}")
        
        return self
    
    # ============== DATE HANDLING ==============
    
    def parse_dates(
        self,
        date_column: str = 'date',
        format: str = None
    ) -> 'DataCleaner':
        """Parse date column to datetime."""
        if date_column in self.df.columns:
            self.df[date_column] = pd.to_datetime(self.df[date_column], format=format)
            self._log(f"Parsed '{date_column}' to datetime")
        
        return self
    
    def add_date_features(
        self,
        date_column: str = 'date'
    ) -> 'DataCleaner':
        """Add useful date features."""
        if date_column not in self.df.columns:
            return self
        
        self.df['year'] = self.df[date_column].dt.year
        self.df['month'] = self.df[date_column].dt.month
        self.df['quarter'] = self.df[date_column].dt.quarter
        self.df['day_of_week'] = self.df[date_column].dt.dayofweek
        self.df['week_of_year'] = self.df[date_column].dt.isocalendar().week
        
        self._log("Added date features: year, month, quarter, day_of_week, week_of_year")
        
        return self
    
    # ============== PIPELINE ==============
    
    def run_full_pipeline(self) -> 'DataCleaner':
        """
        Run complete cleaning pipeline with sensible defaults.
        """
        return (
            self
            .parse_dates()
            .remove_duplicates()
            .handle_missing_values(strategy='auto')
            .normalize_province_names()
            .handle_outliers(strategy='clip')
            .add_date_features()
        )
    
    def get_clean_data(self) -> pd.DataFrame:
        """Return cleaned DataFrame."""
        return self.df
    
    def save_clean_data(self, output_path: str) -> None:
        """Save cleaned data to CSV."""
        self.df.to_csv(output_path, index=False)
        self._log(f"Saved cleaned data to {output_path}")
    
    def get_data_quality_report(self) -> Dict[str, Any]:
        """Generate data quality report."""
        if self.df is None:
            return {}
        
        return {
            'total_records': len(self.df),
            'total_columns': len(self.df.columns),
            'missing_values': self.df.isnull().sum().to_dict(),
            'missing_percentage': (self.df.isnull().sum() / len(self.df) * 100).to_dict(),
            'duplicates': self.df.duplicated().sum(),
            'data_types': self.df.dtypes.astype(str).to_dict(),
            'memory_usage_mb': self.df.memory_usage(deep=True).sum() / 1024**2
        }


if __name__ == '__main__':
    from pathlib import Path
    
    # Test with sample data
    data_path = Path(__file__).parent.parent.parent / 'data' / 'raw' / 'sample_government_data.csv'
    output_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'cleaned_government_data.csv'
    
    if data_path.exists():
        cleaner = DataCleaner()
        cleaner.load_data(str(data_path))
        cleaner.run_full_pipeline()
        cleaner.save_clean_data(str(output_path))
        
        print("Cleaning Report:")
        for log in cleaner.cleaning_log:
            print(f"  - {log['message']}")
        
        print("\nData Quality Report:")
        report = cleaner.get_data_quality_report()
        print(f"  Total records: {report['total_records']}")
        print(f"  Total columns: {report['total_columns']}")
        print(f"  Duplicates: {report['duplicates']}")
