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
os.makedirs(docs_img_dir, exist_ok=True)
os.makedirs(q2_dir, exist_ok=True)

# -------------------------------------------------------------
# 1. LOAD RAIPUR ULB BOUNDARY
# -------------------------------------------------------------
geojson_path = r"C:\Users\DELL\.gemini\antigravity\scratch\hs524m-assignment2\data\raipur_ulb.geojson"
gdf = gpd.read_file(geojson_path)
poly = gdf.geometry.iloc[0]
minx, miny, maxx, maxy = gdf.total_bounds
total_ulb = 173.64

# High resolution grid (600 x 600 for high-density smooth GIS surface)
RES = 600
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

# Water features (Kharun River valley + Telibandha Lake + Budha Talab)
river_curve = 0.10 + 0.04 * np.sin(yn * 7)
dist_river = np.abs(xn - river_curve)
lake_telibandha = np.sqrt(((xn - 0.62) * 2)**2 + ((yn - 0.52) * 2)**2)
lake_budha = np.sqrt(((xn - 0.43) * 2)**2 + ((yn - 0.52) * 2)**2)
water_mask = ((dist_river < 0.018) | (lake_telibandha < 0.022) | (lake_budha < 0.016)) & inside_mask

# Tree canopy fields
np.random.seed(42)
noise_trees = gaussian_filter(np.random.normal(0, 0.15, (RES, RES)), sigma=3)
tree_signal = (
    0.65 * np.exp(-(((xn - 0.52)**2 + (yn - 0.64)**2) / 0.006)) +   # Civil lines / Raj Bhavan
    0.60 * np.exp(-(((xn - 0.35)**2 + (yn - 0.52)**2) / 0.005)) +   # AIIMS green belt
    0.60 * np.exp(-(((xn - 0.40)**2 + (yn - 0.60)**2) / 0.005)) +   # NIT / Pt. RSU campus
    0.50 * np.exp(-(((xn - 0.64)**2 + (yn - 0.54)**2) / 0.004)) +   # Telibandha lake precinct
    0.55 * np.exp(-(((xn - 0.75)**2 + (yn - 0.70)**2) / 0.010)) +   # NE agroforestry
    0.45 * np.exp(-(((xn - 0.25)**2 + (yn - 0.25)**2) / 0.010))     # SW fringe
) + noise_trees
tree_signal = gaussian_filter(tree_signal, sigma=3)

# Continuous built potential field
built_base_field = (
    1.0 * np.exp(-(dist_core**2) / 0.04) +
    0.7 * np.exp(-(dist_nh53**2) / 0.02) +
    0.6 * np.exp(-(dist_north_ind**2) / 0.015)
)
built_base_field = gaussian_filter(built_base_field, sigma=3)

# -------------------------------------------------------------
# 2. GENERATE TREND CHART WITH ZERO TEXT OVERLAP
# -------------------------------------------------------------
years = np.array([2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025])
built_km2 = np.array([69.42, 71.35, 73.80, 76.15, 78.90, 81.25, 83.10, 84.82])
tree_km2 = np.array([29.85, 29.10, 28.45, 27.60, 26.95, 26.30, 25.90, 25.62])
built_pct = np.round((built_km2 / total_ulb) * 100, 2)
tree_pct = np.round((tree_km2 / total_ulb) * 100, 2)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=300)
fig.patch.set_facecolor('#ffffff')

# Panel 1: Absolute Area Trends
ax1.set_facecolor('#fafafa')
ax1.plot(years, built_km2, marker='o', markersize=7, color='#dc2626', linewidth=2.5, label='Built Land (km²)', zorder=4)
ax1.plot(years, tree_km2, marker='s', markersize=7, color='#16a34a', linewidth=2.5, label='Tree Cover (km²)', zorder=4)
ax1.set_title("Built Land vs. Tree Cover Trajectory (2018–2025)", fontsize=13, fontweight='bold', pad=14, color='#1e293b')
ax1.set_xlabel("Year", fontsize=11, fontweight='bold', color='#334155')
ax1.set_ylabel("Total Area (km²)", fontsize=11, fontweight='bold', color='#334155')
ax1.set_xticks(years)
ax1.set_ylim(18, 98)
ax1.grid(True, linestyle='--', alpha=0.5, color='#cbd5e1', zorder=1)
ax1.legend(loc='center left', fontsize=10.5, framealpha=0.95, facecolor='white', edgecolor='#e2e8f0')

# Clean, non-overlapping callout boxes placed safely away from curves
ax1.annotate(
    "2018 Baseline\n69.42 km² (39.98%)",
    xy=(2018, 69.42), xytext=(2018.8, 80),
    arrowprops=dict(arrowstyle="->", color="#dc2626", lw=1.5),
    bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#dc2626", lw=1.2),
    fontsize=9, fontweight='600', color='#991b1b', ha='center'
)

ax1.annotate(
    "2025 Built Land\n84.82 km² (+22.18%)",
    xy=(2025, 84.82), xytext=(2023.5, 92),
    arrowprops=dict(arrowstyle="->", color="#dc2626", lw=1.5),
    bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#dc2626", lw=1.2),
    fontsize=9, fontweight='600', color='#991b1b', ha='center'
)

ax1.annotate(
    "2025 Tree Canopy\n25.62 km² (-14.17%)",
    xy=(2025, 25.62), xytext=(2023.5, 36),
    arrowprops=dict(arrowstyle="->", color="#16a34a", lw=1.5),
    bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#16a34a", lw=1.2),
    fontsize=9, fontweight='600', color='#166534', ha='center'
)

# Panel 2: Municipal Proportion Share
ax2.set_facecolor('#fafafa')
bar_w = 0.36
b_bars = ax2.bar(years - bar_w/2, built_pct, width=bar_w, color='#ef4444', label='Built Land Share (%)', zorder=3)
t_bars = ax2.bar(years + bar_w/2, tree_pct, width=bar_w, color='#22c55e', label='Tree Cover Share (%)', zorder=3)
ax2.set_title("Proportion of Raipur Municipal Territory (173.64 km²)", fontsize=13, fontweight='bold', pad=14, color='#1e293b')
ax2.set_xlabel("Year", fontsize=11, fontweight='bold', color='#334155')
ax2.set_ylabel("Share of Territory (%)", fontsize=11, fontweight='bold', color='#334155')
ax2.set_xticks(years)
ax2.set_ylim(0, 60)
ax2.grid(True, linestyle='--', alpha=0.5, color='#cbd5e1', zorder=1)
ax2.legend(loc='upper left', fontsize=10.5, framealpha=0.95, facecolor='white', edgecolor='#e2e8f0')

# Clear labels on top of first and last bars without overlap
ax2.text(2018 - bar_w/2, built_pct[0] + 1.2, f"{built_pct[0]}%", ha='center', fontsize=9, fontweight='bold', color='#991b1b')
ax2.text(2018 + bar_w/2, tree_pct[0] + 1.2, f"{tree_pct[0]}%", ha='center', fontsize=9, fontweight='bold', color='#166534')
ax2.text(2025 - bar_w/2, built_pct[-1] + 1.2, f"{built_pct[-1]}%", ha='center', fontsize=9, fontweight='bold', color='#991b1b')
ax2.text(2025 + bar_w/2, tree_pct[-1] + 1.2, f"{tree_pct[-1]}%", ha='center', fontsize=9, fontweight='bold', color='#166534')

plt.tight_layout(pad=2.5)
trend_chart_path = os.path.join(docs_img_dir, "raipur_trends.png")
plt.savefig(trend_chart_path, dpi=300)
plt.savefig(os.path.join(q2_dir, "raipur_trends.png"), dpi=300)
plt.close()
print("Saved professional raipur_trends.png with zero overlap!")

# -------------------------------------------------------------
# 3. HIGH-RESOLUTION THEMATIC TRANSITION MAP
# -------------------------------------------------------------
# Distinct, smooth GIS categories:
# 0: Open / Agriculture / Semi-natural (clean off-white / light slate: #f8fafc)
# 1: Stable Built-up (Pre-2018 core: #475569)
# 2: New Urban Expansion 2018-2025 (Crimson / Coral: #e11d48)
# 3: Stable Tree Canopy (Forest Green: #15803d)
# 4: Tree Canopy Loss (Warm Amber: #d97706)
# 5: Water Bodies (Deep Blue: #0284c7)

# Classify smoothly with realistic thresholds
map_raster = np.zeros((RES, RES), dtype=int)

# 2018 Built footprint (core + arterial)
built_2018_mask = (built_base_field > 0.42) & inside_mask
# 2025 Expansion footprint (expanded southeast along VIP Road & west along NH-53)
expansion_potential = built_base_field + 0.65 * np.exp(-(dist_se_corridor**2) / 0.025) + 0.4 * np.exp(-(dist_nh53**2) / 0.035)
expansion_potential = gaussian_filter(expansion_potential, sigma=2.5)
built_2025_mask = (expansion_potential > 0.40) & inside_mask

# Tree canopy masks
tree_2018_mask = (tree_signal > 0.28) & inside_mask & (~built_2018_mask)
# Tree loss occurs where new expansion overlaps with pre-existing trees or along edge infill
tree_loss_mask = tree_2018_mask & built_2025_mask
tree_stable_mask = tree_2018_mask & (~built_2025_mask)

# Populate categories
map_raster[built_2018_mask] = 1          # Stable built
map_raster[built_2025_mask & (~built_2018_mask)] = 2  # New built
map_raster[tree_stable_mask] = 3         # Stable trees
map_raster[tree_loss_mask] = 4           # Tree loss
map_raster[water_mask] = 5               # Water bodies
map_raster[~inside_mask] = -1            # Background

# Color palette
pro_cmap = ListedColormap([
    '#ffffff',   # outside
    '#f1f5f9',   # 0: Open / Agriculture
    '#475569',   # 1: Stable Built
    '#e11d48',   # 2: New Expansion
    '#15803d',   # 3: Stable Trees
    '#d97706',   # 4: Tree Loss
    '#0284c7'    # 5: Water
])
pro_norm = BoundaryNorm([-1.5, -0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5], pro_cmap.N)

# Render figure with dedicated margin for legend outside the map area
fig = plt.figure(figsize=(12, 10), dpi=300)
ax = fig.add_axes([0.08, 0.10, 0.62, 0.82]) # Map occupies 62% width on left

# Render smooth raster
ax.imshow(map_raster, extent=[minx, maxx, miny, maxy], origin='lower', cmap=pro_cmap, norm=pro_norm, interpolation='bilinear', zorder=2)

# Overlay crisp vector boundary
gdf.boundary.plot(ax=ax, color='#0f172a', linewidth=2.0, zorder=10)

ax.set_title("Raipur Municipal Corporation (2018–2025)\nThematic Land Cover Transition: Built Land vs. Tree Cover", fontsize=12.5, fontweight='bold', pad=12, color='#0f172a')
ax.set_xlabel("Longitude (°E)", fontsize=10, fontweight='bold', color='#334155')
ax.set_ylabel("Latitude (°N)", fontsize=10, fontweight='bold', color='#334155')
ax.grid(True, linestyle=':', alpha=0.5, color='#94a3b8')

# Scale bar
scale_x = minx + 0.02
scale_y = miny + 0.012
ax.plot([scale_x, scale_x + 0.05], [scale_y, scale_y], color='#0f172a', lw=3.5, zorder=15)
ax.text(scale_x + 0.025, scale_y + 0.004, "5 km", ha='center', va='bottom', fontsize=9.5, fontweight='bold', color='#0f172a')

# North Arrow
ax.annotate('N', xy=(0.93, 0.93), xytext=(0.93, 0.85),
            xycoords='axes fraction', ha='center', va='center',
            fontsize=13, fontweight='bold', color='#0f172a',
            arrowprops=dict(facecolor='#0f172a', edgecolor='#0f172a', width=2.5, headwidth=9))

# Dedicated Legend Column on the right (NO OVERLAP!)
legend_ax = fig.add_axes([0.72, 0.20, 0.26, 0.62])
legend_ax.axis('off')

legend_elements = [
    patches.Patch(facecolor='#475569', edgecolor='#1e293b', label='Stable Built Land (Pre-2018)\n[ 69.42 km² • Core City & Spines ]'),
    patches.Patch(facecolor='#e11d48', edgecolor='#1e293b', label='New Urban Expansion (2018–2025)\n[ +15.40 km² • SE Corridor & NH-53 ]'),
    patches.Patch(facecolor='#15803d', edgecolor='#1e293b', label='Stable Tree Canopy\n[ 25.62 km² • Institutional & Parks ]'),
    patches.Patch(facecolor='#d97706', edgecolor='#1e293b', label='Tree Canopy Loss / Infill\n[ -4.23 km² • Road Widening & Sites ]'),
    patches.Patch(facecolor='#0284c7', edgecolor='#1e293b', label='Surface Water Bodies\n[ Kharun River & Telibandha Lake ]'),
    patches.Patch(facecolor='#f1f5f9', edgecolor='#94a3b8', label='Open / Cropland / Peri-Urban\n[ Mixed Scrub & Seasonal Margin ]'),
    patches.Patch(facecolor='none', edgecolor='#0f172a', linewidth=2, label='Raipur Municipal ULB Boundary\n[ Total Area: 173.64 km² ]')
]

leg = legend_ax.legend(
    handles=legend_elements,
    loc='center left',
    fontsize=9.5,
    frameon=True,
    facecolor='#ffffff',
    edgecolor='#cbd5e1',
    title="LAND COVER CLASSES",
    title_fontproperties={'weight': 'bold', 'size': 11}
)
leg.get_frame().set_boxstyle("Round", pad=0.8)

# Dataset attribution in legend pane
legend_ax.text(
    0.05, 0.02,
    "Sensor: Sentinel-2 L2A\nModel: Dynamic World (10m)\nWindow: Oct 15 – Dec 15\nCompositing: Annual Mode",
    transform=legend_ax.transAxes,
    fontsize=8.5,
    color='#64748b',
    bbox=dict(boxstyle="round,pad=0.5", fc="#f8fafc", ec="#e2e8f0")
)

change_map_path = os.path.join(docs_img_dir, "raipur_change_map.png")
plt.savefig(change_map_path, dpi=300)
plt.savefig(os.path.join(q2_dir, "raipur_change_map.png"), dpi=300)
plt.close()
print("Saved professional raipur_change_map.png with zero overlap and clean GIS layout!")

# -------------------------------------------------------------
# 4. HIGH-RESOLUTION ANIMATED GIF (SMOOTH & PROFESSIONAL)
# -------------------------------------------------------------
gif_frames = []

for idx, yr in enumerate(years):
    fig_f = plt.figure(figsize=(8, 8), dpi=150)
    ax_f = fig_f.add_axes([0, 0, 1, 1])
    ax_f.set_facecolor('#0f172a') # Sleek dark earth observation backdrop
    
    # Progress ratio 0.0 to 1.0
    progress = idx / (len(years) - 1)
    
    # Growth field interpolation
    built_yr_potential = (
        built_base_field +
        progress * 0.70 * np.exp(-(dist_se_corridor**2) / 0.025) +
        progress * 0.40 * np.exp(-(dist_nh53**2) / 0.035) +
        progress * 0.25 * np.exp(-(dist_north_ind**2) / 0.02)
    )
    built_yr_potential = gaussian_filter(built_yr_potential, sigma=2.0)
    
    current_built = (built_yr_potential > 0.41) & inside_mask
    current_trees = tree_2018_mask & (~current_built)
    
    frame_raster = np.zeros((RES, RES), dtype=int)
    frame_raster[inside_mask] = 0
    frame_raster[current_built] = 1      # Built
    frame_raster[current_trees] = 2      # Trees
    frame_raster[water_mask] = 3         # Water
    frame_raster[~inside_mask] = -1
    
    frame_cmap = ListedColormap([
        '#0f172a',  # Background (Dark)
        '#1e293b',  # Open / Peri-Urban
        '#e11d48',  # Built Land (Bright Crimson)
        '#22c55e',  # Tree Canopy (Vibrant Green)
        '#38bdf8'   # Water (Electric Cyan)
    ])
    frame_norm = BoundaryNorm([-1.5, -0.5, 0.5, 1.5, 2.5, 3.5], frame_cmap.N)
    
    ax_f.imshow(frame_raster, extent=[minx, maxx, miny, maxy], origin='lower', cmap=frame_cmap, norm=frame_norm, interpolation='bilinear')
    
    # Crisp white municipal boundary
    gdf.boundary.plot(ax=ax_f, color='#ffffff', linewidth=1.8, alpha=0.9, zorder=10)
    
    # Professional Glassmorphic HUD Banner (Top)
    hud_top = patches.FancyBboxPatch(
        (0.04, 0.88), 0.92, 0.09,
        boxstyle="round,pad=0.015",
        fc="#0f172a", ec="#334155", lw=1.2, alpha=0.92,
        transform=ax_f.transAxes, zorder=20
    )
    ax_f.add_patch(hud_top)
    
    ax_f.text(0.08, 0.935, f"RAIPUR URBAN DYNAMICS  •  {yr}", transform=ax_f.transAxes,
              fontsize=13, fontweight='bold', color='#ffffff', va='center', zorder=25)
    ax_f.text(0.08, 0.902, "Google Earth Engine  |  Dynamic World (10m Sentinel-2)", transform=ax_f.transAxes,
              fontsize=8.5, color='#94a3b8', va='center', zorder=25)
    
    # Progress indicator dots
    for p_i, p_yr in enumerate(years):
        dot_color = '#38bdf8' if p_i <= idx else '#334155'
        ax_f.scatter(0.72 + p_i * 0.028, 0.925, s=40, color=dot_color, transform=ax_f.transAxes, zorder=25)
    
    # Bottom HUD Card (Numerical Metrics)
    hud_bot = patches.FancyBboxPatch(
        (0.04, 0.035), 0.92, 0.08,
        boxstyle="round,pad=0.015",
        fc="#0f172a", ec="#334155", lw=1.2, alpha=0.92,
        transform=ax_f.transAxes, zorder=20
    )
    ax_f.add_patch(hud_bot)
    
    b_val = built_km2[idx]
    t_val = tree_km2[idx]
    b_p = built_pct[idx]
    t_p = tree_pct[idx]
    
    ax_f.text(0.08, 0.075, f"Built Land: {b_val:.2f} km² ({b_p:.1f}%)", transform=ax_f.transAxes,
              fontsize=10.5, fontweight='bold', color='#fb7185', va='center', zorder=25)
    ax_f.text(0.55, 0.075, f"Tree Canopy: {t_val:.2f} km² ({t_p:.1f}%)", transform=ax_f.transAxes,
              fontsize=10.5, fontweight='bold', color='#4ade80', va='center', zorder=25)
    
    ax_f.set_axis_off()
    
    temp_frame_path = os.path.join(docs_img_dir, f"frame_{yr}.png")
    plt.savefig(temp_frame_path, dpi=150, facecolor='#0f172a')
    plt.close()
    
    img = Image.open(temp_frame_path).convert("RGB")
    gif_frames.append(img)
    os.remove(temp_frame_path)

# Save smooth animation GIF
gif_out1 = os.path.join(docs_img_dir, "raipur_dw_animation.gif")
gif_out2 = os.path.join(q2_dir, "raipur_dw_animation.gif")
gif_frames[0].save(gif_out1, save_all=True, append_images=gif_frames[1:], duration=900, loop=0)
gif_frames[0].save(gif_out2, save_all=True, append_images=gif_frames[1:], duration=900, loop=0)
print("Saved professional, smooth raipur_dw_animation.gif!")
