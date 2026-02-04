import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import yaml

with open("config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

def CAQI(row):
    p = row['parameter']
    v = row['day_max_value']
    if p == "pm10 µg/m³" or p == "pm25 µg/m³":
        v = row['day_mean_value']
    
    if p not in config['CAQI_breakpoints']:
        return None

    breakpoints = config['CAQI_breakpoints'][p]
    
    if v == None:
        category = None
    elif v <= breakpoints[0]:
        category = 1
    elif v <= breakpoints[1]:
        category = 2
    elif v <= breakpoints[2]:
        category = 3
    elif v <= breakpoints[3]:
        category = 4
    elif v <= breakpoints[4]:
        category = 5
    else:
        category = 6
        
    return category

def CAQI_qualitative(category):
    if category == 1:
        return "Good"
    elif category == 2:
        return "Fair"
    elif category == 3:
        return "Moderate"
    elif category == 4:
        return "Poor"
    elif category == 5:
        return "Very Poor"
    elif category == 6:
        return "Extremely Poor"
    else: return None


def calculate_compliance_eu_2030_days(row, aggregation="day"):  
    p = row['parameter']
    if aggregation == "day":
        v = row['day_mean_value']
        if p == 'o3 µg/m³':
            v = row['mda8']
    
    elif aggregation == "station":
        v = row['day_mean_value_per_station']
        if p == 'o3 µg/m³':
            v = None
    
    
    breakpoints = config['new_standards_day']
    
    if p not in breakpoints:
        return None

    if pd.isna(v): 
        return None
    
    if v > breakpoints[p]:
        return 1
    
    return 0






def Cutting_Hourly_Values():
    print("Preparing data...")
    clean_data = pd.read_csv("data/processed/clean.csv")
    clean_data.drop(columns=['value', 'local_datetime', 'utc_datetime', 'station_name', 'sensor_id', 'day_mean_value_per_station', 'sensor_percent_coverage_per_day', 'sensors_percent_coverage_per_year', 'valid_sensor',  'utc_datetime', 'median_hourly_value',	'rolling_8h_mean', 'day_max_value_per_station', 'day_median_value_per_station', 'mean_sensor_percent_coverage_per_day'], inplace = True)
    clean_data.drop_duplicates(keep="first", inplace = True, ignore_index=True)
    clean_data.to_csv("data/processed/daily_data.csv", index=False)
    return clean_data



def Make_Compliance_Table():
    print("Making compliance table...")
    df = pd.read_csv("data/processed/daily_data.csv")
    report = []  
    stats = df.groupby(['parameter', 'city', 'year'])['day_mean_value'].mean()
    stats = pd.DataFrame(stats)
    
    for row in stats.itertuples():
        p, city, year = row.Index  # The MultiIndex tuple
        media = stats.loc[(p, city, year), 'day_mean_value']
        
        res = {
            'City' : city,
            'Parameter': p,
            'Year' : year,
            'Yearly Average (µg/m³)': round(media, 2),
            'Current yearly limit (µg/m³)': "Not regualted",
            '2030 yearly limit (µg/m³)': "Not regulated",
            'Compliance (Yearly Average)': "Not Applicable",
            'Percent Above Current Standards': "Not Applicable",
            'Percent Above 2030 Standards': "Not Applicable",
            'Daily limit value (µg/m³)': "Not regulated",
            'Days above limit value': "Not Applicable",
            'Current days limit': "Not regualted",
            '2030 days limit': "Not regulated",
            'Compliance (Days)' : "Not Applicable"
        }

        # PM2.5, PM10, NO2
        for key in config['current_standards_year']:
            if p == key:
                # Controllo Media Annua
                
                res['Current yearly limit (µg/m³)'] = config['current_standards_year'][key]
                res['2030 yearly limit (µg/m³)'] = config['new_standards_year'][key]

                if media > config['current_standards_year'][key]:
                    res['Compliance (Yearly Average)'] = f"Critical (Above current limits and above 2030 limits)"
                    res['Percent Above Current Standards'] = f"{((media / config['current_standards_year'][key]) -1) *100}% above current standards"
                    res['Percent Above 2030 Standards'] = f"{((media / config['new_standards_year'][key]) -1) *100}% above 2030 standards"
                
                elif media <= config['current_standards_year'][key] and media > config['new_standards_year'][key]:
                    res['Compliance (Yearly Average)'] = f"Problematic (Below current limit but above 2030 limit)"
                    
                    res['Percent Above Current Standards'] = f"Below current standards"
                    res['Percent Above 2030 Standards'] = f"{((media / config['new_standards_year'][key]) -1) *100}% above 2030 standards"
                
                elif media <= config['new_standards_year'][key]:
                    res['Compliance (Yearly Average)'] = f"Good (Below current limit and also below 2030 limit)"
                    res['Percent Above Current Standards'] = f"Below current standards"
                    res['Percent Above 2030 Standards'] = f"Below 2030 standards"
                
                # Controllo giorni di sforamento
                if key == 'pm10 µg/m³':
                    giorni_over_45 = len(df[(df['parameter'] == "pm10 µg/m³") & (df['year'] == year) & (df['city'] == city) &
                                          (df['day_mean_value'] > 45)])
                    res['Daily limit value (µg/m³)'] = 45
                    res['Days above limit value'] = giorni_over_45
                    res['Current days limit'] = 35
                    res['2030 days limit'] = 18
                    # Limite attuale 35 giorni, limite 2030 ridotto a 18 giorni
                    if giorni_over_45 > 35: res['Compliance (Days)'] = f"Critical (Above current limits and above 2030 limits"
                    elif giorni_over_45 > 18 and giorni_over_45 <= 35: res['Compliance (Days)'] = f"Problematic (Below current limit but above 2030 limit"
                    elif giorni_over_45 <= 18: res['Compliance (Days)'] = f"Good (Below current limit and also below 2030 limit"

                if key == 'pm25 µg/m³':
                    giorni_over_25 = len(df[(df['parameter'] == "pm25 µg/m³") & (df['year'] == year) & (df['city'] == city) &
                                          (df['day_mean_value'] > 25)])
                    res['Daily limit value (µg/m³)'] = 25
                    res['Days above limit value'] = giorni_over_25
                    
                    res['2030 days limit'] = 18
                    # Introdotto limite 2030 a 18 giorni
                    if giorni_over_25 > 18: res['Compliance (Days)'] = f"Problematic (Above 2030 limit)"
                    elif giorni_over_25 <= 18: res['Compliance (Days)'] = f"Good (Below 2030 limit)"
                
                if key == 'no2 µg/m³':
                    giorni_over_50 = len(df[(df['parameter'] == "no2 µg/m³") & (df['year'] == year) & (df['city'] == city) &
                                          (df['day_mean_value'] > 50)])
                    res['Daily limit value (µg/m³)'] = 50
                    res['Days above limit value'] = giorni_over_50
                    
                    res['2030 days limit'] = 18
                    # Introdotto limite 2030 a 18 giorni
                    if giorni_over_50 > 18: res['Compliance (Days)'] = f"Problematic (Above 2030 limit)"
                    elif giorni_over_50 <= 18: res['Compliance (Days)'] = f"Good (Below 2030 limit)"

        # Logica speciale per Ozono (O3)
        if p == 'o3 µg/m³':
            res['Daily limit value (µg/m³)'] = 120
            res['Current days limit'] = 25
            res['2030 days limit'] = 18
            if year >= config['yearfrom'] + 2:
                years_range = [year, year - 1, year - 2]
                years_avaiable = df[(df['parameter'] == "o3 µg/m³") & 
                       (df['year'].isin(years_range)) & 
                       (df['city'] == city)]['year'].unique()
                
                if len(years_avaiable) == 3:

                    # Sforamenti della soglia 120 µg/m³ (media su tre anni)
                    giorni_over_120 = len(df[(df['parameter'] == "o3 µg/m³") & (df['year'].isin(years_range)) & (df['city'] == city) &
                                                (df['mda8'] > 120)]) / 3
                    giorni_over_120 = round(giorni_over_120, 1)
                    res['Days above limit value'] = giorni_over_120
                    # Attualmente: max 25 giorni/anno. 2030: l'obiettivo è ridurre a 18 o meno.
                    if giorni_over_120 > 25: res['Compliance (Days)'] = f"Critical (Above current limits and above 2030 limits"
                    elif giorni_over_120 > 18 and giorni_over_120 <= 25: res['Compliance (Days)'] = f"Problematic (Below current limit but above 2030 limit"
                    elif giorni_over_120 <= 18: res['Compliance (Days)'] = f"Good (Below current limit and also below 2030 limit"

            
        report.append(res)
    
    report = pd.DataFrame(report)
    flags = pd.read_csv("results/quality_checks/cities_quality.csv")
    flags = flags.rename(columns= {'city' : 'City', 'year' : 'Year', 'parameter' : 'Parameter', 'flag_city_parameter' : 'Flag', 'year_median_active_sensors_per_city_parameter' : 'Median active sensors', 'percent_days_avaiable_per_city_year' : 'Percent days avaiable'})
    flags = flags[['City', 'Year', 'Parameter', 'Flag', 'Median active sensors', 'Percent days avaiable']]    
    report = report.merge(flags, on=['City', 'Year', 'Parameter'], how='left')
    Path("results").mkdir(parents=True, exist_ok=True)
    report.to_csv("results/compliance_table.csv", index=False)
    print("Done!")


def Make_Plots():
    print("Making Plots...")
    df = pd.read_csv("data/processed/daily_data.csv")
    Path("results/plots/main").mkdir(parents=True, exist_ok=True)
    
    # BOXPLOT
    g = sns.catplot (
        data=df, 
        x = "city", 
        y = "day_mean_value", 
        hue = "city", 
        col= "parameter", 
        kind = "box",
        sharey= False, 
        palette="Set1")
    
    g.set_titles(col_template="{col_name}")
    g.set_axis_labels("City", "Daily mean Value (µg/m³)")
    g.figure.suptitle("Dispersion of daily measures", y=1.10, fontsize=18)
    g.figure.text(0.5, 1.03, "Dispersion of daily mean value for each city and parameter", ha='center', va='center', fontsize=12, style='italic')

    g.figure.savefig("results/plots/main/daily_averages_boxplot.png", bbox_inches='tight')
    plt.close(g.figure)
    print("Plot 1 done!")

    # DENSITY PLOTS
    Path("results/plots/density_plots").mkdir(parents=True, exist_ok=True)

    for parameter in config['parameters']:
        p = parameter.replace(" µg/m³", "")
        temp_df = df[df['parameter'] == parameter]

        g = sns.displot(
            data=temp_df, 
            x='day_mean_value', 
            hue='city',  
            kde=True, 
            stat="density", 
            common_norm=False,
            palette="Set1")
        
        g.set_titles(col_template="{col_name}")
        g.set_axis_labels("Dalily mean Value (µg/m³)")
        g.figure.suptitle(f"Distribution of daily measures for {p}", y=1.10, fontsize=18)
        g.figure.text(0.5, 1.03, "Mean value density plot", ha='center', va='center', fontsize=12, style='italic')
        g._legend.set_title("City")
        g.figure.savefig(f"results/plots/density_plots/daily_averages_densityplot_{p}.png", bbox_inches='tight')
        plt.close(g.figure)
    
    print("Plot 2 done!")
    
    # SEASONAL TRENDS
    Path("results/plots/seasonal_trends").mkdir(parents=True, exist_ok=True)

    for parameter in config['parameters']:
        temp_df = df[df['parameter'] == parameter]  
        
        p = parameter.replace(" µg/m³", "") 
        g = sns.catplot(
            data=temp_df, 
            x="season", 
            y="mean_value_per_season", 
            col="city",
            col_order=config['locations'],
            hue="city",
            col_wrap=3, 
            kind="bar", 
            palette="Dark2",
            order=['winter', 'spring', 'summer', 'fall'])
        
        g.set_titles(col_template="{col_name}")
        g.set_axis_labels("Days", "Mean Value (µg/m³)")
        g.figure.suptitle(f"Seasonal trends for {p}", y=1.05, fontsize=18)
        g.figure.text(0.5, 1.01, "Mean value for each season, city and parameter", ha='center', va='center', fontsize=12, style='italic')
        g._legend.set_title("City")
        g.figure.savefig(f"results/plots/seasonal_trends/seasonal_trends_{p}.png", bbox_inches='tight')
        plt.close(g.figure)

    print("Plot 3 done!")

    # CAQI per parameter 
    Path("results/plots/CAQI").mkdir(parents=True, exist_ok=True)
    df['CAQI'] = df[['parameter', 'day_mean_value', 'day_max_value']].apply(CAQI, axis=1)
    df['CAQI_qual'] = df['CAQI'].apply(CAQI_qualitative)

    for parameter in config['parameters']:
        temp_df = df[df['parameter'] == parameter]
        v = 'day_max_value'
        V = "Max daily value"  
        
        p = parameter.replace(" µg/m³", "")
        if parameter == "pm10 µg/m³" or parameter == "pm25 µg/m³":
            v = 'day_mean_value'
            V = "Mean daily value"
        g = sns.catplot(
            data=temp_df, 
            x ="day", 
            y=v, 
            hue="CAQI_qual", 
            col="city",            
            col_order=config['locations'],
            col_wrap=3,
            kind="bar", 
            errorbar=None, 
            hue_order=['Good', 'Fair', 'Moderate', 'Poor', 'Very Poor', 'Extremely Poor'])
        
        g.set_titles(col_template="{col_name}")
        g.set_axis_labels("Days", V)
        g.figure.suptitle("CAQI (per parameter)", y=1.05, fontsize=18)
        g.figure.text(0.5, 1.01, f"CAQI for {p}", ha='center', va='center', fontsize=12, style='italic')
        g._legend.set_title("CAQI")
        g.set_xticklabels([])
        g.tick_params(bottom=False) #delete the text on the x-axis because ilegbiles
        
        g.figure.savefig(f"results/plots/CAQI/CAQI_per_parameter/CAQI_{p}.png", bbox_inches='tight')
        plt.close(g.figure)
    print("Plot 4 done!")

    # CAQI Global
    df['CAQI_global'] = df.groupby(['city', 'day'])['CAQI'].transform('max')
    df['CAQI_global_qual'] = df['CAQI_global'].apply(CAQI_qualitative)

    g = sns.catplot(
        data=df, 
        x ="day", 
        y="day_median_value", 
        hue="CAQI_global_qual", 
        col="city",
        col_order=config['locations'],
        col_wrap=3, 
        kind="bar", 
        errorbar=None, 
        hue_order=['Good', 'Fair', 'Moderate', 'Poor', 'Very Poor', 'Extremely Poor'])
    
    g.set_titles(col_template="{col_name}")
    g.set_axis_labels("Days", "Median Value (µg/m³)")
    g.figure.suptitle("Daily CAQI (global)", y=1.10, fontsize=18)
    g.figure.text(0.5, 1.03, "Median value and global CAQI for each day, city", ha='center', va='center', fontsize=12, style='italic')
    g._legend.set_title("CAQI")
    g.set_xticklabels([])
    g.tick_params(bottom=False) #delete the text on the x-axis because ilegbiles
    
    g.figure.savefig("results/plots/CAQI/CAQI_global.png", bbox_inches='tight')
    plt.close(g.figure)
    print("Plot 5 done!")

    df['count_days_for_CAQI'] = df.groupby(['CAQI_global_qual', 'city'])['day'].transform('nunique')

    # CAQI count
    g = sns.catplot(
        data=df, 
        x="CAQI_global_qual", 
        y="count_days_for_CAQI", 
        col="city", 
        col_order=config['locations'],
        col_wrap=3, 
        hue="CAQI_global_qual", 
        kind="bar", 
        order=['Good', 'Fair', 'Moderate', 'Poor', 'Very Poor', 'Extremely Poor'],
        hue_order=['Good', 'Fair', 'Moderate', 'Poor', 'Very Poor', 'Extremely Poor'])
    
    g.set_titles(col_template="{col_name}")
    g.set_axis_labels("CAQI", "Days)")
    g.figure.suptitle("CAQI (global) Frequency", y=1.10, fontsize=18)
    g.figure.text(0.5, 1.03, "Frequency for each CAQI category per city", ha='center', va='center', fontsize=12, style='italic')
    g.set_xticklabels(rotation=45)

    g.figure.savefig("results/plots/CAQI/count_CAQI.png", bbox_inches='tight')
    plt.close(g.figure)
    print("Plot 6 done!")



    # ANNUAL MEAN
    
    for parameter in config['parameters']:
        if parameter != "o3 µg/m³":
            temp_df = df[df['parameter'] == parameter]
                    
            p = parameter.replace(" µg/m³", "")
            g = sns.catplot(
            data=temp_df, 
            x="year", 
            y="day_mean_value", 
            col="city",
            col_order=config['locations'],
            hue="flag_city_parameter",
            col_wrap=3,
            kind="bar", 
            palette="Blues",
            hue_order=['Very Low', 'Low', 'Medium', 'High'],
            edgecolor="black")
            for ax in g.axes.flat:
                ax.axhline(config['new_standards_year'][parameter], color='black', linestyle='--', linewidth=1.5, zorder=2)
                    
            g.set_titles(col_template="{col_name}")
            g.set_axis_labels("Year", "Mean Value (µg/m³)")
            g.figure.suptitle(f"Annual trend for {p}", y=1.05, fontsize=18)  
            g.figure.text(0.5, 1.01, f"Mean annual value for each year and city", ha='center', va='center', fontsize=12, style='italic')
            g._legend.set_title("Quality Flag")
                    
            g.figure.savefig(f"results/plots/main/trends_annual_{p}.png", bbox_inches='tight')
            plt.close(g.figure)

    print("Plot 7 done!")
    
    # COMPLIANCE DAYS
    df['compliance_ue_2030_days'] = df[['parameter', 'day_mean_value', 'day_max_value' ,'mda8']].apply(calculate_compliance_eu_2030_days, axis=1)
    #df['count_days_for_ue_2030'] = df.groupby(['year', 'city', 'parameter'])['compliance_ue_2030_days'].transform('sum')
    for parameter in config['parameters']:
        temp_df = df[df['parameter'] == parameter].groupby(['year', 'city', 'flag_city_parameter'])['compliance_ue_2030_days'].sum().reset_index()
        
        p = parameter.replace(" µg/m³", "")
        g = sns.catplot(
            data=temp_df, 
            x="year", 
            y="compliance_ue_2030_days", 
            hue="flag_city_parameter", 
            col="city",
            col_order=config['locations'],
            col_wrap=3, 
            kind="bar",
            palette="Blues",
            hue_order=['Very Low', 'Low', 'Medium', 'High'],
            edgecolor="black")
        
        for ax in g.axes.flat:
                ax.axhline(18, color='black', linestyle='--', linewidth=1.5, zorder=2)
        
        g.set_titles(col_template="{col_name}")
        g.set_axis_labels("Year", "Days")
        g.figure.suptitle(f"{p} Compliance with EU 2030's rule (daily maximums)", y=1.05, fontsize=18)
        g.figure.text(0.5, 1.01, "Days above the limit for each city and year", ha='center', va='center', fontsize=12, style='italic')
        g._legend.set_title("Quality Flag")
        g.figure.savefig(f"results/plots/main/compliance_days_2030_{p}.png", bbox_inches='tight')
        plt.close(g.figure)
    print("Plot 8 done!") 



def Quality_Plots_deepdive():
    print("Creating quality checks figures...")

    clean_data = pd.read_csv("data/processed/clean.csv")
    # QUALITY DEEPDIVE
    Path("results/quality_checks/deepdive").mkdir(parents=True, exist_ok=True)
    
    for city in config['quality_deep_locations']:
        data = clean_data[clean_data['city'] == city]
        g = sns.displot(                                                                                            # Plotting sensors percent coverage per year
        data = data,
        x = "sensor_percent_coverage_per_day",
        col = "parameter",
        row="year",
        hue = "station_name",
        kind="ecdf",
        palette="Set1" 
                )
        g.set_titles(col_template="{col_name}")
        g.set_axis_labels("Daily Coverage (%)", "Density")
        g.figure.suptitle(f"{city}'s sensor quality: daily coverage", y=1.05, fontsize=20)
        g.figure.text(0.5, 1.03, "ECDF of daily percent coverage for each sensor and parameter", ha='center', va='center', fontsize=12, style='italic')
        g._legend.set_title("Station Name")
        g.figure.savefig(f"results/quality_checks/deepdive/{city}_sensor_percent_coverage_per_day.png", bbox_inches='tight')
        plt.close(g.figure)

    print("1/4")

    for city in config['quality_deep_locations']:
        data = clean_data[clean_data['city'] == city]
        g = sns.catplot(                                                                                            # Plotting sensors percent coverage per year
        data = data, 
        x = "year", 
        y = "sensors_percent_coverage_per_year",
        col = "parameter",
        hue = "station_name", 
        kind = "bar",
        palette="Set1" 
        )
        g.set_titles(col_template="{col_name}")
        g.set_axis_labels("Year", "Days Avaiable (%)")
        g.figure.suptitle(f"{city}'s sensors' quality: days avaiable", y=1.10, fontsize=18)
        g.figure.text(0.5, 1.03, "Percent days avaiable for each year, city, parameter and sensor", ha='center', va='center', fontsize=12, style='italic')
        g._legend.set_title("Station Name")
        g.figure.savefig(f"results/quality_checks/deepdive/{city}_sensors_percent_coverage_per_year.png", bbox_inches='tight')
        plt.close(g.figure)

    print("2/4")
    

    for city in config['quality_deep_locations']:
        data = clean_data[clean_data['city'] == city]
        g = sns.relplot(                                                                                            # Plottinge active sensors per day
        data = data, 
        x = "day", 
        y = "active_sensors_per_day_city_parameter",
        col = "parameter",
        hue = "parameter",
        kind = "line",
        palette="Dark2",
        hue_order=["no2 µg/m³", "o3 µg/m³", "pm10 µg/m³", "pm25 µg/m³"]  
        )
        g.set_titles(col_template="{col_name}")
        g.set_axis_labels("Day", "Active Sensors")   
        g.figure.suptitle(f"{city}'s active sensors", y=1.10, fontsize=18)
        g.figure.text(0.5, 1.03, "Active sensors per parameter", ha='center', va='center', fontsize=12, style='italic')
        g._legend.set_title("Parameter")
        g.set_xticklabels([])
        g.tick_params(bottom=False)
        g.figure.savefig(f"results/quality_checks/deepdive/{city}_active_sensors_per_day.png", bbox_inches='tight')
        plt.close(g.figure)
    print("3/4")

    for city in config['quality_deep_locations']:
        data = clean_data[clean_data['city'] == city]
        g = sns.catplot(                                                                                            # Plotting city percent days avaiable per year
        data = data, 
        x = "year", 
        y = "percent_days_avaiable_per_city_year",
        col = "parameter",
        hue = "parameter", 
        kind = "bar",
        palette="Dark2",
        hue_order=["no2 µg/m³", "o3 µg/m³", "pm10 µg/m³", "pm25 µg/m³"] 
        )
        g.set_titles(col_template="{col_name}")
        g.set_axis_labels("Year", "Days Avaiable (%)")
        g.figure.suptitle(f"{city}'s days avaiable", y=1.10, fontsize=18)
        g.figure.text(0.5, 1.03, "Percent days avaiable per parameter", ha='center', va='center', fontsize=12, style='italic')
        g._legend.set_title("Parameter")
        g.figure.savefig(f"results/quality_checks/deepdive/{city}_percent_days_avaiable_per_year.png", bbox_inches='tight')
        plt.close(g.figure)
    print("4/4")

    
    
    
def Deep_Dive_table():

    clean_data = pd.read_csv("data/processed/clean.csv")

    print("Making deep dive tables...")

    # AGGREGATION
    for city in config['quality_deep_locations']:
        data = clean_data[clean_data['city'] == city].copy()
        
        data['annual_mean'] = round(data.groupby(['year', 'city', 'parameter'])['day_mean_value'].transform('mean'), 2)
        data['annual_mean_median'] = round(data.groupby(['year', 'parameter'])['day_median_value'].transform('mean'), 2)
        data['annual_mean_max'] = round(data.groupby(['year', 'parameter'])['day_max_value'].transform('mean'), 2)
        data['annual_mean_median_gap'] = round(data['annual_mean'] - data['annual_mean_median'], 2)
        data['annual_mean_max_gap']    = round(data['annual_mean'] - data['annual_mean_max'], 2)
        data['annual_max_median_gap']  = round(data['annual_mean_max'] - data['annual_mean_median'], 2)
        data = data[['year', 'parameter', 'flag_city_parameter', 'annual_mean', 'annual_mean_median', 'annual_mean_max', 'annual_mean_median_gap', 'annual_mean_max_gap', 'annual_max_median_gap']].drop_duplicates()

        data.to_csv(f"results/quality_checks/deepdive/{city}_aggregation.csv", index=False)

    # STATIONS ANNUAL MEAN
    for city in config['quality_deep_locations']:
        data = clean_data[clean_data['city'] == city].copy()
        desciptive = data.groupby(['parameter', 'year', 'station_name', 'sensors_percent_coverage_per_year'])['day_mean_value_per_station'].describe()
        desciptive.to_csv(f"results/quality_checks/deepdive/{city}_annual_mean_per_station_descriptive.csv")
    
    # STATIONS EXCEEDANCE DAYS
    for city in config['quality_deep_locations']:
        data = clean_data[(clean_data['city'] == city) & (clean_data['parameter'] != "o3 µg/m³")].copy() # O3 excluded for absence of mda8 for station!
        data['exceedance_per_station'] = data.apply(lambda x: calculate_compliance_eu_2030_days(x, aggregation="station"), axis=1)
        data = data.drop_duplicates(subset=['day', 'parameter', 'station_name', 'exceedance_per_station'])
        data['exceedance_days_per_station'] = data.groupby(['year', 'parameter', 'station_name'])['exceedance_per_station'].transform('sum')
        desciptive = data.groupby(['parameter', 'year', 'station_name', 'sensors_percent_coverage_per_year'])[['exceedance_days_per_station']].first()
        desciptive = pd.DataFrame(desciptive)
        desciptive.to_csv(f"results/quality_checks/deepdive/{city}_exceedance_days_per_station_descriptive.csv")
