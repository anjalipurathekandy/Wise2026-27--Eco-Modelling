# Landscape preprocessing (LULC 2005)

All steps are in `create_landscape.py`. Run from the `Eco-Modelling` folder (paths are relative to it).

**Input:** `Decadal_LULC_India/data/LULC_2005.tif` – India LULC, 100 m pixels, UTM 44N (EPSG:32644), 19 IGBP-based classes, no-data = 127. Class definitions: `Decadal_LULC_India/comp/Decadal_LULC_India.pdf` (Table 2).

## Steps

1. **Reproject** – `project_tif_to_epsg4326` (GDAL warp) → `LULC_2005_EPSG4326.tif` (~1.1 GB). Slow; call is commented out once the file exists. Pixels become 0.000932° (~102–103 m).
2. **Area of interest** – lat 8.85–9.95, lon 76.60–77.70. `calculate_length_and_area` gives ~122.45 km (height) × ~120.81 km (width) ≈ 14,793 sq. km (1° lat = 111.32 km; longitude scaled by cos(mean lat)).
3. **Crop** – `crop_to_area_of_interest` → `..._study_area.tif` (1180 × 1181 px).
4. **Plot original classes** – `plot_landscape` → `..._study_area.png`. Colors/names come from the `lulc_classes` dict (pixel value → name, color): greens = forests, yellow = plantations, blues = water. 127 is set to 0 (background); legend lists only classes present.
5. **Merge classes** – `merge_classes_and_plot_landscape` recodes pixels using the module-level `merged_classes` dict (new value → name, color, original values) → `..._merged.tif` (Byte) and `.png`.

   | New | Class | Original values |
   |---|---|---|
   | 0 | Background | 0, 127 |
   | 1 | Forest | 1, 4, 12, 15, 16, 19 |
   | 2 | Cropland & Plantations | 2, 7, 10 |
   | 3 | Built-up Land | 3 |
   | 4 | Shrubland & Grassland | 5, 14 |
   | 5 | Barren Land & Wasteland | 6, 8 |
   | 6 | Water Bodies | 9, 11, 17 |
   | 7 | Other | 13, 18 |

   Text under the legend: width, height, total area, forest area, permanent water body area (original class 9 only). Class areas = pixel share × total area (average pixel size).
6. **Upscale** – `upscale_tif(..., pixel_size_m)` resamples the merged tif to a coarser grid (m → degrees via /111,320) with `mode` resampling (most frequent class per new pixel, so classes stay valid) → `..._merged_<N>mx<N>m.tif` and `.png`. Pixels with at least `min_water_pixels` (default 3) permanent water pixels (original class 9, counted by sum-resampling a 0/1 mask) are forced to Water Bodies, so rivers/lakes stay connected. Plot text: pixel size, total pixels, total/forest area, permanent water body (computed at original resolution). 100 m: 1,393,580 px; 300 m: 408 × 408 = 166,464 px. The script is currently set to 500 m.

## Outputs (this folder)

`LULC_2005_EPSG4326{.tif, _study_area.tif/.png, _merged.tif/.png, _merged_300mx300m.tif/.png, _merged_500mx500m.tif/.png}`

## Notes

- Requires GDAL (`osgeo`), matplotlib, numpy, basemap.
- Forest area on upscaled maps shifts slightly because water pixels take precedence over other classes.
- To change the merging or colors, edit `merged_classes` (keep new values consecutive from 0).
