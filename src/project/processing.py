import pandas as pd
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import yaml

with open("config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

def Clean():
    print("Cleaning Data")

    raw_data = pd.read_csv("data/raw/raw_data.csv")                                                                     # Accessing raw data

    # Descritptive stats for raw data
    Path("data/descriptive").mkdir(parents=True, exist_ok=True)
    pre_cleaning_descriptive = raw_data.groupby(['city', 'parameter', 'station_name'])['value'].describe()                      # Descriptive stats for each sensor
    pre_cleaning_descriptive.to_csv("data/descriptive/pre_cleaning_descriptive.csv")                                            # Saving as csv

    # Convert to datetime
    raw_data["period.datetime_from.utc"] = pd.to_datetime(raw_data["period.datetime_from.utc"], format='ISO8601', utc=True)     # Convert to datetime format
    raw_data.rename(columns= {"period.datetime_from.utc" : "utc_datetime"}, inplace=True)                                       # Rename utc_datetime
    raw_data['local_datetime'] = raw_data['utc_datetime'].dt.tz_convert('Europe/Rome')                                          # Creating local_datetime variable
    
    # Basic cleaning
    raw_data.drop_duplicates(inplace=True)                                                                                      # Drop duplicates
    raw_data.dropna(subset=['value', 'utc_datetime'], inplace=True)                                                 # Drop NA for measurements or date
    raw_data.drop(raw_data[raw_data.value < 0].index, inplace=True)                                                             # Exclude neagtive values
    for parameter, cap in config['implausible_value_caps'].items():
        implausble_values = raw_data[(raw_data['parameter'] == parameter) & (raw_data.value > cap)].index
        raw_data.drop(implausble_values, inplace=True)                                                             # Exclude implausibly high values

    clean_data = raw_data[['value', 'parameter', 'city', 'station_name', 'sensor_id', 'utc_datetime', 'local_datetime']].copy() # Creating clean_df with selected columns

    print("Done!")
    return clean_data



def Get_Season(row):                                        # Function for getting the season
    
    date = row['local_datetime']                            # Taking Local Datetime
    if pd.isnull(date):
        return None                                         # If there is no date, return None
        
    month_and_day = (date.month, date.day)                  # Creatinf a tuple with month and day
    if (3, 20) <= month_and_day <= (6, 20):                 # For each season, we check wheter the date in comprised between the beginning and end dates of the season
        return "spring"
    elif (6, 21) <= month_and_day <= (9, 21):
        return "summer"
    elif (9, 22) <= month_and_day <= (12, 20):
        return "fall"
    else:
        return "winter"



def Time_Aggregation(clean_data):
    print("Aggregating Data...")

    clean_data["day"] = clean_data["local_datetime"].dt.date                            # Creating the day variable with the date
    clean_data['day_of_the_week'] = clean_data["local_datetime"].dt.day_name()          # Creating a variable for the days of the week
    clean_data['season'] = clean_data.apply(Get_Season, axis=1)                         # Creating a variable fot season using the Get_Season function
    clean_data['year'] = clean_data['local_datetime'].dt.year                           # Creating a variable for year

    print("Done!")
    return clean_data


def Flag_City(x):

    if x['year_median_active_sensors_per_city_parameter'] >= config["flags"]["sensors_active_per_day_high_flag"] and x['percent_days_avaiable_per_city_year'] >= config["flags"]["percent_days_avaiable_high_flag"]:
        flag = "High"

    elif x['year_median_active_sensors_per_city_parameter'] >= config["flags"]["sensors_active_per_day_medium_flag"] and x['percent_days_avaiable_per_city_year'] >= config["flags"]["percent_days_avaiable_medium_flag"]:
        flag = "Medium"

    elif x['year_median_active_sensors_per_city_parameter'] >= config["flags"]["sensors_active_per_day_low_flag"] or x['percent_days_avaiable_per_city_year'] >= config["flags"]["percent_days_avaiable_low_flag"]:
        flag = "Low"

    else:
        flag = "Very Low"

    return flag


def Quality_Checks(clean_data):

    print("Doing Quality Checks...")

    # SENSORS

    clean_data['sensor_percent_coverage_per_day'] = round((clean_data.groupby(
        ['day', 'sensor_id'])['local_datetime'].transform('nunique') / 24) * 100, 2)    
    
    clean_data['mean_sensor_percent_coverage_per_day'] = round(clean_data.groupby(
        ['sensor_id', 'year'])['sensor_percent_coverage_per_day'].transform('mean'), 2)        # Creating a variable for sensors day coverage percent

    clean_data['sensors_percent_coverage_per_year'] = round((clean_data.groupby(
        ['year', 'city', 'parameter', 'station_name', 'sensor_id'])['day'].transform('nunique') / 365) *100, 2)               # Creating a variable for sensors percent coverage for year

    clean_data['valid_sensor'] = ((clean_data['sensors_percent_coverage_per_year'] >= config["flags"]["percent_coverage_valid_sensor"])
                                            & (clean_data['mean_sensor_percent_coverage_per_day'] >= config["flags"]["percent_daily_coverage_valid_sensor"]))           # Selecting valid sensors
    
    # SENSORS METADATA
    sensors_per_parameter = clean_data[['city', 'station_name', 'parameter', 'sensor_id']].drop_duplicates().copy()
    sensors = pd.read_csv("data/raw/sensors.csv")
    sensors = sensors.drop(columns=['instruments', 'sensors', 'country.id', 'country.code', 'owner.id', 'provider.id', 'datetime_first.utc', 'datetime_last.utc', 'id', 'bounds'])
    sensors = sensors.rename(columns={"name" : "station_name", "country.name" : "country", "owner.name" : "owner", "provider.name" : "provider", "coordinates.latitude" : "latitude", "coordinates.longitude" : "longitude", "datetime_first.local" : "datetime_from", "datetime_last.local" : "datetime_to"})
    sensors = sensors_per_parameter.merge(sensors, how="left", on='station_name')
    
    # SAVING DATAFRAMES

    print("Saving quality checks dataframes...")
    processed_decriptive = clean_data.groupby(['year', 'city', 'parameter', 'station_name'])['value'].describe()
    processed_decriptive.to_csv("data/descriptive/processed_descriptive.csv")

    quality_checks_sensors = clean_data.groupby(['year', 'city', 'parameter', 'station_name', 'sensor_id'])[['mean_sensor_percent_coverage_per_day' ,'sensors_percent_coverage_per_year', 'valid_sensor']].first()
    quality_checks_sensors = pd.DataFrame(quality_checks_sensors)
    quality_checks_sensors.to_csv("results/quality_checks/sensors_quality.csv")

    sensors.to_csv("data/descriptive/sensors_metadata.csv", index=False)

    # EXCLUDING INVALID SENSORS
    if config["flags"]["exclude_invalid_sensors"]:
        clean_data.drop(clean_data[clean_data['valid_sensor'] == False].index, inplace=True)                  # Excluding invalid sensors

    # EXCLUDING INVALID DAYS (for each sensor)
    if config["flags"]["exclude_invalid_days"]:
        clean_data.drop(clean_data[clean_data['sensor_percent_coverage_per_day'] < config["flags"]["percent_coverage_valid_day"]].index, inplace=True)

    # CITIES

    clean_data['active_sensors_per_day_city_parameter'] = clean_data.groupby(
        ['day', 'city', 'parameter'])['sensor_id'].transform('nunique')                                     # Creating a variable for active sensors per day in each city for each parameter

    clean_data['year_median_active_sensors_per_city_parameter'] = clean_data.groupby(
        ['city', 'parameter', 'year'])['active_sensors_per_day_city_parameter'].transform('median')          # Creating a variable for median acrive sensor per year (city and parameter)

    clean_data['percent_days_avaiable_per_city_year'] = round((clean_data.groupby(['city', 'parameter', 'year'])['day'].transform('nunique') / 365) * 100, 2)

 
    clean_data['flag_city_parameter'] = clean_data.apply(Flag_City, axis=1)                                # Flagging cities

    # SAVING DATAFRAME

    quality_checks_city = clean_data.groupby(['city', 'year', 'parameter'])[['year_median_active_sensors_per_city_parameter', 'percent_days_avaiable_per_city_year', 'flag_city_parameter']].first()
    quality_checks_city = pd.DataFrame(quality_checks_city)
    Path("results/quality_checks").mkdir(parents=True, exist_ok=True)
    quality_checks_city.to_csv("results/quality_checks/cities_quality.csv")

    return clean_data




def Quality_Plots_heatmaps():
    # CITIES QUALITY HEATMAPS
    print("Creating plots...")
    Path("results/quality_checks/figures").mkdir(parents=True, exist_ok=True)
    c = pd.read_csv("results/quality_checks/cities_quality.csv")

    pivot_quality_active_sensors = c.pivot(index=['city', 'year'], columns='parameter', values='year_median_active_sensors_per_city_parameter')
    figure, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(pivot_quality_active_sensors, annot=True, linewidth=.5, yticklabels=True)
    figure.suptitle("Active sensors heatmap", y=1.10, fontsize=18)
    figure.text(0.5, 1.03, "Median active sensors for each city, year and parameter", ha='center', va='center', fontsize=12, style='italic')
    figure.savefig("results/quality_checks/figures/median_active_sensors_heatmap.png", bbox_inches='tight')
    plt.close()

    pivot_quality_days_avaiable = c.pivot(index=['city', 'year'], columns='parameter', values='percent_days_avaiable_per_city_year')
    figure, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(pivot_quality_days_avaiable, annot=True, fmt=".1f", linewidth=.5, yticklabels=True)
    figure.suptitle("Days avaiable heatmap", y=1.10, fontsize=18)
    figure.text(0.5, 1.03, "Percent days avaiable for each city, year and parameter", ha='center', va='center', fontsize=12, style='italic')
    figure.savefig("results/quality_checks/figures/days_avaiable_heatmap.png", bbox_inches='tight')
    plt.close()
    

def add_roll_and_mda8(g, tz_local="Europe/Rome"):

    g = g.sort_values("utc_datetime")

    s = (g.drop_duplicates("utc_datetime")
            .set_index("utc_datetime")["median_hourly_value"]
            .asfreq("h"))

    r8 = s.rolling(8, min_periods=6).mean()
    day_local = r8.index.tz_convert(tz_local).floor("D")
    mda8 = r8.groupby(day_local).max()

    total = pd.Series(1, index=r8.index).groupby(day_local).sum()
    valid = r8.notna().groupby(day_local).sum()
    thresh = np.ceil(total * 0.75).astype(int)   # gestisce DST (23/25 ore)
    mda8_valid = mda8.where(valid >= thresh)

    hourly_out = pd.DataFrame({"utc_datetime": r8.index, "rolling_8h_mean": r8.values})

       
    daily_out = pd.DataFrame({"day": mda8_valid.index.date, "mda8": mda8_valid.values})
        
    return hourly_out, daily_out

def Calculate_Average_Values(clean_data):
    print("Calculating average values...")

    # Daily means
    clean_data['day_mean_value_per_station'] = clean_data.groupby(['day', 'city', 'parameter', 'station_name'])['value'].transform('mean')
    clean_data['day_mean_value'] = clean_data.groupby(['day', 'city', 'parameter'])['day_mean_value_per_station'].transform('mean')

    # Max values (needed for o3 and no2)
    clean_data['day_max_value_per_station'] = clean_data.groupby(['day', 'city', 'parameter', 'station_name'])['value'].transform('max')
    clean_data['day_max_value'] = clean_data.groupby(['day', 'city', 'parameter'])['day_max_value_per_station'].transform('max')
    
    # Seasonal, week day and yearly averages
    clean_data['mean_value_per_weekday'] = clean_data.groupby(['day_of_the_week', 'city', 'parameter'])['day_mean_value'].transform('mean')
    clean_data['mean_value_per_season'] = clean_data.groupby(['season', 'city', 'parameter'])['day_mean_value'].transform('mean')
    clean_data['mean_value_per_year'] = clean_data.groupby(['year', 'city', 'parameter'])['day_mean_value'].transform('mean')

    # Median values
    clean_data["median_hourly_value"] = (clean_data.groupby(["city", "parameter", "utc_datetime"])["value"].transform("median"))
    clean_data["day_median_value_per_station"] = clean_data.groupby(['day', 'city', 'parameter', 'station_name'])['value'].transform('median')
    clean_data['day_median_value'] = clean_data.groupby(['day', 'city', 'parameter'])['day_median_value_per_station'].transform('median')
    
    # Add rolling 8h mean and max rolling 8h mean
    hourly_tbl = []
    daily_tbl = []

    for (city, param), g in clean_data.groupby(["city", "parameter"]):
        h, d = add_roll_and_mda8(g)
        h["city"], h["parameter"] = city, param
        d["city"], d["parameter"] = city, param
        hourly_tbl.append(h)
        daily_tbl.append(d)

    hourly_tbl = pd.concat(hourly_tbl, ignore_index=True)
    daily_tbl  = pd.concat(daily_tbl,  ignore_index=True)

    clean_data = clean_data.merge(hourly_tbl, on=["city", "parameter", "utc_datetime"], how="left")
    clean_data = clean_data.merge(daily_tbl, on=["city", "parameter", "day"], how="left")

    
    print("Done!")
    return clean_data

def Save_Clean(clean_data):
    print("Saving clean dataframe...")
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    clean_data.to_csv("data/processed/clean.csv", index=False)
    print("Done!")