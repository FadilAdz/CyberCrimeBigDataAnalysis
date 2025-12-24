"""
Machine Learning Module for Cyber Crime Prediction
Time series prediction with Random Forest and Linear Regression.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class CyberCrimePredictor:
    """
    Time series prediction for cyber crime trends.
    Uses ensemble methods and regression for forecasting.
    """
    
    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.target_column = 'incident_count'
        self.trained = False
        self.metrics = {}
        self.forecast_df = None
    
    def prepare_time_series_data(
        self,
        df: pd.DataFrame,
        date_column: str = 'date',
        agg_level: str = 'M',
        target: str = 'incident_count'
    ) -> pd.DataFrame:
        """
        Prepare time series data from incident-level data.
        
        Args:
            df: Raw incident data
            date_column: Column with dates
            agg_level: Aggregation level ('D', 'W', 'M')
            target: Target variable to predict
        """
        # Ensure date column is datetime
        df = df.copy()
        df[date_column] = pd.to_datetime(df[date_column])
        
        # Aggregate to specified level
        if agg_level == 'M':
            df['period'] = df[date_column].dt.to_period('M').dt.to_timestamp()
        elif agg_level == 'W':
            df['period'] = df[date_column].dt.to_period('W').dt.to_timestamp()
        else:
            df['period'] = df[date_column].dt.date
        
        # Aggregate counts
        time_series = df.groupby('period').agg({
            df.columns[0]: 'count',  # Count incidents
        }).rename(columns={df.columns[0]: 'incident_count'})
        
        # Add additional aggregations if columns exist
        if 'financial_loss_idr' in df.columns:
            loss_agg = df.groupby('period')['financial_loss_idr'].sum()
            time_series['total_financial_loss'] = loss_agg
        
        if 'victims_count' in df.columns:
            victims_agg = df.groupby('period')['victims_count'].sum()
            time_series['total_victims'] = victims_agg
        
        # Attack type distribution per period
        if 'attack_type' in df.columns:
            attack_dist = df.groupby(['period', 'attack_type']).size().unstack(fill_value=0)
            attack_dist.columns = [f'attack_{col}' for col in attack_dist.columns]
            time_series = time_series.join(attack_dist)
        
        time_series = time_series.reset_index()
        time_series = time_series.sort_values('period').reset_index(drop=True)
        
        return time_series
    
    def create_features(
        self,
        df: pd.DataFrame,
        target_col: str = 'incident_count',
        n_lags: int = 6
    ) -> pd.DataFrame:
        """
        Create time series features for ML models.
        
        Features:
        - Lag features (previous N periods)
        - Rolling statistics (mean, std)
        - Trend features (month, quarter)
        - Exponential moving average
        """
        df = df.copy()
        
        # Date features
        df['month'] = pd.to_datetime(df['period']).dt.month
        df['quarter'] = pd.to_datetime(df['period']).dt.quarter
        df['year'] = pd.to_datetime(df['period']).dt.year
        
        # Lag features
        for i in range(1, n_lags + 1):
            df[f'lag_{i}'] = df[target_col].shift(i)
        
        # Rolling statistics
        for window in [3, 6, 12]:
            if len(df) >= window:
                df[f'rolling_mean_{window}'] = df[target_col].rolling(window=window).mean()
                df[f'rolling_std_{window}'] = df[target_col].rolling(window=window).std()
        
        # Exponential moving average
        df['ema_3'] = df[target_col].ewm(span=3, adjust=False).mean()
        df['ema_6'] = df[target_col].ewm(span=6, adjust=False).mean()
        
        # Trend (percentage change)
        df['pct_change'] = df[target_col].pct_change()
        
        # Month-over-month growth
        df['mom_growth'] = df[target_col].diff()
        
        # Drop rows with NaN from lagging
        df = df.dropna()
        
        return df
    
    def train(
        self,
        df: pd.DataFrame,
        target_col: str = 'incident_count',
        test_size: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train prediction models.
        
        Args:
            df: Prepared time series data with features
            target_col: Target column to predict
            test_size: Fraction for test set
        """
        self.target_column = target_col
        
        # Define features (exclude target and period)
        self.feature_columns = [
            col for col in df.columns 
            if col not in [target_col, 'period', 'total_financial_loss', 'total_victims']
            and not col.startswith('attack_')
        ]
        
        X = df[self.feature_columns]
        y = df[target_col]
        
        # Time series split (no shuffle)
        split_idx = int(len(df) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest
        self.models['random_forest'] = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        self.models['random_forest'].fit(X_train_scaled, y_train)
        
        # Train Linear Regression
        self.models['linear_regression'] = LinearRegression()
        self.models['linear_regression'].fit(X_train_scaled, y_train)
        
        # Train Ridge Regression
        self.models['ridge'] = Ridge(alpha=1.0)
        self.models['ridge'].fit(X_train_scaled, y_train)
        
        # Evaluate models
        self.metrics = {}
        for name, model in self.models.items():
            y_pred = model.predict(X_test_scaled)
            self.metrics[name] = {
                'mae': mean_absolute_error(y_test, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                'r2': r2_score(y_test, y_pred),
                'mape': np.mean(np.abs((y_test - y_pred) / y_test)) * 100
            }
        
        self.trained = True
        
        return {
            'metrics': self.metrics,
            'feature_importance': self.get_feature_importance(),
            'test_predictions': {
                name: model.predict(X_test_scaled)
                for name, model in self.models.items()
            },
            'y_test': y_test.values,
            'test_dates': df['period'].iloc[split_idx:].values
        }
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance from Random Forest."""
        if 'random_forest' not in self.models:
            return pd.DataFrame()
        
        importance = self.models['random_forest'].feature_importances_
        df_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return df_importance
    
    def forecast(
        self,
        df: pd.DataFrame,
        periods: int = 6,
        model_name: str = 'random_forest'
    ) -> pd.DataFrame:
        """
        Forecast future periods.
        
        Args:
            df: Historical data with features
            periods: Number of periods to forecast
            model_name: Model to use for prediction
        """
        if not self.trained:
            raise ValueError("Model not trained. Call train() first.")
        
        model = self.models.get(model_name)
        if model is None:
            raise ValueError(f"Model {model_name} not found")
        
        # Get last row as base
        last_row = df.iloc[-1:].copy()
        last_period = pd.to_datetime(last_row['period'].values[0])
        
        predictions = []
        
        for i in range(1, periods + 1):
            # Calculate next period
            next_period = last_period + pd.DateOffset(months=i)
            
            # Update features for prediction
            pred_row = last_row.copy()
            pred_row['period'] = next_period
            pred_row['month'] = next_period.month
            pred_row['quarter'] = next_period.quarter
            pred_row['year'] = next_period.year
            
            # Use current values as lag (simplified approach)
            # In production, would use actual predictions for recursive forecast
            X_pred = pred_row[self.feature_columns]
            X_pred_scaled = self.scaler.transform(X_pred)
            
            pred_value = model.predict(X_pred_scaled)[0]
            
            # Ensure non-negative
            pred_value = max(0, pred_value)
            
            predictions.append({
                'period': next_period,
                'predicted_incidents': round(pred_value),
                'forecast_month': i
            })
            
            # Update last row for next iteration
            last_row[self.target_column] = pred_value
        
        self.forecast_df = pd.DataFrame(predictions)
        return self.forecast_df
    
    def get_prediction_intervals(
        self,
        df: pd.DataFrame,
        periods: int = 6,
        confidence: float = 0.95
    ) -> pd.DataFrame:
        """Get prediction with confidence intervals using ensemble."""
        if not self.trained:
            raise ValueError("Model not trained")
        
        # Get predictions from all models
        all_preds = []
        for name in self.models.keys():
            preds = self.forecast(df, periods, name)
            preds['model'] = name
            all_preds.append(preds)
        
        combined = pd.concat(all_preds)
        
        # Calculate statistics
        summary = combined.groupby('period')['predicted_incidents'].agg([
            'mean', 'std', 'min', 'max'
        ]).reset_index()
        
        # Calculate confidence intervals
        z_score = 1.96 if confidence == 0.95 else 1.645
        summary['lower_bound'] = (summary['mean'] - z_score * summary['std']).clip(lower=0)
        summary['upper_bound'] = summary['mean'] + z_score * summary['std']
        
        return summary
    
    def get_model_comparison(self) -> pd.DataFrame:
        """Compare all trained models."""
        if not self.metrics:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.metrics).T
        df.index.name = 'model'
        df = df.reset_index()
        
        return df


def run_prediction_pipeline(
    df: pd.DataFrame,
    forecast_months: int = 6
) -> Dict[str, Any]:
    """
    Run complete prediction pipeline.
    
    Args:
        df: Raw incident data
        forecast_months: Number of months to forecast
        
    Returns:
        Dictionary with all prediction results
    """
    predictor = CyberCrimePredictor()
    
    # Prepare time series
    ts_data = predictor.prepare_time_series_data(df)
    
    # Create features
    feature_data = predictor.create_features(ts_data)
    
    # Train models
    training_results = predictor.train(feature_data)
    
    # Forecast
    forecast = predictor.forecast(feature_data, periods=forecast_months)
    
    # Get confidence intervals
    confidence_intervals = predictor.get_prediction_intervals(
        feature_data, 
        periods=forecast_months
    )
    
    return {
        'time_series_data': ts_data,
        'feature_data': feature_data,
        'training_results': training_results,
        'model_comparison': predictor.get_model_comparison(),
        'feature_importance': predictor.get_feature_importance(),
        'forecast': forecast,
        'confidence_intervals': confidence_intervals,
        'predictor': predictor
    }


if __name__ == '__main__':
    from pathlib import Path
    
    # Test with sample data
    data_path = Path(__file__).parent.parent.parent / 'data' / 'raw' / 'sample_government_data.csv'
    
    if data_path.exists():
        df = pd.read_csv(data_path)
        results = run_prediction_pipeline(df, forecast_months=6)
        
        print("Model Comparison:")
        print(results['model_comparison'].to_string())
        
        print("\nTop 5 Important Features:")
        print(results['feature_importance'].head())
        
        print("\n6-Month Forecast:")
        print(results['forecast'])
        
        print("\nForecast with Confidence Intervals:")
        print(results['confidence_intervals'])
