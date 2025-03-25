import pandas as pd
from geopy.geocoders import Nominatim
import time

# Initialize the geolocator with a specific user agent for Afghanistan
geolocator = Nominatim(user_agent="afghanistan_geoapi")

def add_location_columns(df, geo_column, retries=3, delay=2):
    provinces = []
    districts = []
    villages = []
    
    for index, row in df.iterrows():
        if isinstance(row[geo_column], str) and pd.notnull(row[geo_column]):
            try:
                parts = row[geo_column].split()
                if len(parts) >= 2:  
                    lat_str, lon_str = parts[0], parts[1]
                    lat, lon = map(float, [lat_str, lon_str])
                    print(f"Processing coordinates: Latitude {lat}, Longitude {lon}")
                    
                    for attempt in range(retries):
                        try:
                            location = geolocator.reverse((lat, lon), exactly_one=True)
                            if location is not None:
                                address = location.raw.get('address', {})
                                province = address.get('state', 'Unknown')
                                district = address.get('county', 'Unknown')
                                village = address.get('town', address.get('village', 'Unknown'))
                            else:
                                province, district, village = 'Unknown', 'Unknown', 'Unknown'
                            break  
                        except Exception as e:
                            print(f"Error for index {index}, attempt {attempt + 1}: {e}")
                            if attempt < retries - 1:
                                time.sleep(delay)  
                    else:
                        province, district, village = 'Error', 'Error', 'Error'
                else:
                    print(f"Invalid GPS data for index {index}: {row[geo_column]}")
                    province, district, village = 'Invalid Data', 'Invalid Data', 'Invalid Data'
            except ValueError as ve:
                print(f"Error processing GPS data for index {index}: {ve}")
                province, district, village = 'Error', 'Error', 'Error'
            except Exception as e:
                print(f"Unexpected error for index {index}: {e}")
                province, district, village = 'Error', 'Error', 'Error'
        else:
            print(f"No valid geolocation data for index {index}: {row[geo_column]}")
            province, district, village = 'No Data', 'No Data', 'No Data'
        
        provinces.append(province)
        districts.append(district)
        villages.append(village)
    
    df['Province'] = provinces
    df['District'] = districts
    df['Village'] = villages
    
    return df
