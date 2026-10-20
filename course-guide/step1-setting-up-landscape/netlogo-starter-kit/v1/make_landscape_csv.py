import numpy as np
from osgeo import gdal

#convert the merged 500 m landscape .tif to a .csv that NetLogo can read (one row per tif row, row 0 = north edge)
input_tif = 'course-guide/step1-setting-up-landscape/preprocessing_in_python/LULC_2005_EPSG4326_merged_500mx500m.tif'
output_csv = 'course-guide/step1-setting-up-landscape/netlogo-starter-kit/v1/landscape_500m.csv'

landscape = gdal.Open(input_tif).ReadAsArray()
np.savetxt(output_csv, landscape, fmt='%d', delimiter=',')

print(f"Saved {output_csv}: {landscape.shape[0]} rows x {landscape.shape[1]} columns")
print("Class counts:", dict(zip(*np.unique(landscape, return_counts=True))))
