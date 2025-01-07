import pandas as pd
import requests
from itertools import combinations

def get_osrm_distance(coord1, coord2, profile='driving'):
    base_url = "http://router.project-osrm.org/route/v1"
    coords = f"{coord1[1]},{coord1[0]};{coord2[1]},{coord2[0]}"
    url = f"{base_url}/{profile}/{coords}"
    
    try:
        response = requests.get(url, params={"overview": "false"})
        response.raise_for_status()
        data = response.json()
        distance = data['routes'][0]['distance']  # Distance in meters
        return distance
    except requests.exceptions.RequestException as e:
        print(f"Error fetching OSRM data: {e}")
        return None

def calculate_distances_from_csv(file_path):
    data = pd.read_csv(file_path)
    locations = list(zip(data['lat'], data['lon']))
    location_names = data['name'].tolist()
    pairs = list(combinations(enumerate(locations), 2))
    
    results = []
    for (idx1, coord1), (idx2, coord2) in pairs:
        distance = get_osrm_distance(coord1, coord2)
        results.append({
            'Location1': location_names[idx1],
            'Location2': location_names[idx2],
            'Distance (meters)': distance
        })
    
    return pd.DataFrame(results)

# Example usage
file_path = 'data_file.csv'  # Reference the CSV file uploaded to GitHub
distance_df = calculate_distances_from_csv(file_path)
print(distance_df)

