"""
Compliance Analysis Page

Detailed comparison of pollution levels against current and 2030 EU standards,
with quality indicators and exceedance statistics.
"""

import streamlit as st
import plotly.express as px
import pandas as pd

# ============================================================================
# CHECK DATA AVAILABILITY
# ============================================================================

if 'clean_df' not in st.session_state:
    st.warning("Please go to the **Overview** page first to load data.")
    st.stop()

clean_df = st.session_state['clean_df']
EU_STANDARDS = st.session_state['EU_STANDARDS']
cities = st.session_state['cities']
pollutants = st.session_state['pollutants']
years = st.session_state['years']

# ============================================================================
# PAGE HEADER
# ============================================================================

st.title("EU Standards Compliance Analysis")

st.markdown("""
<div class="info-card" id="compliance-intro">
    <h3>What This Page Shows</h3>
    <p>This analysis compares actual pollution levels against:</p>
    <ul>
        <li><strong>Current EU Standards</strong> (Directive 2008/50/EC) - legally binding today</li>
        <li><strong>2030 EU Targets</strong> (Directive 2024/2881) - stricter limits cities must meet by 2030</li>
    </ul>
    <p><strong>Color coding</strong>: Bars are colored by data <strong>quality flags</strong> 
    ( High, Medium, Low, Very Low), showing confidence in measurements.</p>
</div>
""", unsafe_allow_html=True)



# ============================================================================
# METHODOLOGY EXPLAINER
# ============================================================================

with st.expander("**How Compliance Is Assessed**", expanded=False):
    st.markdown("""
    #### Annual Average Compliance
    
    **Method**: 
                
        1. Calculate daily mean for each city (median across stations)
        2. Compute annual mean of daily values
        3. Compare against EU annual limits
    
    **EU Requirements**:
                
        - NO₂: Annual mean ≤ 40 µg/m³ (current) | ≤ 20 µg/m³ (2030)
        - PM₁₀: Annual mean ≤ 40 µg/m³ (current) | ≤ 20 µg/m³ (2030)
        - PM₂.₅: Annual mean ≤ 25 µg/m³ (current) | ≤ 10 µg/m³ (2030)
        - O₃: See MDA8 below
    
    ---
    
    #### Daily Exceedance Compliance
    
    **Method**: Count days where daily mean exceeds limit
    
    **EU Requirements**:
    
        - NO₂: Daily mean ≤ 25 µg/m³ (2030), max 18 exceedances/year
        - PM₁₀: Daily mean ≤ 50 µg/m³ (current) | ≤ 45 µg/m³ (2030), max 35 exceedances/year
        - PM₂.₅: Daily mean ≤ 25 µg/m³ (2030), max 18 exceedances/year
    
    ---
    
    #### O₃ MDA8 (Maximum Daily Average 8-hour)
    
    **Method** (EPA-compliant):
                
        1. Calculate rolling 8-hour average for each hour (requires ≥6/8 hours valid)
        2. Take maximum 8-hour average per day (MDA8)
        3. MDA8 valid only if ≥75% of hours available
        4. Count days where MDA8 > 120 µg/m³
    
        **EU Requirement**: Max 25 exceedances/year (3-year average)
    
        **Why MDA8?** Ozone peaks during day, so 8-hour rolling captures sustained exposure better than daily mean.
    
    ---
    
    #### Quality Flags
    
    Compliance percentages are shown alongside **quality indicators**:
                
        - High: ≥3 median active sensors per day AND ≥80% days avaiable per year 
        - Medium: ≥2 median active sensors per day AND ≥70% days avaiable per year 
        - Low: ≥2 median active sensors per day AND ≥60% days avaiable per year 
        - Very Low: Below all thresholds
    
    **Important**: Low-quality data doesn't mean pollution is low/high, just that we have fewer measurements.
    """)


# ============================================================================
# POLLUTANT-BY-POLLUTANT ANALYSIS
# ============================================================================

st.markdown("""
            <div id='pollutants-card'> 
                <h5>Compliance analysis is presented pollutant by pollutant. Use the tabs to switch between them.</h5>   
            </div>""", 
            unsafe_allow_html=True)
cols = st.columns(len(pollutants))
for i, pollutant in enumerate(pollutants):
    with cols[i]:
        st.markdown(f" <button class='pollutant-button' style='margin: 5px; padding: 10px 20px; border-radius: 8px; background-color: #8FDDFA; color: black; border: none; cursor: pointer;'> <a href='#{pollutant}' style='text-decoration: none; color: black;'>{pollutant}</a></button>", 
                    unsafe_allow_html=True, width='stretch')

st.space("medium")

if clean_df.empty:
    st.warning("No data available for analysis.")
    st.stop()

for pollutant in pollutants:
    
    st.markdown(f"<div id='{pollutant}'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.header(f"{(pollutant).split()[0].upper()} Compliance Analysis")
    
    # Filter data
    poll_df = clean_df[clean_df['parameter'] == pollutant]
    
    # Get thresholds
    thresholds = EU_STANDARDS.get(pollutant, {})
    
    # ========================================================================
    # SECTION 1: ANNUAL AVERAGES
    # ========================================================================
    
    st.subheader("Annual Averages with Quality Indicators")
    st.info("**Reading this chart:** Bars represent annual averages values. If bar are higher than the dashed lines it means they are over the EU current tHreshold or 2030 target value. The color of the bar represent the data quality for the given year")
    
    # Calculate annual averages with quality flags
    annual = poll_df.groupby(['city', 'year'])['day_mean_value'].mean().reset_index()
    flag = poll_df.groupby(['year', 'city'])['flag_city_parameter'].first().reset_index()
    annual = annual.merge(flag, on=['year', 'city'], how='left')
    
    # Create faceted bar chart
    fig = px.bar(
        annual,
        x='year',
        y='day_mean_value',
        color='flag_city_parameter',
        barmode='stack',
        facet_col='city',
        facet_col_wrap=3,
        facet_row_spacing=0.15,
        category_orders={'flag_city_parameter': ['High', 'Medium', 'Low', 'Very Low']},
        title="Annual Averages by City",
        labels={'day_mean_value': 'Concentration (µg/m³)', 'year': 'Year', 
                'flag_city_parameter': 'Data Quality'},
        color_discrete_map= {'High' : '#4F990B', 'Medium': '#CCF466', 'Low' : '#F1A63B', 'Very Low' : '#F1603B'},
        height=600
    )
    
    # Simplify facet titles
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    
    # Add threshold lines
    if 'annual_2030' in thresholds:
        fig.add_hline(
            y=thresholds['annual_2030'],
            line_dash="dash",
            line_color="red",
            annotation_text="2030 Target",
            annotation_position="top left"
        )
    
    if 'annual_current' in thresholds:
        fig.add_hline(
            y=thresholds['annual_current'],
            line_dash="dash",
            line_color="orange",
            annotation_text="Current Standard",
            annotation_position="bottom left"
        )
    
    fig.update_layout(
        legend=dict(
            title="Data Quality",
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig, width='stretch')
    
    # Quality summary metrics
    st.space("medium")
    
    st.markdown("#### Data Quality Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        high_pct = round(len(annual[annual['flag_city_parameter'] == 'High']) / len(annual) * 100, 1)
        st.metric("High Quality", f"{high_pct}%", 
                 help="Years with ≥3 median active sensors per day AND ≥80% days avaiable per year")
    with col2:
        medium_pct = round(len(annual[annual['flag_city_parameter'] == 'Medium']) / len(annual) * 100, 1)
        st.metric("Medium Quality", f"{medium_pct}%",
                 help="Years with ≥2 median active sensors per day AND ≥70% days avaiable per year")
    with col3:
        low_pct = round(len(annual[annual['flag_city_parameter'] == 'Low']) / len(annual) * 100, 1)
        st.metric("Low Quality", f"{low_pct}%",
                 help="Years with ≥2 median active sensors per day AND ≥60% days avaiable per year")
    with col4:
        vlow_pct = round(len(annual[annual['flag_city_parameter'] == 'Very Low']) / len(annual) * 100, 1)
        st.metric("Very Low Quality", f"{vlow_pct}%",
                 help="Years with <2 median active sensors per day OR <60% days avaiable per year")
    
    # Compliance summary
    st.space("medium")
    st.markdown("#### Compliance Summary for Annual Averages")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'annual_current' in thresholds and thresholds['annual_current'] is not None:
            above_current = len(annual[annual['day_mean_value'] > thresholds['annual_current']])
            above_current_pct = round(above_current / len(annual) * 100, 1)
            
            delta_color = "inverse" if above_current_pct > 0 else "normal"
            st.metric(
                "Years Above Current Standard", 
                f"{above_current_pct}%",
                delta=f"{above_current} of {len(annual)} city-years",
                delta_color=delta_color,
                help=f"Exceeds {thresholds['annual_current']} µg/m³"
            )
        else:
            st.metric("Current Standard", "Not Defined")
    
    with col2:
        if 'annual_2030' in thresholds and thresholds['annual_2030'] is not None:
            above_2030 = len(annual[annual['day_mean_value'] > thresholds['annual_2030']])
            above_2030_pct = round(above_2030 / len(annual) * 100, 1)
            
            delta_color = "inverse" if above_2030_pct > 0 else "normal"
            st.metric(
                "Years Above 2030 Target", 
                f"{above_2030_pct}%",
                delta=f"{above_2030} of {len(annual)} city-years",
                delta_color=delta_color,
                help=f"Exceeds {thresholds['annual_2030']} µg/m³"
            )
        else:
            st.metric("2030 Target", "Not Defined")

    if not annual.empty and 'annual_current' in thresholds and thresholds['annual_current'] is not None and 'annual_2030' in thresholds and thresholds['annual_2030'] is not None:
        with st.expander("City-by-City Compliance Details", expanded=False):
            for city in cities:
                city_years = annual[annual['city'] == city]
                if not city_years.empty:
                    with st.expander(f"### {city}", expanded=False):
                        compliant_current = len(city_years[city_years['day_mean_value'] <= thresholds.get('annual_current', float('inf'))])
                        compliant_2030 = len(city_years[city_years['day_mean_value'] <= thresholds.get('annual_2030', float('inf'))])
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("**Years compliant with current standard**", f"{compliant_current}/{len(city_years)}", help=f"Years where {city} met current annual standard of {thresholds.get('annual_current', 'N/A')} µg/m³")
                        with col2:
                            st.metric("**Years compliant with 2030 target**", f"{compliant_2030}/{len(city_years)}", help=f"Years where {city} met 2030 annual target of {thresholds.get('annual_2030', 'N/A')} µg/m³")
            
    # ========================================================================
    # SECTION 2: DAILY EXCEEDANCES (for NO2, PM10, PM2.5)
    # ========================================================================
    
    if pollutant != 'o3 µg/m³':
        st.space("medium")
        st.subheader("Daily Concentration Time Series")
        
        st.info("""
        **Reading This Chart**: Each line shows daily mean concentrations for a city over time. 
        Spikes above thresholds indicate exceedance days. Color indicates data quality for that year.
        """)
        
        # Prepare daily data
        daily_avg = poll_df.groupby(['year', 'day', 'city'])['day_mean_value'].mean().reset_index()
        flag_daily = poll_df.groupby(['year', 'city'])['flag_city_parameter'].first().reset_index()
        daily_avg = daily_avg.merge(flag_daily, on=['year', 'city'], how='left')
        
        # Create faceted line chart
        fig2 = px.line(
            daily_avg,
            x='day',
            y='day_mean_value',
            color='flag_city_parameter',
            facet_col='city',
            facet_col_wrap=3,
            facet_row_spacing=0.15,
            title=f"{pollutant} Daily Time Series by City",
            labels={'day_mean_value': f'Daily Mean (µg/m³)', 'day': 'Date',
                   'flag_city_parameter': 'Quality'},
            category_orders={'flag_city_parameter': ['High', 'Medium', 'Low', 'Very Low']},
            color_discrete_map= {'High' : '#4F990B', 'Medium': '#CCF466', 'Low' : '#F1A63B', 'Very Low' : '#F1603B'},
            height=700
        )
        
        fig2.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        
        # Add daily thresholds
        if 'daily_current' in thresholds and thresholds['daily_current'] is not None:
            fig2.add_hline(
                y=thresholds['daily_current'],
                line_dash="dash",
                line_color="orange",
                annotation_text="Current",
                annotation_position="top left"
            )
        
        if 'daily_2030' in thresholds and thresholds['daily_2030'] is not None:
            fig2.add_hline(
                y=thresholds['daily_2030'],
                line_dash="dash",
                line_color="red",
                annotation_text="2030",
                annotation_position="top left"
            )
        
        fig2.update_layout(
            hovermode='x unified',
            legend=dict(title="Quality", orientation="h", y=-0.2, xanchor="center", x=0.5)
        )
        
        st.plotly_chart(fig2, width='stretch')
        
        # Exceedance summary
        st.space("medium")
        st.markdown("#### Daily Exceedance Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'daily_current' in thresholds and thresholds['daily_current'] is not None:
                days_above_current = len(daily_avg[daily_avg['day_mean_value'] > thresholds['daily_current']])
                days_pct_current = round(days_above_current / len(daily_avg) * 100, 2)
                
                st.metric(
                    "Days Above Current Standard",
                    f"{days_pct_current}%",
                    delta=f"{days_above_current} of {len(daily_avg)} city-days",
                    delta_color="inverse",
                    help=f"Daily mean > {thresholds['daily_current']} µg/m³"
                )
            else:
                st.metric("Current Daily Standard", "Not Defined")
        
        with col2:
            if 'daily_2030' in thresholds and thresholds['daily_2030'] is not None:
                days_above_2030 = len(daily_avg[daily_avg['day_mean_value'] > thresholds['daily_2030']])
                days_pct_2030 = round(days_above_2030 / len(daily_avg) * 100, 2)
                
                st.metric(
                    "Days Above 2030 Target",
                    f"{days_pct_2030}%",
                    delta=f"{days_above_2030} of {len(daily_avg)} city-days",
                    delta_color="inverse",
                    help=f"Daily mean > {thresholds['daily_2030']} µg/m³"
                )
            else:
                st.metric("2030 Daily Target", "Not Defined")
    
    if not daily_avg.empty and 'daily_2030' in thresholds and thresholds['daily_2030'] is not None:
        with st.expander("City-by-City Compliance Details", expanded=False):
            st.warning("""Exceedance days are highly influenced by the number of valid measurements. Low-quality years may heavily undercount exceedances.""")
            for city in cities:
                city_years = daily_avg[daily_avg['city'] == city]
                if not city_years.empty:
                    with st.expander(f"### {city}", expanded=False):
                        compliant_current = len(city_years[city_years['day_mean_value'] > thresholds.get('daily_current', float('inf'))])
                        compliant_2030 = len(city_years[city_years['day_mean_value'] > thresholds.get('daily_2030', float('inf'))])
                        exceedances_current = city_years.groupby('year')['day_mean_value'].apply(lambda x: (x > thresholds.get('daily_current', float('inf'))).sum()).reset_index(name='exceedances_current')
                        exceedances_2030 = city_years.groupby('year')['day_mean_value'].apply(lambda x: (x > thresholds.get('daily_2030', float('inf'))).sum()).reset_index(name='exceedances_2030')

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            if 'daily_current' in thresholds and thresholds['daily_current'] is not None:
                                st.metric("**Days above current standard**", f"{compliant_current} (/{len(city_years)})", help=f"Days where {city} met current daily standard of {thresholds.get('daily_current', 'N/A')} µg/m³")
                            else:
                                st.metric("Current Daily Standard", "Not Defined")
                        with col2:
                            if 'daily_current' in thresholds and thresholds['daily_current'] is not None:
                                 st.metric("**Compliance with current exceedance limit**", f"{len(exceedances_current[exceedances_current['exceedances_current'] <= 35])} of {len(exceedances_current)}", help=f"EU currenlty allows max 35 exceedances/year for daily standard")
                            else:
                                st.metric("Compliance with current exceedance limit", "Not Defined")
                        with col3:
                            st.metric("**Days above 2030 target**", f"{compliant_2030} (/{len(city_years)})", help=f"Days where {city} met 2030 daily target of {thresholds.get('daily_2030', 'N/A')} µg/m³")
                        with col4:
                            st.metric("**Compliance with exceedance limit**", f"{len(exceedances_2030[exceedances_2030['exceedances_2030'] <= 18])} of {len(exceedances_2030)} years", help=f"EU requires max 18 exceedances/year for 2030 daily target")
            
    
    # ========================================================================
    # SECTION 3: O3 MDA8 (special handling)
    # ========================================================================
    
    else:  # O3
        st.space("medium")
        st.subheader("MDA8 (Maximum Daily Average 8-hour) Time Series")
        
        st.info("""
        **What is MDA8?** The highest 8-hour rolling average in each day. 
        This metric better captures sustained ozone exposure than simple daily means.
        
        **EU Standard**: MDA8 should not exceed 120 µg/m³ more than 25 days per year (3-year average).
        """)
        
        # Prepare MDA8 data
        mda8_data = poll_df.groupby(['year', 'day', 'city'])['mda8'].mean().reset_index()
        flag_mda8 = poll_df.groupby(['year', 'city'])['flag_city_parameter'].first().reset_index()
        mda8_data = mda8_data.merge(flag_mda8, on=['year', 'city'], how='left')
        
        # Create faceted line chart
        fig3 = px.line(
            mda8_data,
            x='day',
            y='mda8',
            color='flag_city_parameter',
            facet_col='city',
            facet_col_wrap=3,
            facet_row_spacing=0.15,
            title=f"{pollutant} MDA8 Daily Values by City",
            labels={'mda8': 'MDA8 (µg/m³)', 'day': 'Date', 'flag_city_parameter': 'Data Quality'},
            category_orders={'flag_city_parameter': ['High', 'Medium', 'Low', 'Very Low']},
            color_discrete_map= {'High' : '#4F990B', 'Medium': '#CCF466', 'Low' : '#F1A63B', 'Very Low' : '#F1603B'},
            height=700
        )
        
        fig3.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        
        # Add MDA8 threshold
        fig3.add_hline(
            y=thresholds['8h_current'],
            line_dash="dash",
            line_color="orange",
            annotation_text="EU Standard (120 µg/m³)",
            annotation_position="top left"
        )
        
        fig3.update_layout(
            hovermode='x unified',
            legend=dict(title="Quality", orientation="h", y=-0.2, xanchor="center", x=0.5)
        )
        
        st.plotly_chart(fig3, width='stretch')
        
        # Exceedance summary
        st.space("medium")
        st.markdown("#### MDA8 Exceedance Summary")
        
        days_above = len(mda8_data[mda8_data['mda8'] > thresholds['8h_current']])
        days_pct = round(days_above / len(mda8_data) * 100, 2)
        
        st.metric(
            "Days Above 120 µg/m³",
            f"{days_pct}%",
            delta=f"{days_above} of {len(mda8_data)} city-days",
            delta_color="inverse",
            help="MDA8 exceeds EU threshold. Should be <25 days/year (3-yr avg)"
        )

        if not mda8_data.empty and '8h_2030' in thresholds and thresholds['8h_2030'] is not None:
            with st.expander("City-by-City Compliance Details", expanded=False):
                st.warning("""Exceedance days are highly influenced by the number of valid measurements. Low-quality years may heavily undercount exceedances.""")
                st.warning("Exceedance days should ideally be calculated as a 3-year rolling average, but this simplified analysis counts exceedances per year for illustrative purposes.")
                
                for city in cities:
                    city_years = mda8_data[mda8_data['city'] == city]
                    if not city_years.empty:
                        with st.expander(f"### {city}", expanded=False):
                            compliant_current = len(city_years[city_years['mda8'] > thresholds.get('8h_current', float('inf'))])
                            compliant_2030 = len(city_years[city_years['mda8'] > thresholds.get('8h_2030', float('inf'))])
                            exceedances_current = city_years.groupby('year')['mda8'].apply(lambda x: (x > thresholds.get('8h_current', float('inf'))).sum()).reset_index(name='exceedances_current')
                            exceedances_2030 = city_years.groupby('year')['mda8'].apply(lambda x: (x > thresholds.get('8h_2030', float('inf'))).sum()).reset_index(name='exceedances_2030')

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("**Days above standard**", f"{compliant_current} (/{len(city_years)})", help=f"Days where {city} met EU standard of {thresholds.get('8h_current', 'N/A')} µg/m³")
                            with col2:
                                st.metric("**Compliance with cuurent exceedance limit**", f"{len(exceedances_current[exceedances_current['exceedances_current'] <= 25])} of {len(exceedances_current)} years", help=f"EU requires max 25 exceedances/year for current daily target")
                            with col3:
                                st.metric("**Compliance with 2030 exceedance limit**", f"{len(exceedances_2030[exceedances_2030['exceedances_2030'] <= 18])} of {len(exceedances_2030)} years", help=f"EU requires max 18 exceedances/year for 2030 daily target")
                

st.markdown(f"<button style='position: fixed; bottom: 20px; right: 20px; padding: 10px 15px; background-color: #8FDDFA; color: black; border: solid 1px #ccc; border-radius: 10px; cursor: pointer; z-index: 1000;'> <a href='#compliance-intro' class='back-to-top' style='text-decoration: none; color: black;'>Back to top</a></button>", unsafe_allow_html=True)    
     

# ============================================================================
# OVERALL SUMMARY
# ============================================================================

st.space("medium")
st.subheader("Overall Compliance Summary")

st.markdown("""
<div class="info-card">
    <h4>Key Takeaways</h4>
    <ul>
        <li><strong>NO₂</strong>: Most cities meet current standards and annual averages are consistently decreasing; 2030 target achievable if current trends continue and more mitigation measures are implemented to reduce daily exceedances</li>
        <li><strong>PM₁₀</strong>: Generally compliant with current; 2030 requires more stringent policies, especially for daily exceedances</li>
        <li><strong>PM₂.₅</strong>: <strong>Biggest challenge</strong> - Most cities are far from 2030 target both for annual and daily exceedances</li>
        <li><strong>O₃</strong>: Generally compliant with current standard but not yet meeting 2030 target in some cities</li>
    </ul>
    
    > Data Quality Note: Few measurements have high quality flags (i.e., are flagged as 'High'). This may affect the reliability of results.
</div>
""", 
unsafe_allow_html=True)