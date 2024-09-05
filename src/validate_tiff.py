"""
Sample script to validate our new generated tiff file.
Get the information on size, shape, and nodata value.
Also print out the different classes of data and their
respective values
"""
import os
from pprint import pprint as pp
import rasterio
import numpy as np

def validate_tiff(tiff_file: str) -> None:
    """
    Validate the TIFF file by printing out the metadata and class information
    """
    with rasterio.open(tiff_file) as src:
        pp(f"Metadata: {src.meta}")
        pp(f"Shape: {src.shape}")
        pp(f"NoData value: {src.nodata}")
        
        data = src.read(1)
        unique_values = np.unique(data)
        pp(f"Unique values: {unique_values}")
        
        class_names = [os.path.splitext(os.path.basename(tiff_file))[0] for tiff_file in src.files]
        pp(f"Class names: {class_names}")

if __name__ == "__main__":
    tiff_file = "../data/merged.tiff"
    validate_tiff(tiff_file)