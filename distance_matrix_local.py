# -*- coding: utf-8 -*-
"""Distance_matrix_local

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/13Dus37BybD28ac4BNue4hN9UyFcaRXMu
"""

import pandas as pd
import requests
import math

# 1) Read input data
file_path = 'C:/Users/daane/Downloads/Re_ project OBP/mini.csv'
data = pd.read_csv(file_path)

locations = []
for i, row in data.iterrows():
    loc = {
        'lon': row['lon'],
        'lat': row['lat'],
        'name': row['name'],
        'unique_name': f"{row['name']}_{i}"
    }
    locations.append(loc)

# Add the UNIVERSAL_DEPOT location
UNIVERSAL_DEPOT = (52.0, 5.0)
locations.append({
    'lon': UNIVERSAL_DEPOT[1],
    'lat': UNIVERSAL_DEPOT[0],
    'name': 'Universal Depot',
    'unique_name': 'Universal_Depot'
})

def get_osrm_distance_submatrix(
    src_batch, dst_batch,
    base_url="http://localhost:5000",
    profile="driving"
):
    """
    Send a table request to OSRM to get the distances between
    src_batch (sources) and dst_batch (destinations).
    Returns a 2D list (or None on error).
    """

    # Combine both source and destination coordinates into one list
    combined = src_batch + dst_batch
    # Build the coordinate string: lon,lat;lon,lat;...
    coords_str = ";".join(f"{loc['lon']},{loc['lat']}" for loc in combined)

    # OSRM indices:
    #   - sources = 0..(len(src_batch)-1)
    #   - destinations = len(src_batch)..(len(src_batch)+len(dst_batch)-1)
    src_indices = list(range(0, len(src_batch)))
    dst_indices = list(range(len(src_batch), len(src_batch) + len(dst_batch)))

    # Construct request
    url = f"{base_url}/table/v1/{profile}/{coords_str}"
    params = {
        "annotations": "distance",
        "sources": ";".join(map(str, src_indices)),
        "destinations": ";".join(map(str, dst_indices))
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Distances is a list of lists with dimension:
        #   len(sources) x len(destinations)
        if "distances" in data:
            return data["distances"]
        else:
            print("No distances found in OSRM response.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error with OSRM request: {e}")
        return None


def create_batched_distance_matrix(locations, batch_size=100):
    """
    Splits 'locations' into smaller sub-batches, then for each pair of
    (source_batch, destination_batch), calls OSRM to fill in the submatrix.
    Returns a complete distance matrix in a DataFrame with no NaN values.
    """
    num_locations = len(locations)
    # All unique names in order
    all_unique_names = [loc['unique_name'] for loc in locations]

    # Prepare empty DataFrame
    full_matrix = pd.DataFrame(
        data=float("nan"),
        index=all_unique_names,
        columns=all_unique_names
    )

    # Outer loop over source batches
    for i in range(0, num_locations, batch_size):
        src_batch = locations[i : i + batch_size]
        src_unique_names = [loc['unique_name'] for loc in src_batch]

        # Inner loop over destination batches
        for j in range(0, num_locations, batch_size):
            dst_batch = locations[j : j + batch_size]
            dst_unique_names = [loc['unique_name'] for loc in dst_batch]

            # Request submatrix from OSRM
            distances = get_osrm_distance_submatrix(src_batch, dst_batch)
            if distances is not None:
                # "distances" is len(src_batch) x len(dst_batch)
                sub_df = pd.DataFrame(
                    data=distances,
                    index=src_unique_names,
                    columns=dst_unique_names
                )
                # Update the corresponding block of the full matrix
                full_matrix.loc[src_unique_names, dst_unique_names] = sub_df

    return full_matrix

# 4) Retrieve and save the many-to-many distance matrix
distance_df = create_batched_distance_matrix(locations, batch_size=100)

# Save the distance matrix to a CSV file (optional)
output_path = 'distance_matrix_with_depot.csv'
distance_df.to_csv(output_path)
print(f"Distance matrix saved to {output_path}")