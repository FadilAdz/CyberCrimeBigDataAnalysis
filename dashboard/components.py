"""
Streamlit Dashboard Components
Reusable chart and visualization components.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import folium
from streamlit_folium import st_folium


# Province coordinates for Indonesia map
PROVINCE_COORDS = {
    'DKI Jakarta': [-6.2088, 106.8456],
    'Jawa Barat': [-6.9175, 107.6191],
    'Jawa Tengah': [-7.1510, 110.1403],
    'Jawa Timur': [-7.5361, 112.2384],
    'Banten': [-6.4058, 106.0640],
    'DI Yogyakarta': [-7.7956, 110.3695],
    'Sumatera Utara': [3.5852, 98.6619],
    'Sumatera Barat': [-0.9471, 100.4172],
    'Sumatera Selatan': [-3.3194, 104.9147],
    'Riau': [0.5071, 101.4478],
    'Kepulauan Riau': [1.0456, 104.0305],
    'Lampung': [-5.4500, 105.2667],
    'Kalimantan Timur': [-0.5022, 117.1536],
    'Kalimantan Selatan': [-3.0926, 115.2838],
    'Kalimantan Barat': [-0.0263, 109.3425],
    'Sulawesi Selatan': [-5.1355, 119.4233],
    'Sulawesi Utara': [1.4748, 124.8421],
    'Bali': [-8.3405, 115.0920],
    'Nusa Tenggara Barat': [-8.6529, 117.3616],
    'Nusa Tenggara Timur': [-8.6574, 121.0794],
    'Papua': [-4.2699, 138.0804],
    'Papua Barat': [-1.3361, 133.1747],
    'Maluku': [-3.2385, 130.1453],
    'Maluku Utara': [1.5709, 127.8088],
    'Gorontalo': [0.6999, 122.4467],
    'Sulawesi Tengah': [-1.4300, 121.4456],
    'Sulawesi Tenggara': [-4.1448, 122.1746],
    'Bengkulu': [-3.7928, 102.2608],
    'Jambi': [-1.6101, 103.6131],
    'Aceh': [4.6951, 96.7494],
    'Kalimantan Tengah': [-1.6815, 113.3824],
    'Kalimantan Utara': [3.0731, 116.0413],
    'Sulawesi Barat': [-2.8441, 119.2321],
    'Bangka Belitung': [-2.7411, 106.4406]
}


def render_kpi_cards(df: pd.DataFrame) -> None:
    """Render KPI summary cards."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Total records
        st.metric(
            label="📊 Total Records",
            value=f"{len(df):,}",
            delta=None
        )
    
    with col2:
        # Total incident count if available
        if 'incident_count' in df.columns:
            total_incidents = df['incident_count'].sum()
            st.metric(
                label="🔢 Total Incidents",
                value=f"{total_incidents:,.0f}",
                delta=None
            )
        elif 'victims_count' in df.columns:
            total_victims = df['victims_count'].sum()
            st.metric(
                label="👥 Total Victims",
                value=f"{total_victims:,.0f}",
                delta=None
            )
        else:
            # Show provinces count
            st.metric(
                label="📍 Provinces",
                value=df['province'].nunique() if 'province' in df.columns else 'N/A',
                delta=None
            )
    
    with col3:
        if 'financial_loss_idr' in df.columns:
            total_loss = df['financial_loss_idr'].sum()
            if total_loss >= 1e12:
                loss_str = f"Rp {total_loss/1e12:.1f}T"
            elif total_loss >= 1e9:
                loss_str = f"Rp {total_loss/1e9:.1f}M"
            else:
                loss_str = f"Rp {total_loss/1e6:.1f}Jt"
            st.metric(
                label="💰 Total Loss",
                value=loss_str,
                delta=None
            )
        else:
            # Show sectors count
            st.metric(
                label="🏢 Sectors",
                value=df['sector'].nunique() if 'sector' in df.columns else 'N/A',
                delta=None
            )
    
    with col4:
        if 'attack_type' in df.columns:
            unique_attacks = df['attack_type'].nunique()
            st.metric(
                label="🎯 Attack Types",
                value=unique_attacks,
                delta=None
            )


def render_trend_chart(
    df: pd.DataFrame,
    date_col: str = 'date',
    value_col: str = 'incident_count'
) -> go.Figure:
    """Create time series trend chart."""
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Aggregate by month
    monthly = df.groupby(df[date_col].dt.to_period('M')).size().reset_index()
    monthly.columns = ['period', 'count']
    monthly['period'] = monthly['period'].dt.to_timestamp()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly['period'],
        y=monthly['count'],
        mode='lines+markers',
        name='Incidents',
        line=dict(color='#3b82f6', width=2),
        marker=dict(size=6),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)'
    ))
    
    # Add trend line
    z = np.polyfit(range(len(monthly)), monthly['count'], 1)
    p = np.poly1d(z)
    fig.add_trace(go.Scatter(
        x=monthly['period'],
        y=p(range(len(monthly))),
        mode='lines',
        name='Trend',
        line=dict(color='#ef4444', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title='📈 Cyber Crime Trend Over Time',
        xaxis_title='Period',
        yaxis_title='Number of Incidents',
        template='plotly_dark',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig


def render_attack_distribution(df: pd.DataFrame) -> go.Figure:
    """Create attack type distribution chart."""
    attack_counts = df['attack_type'].value_counts().reset_index()
    attack_counts.columns = ['attack_type', 'count']
    
    fig = px.bar(
        attack_counts,
        x='count',
        y='attack_type',
        orientation='h',
        title='🎯 Attack Type Distribution',
        color='count',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        template='plotly_dark',
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False
    )
    
    return fig


def render_severity_pie(df: pd.DataFrame) -> go.Figure:
    """Create severity distribution pie chart."""
    severity_counts = df['severity'].value_counts()
    
    colors = {
        'Critical': '#dc2626',
        'High': '#f97316',
        'Medium': '#eab308',
        'Low': '#22c55e'
    }
    
    fig = go.Figure(data=[go.Pie(
        labels=severity_counts.index,
        values=severity_counts.values,
        hole=0.4,
        marker_colors=[colors.get(s, '#6b7280') for s in severity_counts.index]
    )])
    
    fig.update_layout(
        title='⚠️ Severity Distribution',
        template='plotly_dark'
    )
    
    return fig


def render_sector_chart(df: pd.DataFrame) -> go.Figure:
    """Create sector-wise incident chart."""
    sector_counts = df['sector'].value_counts().head(10).reset_index()
    sector_counts.columns = ['sector', 'count']
    
    fig = px.bar(
        sector_counts,
        x='sector',
        y='count',
        title='🏢 Top 10 Targeted Sectors',
        color='count',
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(
        template='plotly_dark',
        xaxis_tickangle=-45,
        showlegend=False
    )
    
    return fig


def render_indonesia_map(df: pd.DataFrame) -> folium.Map:
    """Create Indonesia heatmap by province."""
    # Aggregate by province
    province_counts = df['province'].value_counts().reset_index()
    province_counts.columns = ['province', 'count']
    
    # Create base map centered on Indonesia
    m = folium.Map(
        location=[-2.5, 118],
        zoom_start=5,
        tiles='CartoDB dark_matter'
    )
    
    # Add markers for each province
    max_count = province_counts['count'].max()
    
    for _, row in province_counts.iterrows():
        province = row['province']
        count = row['count']
        
        if province in PROVINCE_COORDS:
            coords = PROVINCE_COORDS[province]
            
            # Scale radius based on count
            radius = 10 + (count / max_count) * 30
            
            # Color based on intensity
            if count > max_count * 0.7:
                color = '#dc2626'
            elif count > max_count * 0.4:
                color = '#f97316'
            elif count > max_count * 0.2:
                color = '#eab308'
            else:
                color = '#22c55e'
            
            folium.CircleMarker(
                location=coords,
                radius=radius,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                popup=f"<b>{province}</b><br>Incidents: {count:,}",
                tooltip=f"{province}: {count:,} incidents"
            ).add_to(m)
    
    return m


def render_heatmap_chart(df: pd.DataFrame) -> go.Figure:
    """Create heatmap of attacks by month and type."""
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.strftime('%Y-%m')
    
    # Create pivot table
    pivot = df.pivot_table(
        index='attack_type',
        columns='month',
        aggfunc='size',
        fill_value=0
    )
    
    # Keep only last 12 months
    pivot = pivot.iloc[:, -12:] if pivot.shape[1] > 12 else pivot
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='Reds',
        hovertemplate='%{y}<br>%{x}: %{z} incidents<extra></extra>'
    ))
    
    fig.update_layout(
        title='🔥 Attack Heatmap by Month',
        template='plotly_dark',
        xaxis_tickangle=-45
    )
    
    return fig


def render_forecast_chart(
    historical: pd.DataFrame,
    forecast: pd.DataFrame,
    confidence: pd.DataFrame = None
) -> go.Figure:
    """Create forecast visualization chart."""
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=historical['period'],
        y=historical['incident_count'],
        mode='lines+markers',
        name='Historical',
        line=dict(color='#3b82f6', width=2)
    ))
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast['period'],
        y=forecast['predicted_incidents'],
        mode='lines+markers',
        name='Forecast',
        line=dict(color='#10b981', width=2, dash='dash')
    ))
    
    # Confidence intervals
    if confidence is not None:
        fig.add_trace(go.Scatter(
            x=list(confidence['period']) + list(confidence['period'][::-1]),
            y=list(confidence['upper_bound']) + list(confidence['lower_bound'][::-1]),
            fill='toself',
            fillcolor='rgba(16, 185, 129, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='95% Confidence'
        ))
    
    fig.update_layout(
        title='🔮 6-Month Cyber Crime Forecast',
        xaxis_title='Period',
        yaxis_title='Predicted Incidents',
        template='plotly_dark',
        hovermode='x unified'
    )
    
    return fig


def render_network_graph(graph_data: Dict) -> str:
    """Generate HTML for network visualization using pyvis."""
    from pyvis.network import Network
    
    net = Network(height='500px', width='100%', bgcolor='#0e1117', font_color='white')
    
    # Add nodes
    for node in graph_data['nodes']:
        size = 20 + node.get('count', 0) / 10
        color = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][node.get('community', 0) % 5]
        net.add_node(
            node['id'],
            label=node['id'],
            size=min(size, 50),
            color=color,
            title=f"Incidents: {node.get('count', 0)}<br>Degree: {node.get('degree', 0):.3f}"
        )
    
    # Add edges
    for edge in graph_data['edges']:
        net.add_edge(
            edge['source'],
            edge['target'],
            width=edge.get('weight', 1) / 5,
            color='#4b5563'
        )
    
    net.toggle_physics(True)
    net.set_options("""
    {
        "physics": {
            "barnesHut": {
                "gravitationalConstant": -3000,
                "springLength": 200
            }
        }
    }
    """)
    
    # Generate HTML
    html = net.generate_html()
    return html


def render_data_table(df: pd.DataFrame, page_size: int = 20) -> None:
    """Render interactive data table."""
    st.dataframe(
        df,
        use_container_width=True,
        height=400
    )


def create_filter_sidebar(df: pd.DataFrame) -> Dict[str, Any]:
    """Create sidebar filters and return selections."""
    st.sidebar.header("🔍 Filters")
    
    filters = {}
    
    # Date range filter
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()
        
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        filters['date_range'] = date_range
    
    # Province filter
    if 'province' in df.columns:
        provinces = ['All'] + sorted(df['province'].unique().tolist())
        selected_provinces = st.sidebar.multiselect(
            "Provinces",
            options=provinces[1:],
            default=[]
        )
        filters['provinces'] = selected_provinces
    
    # Attack type filter
    if 'attack_type' in df.columns:
        attack_types = ['All'] + sorted(df['attack_type'].unique().tolist())
        selected_attacks = st.sidebar.multiselect(
            "Attack Types",
            options=attack_types[1:],
            default=[]
        )
        filters['attack_types'] = selected_attacks
    
    # Sector filter
    if 'sector' in df.columns:
        sectors = ['All'] + sorted(df['sector'].unique().tolist())
        selected_sectors = st.sidebar.multiselect(
            "Sectors",
            options=sectors[1:],
            default=[]
        )
        filters['sectors'] = selected_sectors
    
    # Severity filter
    if 'severity' in df.columns:
        severities = st.sidebar.multiselect(
            "Severity",
            options=['Critical', 'High', 'Medium', 'Low'],
            default=[]
        )
        filters['severities'] = severities
    
    return filters


def apply_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """Apply filters to dataframe."""
    filtered_df = df.copy()
    
    # Date filter
    if 'date_range' in filters and len(filters['date_range']) == 2:
        filtered_df['date'] = pd.to_datetime(filtered_df['date'])
        start_date, end_date = filters['date_range']
        filtered_df = filtered_df[
            (filtered_df['date'].dt.date >= start_date) &
            (filtered_df['date'].dt.date <= end_date)
        ]
    
    # Province filter
    if filters.get('provinces'):
        filtered_df = filtered_df[filtered_df['province'].isin(filters['provinces'])]
    
    # Attack type filter
    if filters.get('attack_types'):
        filtered_df = filtered_df[filtered_df['attack_type'].isin(filters['attack_types'])]
    
    # Sector filter
    if filters.get('sectors'):
        filtered_df = filtered_df[filtered_df['sector'].isin(filters['sectors'])]
    
    # Severity filter
    if filters.get('severities'):
        filtered_df = filtered_df[filtered_df['severity'].isin(filters['severities'])]
    
    return filtered_df
