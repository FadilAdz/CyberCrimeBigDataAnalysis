"""
Big Data Analysis Dashboard: Cyber Crime in Indonesia
Interactive Streamlit dashboard for cyber crime analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dashboard.components import (
    render_kpi_cards,
    render_trend_chart,
    render_attack_distribution,
    render_severity_pie,
    render_sector_chart,
    render_indonesia_map,
    render_heatmap_chart,
    render_forecast_chart,
    render_network_graph,
    render_data_table,
    create_filter_sidebar,
    apply_filters
)

# Page configuration
st.set_page_config(
    page_title="Cyber Crime Analysis Indonesia",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #334155;
    }
    .stMetric label {
        color: #94a3b8 !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #f1f5f9 !important;
        font-size: 2rem !important;
    }
    h1, h2, h3 {
        color: #f1f5f9 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #1e293b;
        border-radius: 8px;
        padding: 0 20px;
        color: #94a3b8;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: white !important;
    }
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Load and cache the dataset."""
    data_path = project_root / 'data' / 'raw' / 'sample_government_data.csv'
    processed_path = project_root / 'data' / 'processed' / 'cleaned_government_data.csv'
    
    # Try processed data first, then raw
    if processed_path.exists():
        df = pd.read_csv(processed_path)
    elif data_path.exists():
        df = pd.read_csv(data_path)
    else:
        # Generate sample data if not exists
        from src.data_collection.government_data import generate_sample_government_data
        df = generate_sample_government_data(output_path=str(data_path))
    
    df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data
def load_news_data():
    """Load scraped news articles."""
    news_paths = [
        project_root / 'data' / 'external' / 'merged_news_data.csv',
        project_root / 'data' / 'external' / 'scraped_real_news.csv',
    ]
    
    for path in news_paths:
        if path.exists():
            df = pd.read_csv(path)
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            return df
    
    return pd.DataFrame()


@st.cache_data
def run_sna_analysis(df):
    """Run and cache SNA analysis results."""
    from src.sna.sna_analysis import analyze_attack_relationships
    return analyze_attack_relationships(df)


@st.cache_data
def run_prediction(df):
    """Run and cache ML prediction results."""
    from src.ml.time_series_model import run_prediction_pipeline
    return run_prediction_pipeline(df, forecast_months=6)


def main():
    # Header
    st.title("🔒 Cyber Crime Analysis Dashboard")
    st.markdown("### Big Data Analysis - Indonesia Cyber Security Trends")
    st.markdown("---")
    
    # Load data
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Please ensure sample data is generated first by running the data collection module.")
        return
    
    # Sidebar filters
    filters = create_filter_sidebar(df)
    filtered_df = apply_filters(df, filters)
    
    # Show filter status
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Showing:** {len(filtered_df):,} of {len(df):,} records")
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Overview",
        "🗺️ Geographic",
        "📈 Trends",
        "🌐 Network Analysis",
        "🔮 Predictions",
        "📰 News",
        "📋 Data Explorer"
    ])
    
    # === TAB 1: OVERVIEW ===
    with tab1:
        st.header("Dashboard Overview")
        
        # KPI Cards
        render_kpi_cards(filtered_df)
        
        st.markdown("---")
        
        # Charts row 1
        col1, col2 = st.columns(2)
        
        with col1:
            fig = render_attack_distribution(filtered_df)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = render_severity_pie(filtered_df)
            st.plotly_chart(fig, use_container_width=True)
        
        # Charts row 2
        col3, col4 = st.columns(2)
        
        with col3:
            fig = render_sector_chart(filtered_df)
            st.plotly_chart(fig, use_container_width=True)
        
        with col4:
            # Top provinces chart
            province_counts = filtered_df['province'].value_counts().head(10)
            import plotly.express as px
            fig = px.bar(
                x=province_counts.values,
                y=province_counts.index,
                orientation='h',
                title='📍 Top 10 Provinces by Incidents',
                color=province_counts.values,
                color_continuous_scale='Purples'
            )
            fig.update_layout(
                template='plotly_dark',
                showlegend=False,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # === TAB 2: GEOGRAPHIC ===
    with tab2:
        st.header("🗺️ Geographic Distribution")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Indonesia Cyber Crime Heatmap")
            m = render_indonesia_map(filtered_df)
            from streamlit_folium import st_folium
            st_folium(m, width=800, height=500)
        
        with col2:
            st.subheader("Province Statistics")
            # Build aggregation dict based on available columns
            agg_dict = {}
            if 'incident_count' in filtered_df.columns:
                agg_dict['incident_count'] = 'sum'
            else:
                agg_dict['attack_type'] = 'count'
            
            if 'victims_count' in filtered_df.columns:
                agg_dict['victims_count'] = 'sum'
            if 'financial_loss_idr' in filtered_df.columns:
                agg_dict['financial_loss_idr'] = 'sum'
            
            province_stats = filtered_df.groupby('province').agg(agg_dict)
            
            # Rename columns
            rename_map = {
                'incident_count': 'Total Incidents',
                'attack_type': 'Incidents',
                'victims_count': 'Victims',
                'financial_loss_idr': 'Loss (IDR)'
            }
            province_stats = province_stats.rename(columns=rename_map)
            province_stats = province_stats.sort_values(
                province_stats.columns[0], ascending=False
            )
            
            st.dataframe(province_stats.head(15), use_container_width=True)
    
    # === TAB 3: TRENDS ===
    with tab3:
        st.header("📈 Time Series Trends")
        
        # Main trend chart
        fig = render_trend_chart(filtered_df)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Heatmap
            fig = render_heatmap_chart(filtered_df)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Year over year comparison
            filtered_df['year'] = filtered_df['date'].dt.year
            yearly = filtered_df.groupby('year').size().reset_index(name='incidents')
            
            import plotly.express as px
            fig = px.bar(
                yearly,
                x='year',
                y='incidents',
                title='📅 Year-over-Year Incidents',
                color='incidents',
                color_continuous_scale='Blues'
            )
            fig.update_layout(template='plotly_dark', showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    # === TAB 4: NETWORK ANALYSIS ===
    with tab4:
        st.header("🌐 Social Network Analysis")
        
        with st.spinner("Running SNA analysis..."):
            try:
                sna_results = run_sna_analysis(filtered_df)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Nodes", sna_results['network_stats']['num_nodes'])
                with col2:
                    st.metric("Edges", sna_results['network_stats']['num_edges'])
                with col3:
                    st.metric("Density", f"{sna_results['network_stats']['density']:.3f}")
                with col4:
                    st.metric("Clustering", f"{sna_results['network_stats']['avg_clustering']:.3f}")
                
                st.markdown("---")
                
                # Network visualization
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("Attack Type Relationship Network")
                    from src.sna.sna_analysis import SNAAnalyzer
                    analyzer = SNAAnalyzer(filtered_df)
                    analyzer.build_attack_network()
                    analyzer.calculate_centrality_metrics()
                    analyzer.detect_communities()
                    graph_data = analyzer.export_graph_json()
                    
                    html = render_network_graph(graph_data)
                    import streamlit.components.v1 as components
                    components.html(html, height=520)
                
                with col2:
                    st.subheader("Top Central Attacks")
                    
                    st.markdown("**By Degree Centrality:**")
                    for attack, score in sna_results['top_attacks']['by_degree']:
                        st.write(f"• {attack}: {score:.4f}")
                    
                    st.markdown("**By Betweenness:**")
                    for attack, score in sna_results['top_attacks']['by_betweenness']:
                        st.write(f"• {attack}: {score:.4f}")
                    
                    st.markdown("---")
                    st.subheader("Communities Detected")
                    for comm_id, members in sna_results['community_summary'].items():
                        st.write(f"**Community {comm_id}:** {', '.join(members)}")
            
            except Exception as e:
                st.error(f"Error in SNA analysis: {e}")
                st.info("Make sure all required packages are installed.")
    
    # === TAB 5: PREDICTIONS ===
    with tab5:
        st.header("🔮 ML Predictions")
        
        with st.spinner("Training prediction models..."):
            try:
                prediction_results = run_prediction(filtered_df)
                
                # Model comparison
                st.subheader("Model Performance Comparison")
                model_df = prediction_results['model_comparison']
                st.dataframe(model_df, use_container_width=True)
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Forecast chart
                    st.subheader("6-Month Forecast")
                    fig = render_forecast_chart(
                        prediction_results['time_series_data'],
                        prediction_results['forecast'],
                        prediction_results['confidence_intervals']
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Feature importance
                    st.subheader("Feature Importance")
                    importance_df = prediction_results['feature_importance']
                    
                    import plotly.express as px
                    fig = px.bar(
                        importance_df.head(10),
                        x='importance',
                        y='feature',
                        orientation='h',
                        title='Top 10 Important Features',
                        color='importance',
                        color_continuous_scale='Greens'
                    )
                    fig.update_layout(
                        template='plotly_dark',
                        yaxis={'categoryorder': 'total ascending'},
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Forecast table
                st.subheader("Forecast Details")
                forecast_table = prediction_results['confidence_intervals'].copy()
                forecast_table['period'] = pd.to_datetime(forecast_table['period']).dt.strftime('%B %Y')
                forecast_table = forecast_table.rename(columns={
                    'period': 'Month',
                    'mean': 'Predicted Incidents',
                    'lower_bound': 'Lower Bound (95%)',
                    'upper_bound': 'Upper Bound (95%)'
                })
                st.dataframe(forecast_table, use_container_width=True)
            
            except Exception as e:
                st.error(f"Error in prediction: {e}")
                st.info("Make sure scikit-learn is installed and data is sufficient for training.")
    
    # === TAB 6: NEWS ===
    with tab6:
        st.header("📰 Cyber Crime News")
        
        # Load news data
        news_df = load_news_data()
        
        if len(news_df) == 0:
            st.warning("No news data found. Run the scraper first:")
            st.code("python src/data_collection/rss_scraper.py", language="bash")
        else:
            st.success(f"📰 {len(news_df)} articles loaded from scraped news data")
            
            # News filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if 'source' in news_df.columns:
                    sources = ['All'] + list(news_df['source'].unique())
                    selected_source = st.selectbox("Filter by Source", sources)
            
            with col2:
                search_term = st.text_input("🔍 Search articles", placeholder="Enter keyword...")
            
            with col3:
                sort_order = st.selectbox("Sort by", ["Newest First", "Oldest First"])
            
            # Apply filters
            filtered_news = news_df.copy()
            
            if selected_source != 'All':
                filtered_news = filtered_news[filtered_news['source'] == selected_source]
            
            if search_term:
                mask = filtered_news['title'].str.contains(search_term, case=False, na=False)
                if 'content' in filtered_news.columns:
                    mask = mask | filtered_news['content'].str.contains(search_term, case=False, na=False)
                filtered_news = filtered_news[mask]
            
            # Sort
            if 'date' in filtered_news.columns:
                filtered_news = filtered_news.sort_values('date', ascending=(sort_order == "Oldest First"))
            
            st.markdown(f"**Showing {len(filtered_news)} articles**")
            st.markdown("---")
            
            # Display articles as cards
            for idx, row in filtered_news.head(20).iterrows():
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        # Title as link
                        url = row.get('url', '#')
                        title = row.get('title', 'No Title')
                        st.markdown(f"### [{title}]({url})")
                        
                        # Source and date
                        source = row.get('source', 'Unknown')
                        date = row.get('date', '')
                        if pd.notna(date):
                            try:
                                date_str = pd.to_datetime(date).strftime('%d %B %Y')
                            except:
                                date_str = str(date)
                        else:
                            date_str = 'Unknown date'
                        
                        st.caption(f"📌 {source} • 📅 {date_str}")
                        
                        # Content preview
                        content = row.get('content', '')
                        if content and len(str(content)) > 10:
                            preview = str(content)[:300] + "..." if len(str(content)) > 300 else str(content)
                            st.write(preview)
                    
                    with col2:
                        st.markdown("")
                        st.link_button("🔗 Read Full", url)
                    
                    st.markdown("---")
    
    # === TAB 7: DATA EXPLORER ===
    with tab7:
        st.header("📋 Data Explorer")
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            st.subheader("Quick Stats")
            st.write(f"**Total Records:** {len(filtered_df):,}")
            st.write(f"**Date Range:** {filtered_df['date'].min().strftime('%Y-%m-%d')} to {filtered_df['date'].max().strftime('%Y-%m-%d')}")
            st.write(f"**Unique Provinces:** {filtered_df['province'].nunique()}")
            st.write(f"**Unique Attack Types:** {filtered_df['attack_type'].nunique()}")
            
            # Download button
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Data",
                data=csv,
                file_name="cyber_crime_data.csv",
                mime="text/csv"
            )
        
        with col1:
            st.subheader("Full Dataset")
            render_data_table(filtered_df)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #64748b; padding: 20px;'>
            <p>🔒 Cyber Crime Analysis Dashboard | Big Data Analysis Project</p>
            <p>Data sources: BSSN, Kominfo, Kepolisian RI, News Scraping (Detik, CNN Indonesia)</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
