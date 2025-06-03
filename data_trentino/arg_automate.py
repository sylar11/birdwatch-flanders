import argparse
import fiona
from shapely.geometry import shape
import geopandas as gpd
import pyogrio
pyogrio.set_gdal_config_options({"OGR_GEOJSON_MAX_OBJ_SIZE": 0}) ##added to avoid bad geojson when too large
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from functools import partial
import pyproj
from shapely.ops import transform
from geocube.api.core import make_geocube
from geocube.rasterize import rasterize_image
from rasterio.enums import MergeAlg
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
from shapely.validation import make_valid
from tqdm.auto import tqdm  # Auto-detects notebook/terminal
import os
import time

def main(crops_str):
    N_WORKERS = max(1, os.cpu_count() - 1) 

    eurostat = "/ceph/hpc/home/dhinakarans/Bart_TMP/Trentino_200mGRID_2.shp"

    path_feature = "/ceph/hpc/home/dhinakarans/Bart_TMP/"+crops_str+".geojson"

    grid = gpd.read_file(eurostat)
    feature = gpd.read_file(path_feature)


    grid = grid.to_crs(grid.crs)
    feature = feature.to_crs(grid.crs)

    feature['fid'] = feature.reset_index(drop=True).index

    grid.id = grid.reset_index(drop=True).index
    grid_indexed = grid.set_index("id")

    fully_within = gpd.sjoin(feature, grid, predicate="within") 
    intersects = gpd.sjoin(feature, grid, predicate="intersects") 
    not_fully_within = intersects[~intersects.fid.isin(fully_within.fid.unique())] 

    # 1. Parallel Geometry Validation ==============================================
    def validate_geometry(geom):
        """Validate a single geometry"""
        return make_valid(geom) if not geom.is_valid else geom

    # Submit all jobs with original indices
    with ThreadPoolExecutor(max_workers=N_WORKERS) as executor:
        futures = {executor.submit(validate_geometry, geom): idx 
                  for idx, geom in enumerate(not_fully_within.geometry)}
        
        # Initialize empty array for results
        validated = [None] * len(not_fully_within)
        
        # Process with progress
        for future in tqdm(as_completed(futures), total=len(futures),
                          desc="Validating geometries"):
            idx = futures[future]
            validated[idx] = future.result()

    not_fully_within.geometry = np.array(validated)

    time.sleep(2)

    # Check for missing IDs first
    missing_ids = set(not_fully_within['id']) - set(grid_indexed.index)
    if missing_ids:
        print(f"Warning: {len(missing_ids)} IDs not found in grid_indexed")

    def calculate_intersection(row):
        """Calculate single intersection with error handling"""
        try:
            return row.geometry.intersection(grid_indexed.loc[row.id].geometry)
        except KeyError:
            return None  # or return an empty geometry

    # Submit all jobs with original indices
    with ThreadPoolExecutor(max_workers=N_WORKERS) as executor:
        futures = {executor.submit(calculate_intersection, row): idx
                  for idx, row in enumerate(not_fully_within.itertuples())}
        
        # Initialize empty array for results
        intersections = [None] * len(not_fully_within)
        
        # Process with progress
        for future in tqdm(as_completed(futures), total=len(futures),
                          desc="Calculating intersections"):
            idx = futures[future]
            intersections[idx] = future.result()

    not_fully_within["intersection_geometry"] = intersections

    time.sleep(5)

    # Step 1: Ensure no None values exist (or replace them)
    not_fully_within["intersection_geometry"] = [
                geom if geom is not None else Polygon() 
                    for geom in not_fully_within.intersection_geometry
                    ]

    # Step 2: Calculate perimeter safely
    not_fully_within["intersection_geometry_perimeter"] = [
                geom.length for geom in not_fully_within.intersection_geometry
                ]

    not_fully_within["intersection_geometry_area"] = [geom.area for geom in not_fully_within.intersection_geometry]

    fully_within_geom_area = fully_within.groupby("id").AREA.sum()/40000
    not_fully_within_geom_area = not_fully_within.groupby("id").intersection_geometry_area.sum()/40000

    area_lengths_per_grid = fully_within_geom_area.add(not_fully_within_geom_area, fill_value=0)
    tree_area = pd.DataFrame(area_lengths_per_grid, columns=["AREA"]).reset_index()

    df  = grid.merge(tree_area, on='id', how='left').fillna(0)

    path_vectors = '/ceph/hpc/home/dhinakarans/Bart_TMP/Vectors/'
    path_geojson = path_vectors + crops_str +'.geojson'

    with open(path_geojson, 'w') as file:
        file.write(df.to_json())

    valid_geometries = df[df.geometry.is_valid]

    cal_census_raster = make_geocube(vector_data=df,measurements=["AREA"],resolution=(-200, 200),fill=0.0,output_crs='EPSG:3035')
        

    path = '/ceph/hpc/home/dhinakarans/Bart_TMP/Raster/'
    path_tiff = path + crops_str +'.tiff'
    print(path_tiff)
    cal_census_raster.rio.to_raster(path_tiff)


    # Open the raster file
    with rasterio.open(path_tiff) as src:
        plt.figure(figsize=(10, 8))
        ax = plt.gca()

        # Plot the raster and get the mappable object
        image = show(src, ax=ax)

        # Add colorbar
        plt.colorbar(image.get_images()[0], ax=ax, label='Pixel values')

        plt.title('Raster Plot')

        # Save the figure instead of showing it
        plt.savefig(f'{crops_str}.png', dpi=300, bbox_inches='tight')  # Save as PNG with high resolution
        plt.close()  # Close the figure to free memory

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process crop data.')
    parser.add_argument('--crops', type=str, required=True, help='Crop type string (e.g., "Grapevine")')
    
    args = parser.parse_args()
    
    main(args.crops)