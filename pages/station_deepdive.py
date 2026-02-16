import streamlit as st
import plotly.express as px
import pandas as pd

sensors_metadata = pd.read_csv("data/descriptive/sensors_metadata.csv")

if 'clean_df' not in st.session_state:
    st.warning("Please go to the overview page to create the data.")   

else: 
    clean_df = st.session_state['clean_df']
    EU_STANDARDS = st.session_state['EU_STANDARDS']
    cities = st.session_state['cities']
    pollutants = st.session_state['pollutants']
    years = st.session_state['years']
    st.title("🏙️ Station-Level Analysis")
    
    st.markdown("""
    <div class="info-card">
        <h3>Station-Level Analysis Overview</h3>
        <p>This section provides a detailed view of monitoring stations within each city. It allows for analysis of station-level data, including sensor coverage, daily averages, and station comparisons.</p>
        <h4>Key features include:</h4> 
        <ul>
            <li>Comparison of sensor coverage across stations</li>
            <li>Distribution of daily averages across stations</li>
            <li>Time series analysis for individual stations</li>
            <li>Comparison of different aggregation methods (mean, max, median)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<h5 style='display: flex; justify-content: center; background-color: #0995C8; padding: 10px; border-radius: 5px; color: #000;'><strong>Use the filters below to explore trends and patterns in the data.</strong></h5>", unsafe_allow_html=True)
   
    
    # City selector
    city_dd = st.selectbox("Select City", clean_df['city'].unique())
    pollutant_dd = st.selectbox("Select Pollutant", clean_df['parameter'].unique())
    
    dd_df = clean_df[
        (clean_df['city'] == city_dd) &
        (clean_df['parameter'] == pollutant_dd)
    ]

    dd_metadata = sensors_metadata[
        (sensors_metadata['city'] == city_dd) &
        (sensors_metadata['parameter'] == pollutant_dd)
    ]
    
    if not dd_df.empty and not dd_metadata.empty:

        st.subheader("Sensors Metadata")
        st.dataframe(dd_metadata)

        sensors_map = px.scatter_map(
            dd_metadata,
            lat='latitude',
            lon='longitude',
            color='station_name',
            map_style='outdoors',
            zoom=10
        )
        st.plotly_chart(sensors_map, width='stretch')

        st.subheader("Sensors Coverage Analysis")
        sensor_coverage = dd_df.groupby(['day', 'station_name'])['value'].count().reset_index(name='count')
        fig_cov = px.ecdf(
            sensor_coverage,
            x='count',
            color='station_name',
            title=f"Sensor Coverage ECDF - {pollutant_dd} in {city_dd}",
            labels={'count': 'Hours of Coverage', 'probability': 'Percent frequency', 'station_name': 'Station Name'}
        )

        st.plotly_chart(fig_cov, width='stretch')

        daily_station = dd_df.groupby(['year', 'day', 'station_name'])['day_mean_value_per_station'].mean().reset_index()
        annual_station = daily_station.groupby(['year', 'station_name'])['day_mean_value_per_station'].count().reset_index(name='count')
        fig_annual_cov = px.bar(
            annual_station,
            x='year',
            y='count',
            color='station_name',
            barmode='group',
            title=f"Annual Sensor Coverage - {pollutant_dd} in {city_dd}",
            labels={'count': 'Days of Coverage', 'probability': 'Percent frequency', 'station_name': 'Station Name'}
        )

        st.plotly_chart(fig_annual_cov, width='stretch')

        st.markdown("---")


        daily_station = dd_df.groupby(['day', 'station_name'])['day_mean_value_per_station'].mean().reset_index()
        st.subheader("Distribution of Measures Across Stations")
        
        fig3 = px.box(
                daily_station,
                x='station_name',
                y='day_mean_value_per_station',
                color='station_name',
                title=f"Distribution of Measures Across Stations - {pollutant_dd} in {city_dd}",
                labels={'day_mean_value_per_station': 'Daily Average (µg/m³)'}
            )
            
        st.plotly_chart(fig3, width='stretch')

        # Station comparison
        st.subheader("Station Aggregate Measures Comparison")
        
        station_avg = dd_df.groupby(['station_name', 'year'])['day_mean_value_per_station'].mean().reset_index()
        
        fig = px.histogram(
            station_avg,
            x='station_name',
            y='day_mean_value_per_station',
            color='year',
            barmode='group',
            title=f"Annual Averages per Station - {pollutant_dd} in {city_dd}",
            labels={'day_mean_value_per_station': 'Average (µg/m³)'}
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Time series by station
        st.subheader("Time Series by Station")
        
        st.info("""
        Select one or more stations to view their time series data.""")
        stations = st.multiselect(
            "Select Stations",
            options=dd_df['station_name'].unique(),
            default=list(dd_df['station_name'].unique())
        )
        
        if stations:
            station_ts = dd_df[dd_df['station_name'].isin(stations)]
            daily_station = station_ts.groupby(['day', 'station_name'])['day_mean_value_per_station'].mean().reset_index()
            
            fig2 = px.line(
                daily_station,
                x='day',
                y='day_mean_value_per_station',
                color='station_name',
                title=f"{pollutant_dd} Time Series by Station"
            )
            
            st.plotly_chart(fig2, width='stretch')

        st.subheader("Aggregation methods comparison")
        
        # Compare different aggregation methods
        agg_methods = ['day_mean_value_per_station', 'day_max_value_per_station', 'day_median_value_per_station']
        agg_df = dd_df.groupby(['station_name', 'year'] + agg_methods).size().reset_index(name='count')
        
        fig4 = px.scatter(
            agg_df,
            x='day_mean_value_per_station',
            y='day_max_value_per_station',
            color='station_name',
            title=f"Comparison of Aggregation Methods: Mean vs Max Value - {pollutant_dd} in {city_dd}",
            labels={
                'day_mean_value_per_station': 'Mean Value (µg/m³)',
                'day_max_value_per_station': 'Max Value (µg/m³)',
                'station_name': 'Station Name'
            },
            trendline="ols",
            trendline_scope="overall",
            trendline_color_override="purple"
        )
        st.plotly_chart(fig4, width='stretch')

        fig5 = px.scatter(
            agg_df,
            x='day_mean_value_per_station',
            y='day_median_value_per_station',
            color='station_name',
            title=f"Comparison of Aggregation Methods: Mean vs Median Value - {pollutant_dd} in {city_dd}",
            labels={
                'day_mean_value_per_station': 'Mean Value (µg/m³)',
                'day_median_value_per_station': 'Median Value (µg/m³)',
                'station_name': 'Station Name'
            },
            trendline="ols",
            trendline_scope="overall",
            trendline_color_override="yellow"
        )
        st.plotly_chart(fig5, width='stretch')

        fig6 = px.bar
        