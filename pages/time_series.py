import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

st.title("📈 Time Series Analysis")

st.markdown("""
<div class="info-card">
    <h3>Time Series Analysis Overview</h3>
    <p>This section enables analysis of how pollution levels have changed over time for each city and pollutant. It can be used to identify trends, seasonal patterns, and changes in data quality over time for each city.</p>
    <h4>Key features include:</h4> 
    <ul>
        <li>Interactive time series plots for each city and pollutant</li>
        <li>Comparison of current vs. 2030 EU standards</li>
        <li>Data quality indicators (High, Medium, Low, Very Low)</li>
    </ul>
</div>
""", unsafe_allow_html=True)
st.markdown("<h5 style='display: flex; justify-content: center; background-color: #0995C8; padding: 10px; border-radius: 5px; color: #000;'><strong>Use the filters below to explore trends and patterns in the data.</strong></h5>", unsafe_allow_html=True)
     
if 'clean_df' not in st.session_state:
    st.warning("Please go to the overview page to create the data.")   

else: 
    clean_df = st.session_state['clean_df']
    EU_STANDARDS = st.session_state['EU_STANDARDS']
    cities = st.session_state['cities']
    pollutants = st.session_state['pollutants']
    years = st.session_state['years']

    if clean_df.empty:
        st.warning("No data for selected filters. Please adjust your selection.")
    else:
        # Single city selector for detailed view
        city_selected = st.selectbox("Select City for Detailed View", cities)
        pollutant_selected = st.selectbox("Select Pollutant", pollutants)
        years_selection = st.slider("Select Year Range", years[0], years[-1], years)
        years_selected = list(range(years_selection[0], years_selection[-1] + 1))
        
        # Filter for selected city and pollutant
        ts_df = clean_df[
            (clean_df['city'] == city_selected) &
            (clean_df['parameter'] == pollutant_selected) & 
            (clean_df['year'] >= years_selected[0]) &
            (clean_df['year'] <= years_selected[-1])
        ]
        
        if not ts_df.empty:
            # Get EU thresholds
            thresholds = EU_STANDARDS.get(pollutant_selected, {})

            
            
            # Daily averages over time
            if pollutant_selected != "o3 µg/m³":
                st.subheader(f"Daily Averages Over Time")
                daily_avg = ts_df.groupby('day')['day_mean_value'].mean().reset_index()
                flag = ts_df.groupby('day')['flag_city_parameter'].first().reset_index()
                daily_avg = daily_avg.merge(flag, on='day', how='left')
                
                fig = px.line(
                    daily_avg,
                    x='day',
                    y='day_mean_value',
                    color='flag_city_parameter',
                    title=f"Daily Average - {pollutant_selected} in {city_selected}",
                    labels={'day_mean_value': f'Concentration ({pollutant_selected})', 
                        'day': 'Date', 'flag_city_parameter': 'Data Quality'},
                    category_orders={'flag_city_parameter': ['High', 'Medium', 'Low', 'Very Low']},
                    color_discrete_map= {'High' : '#4F990B', 'Medium': '#CCF466', 'Low' : '#F1A63B', 'Very Low' : '#F1603B'},
                )
                
                # Add EU thresholds
                if 'daily_current' in thresholds and thresholds['daily_current'] is not None:
                    fig.add_hline(
                        y=thresholds['daily_current'],
                        line_dash="dash",
                        line_color="orange",
                        annotation_text="EU Current Standard"
                    )
                
                if 'daily_2030' in thresholds and thresholds['daily_2030'] is not None:
                    fig.add_hline(
                        y=thresholds['daily_2030'],
                        line_dash="dash",
                        line_color="red",
                        annotation_text="EU 2030 Target"
                    )
                
                fig.update_layout(height=500)
                st.plotly_chart(fig, width='stretch')

                # Key Metrics Row
                st.markdown("#### Key Metrics")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    days_recorded = daily_avg['day'].nunique()
                    st.metric("Days recorded", days_recorded)
                with col2:
                    total_days = len(pd.date_range(start=f'{years_selected[0]}-01-01', end=f'{years_selected[-1]}-12-31'))
                    st.metric("Percent_days_avaiable", f"{round(days_recorded / total_days * 100, 2)}%")

                with col3:
                    if 'daily_current' in thresholds and thresholds['daily_current'] is not None:
                        days_above_current = len(daily_avg[daily_avg['day_mean_value'] > thresholds.get('daily_current', 0)]['day'].unique())
                        st.metric("Days above current threshold", f"{days_above_current} ({round(days_above_current / days_recorded * 100, 2)}%)")
                    else: 
                        st.metric("Days above current threshold", "N/A")
                with col4:
                    days_above_2030 = len(daily_avg[daily_avg['day_mean_value'] > thresholds.get('daily_2030', 0)]['day'].unique())
                    st.metric("Days above 2030 target", f"{days_above_2030} ({round(days_above_2030 / days_recorded * 100, 2)}%)")

                st.markdown("---")

            else:
                daily_avg = ts_df.groupby('day')['mda8'].mean().reset_index()
                st.subheader(f"Daily MDA8 Over Time")

                fig = px.line(
                    daily_avg,
                    x='day',
                    y='mda8',
                    title=f"MDA8 - {pollutant_selected} in {city_selected}",
                    labels={'mda8': f'Concentration ({pollutant_selected})', 
                        'day': 'Date', 'flag_city_parameter': 'Data Quality'},                    
                    color_discrete_map= {'High' : '#4F990B', 'Medium': '#CCF466', 'Low' : '#F1A63B', 'Very Low' : '#F1603B'},
                )
                
                # Add EU thresholds
                if '8h_current' in thresholds:
                    fig.add_hline(
                        y=thresholds['8h_current'],
                        line_dash="dash",
                        line_color="orange",
                        annotation_text="EU Standard"
                    )
                
            
                
                fig.update_layout(height=500)
                st.plotly_chart(fig, width='stretch')

                # Key Metrics Row
                st.markdown("#### Key Metrics")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Days recorded", len(daily_avg['day'].unique()))
                with col2:
                    st.metric("Percent_days_avaiable", f"{round(daily_avg['day'].nunique() / len(pd.date_range(start=f'{years_selected[0]}-01-01', end=f'{years_selected[-1]}-12-31')) * 100, 2)}%")

                
                with col3:
                    st.metric("Days above threshold", len(daily_avg[daily_avg['mda8'] > thresholds.get('8h_current', 0)]['day'].unique()))
               
                st.markdown("---")
                
            # Annual trends
            st.subheader(f"Annual Trends")
            if pollutant_selected != "o3 µg/m³":
                annual_avg = ts_df.groupby('year')['day_mean_value'].mean().reset_index()
                flag = ts_df.groupby('year')['flag_city_parameter'].first().reset_index()
                annual_avg = annual_avg.merge(flag, on='year', how='left')
                
                fig2 = px.bar(
                    annual_avg,
                    x='year',
                    y='day_mean_value',
                    color='flag_city_parameter',
                    title=f"Annual Average - {pollutant_selected} in {city_selected}", 
                    labels={'day_mean_value': f'Concentration ({pollutant_selected})', 'year': 'Year', 'flag_city_parameter': 'Data Quality'},
                    category_orders={'flag_city_parameter': ['High', 'Medium', 'Low', 'Very Low']},
                    color_discrete_map= {'High' : '#4F990B', 'Medium': '#CCF466', 'Low' : '#F1A63B', 'Very Low' : '#F1603B'},
                    error_y=ts_df.groupby(['city', 'year'])['day_mean_value'].std().reset_index()['day_mean_value'],
                    barmode='stack')
                
                if 'annual_current' in thresholds:
                    fig2.add_hline(
                        y=thresholds['annual_current'],
                        line_dash="dash",
                        line_color="orange",
                        annotation_text="EU Current Standard"
                    )
                
                if 'annual_2030' in thresholds:
                    fig2.add_hline(
                        y=thresholds['annual_2030'],
                        line_dash="dash",
                        line_color="red",
                        annotation_text="2030 Target"
                    )
                
                fig2.update_layout(
                    title=f"Annual Average Trend - {city_selected}",
                    xaxis_title="Year",
                    yaxis_title=f"Concentration ({pollutant_selected})",
                    height=400
                )
                st.plotly_chart(fig2, width='stretch')

                # Key Metrics Row
                st.markdown("#### Key Metrics")
                col1, col2, col3 = st.columns(3)
                    
                with col1:
                    st.metric("Years recorded", f"{len(annual_avg['year'].unique())} out of {len(years_selected)}")
                with col2:
                    st.metric("Years above current threshold", f"{len(annual_avg[annual_avg['day_mean_value'] > thresholds.get('annual_current', 0)]['year'].unique())} out of {len(annual_avg['year'].unique())}")
                with col3:
                    st.metric("Years above 2030 threshold", f"{len(annual_avg[annual_avg['day_mean_value'] > thresholds.get('annual_2030', 0)]['year'].unique())} out of {len(annual_avg['year'].unique())}")
            else:
                annual_avg = ts_df.groupby('year')['mda8'].mean().reset_index()
                
                fig2 = px.bar(
                    annual_avg,
                    x='year',
                    y='mda8',
                    title=f"Annual MDA8 Average - {pollutant_selected} in {city_selected}", 
                    labels={'mda8': f'Concentration ({pollutant_selected})', 'year': 'Year'},
                    error_y=ts_df.groupby(['city', 'year'])['mda8'].std().reset_index()['mda8']
                )

                st.plotly_chart(fig2, width='stretch')

                st.markdown("---")
            

            st.subheader(f"Seasonal Patterns")

            if pollutant_selected != "o3 µg/m³":
                seasonal = ts_df.groupby(['city', 'season'])['day_mean_value'].mean().reset_index()
            
                fig3 = px.bar(
                    seasonal,
                    x='season',
                    y='day_mean_value',
                    title=f"Seasonal Patterns - {pollutant_selected} in {city_selected}",
                    labels={'day_mean_value': 'Average (µg/m³)', 'season': 'Season'},
                    category_orders={'season': ['winter', 'spring', 'summer', 'fall']},
                    error_y=ts_df.groupby(['city', 'season'])['day_mean_value'].std().reset_index()['day_mean_value']
                )
                st.plotly_chart(fig3, width='stretch')
            else:
                seasonal = ts_df.groupby(['city', 'season'])['mda8'].mean().reset_index()
            
                fig3 = px.bar(
                    seasonal,
                    x='season',
                    y='mda8',
                    title=f"Seasonal Patterns - {pollutant_selected} in {city_selected}",
                    labels={'mda8': 'Average MDA8 (µg/m³)', 'season': 'Season'},
                    category_orders={'season': ['winter', 'spring', 'summer', 'fall']},
                    error_y=ts_df.groupby(['city', 'season'])['mda8'].std().reset_index()['mda8']
                )
                st.plotly_chart(fig3, width='stretch')
