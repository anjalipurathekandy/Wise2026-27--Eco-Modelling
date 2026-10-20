import numpy as np
import matplotlib.pyplot as plt
from osgeo import gdal
import math
from matplotlib.colors import ListedColormap
from mpl_toolkits.basemap import Basemap

#Using GDAL, project the .tif file from its co-ordinate system to EPSG:4326 (WGS84) and save it as a new .tif file
def project_tif_to_epsg4326(input_tif, output_tif):

    dataset = gdal.Open(input_tif)
    target_srs = 'EPSG:4326'
    gdal.Warp(output_tif, dataset, dstSRS=target_srs)

    return output_tif

#given the latmin, latmax, lonmin, lonmax values for the area of interest, find the length of the sides of the rectangle (km) and area (sq. km)
def calculate_length_and_area(latmin, latmax, lonmin, lonmax):
    #the inputs are the minimum and maximum latitude and longitude values for the area of interest (EPS:4326)

    lat_length = (latmax - latmin) * 111.32  # Approximate conversion factor for latitude to kilometers
    lon_length = (lonmax - lonmin) * 111.32 * abs(math.cos(math.radians((latmin + latmax) / 2)))  # Adjust for longitude based on latitude
    area = lat_length * lon_length

    return lat_length, lon_length, area

#given the latmin, latmax, lonmin, lonmax values for the area of interest, crop the .tif file to that area and save it as a new .tif file
def crop_to_area_of_interest(input_tif, output_tif, latmin, latmax, lonmin, lonmax):
    dataset = gdal.Open(input_tif)
    geotransform = dataset.GetGeoTransform()

    x_min = int((lonmin - geotransform[0]) / geotransform[1])
    x_max = int((lonmax - geotransform[0]) / geotransform[1])
    y_min = int((latmax - geotransform[3]) / geotransform[5])
    y_max = int((latmin - geotransform[3]) / geotransform[5])

    cropped_dataset = dataset.ReadAsArray(x_min, y_min, x_max - x_min, y_max - y_min)

    driver = gdal.GetDriverByName('GTiff')
    out_dataset = driver.Create(output_tif, x_max - x_min, y_max - y_min, 1, gdal.GDT_Float32)
    out_dataset.SetGeoTransform((
        lonmin, geotransform[1], 0,
        latmax, 0, geotransform[5]
    ))
    out_dataset.SetProjection(dataset.GetProjection())
    out_dataset.GetRasterBand(1).WriteArray(cropped_dataset)

    return output_tif

#given the latmin, latmax, lonmin, lonmax values for the area of interest, plot the .tif file and save it as a .png file
def plot_landscape(study_area, output_file, latmin, latmax, lonmin, lonmax):

    dataset = gdal.Open(study_area).ReadAsArray()

    unique_values = set(dataset.flatten())
    num_unique_values = len(unique_values)

    #map all pixels with 127 (nan) to 0 (background)
    dataset[dataset == 127] = 0

    #pixel value: (land use type, color); greens = forests, yellow = plantations, blues = water
    lulc_classes = {
        0: ('Background', 'white'),
        1: ('Deciduous Broadleaf Forest', '#2e8b57'),
        2: ('Cropland', '#f4a460'),
        3: ('Built-up Land', '#d62728'),
        4: ('Mixed Forest', '#228b22'),
        5: ('Shrubland', '#9acd32'),
        6: ('Barren Land', 'black'),
        7: ('Fallow Land', '#deb887'),
        8: ('Wasteland', '#a9a9a9'),
        9: ('Water Bodies', '#0000cd'),
        10: ('Plantations', '#ffd700'),
        11: ('Aquaculture', '#4682b4'),
        12: ('Mangrove Forest', '#006400'),
        13: ('Salt Pan', '#e6e6fa'),
        14: ('Grassland', '#adff2f'),
        15: ('Evergreen Broadleaf Forest', '#004d00'),
        16: ('Deciduous Needleleaf Forest', '#66cdaa'),
        17: ('Permanent Wetlands', '#87cefa'),
        18: ('Snow & Ice', '#f0ffff'),
        19: ('Evergreen Needleleaf Forest', '#3cb371'),
    }
    cmap = ListedColormap([lulc_classes[i][1] for i in range(len(lulc_classes))])

    fig, ax = plt.subplots(figsize=(10, 10))

    print(range(int(latmin), int(latmax + 0.05), 5))

    map = Basemap(projection='cyl', llcrnrlat=latmin, urcrnrlat=latmax, llcrnrlon=lonmin, urcrnrlon=lonmax, resolution='i')
    img = map.imshow(np.flipud(dataset), cmap=cmap, vmin=-0.5, vmax=len(lulc_classes) - 0.5, interpolation='nearest')
    parallels = np.linspace(latmin, latmax, 2, endpoint=True)
    meridians = np.linspace(lonmin, lonmax, 2, endpoint=True)
    map.drawparallels(parallels, labels=[1, 0, 0, 0], fontsize=12)
    map.drawmeridians(meridians, labels=[0, 0, 0, 1], fontsize=12)
    plt.title('Study Area', fontsize=16)
    plt.legend(handles=[plt.Line2D([0], [0], marker='s', color='w', label=lulc_classes[int(val)][0],
                                   markersize=12,
                                   markerfacecolor=lulc_classes[int(val)][1]) for val in sorted(unique_values) if val not in (0, 127)],
                                   loc='upper right', 
                                   bbox_to_anchor=(1.47, 1),
                                   fontsize=14)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    return

#new pixel value: (new land use type, color, [original pixel values merged into it])
merged_classes = {
    0: ('Background', 'white', [0, 127]),
    1: ('Forest', '#228b22', [1, 4, 12, 15, 16, 19]),
    2: ('Cropland & Plantations', '#ffd700', [2, 7, 10]),
    3: ('Built-up Land', '#d62728', [3]),
    4: ('Shrubland & Grassland', '#9acd32', [5, 14]),
    5: ('Barren Land & Wasteland', 'black', [6, 8]),
    6: ('Water Bodies', '#0000cd', [9, 11, 17]),
    7: ('Other', '#a9a9a9', [13, 18]),
}

#plot an array of merged classes with a legend and the given text below the legend, and save it as a .png file
def plot_merged_landscape(merged, output_file, latmin, latmax, lonmin, lonmax, info_text):

    cmap = ListedColormap([merged_classes[i][1] for i in range(len(merged_classes))])

    fig, ax = plt.subplots(figsize=(10, 10))

    map = Basemap(projection='cyl', llcrnrlat=latmin, urcrnrlat=latmax, llcrnrlon=lonmin, urcrnrlon=lonmax, resolution='i')
    img = map.imshow(np.flipud(merged), cmap=cmap, vmin=-0.5, vmax=len(merged_classes) - 0.5, interpolation='nearest')
    parallels = np.linspace(latmin, latmax, 2, endpoint=True)
    meridians = np.linspace(lonmin, lonmax, 2, endpoint=True)
    map.drawparallels(parallels, labels=[1, 0, 0, 0], fontsize=12)
    map.drawmeridians(meridians, labels=[0, 0, 0, 1], fontsize=12)
    plt.title('Study Area', fontsize=16)
    legend = plt.legend(handles=[plt.Line2D([0], [0], marker='s', color='w', label=merged_classes[val][0],
                                   markersize=12,
                                   markerfacecolor=merged_classes[val][1]) for val in np.unique(merged) if val != 0],
                                   loc='upper right',
                                   bbox_to_anchor=(1.47, 1),
                                   fontsize=14)

    fig.canvas.draw()
    legend_box = legend.get_window_extent().transformed(ax.transAxes.inverted())
    ax.text(legend_box.x0, legend_box.y0 - 0.03, info_text, transform=ax.transAxes, ha='left', va='top', fontsize=14)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    return

#merge similar land use classes into new ones, save the merged .tif file and plot it as a .png file
def merge_classes_and_plot_landscape(study_area, output_tif, output_file, latmin, latmax, lonmin, lonmax):

    source = gdal.Open(study_area)
    dataset = source.ReadAsArray()
    merged = np.zeros(dataset.shape, dtype=np.uint8)
    for new_val, (_, _, old_vals) in merged_classes.items():
        merged[np.isin(dataset, old_vals)] = new_val

    #save the merged landscape as a new .tif file
    out_dataset = gdal.GetDriverByName('GTiff').Create(output_tif, source.RasterXSize, source.RasterYSize, 1, gdal.GDT_Byte)
    out_dataset.SetGeoTransform(source.GetGeoTransform())
    out_dataset.SetProjection(source.GetProjection())
    out_dataset.GetRasterBand(1).WriteArray(merged)
    out_dataset.FlushCache()
    out_dataset = None

    #side lengths, total area and forest area (forest pixels x average pixel area) shown below the legend
    lat_length, lon_length, area = calculate_length_and_area(latmin, latmax, lonmin, lonmax)
    forest_area = area * np.count_nonzero(merged == 1) / merged.size
    water_area = area * np.count_nonzero(dataset == 9) / dataset.size    #permanent water bodies = original value 9 only
    info_text = (f'Width: {lon_length:.2f} km\nHeight: {lat_length:.2f} km\n'
                 f'Total area: {area:.2f} sq. km\nForest area: {forest_area:.2f} sq. km\n'
                 f'Permanent water body: {water_area:.2f} sq. km')
    plot_merged_landscape(merged, output_file, latmin, latmax, lonmin, lonmax, info_text)

    return output_tif

#upscale the pixel size of a merged .tif file (e.g. 100 m -> 300 m) by taking the most frequent class in each new pixel, save it as a new .tif file and plot it
#new pixels containing at least min_water_pixels permanent water body pixels (value 9 in study_area) are given preference and set to Water Bodies
def upscale_tif(input_tif, study_area, output_tif, output_file, latmin, latmax, lonmin, lonmax, pixel_size_m=300, min_water_pixels=3):
    pixel_size_deg = pixel_size_m / 111320  # Approximate conversion factor for meters to degrees (EPSG:4326)

    source = gdal.Open(input_tif)
    gdal.Warp(output_tif, source, xRes=pixel_size_deg, yRes=pixel_size_deg, resampleAlg='mode', outputType=gdal.GDT_Byte)

    upscaled = gdal.Open(output_tif, gdal.GA_Update)

    #give preference to permanent water body pixels: flag every new pixel that contains at least min_water_pixels of them (sum resampling of a 0/1 mask)
    original = gdal.Open(study_area)
    water_array = (original.ReadAsArray() == 9).astype(np.uint8)
    mask_ds = gdal.GetDriverByName('MEM').Create('', original.RasterXSize, original.RasterYSize, 1, gdal.GDT_Byte)
    mask_ds.SetGeoTransform(original.GetGeoTransform())
    mask_ds.SetProjection(original.GetProjection())
    mask_ds.GetRasterBand(1).WriteArray(water_array)
    gt = upscaled.GetGeoTransform()
    bounds = (gt[0], gt[3] + gt[5] * upscaled.RasterYSize, gt[0] + gt[1] * upscaled.RasterXSize, gt[3])
    water_mask = gdal.Warp('', mask_ds, format='MEM', outputBounds=bounds, width=upscaled.RasterXSize, height=upscaled.RasterYSize,
                           resampleAlg='sum', outputType=gdal.GDT_UInt16).ReadAsArray()
    upscaled_array = upscaled.ReadAsArray()
    upscaled_array[water_mask >= min_water_pixels] = 6
    upscaled.GetRasterBand(1).WriteArray(upscaled_array)
    upscaled.FlushCache()

    n_pixels = upscaled.RasterXSize * upscaled.RasterYSize
    print(f"Pixels before upscaling: {source.RasterXSize} x {source.RasterYSize} = {source.RasterXSize * source.RasterYSize}")
    print(f"Pixels after upscaling to {pixel_size_m} m: {upscaled.RasterXSize} x {upscaled.RasterYSize} = {n_pixels}")

    lat_length, lon_length, area = calculate_length_and_area(latmin, latmax, lonmin, lonmax)
    forest_area = area * np.count_nonzero(upscaled_array == 1) / upscaled_array.size
    water_area = area * water_array.sum() / water_array.size    #permanent water bodies = original value 9 only, from the original resolution
    info_text = (f'Pixel size: {pixel_size_m} m x {pixel_size_m} m\n'
                 f'Total pixels: {n_pixels} ({upscaled.RasterXSize} x {upscaled.RasterYSize})\n'
                 f'Total area: {area:.2f} sq. km\nForest area: {forest_area:.2f} sq. km\n'
                 f'Permanent water body: {water_area:.2f} sq. km')
    plot_merged_landscape(upscaled_array, output_file, latmin, latmax, lonmin, lonmax, info_text)

    return output_tif

input_tif ='Decadal_LULC_India/data/LULC_2005.tif'
output_tif = 'course-guide/step1-setting-up-landscape/preprocessing_in_python/LULC_2005_EPSG4326.tif'
# project_tif_to_epsg4326(input_tif, output_tif)    # uncomment this line to project the .tif file to EPSG:4326

latmin = 8.85
latmax = 9.95
lonmin = 76.60
lonmax = 77.70

lat_length, lon_length, area = calculate_length_and_area(latmin, latmax, lonmin, lonmax)
print(f"Length of latitude side: {lat_length:.2f} km")
print(f"Length of longitude side: {lon_length:.2f} km")
print(f"Area: {area:.2f} sq. km")

study_area_tif = 'course-guide/step1-setting-up-landscape/preprocessing_in_python/LULC_2005_EPSG4326_study_area.tif'
study_area = crop_to_area_of_interest(output_tif, study_area_tif, latmin, latmax, lonmin, lonmax) 

output_file = 'course-guide/step1-setting-up-landscape/preprocessing_in_python/LULC_2005_EPSG4326_study_area.png'
plot_landscape(study_area, output_file, latmin, latmax, lonmin, lonmax)
merged_tif = 'course-guide/step1-setting-up-landscape/preprocessing_in_python/LULC_2005_EPSG4326_merged.tif'
merged_file = 'course-guide/step1-setting-up-landscape/preprocessing_in_python/LULC_2005_EPSG4326_merged.png'
merge_classes_and_plot_landscape(study_area, merged_tif, merged_file, latmin, latmax, lonmin, lonmax)

upscaled_tif = 'course-guide/step1-setting-up-landscape/preprocessing_in_python/LULC_2005_EPSG4326_merged_300mx300m.tif'
upscaled_file = 'course-guide/step1-setting-up-landscape/preprocessing_in_python/LULC_2005_EPSG4326_merged_300mx300m.png'
upscale_tif(merged_tif, study_area, upscaled_tif, upscaled_file, latmin, latmax, lonmin, lonmax, 300, 1)

upscaled_tif = 'course-guide/step1-setting-up-landscape/preprocessing_in_python/LULC_2005_EPSG4326_merged_500mx500m.tif'
upscaled_file = 'course-guide/step1-setting-up-landscape/preprocessing_in_python/LULC_2005_EPSG4326_merged_500mx500m.png'
upscale_tif(merged_tif, study_area, upscaled_tif, upscaled_file, latmin, latmax, lonmin, lonmax, 500, 2)
