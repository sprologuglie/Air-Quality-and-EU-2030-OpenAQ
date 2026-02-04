import pandas as pd
import yaml
from .fetch import Coordinates, Get_Sensors, Get_Data, Save_Raw, Retry_Failed, Close_OpenAQ_Client
from .processing import Clean, Time_Aggregation, Quality_Checks, Quality_Plots_heatmaps, Calculate_Average_Values, Save_Clean
from .results import Cutting_Hourly_Values, Make_Compliance_Table, Make_Plots, Quality_Plots_deepdive, Deep_Dive_table

with open("config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

locations = config["locations"]

def fetch_data(retry_failed = config["pipeline"]["retry_failed"]):
    print(f"Fetching data for {locations} begin")

    coordinates = Coordinates(locations=locations)
    sensors = Get_Sensors(coordinates=coordinates)
    raw_data, failed = Get_Data(sensors=sensors)
    Save_Raw(raw_data, failed)

    if failed and retry_failed:
        df, failed_list = Retry_Failed(failed=failed)
        if not df.empty:
            raw_data = pd.concat([raw_data, df], ignore_index=True)
        Save_Raw(raw_data, failed_list)
    
    Close_OpenAQ_Client()
    

def clean_data():
    print("Start cleaning...")
    df = Clean()
    df = Time_Aggregation(df)
    df = Quality_Checks(df)
    Quality_Plots_heatmaps()
    df = Calculate_Average_Values(df)
    Save_Clean(df)

def get_results():
    print("Processing results...")
    Cutting_Hourly_Values()
    Make_Compliance_Table()
    Make_Plots()
    Quality_Plots_deepdive()
    Deep_Dive_table()
    print("Pipeline finished")

def run_pipeline(do_fetch=config["pipeline"]["do_fetch"], do_clean=config["pipeline"]["do_clean"], do_results=config["pipeline"]["do_results"]):
    if do_fetch:
        fetch_data()
    if do_clean:
        clean_data()
    if do_results:
        get_results()


if __name__ == "__main__":
    run_pipeline()
