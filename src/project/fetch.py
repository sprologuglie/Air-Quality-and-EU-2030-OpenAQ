from openaq import OpenAQ
from openaq.shared.exceptions import ServerError, ApiKeyMissingError, RateLimitError, TimeoutError, GatewayTimeoutError
import pandas as pd
from math import ceil
from geopy.geocoders import Nominatim
import yaml
from time import sleep
from pathlib import Path
import os
from dotenv import load_dotenv
import httpx


with open("config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

load_dotenv()
API_KEY = os.environ["API_KEY"]
client = OpenAQ(api_key = API_KEY)

def Coordinates(locations): # First we retieve the coordinates for our locations
    coordinates = []                                                                    # Coordinates list

    for l in locations:
        print(f"Fetching coordinates of {l}")
        geolocator = Nominatim(user_agent="Air_quality_and_EU_tresholds")                       # Using Nominatim API
        location = geolocator.geocode(l, language='it')                                 # Fetching geolocation data
        coordinates.append((location.latitude, location.longitude, l))                  # Append to coordinates list
        print(f"The coordinates of {l} are {location.latitude}, {location.longitude}")
        sleep(1)

    return coordinates

def Get_Sensors(coordinates):
    
    sensors = []
    sensors_data = []                                                                           # Empty list to appens sensors info

    for lat, long, loc in coordinates:
        try:
            response = client.locations.list(coordinates=(lat, long), radius=config["openaq"]["radius"], limit=100, mobile=config["openaq"]["mobile"], monitor=config["openaq"]["monitor"]) # Search for stations in a radius from the coordinates
            data = response.dict()                                                             # Convert results in a dict
            sensors_df = pd.json_normalize(data['results'])                                    # Create a df with stations
            if sensors_df.empty:
                print(f"No sensors found in {loc}")
                continue
            sensors_data.append(sensors_df)
            sleep(1)
        except ApiKeyMissingError:
            print("Please load a valid API key")
            raise    

        for r in sensors_df.index:                                                  # For every row in the stations df
            df = pd.DataFrame(sensors_df.iloc[r]['sensors'])                        # Create a df with sensors for every istrument
            station_name = sensors_df.iloc[r]['name']                               # Store the name of the station
            for index in df.index:                                                  # For each row in the sensors df (every sensor in the station)
                sensor_parameter = df.iloc[index]['name']                           # Store the parameter
                if sensor_parameter in config["parameters"]:                        # If the parameter is one of the four
                    sensor_id = int(df.iloc[index]['id'])                               # Store the ID
                    sensors.append((station_name, sensor_id, sensor_parameter, loc))    # Sore everything in a tuple and append to the list
                    print(f"Sensor found for City: {loc}, Station name: {station_name}, Parameter: {sensor_parameter}, ID: {sensor_id}")
    
    sensors_complete = pd.concat(sensors_data, ignore_index=True)
    Path("data/raw").mkdir(parents=True, exist_ok=True) 
    sensors_complete.to_csv("data/raw/sensors.csv", index=False)
    return sensors


def Get_Data(sensors):

    dfs_list = []                                                                                   # Data frames list
    failed = []
    empty = []

    for n, i, p, c in sensors:
        for year in range(config["yearfrom"], config["yearto"] + 1):    
            # Count call
            response = client.measurements.list(sensors_id=i, datetime_from=f"{year}-01-01", datetime_to=f"{year + 1}-01-01", limit=1, rollup="hourly")
            client.transport.client.timeout = httpx.Timeout(30.0, connect=10.0, read=30.0, write=30.0, pool=30.0)
            data = response.dict()                                                                      # Convert response to dictionary
            found = data["meta"]["found"]                                                               # Accessing the number of results found
            sleep(1)
            if not isinstance(found, int):                                                              # Ensuring the number of results is an int
                raise ValueError(f"found non è un int: {found}")

            if found == 0:
                print(f"No data avaiable for sensor {n}, year {year} and parameter {p}")                             
            
            else:
                pages = ceil(found / 1000)                                                                  # Calculating the number of pages needed
                print(f"{found} measurements found for sensor {n}, year {year} and parameter {p}. Fetching data...")

                dfs_list2 = []
                # Fetch daily data for each sensor id for the correct number of pages
                for page in range(1, pages + 1):
                    try:    
                        response = client.measurements.list(sensors_id=i, datetime_from=f"{year}-01-01", datetime_to=f"{year + 1}-01-01", limit=1000, rollup="hourly", page=page)
                        data = response.dict()
                        df_data = pd.json_normalize(data['results'])
                        n_rows = len(df_data.index)
                        print(f"Page {page}: {n_rows} rows")

                        if n_rows == 0:
                            print(f"Page {page} empty, stopping pagination for this chunk.")
                            break

                        else:
                            dfs_list2.append(df_data)
                            print(f"Page {page} retrieved")
                            sleep(1)
                    
                    except ServerError:
                        failed_page = (n, i, p, c, year, page)
                        print("Failed call for:", failed_page, "Server Error")
                        failed.append(failed_page)
                        continue

                    except (TimeoutError, GatewayTimeoutError, httpx.TimeoutException):
                        failed_page = (n, i, p, c, year, page)
                        print("Failed call for:", failed_page, "Timeout Error")
                        failed.append(failed_page)
                        continue

                    except RateLimitError:
                        failed_page = (n, i, p, c, year, page)
                        print("Failed call for:", failed_page, "Rate Limit Error: Waiting...")
                        failed.append(failed_page)
                        sleep(10)
                        continue
                        
                if not dfs_list2:
                    empty_data = f"No data collected for sensor {n}, year {year}, parameter {p}"
                    print(empty_data)
                    empty.append(empty_data)
                    continue

                df = pd.concat(dfs_list2, ignore_index=True)
                df['sensor_id'] = i                                                                         # Adding sensor ID, name, city and parameter to the measurements
                df['station_name'] = n
                df['city'] = c
                df['parameter'] = p
                dfs_list.append(df)
                print(f"Fetching data for sensor {n}, year {year} and parameter {p} done!")

            
    complete_df = pd.concat(dfs_list, ignore_index=True)

    return complete_df, failed

def Retry_Failed(failed):
    print("Retrying failed calls...")

    dfs_list = []
    failed_list = []
    max_attempts = config["openaq"]["max_attempts"]
    
    for n, i, p, c, year, page in failed:
        for attempt in range(max_attempts + 1):
            delay = 1
            try:
                print("Attempt", attempt + 1)
                response = client.measurements.list(sensors_id=i, datetime_from=f"{year}-01-01", datetime_to=f"{year + 1}-01-01", limit=1000, rollup="hourly", page=page)
                data = response.dict()
                df_data = pd.json_normalize(data['results'])
                n_rows = len(df_data.index)
                print(f"Page {page}: {n_rows} rows")

                if n_rows == 0:
                    print(f"Page {page} empty, stopping pagination for this chunk.")
                    break

                else:
                    df_data['sensor_id'] = i                                                                         # Adding sensor ID, name, city and parameter to the measurements
                    df_data['station_name'] = n
                    df_data['city'] = c
                    df_data['parameter'] = p
                    dfs_list.append(df_data)
                    print(f"Page {page} retrieved")
                    sleep(1)

                break 
            
            except ServerError:
                if attempt == max_attempts:
                    print("Failed")
                    failed = f"Failed for sensor {n}, year {year}, parameter {p}, page {page}"                   
                    failed_list.append(failed)
                else:
                    print("Server Error: Retrying...")
                    delay *= 2
                    sleep(delay)
                continue

            except TimeoutError:
                if attempt == max_attempts:
                    print("Failed")
                    failed = f"Failed for sensor {n}, year {year}, parameter {p}, page {page}"                   
                    failed_list.append(failed)
                else:
                    print("Timeout Error: Retrying...")
                    delay *= 2
                    sleep(delay)
                continue

            except RateLimitError:
                if attempt == max_attempts:
                    print("Failed")
                    failed = f"Failed for sensor {n}, year {year}, parameter {p}, page {page}"                   
                    failed_list.append(failed)
                else:
                    print("Rate Limit Error: Waiting...")
                    delay *= 2
                    sleep(delay)
                continue
    
    if not dfs_list:
        print(f"No results collected for sensor {n}, year {year}, parameter {p}")
        df = pd.DataFrame()

    else:
        df = pd.concat(dfs_list, ignore_index=True)

    print("Done!")
    return df, failed_list



def Save_Raw(df, failed_list):
    print("Saving raw data...")
    Path("data/raw").mkdir(parents=True, exist_ok=True)                                                 # Making data/raw directory
    df.to_csv("data/raw/raw_data.csv", index=False)                                                                  # Saving hte raw data Dataframe in csv
    if failed_list:
        failed_df = pd.DataFrame(failed_list)
        failed_df.to_csv("data/raw/failed.csv", index=False)
    print("Done!")

def Close_OpenAQ_Client():  
    client.close()                                                                                      # Closig contact with OpenAQ API