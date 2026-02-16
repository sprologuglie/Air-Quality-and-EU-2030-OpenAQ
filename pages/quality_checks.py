import streamlit as st
import plotly.express as px
import pandas as pd

if 'clean_df' not in st.session_state:
    st.warning("Please go to the overview page to create the data.")   

else: 
    clean_df = st.session_state['clean_df']
    EU_STANDARDS = st.session_state['EU_STANDARDS']
    cities = st.session_state['cities']
    pollutants = st.session_state['pollutants']
    years = st.session_state['years']
    quality_df = st.session_state['quality_df']
    
    st.title("🔍 Data Quality Assessment")
    
    st.markdown("""
                <div class="info-card">
                <h3>Data Quality Overview</h3>
    <p> Evaluate data completeness and reliability using:
    <ul>
        <li><strong>Days coverage</strong>: % of hours with data per day
        <li><strong>Sensor coverage</strong>: mean % of hours with data per day and % of days with data per year
        <li><strong>Quality flags</strong>: Based on <strong>sensor count</strong> and <strong>coverage thresholds</strong>
    </ul>
    """, unsafe_allow_html=True)
    
    # Quality overview table
    st.subheader("Quality Summary by City")
    
    if not quality_df.empty:
        st.dataframe(quality_df, width='stretch')
    else:
        st.warning("Quality data not available.")
    
    # Coverage heatmap
    st.subheader("Number of Active Sensors Coverage Heatmap")
    
    pivot = quality_df.pivot(
        index=['city', 'year'],
        columns='parameter',
        values='year_median_active_sensors_per_city_parameter'
    )
    pivot.index = [f"{city} {year}" for city, year in pivot.index]
    
    fig = px.imshow(
    pivot,
    text_auto='.1f',
    aspect="auto",                   
    title="Median Active Sensors per City-Year-Parameter",
    labels=dict(color="Median Active Sensors")
    )
    fig.update_layout(height=750)
    fig.update_yaxes(dtick=1)
    st.plotly_chart(fig, width='stretch')

    # Yearly coverage
    st.subheader("Days Available Coverage Heatmap")
 
        
    pivot2 = quality_df.pivot(
        index=['city', 'year'],
        columns='parameter',
        values='percent_days_avaiable_per_city_year'
    )
    
    pivot2.index = [f"{city} {year}" for city, year in pivot2.index]
        
    fig2 = px.imshow(
    pivot2,
    text_auto='.1f',
    aspect="auto",                   
    title="Days Available per City-Year-Parameter",
    labels=dict(color="Percent Days Available"))
    fig2.update_layout(height=750)
    fig2.update_yaxes(dtick=1)
    st.plotly_chart(fig2, width='stretch')
        


    # Compare different aggregation methods





    st.subheader("Aggregation methods comparison")

    
    city_selected = st.selectbox("Select Cities for Detailed View", cities)
    pollutant = st.selectbox("Select Pollutant for Comparison", pollutants)
    years_selection = st.slider("Select Year Range", years[0], years[-1], years)
    years_selected = list(range(years_selection[0], years_selection[1] + 1))
    
    comp_df = clean_df[
        (clean_df['city'] == city_selected) &
        (clean_df['parameter'] == pollutant) &
        (clean_df['year'].isin(years_selected))
    ]

    st.info( """
            Compare annual means using different aggreagation strategies: 

        - Annual Mean Mean Value = Annual mean of daily means of daily mean values per station
        - Annual Mean Median Value = Annual mean of daily medians of daily median values per station
        - Annual Mean Max Value = Annual mean of daily max vlues
            """)
    agg_methods = ['day_mean_value', 'day_median_value', 'day_max_value']
    agg_df = comp_df.groupby(['city', 'year'] + agg_methods).size().reset_index(name='count')

    yearly_agg = agg_df.groupby(['city', 'year'])[['day_mean_value', 'day_median_value', 'day_max_value']].mean().reset_index()
    yearly_agg = yearly_agg.round(1)
    yearly_agg = yearly_agg.rename(columns={
        'day_mean_value': 'Annual Mean Mean Value (µg/m³)',
        'day_max_value': 'Annual Mean Max Value (µg/m³)',
        'day_median_value': 'Annual Mean Median Value (µg/m³)'
    })
    st.dataframe(yearly_agg, width='stretch')

    
    fig4 = px.scatter(
            agg_df,
            x='day_mean_value',
            y='day_max_value',
            title="Comparison of Aggregation Methods - Daily Mean Values vs Daily Max Values",
            labels={
                'day_mean_value': 'Mean Value (µg/m³)',
                'day_max_value': 'Max Value (µg/m³)'
            },
            trendline="ols",
            trendline_color_override='red',
            
        )
    
    fig4.update_yaxes(range = [0, 300])


    fig5 = px.scatter(
            agg_df,
            x='day_mean_value',
            y='day_median_value',
            title="Comparison of Aggregation Methods - Daily Mean Values vs Daily Max Values",
            labels={
                'day_mean_value': 'Mean Value (µg/m³)',
                'day_median_value': 'Median Value (µg/m³)'
            },
            trendline="ols",
            trendline_color_override='red'
        )
    
    fig5.update_yaxes(range = [0, 300])

    st.plotly_chart(fig5, width='stretch')
    st.plotly_chart(fig4, width='stretch')

    res_1 = px.get_trendline_results(fig4)
    res_2 = px.get_trendline_results(fig5)

    const_1, coef_1 = res_1.iloc[0]["px_fit_results"].params
    const_2, coef_2 = res_2.iloc[0]["px_fit_results"].params

    eq_1 = f"Daily Max Value = {const_1:.2f} + {coef_1:.2f} Daily Mean Value"
    eq_2 = f"Daily Median Value = {const_2:.2f} + {coef_2:.2f} Daily Mean Value"

    st.markdown("#### Key Metrics")
    col_1, col_2 = st.columns(2)
    with col_1:
        st.metric("Mean vs Median Regression Line", f"{eq_2}")
    with col_2:
        st.metric("Mean vs Max Regression line", f"{eq_1}")
