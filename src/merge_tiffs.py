"""
TODO: Add some more error handling especially with the
rasterio IO operations. Right now it is pure inshallah.
"""
import os
import numpy as np
import rasterio
from typing import List

def get_tiff_files_from_folder(folder_path: str) -> List[str]:
    """
    Get all TIFF files from the specified folder.

    Args:
    folder_path (str): Path to the folder containing the TIFF files

    Returns:
    List[str]: List of paths to the TIFF files
    """
    tiff_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.tiff')]
    tiff_files.sort()  
    return tiff_files

def extract_class_name(tiff_file: str) -> str:
    """
    Extract the class name from the TIFF filename.

    Args:
    tiff_file (str): Path to the TIFF file

    Returns:
    str: Class name extracted from the filename
    """
    base_name = os.path.basename(tiff_file)
    class_name = os.path.splitext(base_name)[0]  
    return class_name

def merge_tiff_files(folder_path: str, output_filename: str, nodata_value: int = -9999) -> None:
    """
    Merge multiple TIFF files from the specified folder into a single TIFF file.
    Each pixel gets assigned the class index based on the highest value across input files.
    Metadata is updated to describe the class names based on the filenames.
    
    Parameters:
    folder_path (str): Path to the folder containing the input TIFF files.
    output_filename (str): Name of the output merged TIFF file.
    nodata_value (int): NoData value to be used for missing data.

    Returns:
    None
    """
    tiff_files = get_tiff_files_from_folder(folder_path)
    
    if not tiff_files:
        raise FileNotFoundError(f"No TIFF files found in the folder: {folder_path}")
    else:
        print(f"Found TIFF files: {tiff_files}")

    with rasterio.open(tiff_files[0]) as src:
        meta = src.meta
        height, width = src.shape

    final_raster = np.full((height, width), nodata_value, dtype=np.int16)
    max_values = np.zeros((height, width))

    class_descriptions = {}

    for idx, tiff_file in enumerate(tiff_files, start=1):
        with rasterio.open(tiff_file) as src:
            data = src.read(1) 

            mask = data > max_values
            final_raster[mask] = idx  
            max_values[mask] = data[mask]  
            
            class_name = extract_class_name(tiff_file)
            class_descriptions[idx] = class_name

    final_raster[max_values == 0] = nodata_value

    meta.update(count=1, dtype=rasterio.int16, nodata=nodata_value)

    tags = {f'class_{idx}': class_name for idx, class_name in class_descriptions.items()}

    output_tiff = os.path.join(folder_path, output_filename)

    with rasterio.open(output_tiff, 'w', **meta) as dst:
        dst.write(final_raster, 1)
        dst.update_tags(**tags)

    print(f"Merged TIFF saved as: {output_tiff}")

if __name__ == "__main__":
    #C:\Users\bventura\OneDrive - Scientific Network South Tyrol\VeB\05_Code\Python\birdwatch-flanders\data_Germany
    #C:\Users\bventura\OneDrive - Scientific Network South Tyrol\VeB\05_Code\Python\birdwatch-flanders\data
    folder_path = "data_Germany/"
    output_filename = "merged_Germany.tiff"
    merge_tiff_files(folder_path, output_filename)
