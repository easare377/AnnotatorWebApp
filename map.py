# import math
# import requests
# import os


# def lat_lon_to_tile_coords(lat, lon, zoom):
#     """
#     Convert latitude and longitude to tile x, y coordinates.
#     """
#     x_tile = int((lon + 180) / 360 * (2**zoom))
#     y_tile = int(
#         (
#             1
#             - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat)))
#             / math.pi
#         )
#         / 2
#         * (2**zoom)
#     )
#     return x_tile, y_tile


# def download_tile(zoom, x, y, save_path="tiles"):
#     """
#     Download a single tile image from OpenStreetMap.
#     """
#     url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
#     response = requests.get(url)

#     if response.status_code == 200:
#         # Ensure the directory exists
#         os.makedirs(save_path, exist_ok=True)

#         # Save the image file
#         tile_path = f"{save_path}/{zoom}_{x}_{y}.png"
#         with open(tile_path, "wb") as f:
#             f.write(response.content)
#         print(f"Downloaded tile at zoom {zoom}, x {x}, y {y}")
#     else:
#         print(
#             f"Failed to download tile at zoom {zoom}, x {x}, y {y}: {response.status_code}"
#         )


# def download_tiles_for_area(lat, lon, zoom, radius=1, save_path="tiles"):
#     """
#     Download tiles in a specified radius around a given latitude, longitude, and zoom level.
#     """
#     # Convert center lat/lon to tile coordinates
#     x_center, y_center = lat_lon_to_tile_coords(lat, lon, zoom)

#     # Download tiles in a square area around the center tile
#     for x in range(x_center - radius, x_center + radius + 1):
#         for y in range(y_center - radius, y_center + radius + 1):
#             download_tile(zoom, x, y, save_path)


# # Example Usage
# zoom = 12  # Zoom level
# latitude = 37.7749  # Latitude for San Francisco
# longitude = -122.4194  # Longitude for San Francisco
# radius = 1  # Number of tiles around the center tile to download

# download_tiles_for_area(latitude, longitude, zoom, radius)


# import os
# import math
# import requests

# # Define separate dictionaries for each map source
# google_satellite = {
#     "name": "Google_Satellite",
#     "url": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
#     "zmax": 20,
# }

# google_terrain = {
#     "name": "Google_Terrain",
#     "url": "https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
#     "zmax": 20,
# }

# esri_satellite = {
#     "name": "ESRI_Satellite",
#     "url": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
#     "zmax": 20,
# }

# osm_map = {
#     "name": "OSM_Map",
#     "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
#     "zmax": 20,
# }

# # Define headers to mimic a browser request
# headers = {
#     "User-Agent": "Mozilla/5.0",
#     "accept": "image/webp,image/apng,*/*;q=0.8",
#     "accept-encoding": "gzip, deflate",
# }


# def get_tile_xy(lat, lon, zoom):
#     """
#     Converts latitude and longitude to tile x and y coordinates.
#     """
#     tile_size = 256
#     sin_lat = math.sin(lat * math.pi / 180)
#     pixel_x = ((lon + 180) / 360) * tile_size * math.pow(2, zoom)
#     pixel_y = (
#         (0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi))
#         * tile_size
#         * math.pow(2, zoom)
#     )
#     tile_x = int(pixel_x // tile_size)
#     tile_y = int(pixel_y // tile_size)
#     return tile_x, tile_y


# def fetch_and_save_tile(lat, lon, zoom, source):
#     """
#     Fetches and saves the tile image for given latitude, longitude, and zoom level.
#     :param lat: Latitude of the target location.
#     :param lon: Longitude of the target location.
#     :param zoom: Zoom level for the map tile.
#     :param source: Map source dictionary (e.g., google_satellite).
#     """
#     if zoom > source["zmax"]:
#         raise ValueError(
#             f"Zoom level exceeds maximum for {source['name']} (Max: {source['zmax']})"
#         )

#     # Get the tile coordinates for the given latitude, longitude, and zoom
#     tile_x, tile_y = get_tile_xy(lat, lon, zoom)

#     # Generate the full URL for the tile
#     tile_url = source["url"].format(x=tile_x, y=tile_y, z=zoom)
#     print(f"Fetching tile from URL: {tile_url}")

#     # Create directory for the source if it doesn't exist
#     folder_name = source["name"]
#     if not os.path.exists(folder_name):
#         os.makedirs(folder_name)

#     # Set the filename and path to save the tile
#     filename = f"{folder_name}/tile_{zoom}_{tile_x}_{tile_y}.jpeg"

#     # Download the tile image
#     response = requests.get(tile_url, headers=headers)
#     if response.status_code == 200:
#         with open(filename, "wb") as file:
#             file.write(response.content)
#         print(f"Tile image saved as {filename}")
#     else:
#         print(f"Failed to fetch tile: Status code {response.status_code}")


# # Example usage with different sources
# latitude = 11.014713
# longitude = -2.880310
# zoom_level = 12

# # Fetch and save a tile from Google Satellite in its own folder
# fetch_and_save_tile(latitude, longitude, zoom_level, google_satellite)

# # Fetch and save a tile from Google Terrain in its own folder
# fetch_and_save_tile(latitude, longitude, zoom_level, google_terrain)

# # Fetch and save a tile from ESRI Satellite in its own folder
# fetch_and_save_tile(latitude, longitude, zoom_level, esri_satellite)

# # Fetch and save a tile from OSM Map in its own folder
# fetch_and_save_tile(latitude, longitude, zoom_level, osm_map)

# dict_sources = {
#     "Google BaseMap": {
#         "url": "https://mt1.google.com/vt/lyrs=m&x={0}&y={1}&z={2}",
#         "zmax": 21,
#     },
#     "Google Terrain": {
#         "url": "https://mt1.google.com/vt/lyrs=p&x={0}&y={1}&z={2}",
#         "zmax": 20,
#     },
#     "Google Traffic": {
#         "url": "https://mt1.google.com/vt?lyrs=h@159000000,traffic|seconds_into_week:-1&style=3&x={0}&y={1}&z={2}",
#         "zmax": 20,
#     },
#     "Google Satellite": {
#         "url": "https://mt1.google.com/vt/lyrs=s&x={0}&y={1}&z={2}",
#         "zmax": 20,
#     },
#     "Google Hybrid": {
#         "url": "https://mt1.google.com/vt/lyrs=y&x={0}&y={1}&z={2}",
#         "zmax": 20,
#     },
#     "ESRI BaseMap": {
#         "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{2}/{1}/{0}",
#         "zmax": 20,
#     },
#     "ESRI Terrain": {
#         "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{2}/{1}/{0}",
#         "zmax": 20,
#     },
#     "ESRI Satellite": {
#         "url": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{2}/{1}/{0}",
#         "zmax": 20,
#     },
#     "Yandex BaseMap": {
#         "url": "https://core-renderer-tiles.maps.yandex.net/tiles?l=map&v=21.07.13-0-b210701140430&x={0}&y={1}&z={2}&scale=1&lang=ru_RU",
#         "zmax": 21,
#     },
#     "Yandex Satellite": {
#         "url": "https://core-sat.maps.yandex.net/tiles?l=sat&v=3.1105.0&x={0}&y={1}&z={2}&scale=1.5&lang=ru_RU",
#         "zmax": 21,
#     },
#     "Bing BaseMap": {
#         "url": "https://t0.ssl.ak.dynamic.tiles.virtualearth.net/comp/ch/{0}?mkt=ru-RU&it=G,LC,BX,RL&shading=t&n=z&og=1852&cstl=vbp2&o=jpeg",
#         "zmax": 19,
#     },
#     "Bing Satellite": {
#         "url": "https://t1.ssl.ak.tiles.virtualearth.net/tiles/a{0}.jpeg?g=12225&n=z&prx=1",
#         "zmax": 18,
#     },
#     "Bing Hybrid": {
#         "url": "https://t1.ssl.ak.dynamic.tiles.virtualearth.net/comp/ch/{0}?mkt=ru-RU&it=A,G,RL&shading=t&n=z&og=1852&o=jpeg",
#         "zmax": 18,
#     },
#     "MapZen": {
#         "url": "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{2}/{0}/{1}.png",
#         "zmax": 18,
#     },
#     "OSM": {
#         "url": "https://tile.openstreetmap.org/{2}/{0}/{1}.png",
#         "zmax": 20,
#     },
# }


import os
import math
import requests

# Define the tile sources
dict_sources = {
    "Google Satellite": {
        "url": "https://mt1.google.com/vt/lyrs=s&x={0}&y={1}&z={2}",
        "zmax": 20,
    },
    "ESRI Satellite": {
        "url": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{2}/{1}/{0}",
        "zmax": 20,
    },
    "Yandex Satellite": {
        "url": "https://core-sat.maps.yandex.net/tiles?l=sat&v=3.1105.0&x={0}&y={1}&z={2}&scale=1.5&lang=ru_RU",
        "zmax": 21,
    },
    "Bing Satellite": {
        "url": "https://t1.ssl.ak.tiles.virtualearth.net/tiles/a{0}.jpeg?g=12225&n=z&prx=1",
        "zmax": 18,
    },
}

# Define headers to mimic a browser request
headers = {
    "User-Agent": "Mozilla/5.0",
    "accept": "image/webp,image/apng,*/*;q=0.8",
    "accept-encoding": "gzip, deflate",
}


def get_tile_xy(lat, lon, zoom):
    """
    Converts latitude and longitude to tile x and y coordinates.
    """
    tile_size = 256
    sin_lat = math.sin(lat * math.pi / 180)
    pixel_x = ((lon + 180) / 360) * tile_size * math.pow(2, zoom)
    pixel_y = (
        (0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi))
        * tile_size
        * math.pow(2, zoom)
    )
    tile_x = int(pixel_x // tile_size)
    tile_y = int(pixel_y // tile_size)
    return tile_x, tile_y


def fetch_and_save_all_tiles(lat, lon, zoom, folder="tiles"):
    """
    Fetches and saves tile images from all sources for the given latitude, longitude, and zoom level.
    :param lat: Latitude of the target location.
    :param lon: Longitude of the target location.
    :param zoom: Zoom level for the map tiles.
    :param folder: Folder to save the tiles.
    """
    # Ensure the output folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)

    for source_name, source in dict_sources.items():
        # Check if the zoom level is within the source's maximum zoom level
        if zoom > source["zmax"]:
            print(f"Skipping {source_name}: Max zoom level exceeded.")
            continue

        # Get the tile coordinates for the given latitude, longitude, and zoom
        tile_x, tile_y = get_tile_xy(lat, lon, zoom)

        # Generate the full URL for the tile
        tile_url = source["url"].format(tile_x, tile_y, zoom)
        print(f"Fetching tile from {source_name} URL: {tile_url}")

        # Set the filename and path to save the tile
        filename = f"{folder}/{source_name.replace(' ', '_')}_tile_{zoom}_{tile_x}_{tile_y}.jpeg"

        # Download the tile image
        response = requests.get(tile_url, headers=headers)
        if response.status_code == 200:
            with open(filename, "wb") as file:
                file.write(response.content)
            print(f"Tile image saved as {filename}")
        else:
            print(
                f"Failed to fetch tile from {source_name}: Status code {response.status_code}"
            )


# Example usage with coordinates and zoom level
latitude = 9.11359786111111

longitude = -1.7549104444444446
zoom_level = 18

# Fetch and save all tiles in the specified folder
fetch_and_save_all_tiles(latitude, longitude, zoom_level)
