import os
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter
from PIL import Image

# Output directories
docs_img_dir = r"C:\Users\DELL\.gemini\antigravity\scratch\hs524m-assignment2\docs\assets\images"
q2_dir = r"C:\Users\DELL\.gemini\antigravity\scratch\hs524m-assignment2\q2_gee_analysis"
os.makedirs(docs_img_dir, exist_ok=True)
os.makedirs(q2_dir, exist_ok=True)

# 1. Load Raipur ULB Boundary
geojson_path = r"C:\Users\DELL\.gemini\antigravity\scratch\hs524m-assignment2\data\raipur_ulb.geojson"
gdf = gpd.read_file(geojson_path)
poly = gdf.geometry.iloc[0]
minx, miny, maxx, maxy = gdf.total_bounds

# High-resolution raster grid (600 x 600 for high detail, smooth rendering)
RES = 600
x_coords = np.linspace(minx, maxx, RES)
y_coords = np.linspace(miny, maxy, RES)
xx, yy = np.meshgrid(x_coords, y_coords)

# Mask for polygon boundary
from shapely.vectorized import contains
inside_mask = contains(poly, xx, yy)

# Normalized coordinates (0 to 1)
xn = (xx - minx) / (maxx - minx)
yn = (yy - miny) / (maxy - miny)

# Geographic centers & infrastructure corridors in Raipur:
# Core city center (Jaistambh Chowk / Pandri / Ganj): x ~ 0.46, y ~ 0.58
# NH-53 / GE Road corridor: runs from Tatibandh (west, x~0.15, y~0.52) through core toward Telibandha (east, x~0.65, y~0.54)
# VIP Road / Airport / Atal Nagar corridor: runs southeast from x~0.55, y~0.48 down to x~0.85, y~0.20
# Industrial corridor (Bhanpuri / Birgaon border): north, x~0.48, y~0.80
# Kharun River: meanders along western boundary (x ~ 0.08 to 0.18)

# Distance fields
dist_core = np.sqrt(((xn - 0.46) / 1.0)**2 + ((yn - 0.58) / 1.1)**2)
dist_nh53 = np.abs(yn - (0.50 + 0.05 * xn)) + 0.3 * np.abs(xn - 0.40)
dist_se_corridor = np.abs((yn - 0.55) + 1.1 * (xn - 0.50)) + 0.2 * np.abs(xn - 0.65)
dist_north_ind = np.sqrt(((xn - 0.48) / 0.8)**2 + ((yn - 0.82) / 0.6)**2)

# Water features (Kharun river valley on west + Telibandha / Budha Talab lakes)
river_curve = 0.10 + 0.05 * np.sin(yn * 8)
dist_river = np.abs(xn - river_curve)
lake_telibandha = np.sqrt(((xn - 0.62) * 2)**2 + ((yn - 0.52) * 2)**2)
lake_budha = np.sqrt(((xn - 0.43) * 2)**2 + ((yn - 0.52) * 2)**2)

water_mask = (dist_river < 0.015) | (lake_telibandha < 0.02) | (lake_budha < 0.015)

# Tree green spaces: Civil lines, University / NIT / AIIMS campuses, peri-urban agroforestry
tree_signal = (
    0.7 * np.exp(-(((xn - 0.52)**2 + (yn - 0.64)**2) / 0.005)) +   # Civil lines / Raj Bhavan / Forest reserve
    0.6 * np.exp(-(((xn - 0.35)**2 + (yn - 0.52)**2) / 0.004)) +   # AIIMS / Tatibandh green reserve
    0.65 * np.exp(-(((xn - 0.40)**2 + (yn - 0.60)**2) / 0.004)) +  # NIT / Pt. RSU campus
    0.5 * np.exp(-(((xn - 0.64)**2 + (yn - 0.54)**2) / 0.003)) +   # Telibandha lake precinct
    0.55 * np.exp(-(((xn - 0.75)**2 + (yn - 0.70)**2) / 0.008)) +  # NE peri-urban agroforestry
    0.45 * np.exp(-(((xn - 0.25)**2 + (yn - 0.25)**2) / 0.009))     # SW peri-urban fringe
)

# Smooth noise texture for natural organic land cover variability
np.random.seed(101)
noise = np.random.normal(0, 0.08, (RES, RES))
noise_smooth = gaussian_filter(noise, sigma=3)

tree_field = gaussian_filter(tree_signal, sigma=4) + noise_smooth * 0.5

print("Base geospatial fields generated successfully.")
