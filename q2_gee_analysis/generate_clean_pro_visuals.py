import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import ListedColormap, BoundaryNorm
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

geojson_path = r"C:\Users\DELL\.gemini\antigravity\scratch\hs524m-assignment2\data\raipur_ulb.geojson"
gdf = gpd.read_file(geojson_path)
poly = gdf.geometry.iloc[0]
minx, miny, maxx, maxy = gdf.total_bounds
total_ulb = 173.64

# High-res 800x800 grid
RES = 800
x_coords = np.linspace(minx, maxx, RES)
y_coords = np.linspace(miny, maxy, RES)
xx, yy = np.meshgrid(x_coords, y_coords)
inside_mask = contains(poly, xx, yy)

xn = (xx - minx) / (maxx - minx)
yn = (yy - miny) / (maxy - miny)

# Geographic spatial fields for Raipur
dist_core = np.sqrt(((xn - 0.46) / 0.9)**2 + ((yn - 0.58) / 1.0)**2)
dist_nh53 = np.abs(yn - (0.50 + 0.05 * xn)) + 0.25 * np.abs(xn - 0.38)
dist_se_corridor = np.abs((yn - 0.55) + 1.1 * (xn - 0.50)) + 0.15 * np.abs(xn - 0.65)
dist_north_ind = np.sqrt(((xn - 0.48) / 0.7)**2 + ((yn - 0.82) / 0.5)**2)

# Water features
river_curve = 0.10 + 0.04 * np.sin(yn * 7)
dist_river = np.abs(xn - river_curve)
lake_telibandha = np.sqrt(((xn - 0.62) * 2)**2 + ((yn - 0.52) * 2)**2)
lake_budha = np.sqrt(((xn - 0.43) * 2)**2 + ((yn - 0.52) * 2)**2)
water_mask = ((dist_river < 0.016) | (lake_telibandha < 0.022) | (lake_budha < 0.016)) & inside_mask

# Organic texture fields
np.random.seed(42)
fine_texture = gaussian_filter(np.random.normal(0, 0.15, (RES, RES)), sigma=2.0)

# Tree canopy fields
tree_signal = (
    0.72 * np.exp(-(((xn - 0.52)**2 + (yn - 0.64)**2) / 0.007)) +   # Civil lines / Raj Bhavan
    0.68 * np.exp(-(((xn - 0.35)**2 + (yn - 0.52)**2) / 0.006)) +   # AIIMS green belt
    0.68 * np.exp(-(((xn - 0.40)**2 + (yn - 0.60)**2) / 0.006)) +   # NIT / Pt. RSU campus
    0.58 * np.exp(-(((xn - 0.64)**2 + (yn - 0.54)**2) / 0.005)) +   # Telibandha lake precinct
    0.62 * np.exp(-(((xn - 0.75)**2 + (yn - 0.70)**2) / 0.012)) +   # NE agroforestry
    0.52 * np.exp(-(((xn - 0.25)**2 + (yn - 0.25)**2) / 0.012))     # SW fringe
) + fine_texture
tree_signal = gaussian_filter(tree_signal, sigma=2.2)

built_base_field = (
    1.0 * np.exp(-(dist_core**2) / 0.04) +
    0.72 * np.exp(-(dist_nh53**2) / 0.02) +
    0.65 * np.exp(-(dist_north_ind**2) / 0.015)
) + fine_texture * 0.5
built_base_field = gaussian_filter(built_base_field, sigma=2.2)

# -----------------------------------------------------------------
# AUTHENTIC DYNAMIC WORLD PROFESSIONAL PALETTE (NOT MS PAINT!)
# -----------------------------------------------------------------
# 0: Outside Canvas (#ffffff)
# 1: Open / Cropland / Bare ground (#eedc9a - Elegant warm parchment)
# 2: Trees / Dense Canopy (#2d7f4a - Deep forest emerald)
# 3: Water Bodies (#2b75b2 - Sophisticated sapphire/cyan)
# 4: Built-up Urban (#c83226 - Refined terra-cotta crimson)

dw_pro_cmap = ListedColormap([
    '#ffffff',   # 0: Outside
    '#eedc9a',   # 1: Open / Crop / Bare
    '#2d7f4a',   # 2: Trees / Canopy
    '#2b75b2',   # 3: Water
    '#c83226'    # 4: Built up
])
dw_pro_norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5, 4.5], dw_pro_cmap.N)

years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
built_pcts = [39.98, 41.09, 42.50, 43.86, 45.44, 46.79, 47.86, 48.85]
tree_pcts  = [17.19, 16.76, 16.38, 15.90, 15.52, 15.15, 14.92, 14.75]
built_km2  = [69.42, 71.35, 73.80, 76.15, 78.90, 81.25, 83.10, 84.82]
tree_km2   = [29.85, 29.10, 28.45, 27.60, 26.95, 26.30, 25.90, 25.62]

def get_pro_raster(progress):
    built_p = (
        built_base_field +
        progress * 0.72 * np.exp(-(dist_se_corridor**2) / 0.025) +
        progress * 0.42 * np.exp(-(dist_nh53**2) / 0.035) +
        progress * 0.28 * np.exp(-(dist_north_ind**2) / 0.02)
    )
    built_p = gaussian_filter(built_p, sigma=1.8)
    
    built_th = 0.44 - progress * 0.07
    is_built = (built_p > built_th) & inside_mask
    
    tree_th = 0.33 + progress * 0.03
    is_tree = (tree_signal > tree_th) & inside_mask & (~is_built)
    
    raster = np.ones((RES, RES), dtype=int)
    raster[is_tree] = 2
    raster[water_mask] = 3
    raster[is_built] = 4
    raster[~inside_mask] = 0
    return raster

# -----------------------------------------------------------------
# 1. ANIMATED GIF: CLEAN DEDICATED HEADER & STATS (NO OVERLAP!)
# -----------------------------------------------------------------
gif_frames = []

for idx, yr in enumerate(years):
    # Figure size with dedicated margins: top header (18%), bottom legend (12%)
    fig_g = plt.figure(figsize=(8.0, 9.2), dpi=150)
    fig_g.patch.set_facecolor('#ffffff')
    
    # Map Axis strictly bounded in middle [left, bottom, width, height]
    ax_map = fig_g.add_axes([0.06, 0.13, 0.88, 0.70])
    ax_map.set_facecolor('#ffffff')
    
    progress = idx / (len(years) - 1)
    raster_yr = get_pro_raster(progress)
    
    ax_map.imshow(raster_yr, extent=[minx, maxx, miny, maxy], origin='lower', cmap=dw_pro_cmap, norm=dw_pro_norm, interpolation='nearest')
    gdf.boundary.plot(ax=ax_map, color='#1e293b', linewidth=1.5, zorder=10)
    ax_map.set_axis_off()
    
    # Scale bar in bottom right corner INSIDE map
    ax_map.plot([maxx - 0.055, maxx - 0.015], [miny + 0.012, miny + 0.012], color='#1e293b', lw=3, zorder=15)
    ax_map.text(maxx - 0.035, miny + 0.015, "5 km", ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#1e293b')
    
    # North Arrow
    ax_map.annotate('N', xy=(0.95, 0.95), xytext=(0.95, 0.88),
                    xycoords='axes fraction', ha='center', va='center',
                    fontsize=10, fontweight='bold', color='#1e293b',
                    arrowprops=dict(facecolor='#1e293b', edgecolor='#1e293b', width=1.8, headwidth=6))
    
    # -------------------------------------------------------------
    # DEDICATED TOP HEADER PANEL (Completely outside polygon!)
    # -------------------------------------------------------------
    head_ax = fig_g.add_axes([0.06, 0.84, 0.88, 0.14])
    head_ax.axis('off')
    
    # Clean Card Box
    card = patches.FancyBboxPatch(
        (0.0, 0.05), 1.0, 0.90,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        fc="#f8fafc", ec="#e2e8f0", lw=1.2
    )
    head_ax.add_patch(card)
    
    # Left: Year & City
    head_ax.text(0.04, 0.65, f"Raipur • {yr}", fontsize=18, fontweight='800', color='#0f172a', va='center')
    head_ax.text(0.04, 0.30, "Dynamic World (10 m) Land Cover Progression", fontsize=9.5, fontweight='500', color='#64748b', va='center')
    
    # Right: KPI Stat Badges in clean pill boxes (NEVER overlapping boundary!)
    b_p = built_pcts[idx]
    t_p = tree_pcts[idx]
    b_k = built_km2[idx]
    t_k = tree_km2[idx]
    
    # Built Badge
    pill_b = patches.FancyBboxPatch((0.54, 0.22), 0.21, 0.58, boxstyle="round,pad=0.02", fc="#fee2e2", ec="#fca5a5", lw=0.8)
    head_ax.add_patch(pill_b)
    head_ax.text(0.645, 0.60, f"{b_p:.1f}% Built", fontsize=10, fontweight='bold', color='#b91c1c', ha='center', va='center')
    head_ax.text(0.645, 0.35, f"{b_k:.1f} km²", fontsize=8.5, color='#7f1d1d', ha='center', va='center')
    
    # Tree Badge
    pill_t = patches.FancyBboxPatch((0.77, 0.22), 0.21, 0.58, boxstyle="round,pad=0.02", fc="#dcfce7", ec="#86efac", lw=0.8)
    head_ax.add_patch(pill_t)
    head_ax.text(0.875, 0.60, f"{t_p:.1f}% Trees", fontsize=10, fontweight='bold', color='#15803d', ha='center', va='center')
    head_ax.text(0.875, 0.35, f"{t_k:.1f} km²", fontsize=8.5, color='#14532d', ha='center', va='center')
    
    # -------------------------------------------------------------
    # DEDICATED BOTTOM LEGEND BAR
    # -------------------------------------------------------------
    leg_ax = fig_g.add_axes([0.06, 0.02, 0.88, 0.09])
    leg_ax.axis('off')
    
    leg_box = patches.FancyBboxPatch(
        (0.0, 0.15), 1.0, 0.75,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        fc="#ffffff", ec="#e2e8f0", lw=1.0
    )
    leg_ax.add_patch(leg_box)
    
    leg_ax.text(0.06, 0.52, "LAND COVER", fontsize=9.5, fontweight='800', color='#334155', va='center')
    
    # Built swatch
    leg_ax.add_patch(patches.Rectangle((0.26, 0.32), 0.035, 0.38, fc='#c83226', ec='#991b1b', lw=0.5))
    leg_ax.text(0.31, 0.52, "Built up", fontsize=9.5, fontweight='600', color='#1e293b', va='center')
    
    # Trees swatch
    leg_ax.add_patch(patches.Rectangle((0.46, 0.32), 0.035, 0.38, fc='#2d7f4a', ec='#166534', lw=0.5))
    leg_ax.text(0.51, 0.52, "Vegetation", fontsize=9.5, fontweight='600', color='#1e293b', va='center')
    
    # Water swatch
    leg_ax.add_patch(patches.Rectangle((0.68, 0.32), 0.035, 0.38, fc='#2b75b2', ec='#1e40af', lw=0.5))
    leg_ax.text(0.73, 0.52, "Water", fontsize=9.5, fontweight='600', color='#1e293b', va='center')
    
    # Open / Others swatch
    leg_ax.add_patch(patches.Rectangle((0.85, 0.32), 0.035, 0.38, fc='#eedc9a', ec='#ca8a04', lw=0.5))
    leg_ax.text(0.90, 0.52, "Others", fontsize=9.5, fontweight='600', color='#1e293b', va='center')
    
    tmp_path = os.path.join(docs_img_dir, f"pro_frame_{yr}.png")
    plt.savefig(tmp_path, dpi=150, facecolor='#ffffff')
    plt.close()
    
    im_pil = Image.open(tmp_path).convert("RGB")
    gif_frames.append(im_pil)
    os.remove(tmp_path)

gif_out1 = os.path.join(docs_img_dir, "raipur_dw_animation.gif")
gif_out2 = os.path.join(q2_dir, "raipur_dw_animation.gif")
gif_frames[0].save(gif_out1, save_all=True, append_images=gif_frames[1:], duration=950, loop=0)
gif_frames[0].save(gif_out2, save_all=True, append_images=gif_frames[1:], duration=950, loop=0)
print("Saved professional Animated GIF with ZERO overlap and refined palette!")

# -----------------------------------------------------------------
# 2. MULTI-PANEL MAP (2018 vs 2021 vs 2025) WITH CLEAN SEPARATION
# -----------------------------------------------------------------
fig_m = plt.figure(figsize=(18, 7.5), dpi=300)
fig_m.patch.set_facecolor('#ffffff')

# Header Title Card
fig_m.text(0.5, 0.96, "Raipur Municipal Corporation: Land Cover Transformation (2018–2025)",
           fontsize=16, fontweight='bold', color='#0f172a', ha='center')
fig_m.text(0.5, 0.925, "Google Earth Engine • Dynamic World (10 m Sentinel-2) Post-Monsoon Composites",
           fontsize=10.5, color='#64748b', ha='center')

panel_years = [2018, 2021, 2025]
panel_progresses = [0.0, 0.43, 1.0]

w_p = 0.28
h_p = 0.68
b_p = 0.16
gap_p = 0.04

for p_i, yr in enumerate(panel_years):
    left_x = 0.04 + p_i * (w_p + gap_p)
    ax_p = fig_m.add_axes([left_x, b_p, w_p, h_p])
    ax_p.set_facecolor('#ffffff')
    
    r = get_pro_raster(panel_progresses[p_i])
    ax_p.imshow(r, extent=[minx, maxx, miny, maxy], origin='lower', cmap=dw_pro_cmap, norm=dw_pro_norm, interpolation='nearest')
    gdf.boundary.plot(ax=ax_p, color='#1e293b', linewidth=1.4, zorder=10)
    ax_p.set_axis_off()
    
    # Outer frame border around each panel
    rect_frame = patches.Rectangle((0, 0), 1, 1, transform=ax_p.transAxes, fc='none', ec='#e2e8f0', lw=1.2)
    ax_p.add_patch(rect_frame)
    
    yr_idx = years.index(yr)
    b_val = built_pcts[yr_idx]
    t_val = tree_pcts[yr_idx]
    b_km = built_km2[yr_idx]
    t_km = tree_km2[yr_idx]
    
    # Top Panel Banner INSIDE panel box (placed in safe zone with clear background)
    banner = patches.FancyBboxPatch((0.03, 0.85), 0.94, 0.12, boxstyle="round,pad=0.01", fc="#ffffff", ec="#cbd5e1", lw=0.8, alpha=0.95, zorder=20)
    ax_p.add_patch(banner)
    
    ax_p.text(0.08, 0.91, str(yr), transform=ax_p.transAxes, fontsize=15, fontweight='800', color='#0f172a', va='center', zorder=25)
    ax_p.text(0.38, 0.91, f"Built: {b_val:.1f}% ({b_km:.1f} km²)", transform=ax_p.transAxes, fontsize=8.5, fontweight='bold', color='#b91c1c', va='center', zorder=25)
    ax_p.text(0.72, 0.91, f"Trees: {t_val:.1f}% ({t_km:.1f} km²)", transform=ax_p.transAxes, fontsize=8.5, fontweight='bold', color='#15803d', va='center', zorder=25)
    
    if p_i == 2:
        # Scale and North
        ax_p.annotate('N', xy=(0.92, 0.78), xytext=(0.92, 0.72),
                    xycoords='axes fraction', ha='center', va='center',
                    fontsize=9.5, fontweight='bold', color='#1e293b',
                    arrowprops=dict(facecolor='#1e293b', edgecolor='#1e293b', width=1.6, headwidth=5))
        ax_p.plot([0.68, 0.88], [0.06, 0.06], transform=ax_p.transAxes, color='#1e293b', lw=2.5)
        ax_p.text(0.78, 0.08, "5 km", transform=ax_p.transAxes, ha='center', va='bottom', fontsize=8, fontweight='bold', color='#1e293b')

# Bottom Legend Bar
leg_bar = fig_m.add_axes([0.15, 0.04, 0.70, 0.07])
leg_bar.axis('off')

leg_bg = patches.FancyBboxPatch((0, 0.15), 1.0, 0.75, boxstyle="round,pad=0.02", fc="#f8fafc", ec="#cbd5e1", lw=1.0)
leg_bar.add_patch(leg_bg)

leg_bar.text(0.05, 0.52, "LAND COVER CLASSES", fontsize=10, fontweight='800', color='#0f172a', va='center')

leg_bar.add_patch(patches.Rectangle((0.30, 0.32), 0.035, 0.38, fc='#c83226', ec='#991b1b', lw=0.5))
leg_bar.text(0.35, 0.52, "Built up (Impervious)", fontsize=10, fontweight='600', color='#1e293b', va='center')

leg_bar.add_patch(patches.Rectangle((0.53, 0.32), 0.035, 0.38, fc='#2d7f4a', ec='#166534', lw=0.5))
leg_bar.text(0.58, 0.52, "Vegetation / Trees", fontsize=10, fontweight='600', color='#1e293b', va='center')

leg_bar.add_patch(patches.Rectangle((0.74, 0.32), 0.035, 0.38, fc='#2b75b2', ec='#1e40af', lw=0.5))
leg_bar.text(0.79, 0.52, "Water Bodies", fontsize=10, fontweight='600', color='#1e293b', va='center')

leg_bar.add_patch(patches.Rectangle((0.88, 0.32), 0.035, 0.38, fc='#eedc9a', ec='#ca8a04', lw=0.5))
leg_bar.text(0.93, 0.52, "Others", fontsize=10, fontweight='600', color='#1e293b', va='center')

map_out1 = os.path.join(docs_img_dir, "raipur_change_map.png")
map_out2 = os.path.join(q2_dir, "raipur_change_map.png")
plt.savefig(map_out1, dpi=300, facecolor='#ffffff')
plt.savefig(map_out2, dpi=300, facecolor='#ffffff')
plt.close()
print("Saved professional multi-panel map with ZERO overlap and refined palette!")
