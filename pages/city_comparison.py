import streamlit as st
import plotly.express as px

if 'clean_df' not in st.session_state:
    st.warning("Please go to the overview page to create the data.")   

else: 
    clean_df = st.session_state['clean_df']
    EU_STANDARDS = st.session_state['EU_STANDARDS']
    cities = st.session_state['cities']
    pollutants = st.session_state['pollutants']
    years = st.session_state['years']

    
    st.title("🗺️ City-to-City Comparison")

    
    st.markdown("""
    <div class="info-card">
        <h3>City-to-City Comparison Overview</h3>
        <p>This section enables comparison of pollution levels across multiple cities for a selected pollutant over time. It can be used to identify differences in trends and patterns between cities.</p>
        <h4>Key features include:</h4> 
        <ul>
            <li>Interactive box plots showing distribution of daily averages across cities</li>
            <li>Line charts of daily averages over time with EU standards overlaid</li>
            <li>Bar charts of annual averages by city and year</li>
            <li>Seasonal pattern analysis by city</li>
            <li>Ability to filter by year range for focused analysis</li>
            <li>Comparison of current vs. 2030 EU standards</li>
            <li>Data quality indicators (High, Medium, Low, Very Low)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<h5 style='display: flex; justify-content: center; background-color: #0995C8; padding: 10px; border-radius: 5px; color: #000;'><strong>Use the filters below to explore trends and patterns in the data.</strong></h5>", unsafe_allow_html=True)
  
    

        
    city_selected = st.multiselect("Select Cities for Detailed View", cities)
    pollutant = st.selectbox("Select Pollutant for Comparison", pollutants)
    years_selection = st.slider("Select Year Range", years[0], years[-1], years)
    years_selected = list(range(years_selection[0], years_selection[1] + 1))
    
    comp_df = clean_df[
        (clean_df['city'].isin(city_selected)) &
        (clean_df['parameter'] == pollutant) &
        (clean_df['year'].isin(years_selected))
    ]
    
    if pollutant != 'o3 µg/m³':
    
        # Box plots by city
        st.subheader("Distribution of Daily Averages")
        
        fig = px.box(
            comp_df,
            x='city',
            y='day_mean_value',
            color='city',
            title=f"{pollutant} Distribution Across Cities",
            labels={'day_mean_value': 'Daily Average (µg/m³)'}
        )
        
        st.plotly_chart(fig, width='stretch')

        thresholds = EU_STANDARDS.get(pollutant, {})
            
        # Daily averages over time
        st.subheader("Daily Averages Over Time")

        daily_avg = comp_df.groupby(['city','day'])['day_mean_value'].mean().reset_index()
            
        fig1 = px.line(
            daily_avg,
            x='day',
            y='day_mean_value',
            color='city',
            title=f"{pollutant} Daily Average - {', '.join(city_selected)}",
            labels={'day_mean_value': f'Concentration ({pollutant})', 
                        'day': 'Date'}
            )
            
            # Add EU thresholds
        if 'daily_current' in thresholds and thresholds['daily_current'] is not None:
                fig1.add_hline(
                    y=thresholds['daily_current'],
                    line_dash="dash",
                    line_color="orange",
                    annotation_text="EU Current Standard"
                )
            
        if 'daily_2030' in thresholds and thresholds['daily_2030'] is not None:
                fig1.add_hline(
                    y=thresholds['daily_2030'],
                    line_dash="dash",
                    line_color="red",
                    annotation_text="EU 2030 Target"
                )
            
        fig1.update_layout(height=500)
        st.plotly_chart(fig1, width='stretch')
            
            # Annual trends
        st.subheader("Annual Trends")
        annual_avg = comp_df.groupby(['city', 'year'])['day_mean_value'].mean().reset_index()
            
        
        fig2 = px.histogram(
            annual_avg,
            x='city',
            y='day_mean_value',
            color='year',
            barmode='group',
            title=f"{pollutant} Annual Average - {', '.join(city_selected)}",
            labels={'day_mean_value': f'Concentration ({pollutant})', 'year': 'Year'},
            category_orders={'year': sorted(years_selected)}
            )
            
            # Add EU thresholds
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
                annotation_text="EU 2030 Target"
            )
            
        st.plotly_chart(fig2, width='stretch')
        
        # Seasonal patterns
        st.subheader("Seasonal Patterns")
        
        seasonal = comp_df.groupby(['city', 'season'])['day_mean_value'].mean().reset_index()
        
        fig4 = px.bar(
            seasonal,
            x='city',
            y='day_mean_value',
            color='season',
            barmode='group',
            title=f"{pollutant} by Season",
            labels={'day_mean_value': 'Average (µg/m³)'},
            category_orders={'season': ['winter', 'spring', 'summer', 'fall']}
        )
        
        st.plotly_chart(fig4, width='stretch')
        
    else:
        # Box plots by city
        st.subheader("Distribution of Daily Averages")
        
        fig = px.box(
            comp_df,
            x='city',
            y='mda8',
            color='city',
            title=f"{pollutant} Distribution Across Cities",
            labels={'mda8': 'MDA8 (µg/m³)'}
        )
        
        st.plotly_chart(fig, width='stretch')

        thresholds = EU_STANDARDS.get(pollutant, {})
            
        # Daily averages over time
        st.subheader("Daily MDA8 Over Time")

        daily_avg = comp_df.groupby(['city','day'])['mda8'].mean().reset_index()
            
        fig1 = px.line(
            daily_avg,
            x='day',
            y='mda8',
            color='city',
            title=f"MDA8 - {pollutant} in {', '.join(city_selected)}",
            labels={'mda8': f'Concentration ({pollutant})', 
                        'day': 'Date'}
            )
            
            # Add EU thresholds
        if '8h_current' in thresholds and thresholds['8h_current'] is not None:
                fig1.add_hline(
                    y=thresholds['8h_current'],
                    line_dash="dash",
                    line_color="orange",
                    annotation_text="EU Standard"
                )
        
            
        fig1.update_layout(height=500)
        st.plotly_chart(fig1, width='stretch')
            
            # Annual trends
        st.subheader("Annual Trend")
        annual_avg = comp_df.groupby(['city', 'year'])['mda8'].mean().reset_index()
            
        
        fig2 = px.histogram(
            annual_avg,
            x='city',
            y='mda8',
            color='year',
            barmode='group',
            title=f"{pollutant} Annual MDA8 Average - {', '.join(city_selected)}",
            labels={'mda8': f'Concentration ({pollutant})', 'year': 'Year'},
            category_orders={'year': sorted(years_selected)}
            )
            
        st.plotly_chart(fig2, width='stretch')
        
        # Seasonal patterns
        st.subheader("Seasonal Patterns")
        
        seasonal = comp_df.groupby(['city', 'season'])['mda8'].mean().reset_index()
        
        fig4 = px.bar(
            seasonal,
            x='city',
            y='mda8',
            color='season',
            barmode='group',
            title=f"{pollutant} by Season",
            labels={'mda8': 'Average MDA8 (µg/m³)'},
            category_orders={'season': ['winter', 'spring', 'summer', 'fall']}
        )
        
        st.plotly_chart(fig4, width='stretch')
        
