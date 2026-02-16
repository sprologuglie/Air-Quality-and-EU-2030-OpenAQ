"""
Overview Page - Dashboard Entry Point

Shows key metrics, summary statistics, and project context.
"""

import streamlit as st
import pandas as pd
import yaml
import plotly.express as px

# ============================================================================
# LOAD DATA
# ============================================================================

# Load config
with open("config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# EU Standards
st.session_state.EU_STANDARDS = {
    "no2 µg/m³": {
        "annual_current": 40,
        "annual_2030": 20,
        "daily_current": None,
        "daily_2030": 25
    },
    "o3 µg/m³": {
        "8h_current": 120,
        "8h_2030": 120
    },
    "pm10 µg/m³": {
        "annual_current": 40,
        "annual_2030": 20,
        "daily_current": 50,
        "daily_2030": 45
    },
    "pm25 µg/m³": {
        "annual_current": 25,
        "annual_2030": 10,
        "daily_current": None,
        "daily_2030": 25
    }
}

@st.cache_data
def load_data():
    """Load processed data and quality checks."""
    try:
        clean = pd.read_parquet("data/clean.parquet")
        quality_city = pd.read_csv("results/quality_checks/cities_quality.csv")
        
        try:
            compliance = pd.read_csv("results/compliance_table.csv")
        except FileNotFoundError:
            compliance = pd.DataFrame()
        
        return clean, quality_city, compliance
    except FileNotFoundError as e:
        st.error(f"Data files not found: {e}")
        st.stop()

# Load data
st.session_state.clean_df, st.session_state.quality_df, st.session_state.compliance_df = load_data()

clean_df = st.session_state.clean_df
compliance_df = st.session_state.compliance_df

st.session_state.cities = sorted(clean_df['city'].unique())
st.session_state.pollutants = sorted(clean_df['parameter'].unique())
st.session_state.years = int(clean_df['year'].min()), int(clean_df['year'].max())

# ============================================================================
# PAGE CONTENT
# ============================================================================

# Hero section
st.title("Italian Cities Air Quality Dashboard")

st.markdown("""
<div class="info-card">
    <h3>Project Goal</h3>
    <p>This dashboard evaluates whether 6 major Italian cities are on track to meet 
    <strong>EU 2030 air quality targets</strong> (Directive 2024/2881), using real-time 
    sensor data from 2021-2025.<br> Air pollution causes ~300,000 premature deaths 
    annually in the EU and has to be taken seriously. The new 2030 standards are 50% stricter than current limits, 
    requiring significant policy action, which would benefit from public information and data driven discussions.</p>
</div>
""", unsafe_allow_html=True)

st.space("medium")  # Spacing

# ============================================================================
# KEY METRICS (Enhanced with cards)
# ============================================================================

st.subheader("Data Coverage")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-card" style="height: 200px;">
        <div style="font-size: 0.875rem; opacity: 0.9;">Cities Analyzed</div>
        <div style="font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0;">6</div>
        <div style="font-size: 0.75rem; opacity: 0.8;">Turin, Milan, Florence, Rome, Naples, Palermo</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card" style="height: 200px;">
        <div style="font-size: 0.875rem; opacity: 0.9;">Pollutants Tracked</div>
        <div style="font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0;">{len(clean_df['parameter'].unique())}</div>
        <div style="font-size: 0.75rem; opacity: 0.8;">NO₂, O₃, PM₁₀, PM₂.₅</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card" style="height: 200px;">
        <div style="font-size: 0.875rem; opacity: 0.9;">Time Period</div>
        <div style="font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0;">5</div>
        <div style="font-size: 0.75rem; opacity: 0.8;">{clean_df['year'].min()}-{clean_df['year'].max()} (years)</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    total_measurements = len(clean_df)
    st.markdown(f"""
    <div class="metric-card" style="height: 200px;">
        <div style="font-size: 0.875rem; opacity: 0.9;">Measurements</div>
        <div style="font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0;">{total_measurements/1e6:.1f}M</div>
        <div style="font-size: 0.75rem; opacity: 0.8;">Hourly sensor readings</div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# CONTEXT: WHY THESE POLLUTANTS?
# ============================================================================

with st.expander("**Understanding the Four Pollutants**", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **NO₂ (Nitrogen Dioxide)**
        - **Source**: Vehicle exhaust, power plants
        - **Health Impact**: Respiratory inflammation, aggravates asthma
        - **Urban Pattern**: Highest near traffic corridors
        - **EU 2030 Target**: 50% reduction (40→20 µg/m³)
        
        **PM₁₀ (Particulate Matter <10µm)**
        - **Source**: Construction, road dust, combustion
        - **Health Impact**: Lung irritation, cardiovascular stress
        - **Urban Pattern**: Higher in industrial/construction areas
        - **EU 2030 Target**: 50% reduction (40→20 µg/m³)
        """)
    
    with col2:
        st.markdown("""
        **O₃ (Ozone)**
        - **Source**: Photochemical reaction (NO₂ + sunlight)
        - **Health Impact**: Lung damage, reduced lung function
        - **Urban Pattern**: Higher in summer, suburban areas
        - **EU 2030 Target**: Unchanged (120 µg/m³ MDA8)
        
        **PM₂.₅ (Fine Particulate <2.5µm)**
        - **Source**: Vehicle emissions, industrial processes
        - **Health Impact**: **Most dangerous** - enters bloodstream
        - **Urban Pattern**: Pervasive, especially in winter
        - **EU 2030 Target**: 60% reduction (25→10 µg/m³)
        """)


# ============================================================================
# COMPLIANCE OVERVIEW
# ============================================================================

st.space("medium")
st.subheader("Complete Compliance Analysis")

if not compliance_df.empty:
    st.info(""" **What This Table Shows**:
                
    > For each city and pollutant, it indicates whether the current standard and the 2030 target are met or not, along with the percentage of years/days in compliance.
        
    **How to Use It**:
               
    > Always account for quality flags to understand the reliability of the results. Critical and problematic compliance identify which cities/pollutants need attention.
        The table can be sorted and filtered by any column to quickly identify trends and outliers.
                
    """)
    st.dataframe(compliance_df, width='stretch')
else:
    st.warning("""
    **Compliance data not yet generated.**
    
    This table will show which cities meet/fail 2030 targets.
    
    Generate by running:
    ```bash
    python -m project.results
    ```
    """)

# ============================================================================
# VISUAL: TREND OVERVIEW
# ============================================================================

st.space("medium")
st.subheader("5-Year Trends: Are We Improving?")

st.info("""
**What to Look For**: Downward trends suggest cities are improving. 
Flat or upward trends  mean current policies aren't enough for 2030 targets.
""")

# Calculate annual averages for all cities and pollutants
annual_trends = clean_df.groupby(['year', 'parameter', 'city'])['day_mean_value'].mean().reset_index()

# Create faceted plot
fig = px.line(
    annual_trends,
    x='year',
    y='day_mean_value',
    color='city',
    facet_col='parameter',
    facet_col_wrap=2,
    title="5-Year Pollution Trends by Pollutant",
    labels={'day_mean_value': 'Annual Average (µg/m³)', 'year': 'Year'},
    height=600
)

# Simplify facet titles
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
)

st.plotly_chart(fig, width='stretch')

# ============================================================================
# KEY INSIGHTS
# ============================================================================

st.space("medium")
st.subheader("Key Insights")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="success-card">
        <h4>Positive Trends</h4>
        <ul>
            <li>NO₂ levels declining in most cities (traffic policies working)</li>
            <li>Some cities already meet 2030 PM₁₀ targets</li>
            <li>O₃ levels stable (meeting current standards)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="warning-card">
        <h4>Areas of Concern</h4>
        <ul>
            <li>PM₂.₅ remains high in northern cities (winter heating)</li>
            <li>Most cities still far from 2030 PM₂.₅ target (10 µg/m³)</li>
            <li>Quality gaps in some years reduce confidence</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# NAVIGATION GUIDE
# ============================================================================

st.space("medium")
st.subheader("Navigate the Dashboard")

st.markdown("""
Use the **page selector in the sidebar** to explore:

- **🎯 Compliance Analysis**: Detailed comparison against EU standards with quality flags
- **📈 Time Series**: Daily and annual trends for individual cities
- **🗺️ City Comparison**: Side-by-side analysis across cities
- **🏙️ Station Deep-Dive**: Within-city variation across monitoring stations
- **🔍 Data Quality**: Sensor coverage, flags and aggregations details
- **⚙️ Methodology**: Complete methodological explanation          

**Tip**: Start with **Compliance Analysis** to see which cities/pollutants need attention, 
then use **Time Series** or **City Comparison** to understand specific temporal patterns. 
**Station Deep-Dive** reveals local hotspots masked by city averages and help analyse each city in more detail.
Visiting **Data Quality** and **Methodology** ensures you interpret results with the right confidence level. 
""")

# ============================================================================
# Author and citaitons
# ============================================================================

 
with st.expander("**Author and citations**", expanded=False):
    st.code("""
@misc{sproloquio2025airquality,
  author = {Sproloquio, Guglielmo},
  title = {Italian Cities Air Quality Dashboard: EU 2030 Compliance Analysis},
  year = {2026},
  url = {https://github.com/sprologuglie/Air-Quality-and-EU-2030-OpenAQ},
  note = {Data from OpenAQ; Standards from EU Directive 2024/2881}
}
    """, language="bibtex")
    
    st.markdown("""
    **Data Attribution**:
    - Air Quality Data: [OpenAQ](https://openaq.org/) (CC BY 4.0)
    - EU Standards: [Directive (EU) 2024/2881](https://eur-lex.europa.eu/eli/dir/2024/2881/oj)
    - Analysis Code: [GitHub Repository](https://github.com/sprologuglie/Air-Quality-and-EU-2030-OpenAQ)
    """)