# Big Data Analysis: Cyber Crime in Indonesia

A comprehensive Big Data Analysis project for analyzing cyber crime patterns in Indonesia using Python, featuring data integration, Social Network Analysis, Machine Learning predictions, and an interactive Streamlit dashboard.

## Features

- **Data Integration**: Government statistics (CSV) + News web scraping
- **Data Cleaning**: Missing values, duplicates, outliers handling
- **Social Network Analysis (SNA)**: Attack relationship mapping, centrality metrics
- **Machine Learning**: Time series prediction with 6-month forecast
- **Interactive Dashboard**: Streamlit with maps, charts, and filters

## Installation

```bash
cd /home/kyra/bigdata
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Run Dashboard
```bash
streamlit run dashboard/app.py
```

## Project Structure

```
bigdata/
├── data/                 # Raw and processed data
├── src/                  # Source code modules
├── dashboard/            # Streamlit application
└── notebooks/            # EDA notebooks
```
