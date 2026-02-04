# Methodology

## 1. Data sources
- Coordinates (Nominatim and Geopy)
  Coordinates (used to search for sensors) for each city were retrived from Nominatim (https://nominatim.org/), an open source geocoding service based on OpenStreetMap (https://www.openstreetmap.org/). The API calls were made through the geopy client service (https://geopy.readthedocs.io/en/stable/)

- Air quality measurements (OpenAQ)
  All the air quality data used comes from OpenAQ, which is a nonprofit organization providing access to air quality data. Such data were retrived using the OpenAQ python SDK (https://python.openaq.org/) which offers a dedicated client library.

## 2. Study design
- Cities and time window
  For the main analysis six italian cities were chosen: Turin, Milan, Florence, Rome, Naples and Palermo. They were chosen for being among the most populated italian cities and for being geographically spread across almost all the italian territory, spanning from north to south, thus being representative of different geographical and social peculiarities within the country
- Pollutants (NO₂, O₃, PM₁₀, PM₂.₅)
  Four pollutants were chosen for these analysis: NO2, O3, PM10 and PM2.5. They were chosen for they are among the most measured and policy relevant. Future developements may include all the regulated pollutants
- Why these pollutants are policy-relevant
  Their monitoring is crucial for two main reasons:
  1. Public Health Impact:
  - Particulate Matter (PM10 and PM2.5): These particles can penetrate deep into the lungs and even enter the bloodstream, causing respiratory and cardiovascular diseases. Reducing their concentration is a primary target for public health policies to reduce premature mortality.
  - Nitrogen Dioxide (NO2): A toxic gas primarily emitted by road transport (diesel engines). It is a major trigger for asthma and reduced lung function in children.
  - Ozone (O3): Unlike others, it is a secondary pollutant formed by chemical reactions. It is a powerful oxidant that causes respiratory distress and is a significant focus for summer smog alerts.
  2. Monitoring these pollutants helps evaluate the effectiveness of "green" transitions. For example, No2 levels are a direct proxy for the success of electric mobility transitions, while Ozone levels are closely linked to rising global temperatures and climate change. Moreover, these pollutants affects vegetation and animals life along with humans.

## 3. Data retrieval

- City geocoding
  - Each city name is geocoded to latitude/longitude using Nominatim (OpenStreetMap).  
  - Coordinates are used to query OpenAQ “locations” within a radius (`config.yml["openaq"]["radius"]`).

- Station/sensor discovery
  - For each OpenAQ location found, the pipeline inspects available sensors and keeps only those whose `sensor_parameter` is in `config.yml["parameters"]`.
  - The discovered stations are saved to `data/raw/sensors.csv`

- Measurement download
  - For each sensor and each year in the configured range, the pipeline downloads measurements from OpenAQ using hourly rollups (`rollup="hourly"`), paginating if needed.
  - Raw measurements are saved to `data/raw/raw_data.csv`
  - Failures (timeouts, rate limits, server errors) are recorded in `data/raw/failed.csv` (if any)
  - Failed queries are attempted again, for a number of attempts specified in `config.yml["openaq"]["max_attempts"]`


## 4. Data cleaning
- Timestamp normalization
  - The datetime provided for each measurement is parsed as UTC and converted to datetime format
  - `local_datetime` is derived using timezone conversion to Europe/Rome

- Basic cleaning rules
  - drop duplicates
  - drop rows with missing value or timestamp
  - remove negative values
  - remove extreme values above a hard cap (see `config.yml` "implausible_value_caps")

- Feature creation
  From `local_datetime` the pipeline adds some time-related variables: (day, day of the week, season, year)
 


## 5. Data quality rules
- Definition of a **"valid day"**
  - Valid days are computed separately for each sensor. A valid day is covered for at least 50% for a given sensor. Invalid days are excluded from all analyses. This parameter are in `config.yml` under "percent_coverage_valid_day".
- Definition of a **“valid sensor”**
  - A valid sensor has: at least 30% mean daily coverage and at least 60% mean yearly coverage. Invalid sensors are excluded. These parameters are in `config.yml` under "percent_daily_coverage_valid_sensor" and "percent_coverage_valid_sensor" respectively.
- Definition of cities' **“flag”**
  - Each city, year, parameter is flagged with a quality based criterium.
  - Confidence labels (High/Medium/Low/Very Low):
**High**     -->     >= 80 days avaiable     --AND--     >= 3 median active sensors per day <br>
**Medium**   -->     >= 70 days avaiable     --AND--     >= 2 median active sensors per day <br>
**Low**      -->     >= 60 days avaiable     --AND--     >= 2 median active sensors per day <br>
**Very Low** -->     <  60 days avaiable     ---OR--      < 2 median active sensors per day <br>
  Such values are in `config.yml` under "sensors_active_per_day_high_flag", "percent_days_avaiable_high_flag", "sensors_active_per_day_medium_flag",  "percent_days_avaiable_medium_flag", "sensors_active_per_day_low_flag" and  "percent_days_avaiable_low_flag"

## 6. Aggregation strategy
For each pollutant, after cleaning and quality checks, the pipeline computes several daily and seasonal aggregates, stored as columns in the processed dataframe. The pipeline computes
  - Daily aggregation:
    - `day_mean_value_per_station` → daily mean per station
    - `day_mean_value` → city-day mean (mean across stations’ daily means)
    - `day_median_value_per_station` → daily median per station
    - `day_median_value` → city-day median (median across stations’ daily medians)
    - `day_max_value_per_station` → daily max value per station
    - `day_max_value` → daily max across stations
  - Other aggregations:
    - `mean_value_per_season`
    - `mean_value_per_year`
  - O3 rolling 8-hour mean and MDA8:
    - For each (city, parameter), the pipeline computes:
      - `rolling_8h_mean` (rolling 8-hour mean on hourly median series)
      - `mda8` (maximum daily 8-hour mean)
    - A DST-aware validity rule is applied: a day is valid for MDA8 if at least 75% of the hours in that day have valid rolling values.

## 7. Indicators and policy metrics
- Annual mean
  - From sensors hourly → sensors daily → daily → yearly
    - Measurements were aggregated starting from hourly values retrieved through the OpenAQ API. First, sensors data were aggregated forming a daily mean for each sensor. Then, sensors daily aggregate were averaged to get a daily mean. Finally, daily measures were again averaged to get a yearly average.
  - Rationale and known biases
    - The choice of using mean values were done to be consistent with european indications. Moreover, using the median daily value (computed by doing the median daily value for each station and taking the median value again) seem to be not significantly different for yearly means (see `notebooks/turin_deep_dive.ipynb`). 
    - There are some known biases in using this method which does not account for population exposure, for episodic peaks, for city areas differences, traffic/background differences and more. Nonetheless, it was chosen as appropiate for the objective

- Exceedance days
  Excedance days are simply the number of days for which the daily mean (or MDA8 for O3) is > than the corresponding threshold

- There are many limitations in this assessment of compliance (see ##12. Limitations and ethical notes)

## 8. Threshold sets

- EU current thresholds (with averaging period definitions)
  The current thresholds were defined following the indications at https://environment.ec.europa.eu/topics/air/air-quality/eu-air-quality-standards_en (such tresholds were imposed over the course of several years of European legislation). Since daily limits remained almost unchanged (O3 remained unchanged, PM2.5 are unchanged relative to stage 1, while PM10 was 50 µg/m³ for stage 1 and 40 µg/m³ for stage 2, while now the limt is 45 µg/m³) <br>
  The relevant values for annual mean limits are stored in `config.yml`:
  "current_standards_year" refer to the annual mean limit value (PM2.5 = 25, PM10 = 40, NO2 = 40) <br>

- EU 2030 targets (with definitions)
  EU 2030 targets were defined following the Directive (EU) 2024/2881 of the European Parliament and of the Council of 23 October 2024 on ambient air quality and cleaner air for Europe (target values are specified in annex I: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ:L_202402881#anx_I). <br>
  They have been sotred in `config.yml` as follows:
  "new_standards_year" refer to the annual mean limit values indicated (PM2.5 = 10, PM10 = 20, NO2 = 20)
  "new_standards_day" refer to the maxium daily values (PM2.5 = 25, PM10 = 45, NO2 = 50, O3 = 120)


## 9. CAQI
- Mapping from pollutant metrics to CAQI categories
   - CAQI breakpoint were taken from this study: https://web.archive.org/web/20160222064802/http://www.airqualitynow.eu/download/CITEAIR-Comparing_Urban_Air_Quality_across_Borders.pdf
   Coherently with the study, the daily max value was used for NO2 and O3, while the daily mean value for PM10 and PM2.5
- Assumptions and caveats
  - Naturally, data are completely insufficient for a robust assessment of general air quality. In the supplementary reports the CAQI was nonetheless included as an exploration for comparing general air quality (across parameters) between cities.

## 10. Outputs
- Output folders:
  data/
    descriptive/
    processed/
    raw/
  results/
    plots/
      CAQI/
      density_plots/
      main/
      seasonal_trends/
    quality_checks/
      deepdive/
      figures/

- Produced tables:
  - data/raw/
    - **Raw Data** --> Collections of raw measurements data ->  `data/raw/raw_data.csv`
    - **Failed** --> Collection of pages for which Errors happened and measurements were not collected -> `data/raw/failed.csv`
    - **Sensors** --> Dataset of sensors found by the OpenAQ API -> `data/raw/sensors.csv`

  - data/processed/
    - **Clean Data** --> Dataset of hourly measurements after the cleaning process -> `data/processed/clean.csv`
    - **Daily Data** --> Dataset for daily aggregates after cleaning -> `data/processed/daily_data.csv`

  - data/descriptive/
    - **Pre Cleaning Descriptive** --> Descriptive statistics of raw measurements data for each sensor -> `data/descriptive/pre_cleaning_descriptive.csv`
    - **Processed Descriptive** --> Descriptive statistics of measurements data after cleaning for each sensor -> `data/descriptive/pre_cleaning_descriptive.csv`
    - **Sensors Metadata** --> Polished dataset with used sensors metadata -> `data/descriptive/sensors_metadata.csv`

  - results/quality_checks
    - **Cities Quality** --> Dataframe containing quality assessment of each city, parameter, year ->  `results/quality_chekcs/cities_quality.csv`
    - **Sensors Quality** --> Dataframe containing quality assessment of each sensor, parameter, year ->  `results/quality_chekcs/sensors_quality.csv`

  - results/quality_checks/deepdive
    - **Torino Aggregation** --> Dataframe confronting different aggregation methods for calculating annual aggregates for the city of Turin -> `results/quality_chekcs/deepdive/Torino_aggregation.csv`
    - **Torino Annual Mean Per Sensor** --> Dataframe containing annual mean aggregates for each sensor in Turin -> `results/quality_chekcs/deepdive/Torino_annual_mean_per_station_descriptive.csv`
    - **Torino Exceedance Days Per Sensor** --> Dataframe calculating exceedance days for each sensor in Turin -> `results/quality_chekcs/deepdive/Torino_exceedance_days_per_station_descriptive.csv`

  - results/
    - **Compliance table** --> Table which compare annual averages and exeedance days with EU cuurent standards and 2030 targets -> `results/compliance_table.csv`

- Produced figures:
  results/
    plots/
      CAQI/
        - CAQI_per_parameter/ 
          - `CAQI_*.png` --> Collection of daily CAQI plots for each parameter separately
        - `CAQI_global.png` --> Daily global CAQI for each city
        - `count_CAQI.png` --> Count plot for each CAQI category per city
      density_plots/ 
        - `daily_averages_densityplot_*.png` --> Collection of desity plots for each city, divided per parameter
      main/
        - `compliance_days_*.png` --> Plots with exceedance days for each city, divided per parameter
        - `trends_annual_*.png` --> Plots with annual means for each city, divided per parameter
        - `daily_averages_boxplot.png` --> Boxplot with distribution of daily averages for each city and parameter
      seasonal_trends/ 
        - `seasonal_trends_*.png` --> Collection of seasonal average values for each city, divided per parameter
    quality_checks/
      deepdive/
        - `Torino_active_sensors_per_day.png` --> Lineplot for active sensors in Torino for each day and parameter
        - `Torino_percent_days_avaiable_per_year.png` --> Barplot with percent days avaiable for each year
        - `Torino_sensors_percent_coverage_per_day.png` --> ECDF for percent coverage of Torino's sensors for each year and parameter
        - `Torino_sensors_percent_coverage_per_year.png` --> Barplot for percent coverage of Torino's sensors for each year and parameter
      figures/
        -`days_avaiable_heatmap.png` --> heatmap of percent days avaiable for each city, year and parameter
        - `median_active_sensors_heatmap.png` --> heatmap of median active sensors for each city, year and parameter


## 11. Reproducibility
- Configuration (config.yml) parameters:
  pipeline -> include option to run only certain steps
    retry_failed -> select if retry for failed pages
    do_fetch -> select if fetch data
    do_clean -> select if doing cleaning and aggregation
    do_results -> select if producing results

  locations -> list of cities to be queried

  parameters -> list of paramteres

  yearfrom -> from which year retrieve measurements
  yearto -> until which year retrieve measurements

  openaq -> select certain parameters for the OpenAQ query
    mobile -> select if quering mobile sensors
    monitor -> select if quering monitors
    radius -> the radius of the circumference from the coordinates from wich searching sensors
    max_attempts -> the number of max retries for failed queries

  implausible_value_caps -> values from which the collected measurements is considered invalid

  flags -> parameters for quality filtering
    sensors_active_per_day_high_flag -> number of median active sensors per day for the high quality flag
    percent_days_avaiable_high_flag -> percent of days avaiable in a year for the high quality flags
    sensors_active_per_day_medium_flag -> number of median active sensors per day for the medium quality flag
    percent_days_avaiable_medium_flag -> percent of days avaiable in a year for the medium quality flags
    percent_coverage_valid_sensor -> mean percent yearly coverage for valid sensors
    percent_daily_coverage_valid_sensor -> mean percent daily coverage for valid sensors
    exclude_invalid_sensors -> selects whether to exclude invalid sensors
    percent_coverage_valid_day -> percent of hours avaiable in a day to be valid
    exclude_invalid_days -> selects whether to exclude invalid days

  new_standards_year -> EU 2030 targets for annual means

  current_standards_year -> EU current standards for annual means

  new_standards_day -> EU 2030 targets for daily maximums

  CAQI_breakpoints -> CAQI breakpoints for each parameter


  quality_deep_locations -> list of cities to perform quality checks

- Determinism: what depends on API availability
  - Data depends on API availability, thus the results obtained by running the pipeline may not be exacltly the same

- Recommended run steps
  **Pipeline stages:**
  1. `fetch_data()` → `data/raw/`
  2. `clean_data()` → `data/processed/` + `data/quality_checks/`
  3. `get_results()` → `results/`

  Run via `pipeline.py` (see README for details).

## 12. Limitations and ethical notes

- Coverage varies across cities, pollutants, and years; quality flags should be used to qualify interpretations.
- Some completeness calculations assume 365 days and 24 hours; leap years and DST can slightly affect percentages.
- Threshold-based labels are only as correct as the threshold definitions implemented in the repository.
- EU quality standards for assessing policy compliance are much more rigid than what this anaysis can implement. Therefore, results have to be taken as exploratory rather than evaluative