"""
Air Quality Dashboard - Italian Cities vs EU 2030 Targets

"""

import streamlit as st

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Italian Air Quality Dashboard",
    page_icon="🌍",
    layout="wide",
    menu_items={
        'Get Help': 'https://github.com/yourusername/air-quality-dashboard',
        'Report a bug': "https://github.com/yourusername/air-quality-dashboard/issues",
        'About': """
        ## Italian Air Quality Dashboard
        
        Analyzing compliance with EU Directive 2024/2881
        
        **Data**: OpenAQ (2021-2025)  
        **Cities**: Turin, Milan, Florence, Rome, Naples, Palermo  
        **Author**: Guglielmo Sproloquio
        """
    }
)

# ============================================================================
# CUSTOM CSS FOR BETTER AESTHETICS
# ============================================================================

st.markdown("""
    <style>
    /* Main container improvements */
    .main {
        padding: 3rem 4rem;
    }
    
    /* Custom card styling */
    
    .info-card {
        background: linear-gradient(135deg, #0995C8 0%, #8FDDFA 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #07749C;
        margin: 1rem 0;
        color: #000000;
    }
    
    .warning-card {
        background: #fff3cd;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
        color: #000000;
    }
    
    .success-card {
        background: #d4edda;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
        color: #000000;
    }
    
    .metric-card, st-key-data_quality_card {
        background: linear-gradient(135deg, #0995C8 0%, #8FDDFA 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: black;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }

    
    /* Better headers */
    h1 {
        color: #1e3a8a;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    h2 {
        color: #3b82f6;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e5e7eb;
    }
    
    h3 {
        color: #6366f1;
        font-weight: 600;
        margin-top: 1.5rem;
    }
    
    /* Sidebar improvements */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Custom metric styling */
    [data-testid="stMetricValue"] {
        font-size: 1.2rem;
        font-weight: 700;
    }
    
    /* Plotly chart container */
    .plot-container {
        margin: 2rem 0;
    }
    
    /* Glossary tooltips */
    .tooltip {
        position: relative;
        display: inline-block;
        border-bottom: 1px dotted #667eea;
        cursor: help;
    }
    
    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    .badge-high {
        background: #d4edda;
        color: #155724;
    }
    
    .badge-medium {
        background: #fff3cd;
        color: #856404;
    }
    
    .badge-low {
        background: #f8d7da;
        color: #721c24;
    }
    

    
    /* Footer */
    .footer {
        padding: 2rem;
        border: solid 1px #e5e7eb;
        border-radius: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

st.html(
    """
    <style>
    div[data-testid="stExpander"] summary {
        background-color: #8FDDFA;
        color: #000000;
        padding: 0.5rem;
        border-radius: 10px;
        font-weight: 600;
    }

    div[data-testid="stExpander"] .stExpanderContent {
        background-color: #f0f0f0;
        color: #000000;
        padding: 1rem;  
        border-radius: 5px;
    }

    div[data-testid="stExpander"] details:hover summary {
        background-color: #0995C8;
        color: #000000;
    }


    </style>
    """
) 




# ============================================================================
# PAGE ROUTING
# ============================================================================

overview = st.Page("pages/overview.py", title="Overview", icon="📊", default=True)
compliance = st.Page("pages/compliance.py", title="Compliance Analysis", icon="🎯")
time_series = st.Page("pages/time_series.py", title="Time Series", icon="📈")
city_comparison = st.Page("pages/city_comparison.py", title="City Comparison", icon="🗺️")
station_deepdive = st.Page("pages/station_deepdive.py", title="Station Deep-Dive", icon="🏙️")
quality_checks = st.Page("pages/quality_checks.py", title="Data Quality", icon="🔍")
methodology = st.Page("pages/methodology.py", title="Methodology", icon="⚙️")

pg = st.navigation([
    overview, 
    compliance, 
    time_series, 
    city_comparison, 
    station_deepdive, 
    quality_checks,
    methodology
], position="top")

pg.run()

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    # Project info expander
    with st.expander("ℹ️ About This Dashboard", expanded=False):
        st.markdown("""
        **Purpose**: Evaluate Italian cities' air quality compliance with EU standards.
        
        **Data Source**: [OpenAQ](https://openaq.org/) - Real-time air quality data from government sensors
        
        **Coverage**:
        - 📍 6 Italian Cities
        - 📅 2021-2025 (5 years)
        - 🔬 4 Pollutants (NO₂, O₃, PM₁₀, PM₂.₅)
        - 📊 Millions of measurements
        
        **Regulatory Framework**:
        - Current: EU Air Quality Directive 2008/50/EC
        - Target: EU Directive 2024/2881 (2030 goals)
        """)
with col2:    
    # Glossary
    with st.expander("📖 Glossary", expanded=False):
        st.markdown("""
        **NO₂** (Nitrogen Dioxide): Traffic pollution, respiratory irritant
        
        **O₃** (Ozone): Secondary pollutant, photochemical smog
        
        **PM₁₀** (Particulate Matter <10µm): Dust, smoke particles
        
        **PM₂.₅** (Particulate Matter <2.5µm): Fine particles, most dangerous
        
        **MDA8** (Maximum Daily Average 8-hour): EPA standard for ozone - highest 8-hour rolling average in a day
        
        **Quality Flags**:
        -  High: ≥3 sensors AND ≥80% days
        - Medium: ≥2 sensors AND ≥70% days
        - Low: ≥2 sensor AND ≥60% days
        - Very Low: Below all thresholds
        """)
with col3:    
    # Methodology
    with st.expander("🔬 Methodology", expanded=False):
        st.markdown("""
        **Data Quality Controls**:
        1. Remove duplicates & negative values
        2. Exclude implausibly high readings
        3. Excluded days with <50% coverage
        4. Require ≥60% valid days per year and ≥30% mean daily coverage for using a station's data
        5. Assign quality flags based on sensor count and coverage for each city/pollutant/year
        
        **Aggregation**:
        - **Station → City**: Mean of station daily means
        - **Hourly → Daily**: Mean (or MDA8 for O₃)
        - **Daily → Annual**: Mean of daily values
        
        **Compliance Assessment**:
        - Annual means vs. EU limits
        - Daily exceedance counts vs. EU thresholds
        - Quality-weighted indicators
        
        ⚠️ **Limitations**:
        - Not official legal compliance (requires certified procedures)
        - Sensor gaps in some periods
        - City aggregates mask local variation
        """)

st.markdown("""
<div class="footer">
    <p><strong>Data Sources & Standards</strong></p>
    <p>Air Quality Data: <a href="https://openaq.org/">OpenAQ</a> | 
    EU Standards: <a href="https://eur-lex.europa.eu/eli/dir/2024/2881/oj">Directive (EU) 2024/2881</a></p>
    <p style="font-size: 0.875rem; color: #868e96; margin-top: 1rem;">
    ⚠️ <em>These are exploratory indicators for policy discussion. 
    Official compliance assessments require certified monitoring procedures.</em>
    </p>
</div>
""", unsafe_allow_html=True)


