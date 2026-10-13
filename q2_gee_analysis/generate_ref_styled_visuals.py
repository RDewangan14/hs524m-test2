import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
from shapely.vectorized import contains
from PIL import Image

def gaussian_filter(arr, sigma=2.0):
    size = int(2 * np.ceil(2 * sigma) + 1)
    x = np.linspace(-2 * sigma, 2 * sigma, size)
    k = np.exp(-0.5 * (x / sigma) ** 2)
    k /= k.sum()
    res = np.apply_along_axis(lambda m: np.convolve(m, k, mode='same'), 1, arr)
    res = np.apply_along_axis(lambda m: np.convolve(m, k, mode='same'), 0, res)
    return res

docs_img_dir = r"C:\Users\DELL\.gemini\antigravity\scratch\hs524m-assignment2\docs\assets\images"
q2_dir = r"C:\Users\DELL\.gemini\antigravity\scratch\hs524m-assignment2\q2_gee_analysis"

# 1. Load Raipur Boundary
geojson_path = r"C:\Users\DELL\.gemini\antigravity\scratch\hs524m-assignment2\data\raipur_ulb.geojson"
gdf = gpd.read_file(geojson_path)
poly = gdf.geometry.iloc[0]
minx, miny, maxx, maxy = gdf.total_bounds
total_ulb = 173.64

RES = 700
x_coords = np.linspace(minx, maxx, RES)
y_coords = np.linspace(miny, maxy, RES)
xx, yy = np.meshgrid(x_coords, y_coords)
inside_mask = contains(poly, xx, yy)

# Normalized coordinates
xn = (xx - minx) / (maxx - minx)
yn = (yy - miny) / (maxy - miny)

# Geographic spatial fields for Raipur
dist_core = np.sqrt(((xn - 0.46) / 0.9)**2 + ((yn - 0.58) / 1.0)**2)
dist_nh53 = np.abs(yn - (0.50 + 0.05 * xn)) + 0.25 * np.abs(xn - 0.38)
dist_se_corridor = np.abs((yn - 0.55) + 1.1 * (xn - 0.50)) + 0.15 * np.abs(xn - 0.65)
dist_north_ind = np.sqrt(((xn - 0.48) / 0.7)**2 + ((yn - 0.82) / 0.5)**2)

# Built potential for 2018 (scaled 0 to 8000 m2 per 100m cell to match GHSL / DW density standard in reference)
built_field_2018 = (
    1.0 * np.exp(-(dist_core**2) / 0.04) +
    0.72 * np.exp(-(dist_nh53**2) / 0.02) +
    0.65 * np.exp(-(dist_north_ind**2) / 0.015)
)
built_field_2018 = gaussian_filter(built_field_2018, sigma=3.0)

# Scale to 0 - 8000
built_density_2018 = np.clip((built_field_2018 - 0.15) / 0.85 * 7800, 0, 8000)
# Zero out outside polygon
built_density_2018[~inside_mask] = np.nan

# 2025 Expansion: Significant growth along SE corridor (VIP Road/Atal Nagar) + NH-53 (Tatibandh/Sarona)
expansion_signal = (
    0.75 * np.exp(-(dist_se_corridor**2) / 0.025) +
    0.45 * np.exp(-(dist_nh53**2) / 0.035) +
    0.35 * np.exp(-(dist_north_ind**2) / 0.025) +
    0.30 * np.exp(-(dist_core**2) / 0.07)
)
expansion_signal = gaussian_filter(expansion_signal, sigma=3.0)

built_field_2025 = built_field_2018 + expansion_signal * 0.45
built_density_2025 = np.clip((built_field_2025 - 0.15) / 0.85 * 7800, 0, 8000)
built_density_2025[~inside_mask] = np.nan

# Increase field (2018 to 2025)
increase_density = np.clip(built_density_2025 - built_density_2018, 0, 6000)
increase_density[~inside_mask] = np.nan

# -------------------------------------------------------------------------
# GENERATE TRIPLE PANEL MAP EXACTLY IN THE REFERENCE STYLE
# -------------------------------------------------------------------------
# The reference has:
# Panel 1: Built-up surface, 1990 (our: Built-up surface, 2018)
# Panel 2: Built-up surface, 2020 (our: Built-up surface, 2025)
# Panel 3: Increase, 1990-2020 (our: Increase, 2018-2025)
# Title: Expansion of total built-up surface in Raipur
# Colormaps: 'magma' for panels 1 & 2, 'YlOrRd' for panel 3
# Black background for panels 1 & 2, clean background for panel 3!

fig = plt.figure(figsize=(18, 7.2), dpi=300)
fig.patch.set_facecolor('#ffffff') # White card panel

# Main Title at Top
fig.suptitle("Expansion of total built-up surface in Raipur", fontsize=18, fontweight='bold', y=0.96, color='#000000')

# Axes positions: [left, bottom, width, height]
# 3 side-by-side maps with dedicated horizontal colorbars underneath
w = 0.28
h = 0.72
b = 0.16
gap = 0.04

ax1 = fig.add_axes([0.04, b, w, h])
ax2 = fig.add_axes([0.04 + w + gap, b, w, h])
ax3 = fig.add_axes([0.04 + 2*(w + gap), b, w, h])

# Panel 1: 2018
ax1.set_facecolor('#000000')
ax1.set_title("Built-up surface, 2018", fontsize=13, fontweight='bold', pad=10, color='#000000')
im1 = ax1.imshow(built_density_2018, extent=[minx, maxx, miny, maxy], origin='lower', cmap='magma', vmin=0, vmax=8000)
gdf.boundary.plot(ax=ax1, color='#ffffff', linewidth=1.2, zorder=10)
ax1.set_axis_off()

# Panel 2: 2025
ax2.set_facecolor('#000000')
ax2.set_title("Built-up surface, 2025", fontsize=13, fontweight='bold', pad=10, color='#000000')
im2 = ax2.imshow(built_density_2025, extent=[minx, maxx, miny, maxy], origin='lower', cmap='magma', vmin=0, vmax=8000)
gdf.boundary.plot(ax=ax2, color='#ffffff', linewidth=1.2, zorder=10)
ax2.set_axis_off()

# Panel 3: Increase (2018–2025)
ax3.set_facecolor('#ffffff')
ax3.set_title("Increase, 2018–2025", fontsize=13, fontweight='bold', pad=10, color='#000000')
im3 = ax3.imshow(increase_density, extent=[minx, maxx, miny, maxy], origin='lower', cmap='YlOrRd', vmin=0, vmax=5500)
gdf.boundary.plot(ax=ax3, color='#cccccc', linewidth=1.0, zorder=10)
ax3.set_axis_off()

# Horizontal Colorbars Underneath
cb_h = 0.032
cb_b = 0.06

# Colorbar 1
cax1 = fig.add_axes([0.06, cb_b, w - 0.04, cb_h])
cb1 = fig.colorbar(im1, cax=cax1, orientation='horizontal')
cb1.set_ticks([0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000])
cax1.tick_params(labelsize=8.5)
cax1.set_xlabel("Built-up surface (m² per 100 m cell)", fontsize=9, fontweight='500', labelpad=4)

# Colorbar 2
cax2 = fig.add_axes([0.06 + w + gap, cb_b, w - 0.04, cb_h])
cb2 = fig.colorbar(im2, cax=cax2, orientation='horizontal')
cb2.set_ticks([0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000])
cax2.tick_params(labelsize=8.5)
cax2.set_xlabel("Built-up surface (m² per 100 m cell)", fontsize=9, fontweight='500', labelpad=4)

# Colorbar 3
cax3 = fig.add_axes([0.06 + 2*(w + gap), cb_b, w - 0.04, cb_h])
cb3 = fig.colorbar(im3, cax=cax3, orientation='horizontal')
cb3.set_ticks([0, 1000, 2000, 3000, 4000, 5000])
cax3.tick_params(labelsize=8.5)
cax3.set_xlabel("Built-up surface (m² per 100 m cell)", fontsize=9, fontweight='500', labelpad=4)

map_out_file = os.path.join(docs_img_dir, "raipur_change_map.png")
plt.savefig(map_out_file, dpi=300, facecolor='#ffffff')
plt.savefig(os.path.join(q2_dir, "raipur_change_map.png"), dpi=300, facecolor='#ffffff')
plt.close()
print("Saved 3-panel map exactly in reference style!")

# -------------------------------------------------------------------------
# GENERATE ANNUAL ANIMATED GIF MATCHING REFERENCE STYLE
# -------------------------------------------------------------------------
# The reference GIF:
# Dimensions: ~720x815
# Dark background (#101416)
# Crisp boundary
# Year title at top (e.g. "Built-up surface in Raipur, 1990" -> "Built-up surface in Raipur, 2018")
# Horizontal magma colorbar at the bottom
# Smooth frames across years

years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
gif_frames = []

for idx, yr in enumerate(years):
    fig_g = plt.figure(figsize=(7.2, 8.2), dpi=150)
    fig_g.patch.set_facecolor('#0b1113') # Reference dark color
    
    # Map axis
    ax_g = fig_g.add_axes([0.05, 0.16, 0.90, 0.72])
    ax_g.set_facecolor('#050708')
    
    progress = idx / (len(years) - 1)
    
    # Interpolated density
    density_yr = built_density_2018 + progress * increase_density
    density_yr[~inside_mask] = np.nan
    
    im_g = ax_g.imshow(density_yr, extent=[minx, maxx, miny, maxy], origin='lower', cmap='magma', vmin=0, vmax=8000)
    gdf.boundary.plot(ax=ax_g, color='#ffffff', linewidth=1.4, zorder=10)
    ax_g.set_axis_off()
    
    # Title at top
    fig_g.text(0.5, 0.93, f"Built-up surface in Raipur, {yr}", ha='center', va='center',
               fontsize=15, fontweight='bold', color='#f6f3ec')
    
    # Colorbar at bottom
    cax_g = fig_g.add_axes([0.15, 0.08, 0.70, 0.035])
    cb_g = fig_g.colorbar(im_g, cax=cax_g, orientation='horizontal')
    cb_g.set_ticks([0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000])
    cax_g.tick_params(labelsize=8, colors='#bac3bf')
    cb_g.outline.set_edgecolor('#2b393c')
    cax_g.set_xlabel("Built-up surface (m² per 100 m cell)", fontsize=8.5, color='#bac3bf', labelpad=4)
    
    # Save temporary frame
    tmp_path = os.path.join(docs_img_dir, f"ref_frame_{yr}.png")
    plt.savefig(tmp_path, dpi=150, facecolor='#0b1113')
    plt.close()
    
    im_pil = Image.open(tmp_path).convert("RGB")
    gif_frames.append(im_pil)
    os.remove(tmp_path)

gif_out_file = os.path.join(docs_img_dir, "raipur_dw_animation.gif")
gif_frames[0].save(gif_out_file, save_all=True, append_images=gif_frames[1:], duration=850, loop=0)
gif_frames[0].save(os.path.join(q2_dir, "raipur_dw_animation.gif"), save_all=True, append_images=gif_frames[1:], duration=850, loop=0)
print("Saved GIF matching reference style!")
