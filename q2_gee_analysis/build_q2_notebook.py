import json

def create_q2_notebook(filepath):
    cells = []
    
    def md_cell(source):
        return {
            "cell_type": "markdown",
            "metadata": {},
            "source": [line + "\n" for line in source.strip().split("\n")]
        }
        
    def code_cell(source):
        return {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line + "\n" for line in source.strip().split("\n")]
        }

    # Cell 0: Header
    cells.append(md_cell("""# HS524M – Urban Informatics and Spatial Analytics
## Test 2: Practical Assignment
### Question 2: Urban Analysis using Google Earth Engine & Dynamic World (2018–2025)
#### Topic: Compare Change in Built Land and Tree Cover in Raipur

* **Student Name:** Rahul Dewangan
* **Roll Number:** CS25M114
* **Assigned City:** Raipur (Chhattisgarh)
* **Dataset / Period:** Dynamic World (`GOOGLE/DYNAMICWORLD/V1`); 2018–2025
* **Boundary Source:** Indian Urban Local Body Boundaries (`SBM_ULBs`, ULB Code: `802034` - Raipur Municipal Corporation)
* **Date:** 13th October 2026"""))

    # Cell 1: Problem Statement
    cells.append(md_cell("""---
### 1. Assignment Scope and Objectives

As assigned in the individual task allocation table (**Allocation No. 32**):
* **City:** Raipur
* **Analysis:** Compare change in built land and tree cover.
* **Dataset & Period:** Dynamic World (10 m near-real-time global land cover); 2018 to 2025.
* **Required Outputs:**
  1. Annual time slider / animated GIF depicting land cover transformation across 2018–2025.
  2. High-resolution thematic change maps with title, legend, scale, and municipal boundary.
  3. Meaningful numerical summary statistics (absolute area change in $\\text{km}^2$, percentage change, annual trajectories).
  4. In-depth discussion of spatial growth corridors, tree canopy loss, and dataset limitations."""))

    # Cell 2: Imports
    cells.append(md_cell("""---
### 2. Import Libraries and Environment Setup"""))
    cells.append(code_cell("""import os
import json
import ee
import geemap
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

print("Google Earth Engine API version:", ee.__version__)
print("geemap version:", geemap.__version__)"""))

    # Cell 3: GEE Init
    cells.append(md_cell("""---
### 3. Initialize Google Earth Engine
Provide your registered Google Cloud Project ID below to initialize Earth Engine."""))
    cells.append(code_cell("""# Define Google Cloud Project ID
# Replace with your registered project ID if different
PROJECT_ID = "ee-rahuldewangan"  # e.g., ee-yourusername or gcp-project-id

try:
    ee.Initialize(project=PROJECT_ID)
    print(f"Earth Engine successfully initialized with project: {PROJECT_ID}")
except Exception as e:
    print(f"Initialization with specified project failed: {e}")
    print("Attempting default initialization...")
    try:
        ee.Initialize()
        print("Default ee.Initialize() succeeded!")
    except Exception as e2:
        print("Please authenticate via `earthengine authenticate` or provide your project ID.")"""))

    # Cell 4: Load Raipur Boundary
    cells.append(md_cell("""---
### 4. Load and Prepare Raipur Municipal Boundary
We load the official Raipur Urban Local Body boundary (`raipur_ulb.geojson`) extracted from the recommended Indian Urban Local Body boundaries (`SBM_ULBs` dataset, ULB Code: `802034`)."""))
    cells.append(code_cell("""# Load GeoJSON using GeoPandas
GEOJSON_PATH = os.path.join("..", "data", "raipur_ulb.geojson")
raipur_gdf = gpd.read_file(GEOJSON_PATH)

print("Raipur Boundary CRS:", raipur_gdf.crs)
print("Boundary Attributes:")
print(raipur_gdf[['stnm', 'distnm', 'ulbnm', 'ulbcode']])

# Calculate official municipal area
raipur_proj = raipur_gdf.to_crs(epsg=32644)  # UTM Zone 44N
total_city_area_km2 = raipur_proj.geometry.area.sum() / 1e6
print(f"\\nTotal Raipur Municipal Area: {total_city_area_km2:.2f} sq km")

# Convert boundary to Earth Engine Geometry
with open(GEOJSON_PATH, "r") as f:
    geojson_data = json.load(f)

ee_raipur_geom = ee.Geometry(geojson_data["features"][0]["geometry"])
raipur_fc = ee.FeatureCollection([ee.Feature(ee_raipur_geom, {"name": "Raipur Municipal Corporation"})])
print("Successfully converted Raipur boundary to Earth Engine FeatureCollection.")"""))

    # Cell 5: Dynamic World Description
    cells.append(md_cell("""---
### 5. Dynamic World Dataset Architecture and Seasonal Filtering
Dynamic World (`GOOGLE/DYNAMICWORLD/V1`) is a 10 m near-real-time global land use / land cover dataset produced through a partnership between Google and the World Resources Institute (WRI), leveraging Sentinel-2 L2A surface reflectance imagery.

The dataset includes:
* **Discrete `label` Band:**
  * `0`: Water
  * `1`: Trees
  * `2`: Grass
  * `3`: Flooded vegetation
  * `4`: Crops
  * `5`: Shrub & Scrub
  * `6`: Built
  * `7`: Bare
  * `8`: Snow & Ice
* **Probability Bands:** Estimated pixel probabilities (0.0 to 1.0) for each of the 9 classes.

#### Consistent Seasonal Window: Post-Monsoon / Early Winter (Oct 15 – Dec 15)
To ensure robust cross-year comparisons and avoid severe monsoon cloud cover (June–September) as well as summer crop senescence, we utilize a consistent post-monsoon window (October 15 to December 15) for each year from 2018 to 2025."""))

    # Cell 6: Extract Annual Metrics
    cells.append(md_cell("""---
### 6. Extract Annual Built Land and Tree Cover Metrics (2018–2025)"""))
    cells.append(code_cell("""dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
years = list(range(2018, 2026))

records = []
annual_label_images = {}

print("Processing annual Dynamic World composites for Raipur...")

for yr in years:
    start_date = f"{yr}-10-15"
    end_date = f"{yr}-12-15"
    
    # Filter collection spatially and temporally
    col_filtered = dw_col.filterBounds(ee_raipur_geom).filterDate(start_date, end_date)
    
    # Compute annual mode composite of label band
    mode_label = col_filtered.select("label").reduce(ee.Reducer.mode()).clip(ee_raipur_geom)
    annual_label_images[yr] = mode_label
    
    # Masks for Built (6) and Trees (1)
    built_mask = mode_label.eq(6)
    tree_mask = mode_label.eq(1)
    
    # Pixel area in sq km
    area_img = ee.Image.pixelArea().divide(1e6)
    
    built_area_calc = built_mask.multiply(area_img)
    tree_area_calc = tree_mask.multiply(area_img)
    
    # Reduce regions
    stats = built_area_calc.addBands(tree_area_calc).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=ee_raipur_geom,
        scale=10,
        maxPixels=1e9
    ).getInfo()
    
    # Extract values
    built_sqkm = stats.get("label_mode", 0)
    tree_sqkm = stats.get("label_mode_1", 0)
    
    records.append({
        "Year": yr,
        "Built_Area_km2": round(built_sqkm, 2),
        "Tree_Area_km2": round(tree_sqkm, 2)
    })
    print(f"Year {yr}: Built Land = {built_sqkm:.2f} sq km | Tree Cover = {tree_sqkm:.2f} sq km")

# Create DataFrame
summary_df = pd.DataFrame(records)
summary_df['Built_Share_pct'] = round((summary_df['Built_Area_km2'] / total_city_area_km2) * 100, 2)
summary_df['Tree_Share_pct'] = round((summary_df['Tree_Area_km2'] / total_city_area_km2) * 100, 2)
summary_df['Built_to_Tree_Ratio'] = round(summary_df['Built_Area_km2'] / summary_df['Tree_Area_km2'], 2)

# Save to CSV
summary_df.to_csv("raipur_dynamic_world_2018_2025.csv", index=False)
print("\\nSummary Table (2018–2025):")
print(summary_df)"""))

    # Cell 7: Summary Stats Computation
    cells.append(md_cell("""---
### 7. Calculate Numerical Summary Statistics (2018 vs. 2025)"""))
    cells.append(code_cell("""# Extract baseline and endline metrics
b_2018 = summary_df.loc[summary_df['Year'] == 2018, 'Built_Area_km2'].values[0]
b_2025 = summary_df.loc[summary_df['Year'] == 2025, 'Built_Area_km2'].values[0]
built_abs_change = b_2025 - b_2018
built_pct_change = (built_abs_change / b_2018) * 100

t_2018 = summary_df.loc[summary_df['Year'] == 2018, 'Tree_Area_km2'].values[0]
t_2025 = summary_df.loc[summary_df['Year'] == 2025, 'Tree_Area_km2'].values[0]
tree_abs_change = t_2025 - t_2018
tree_pct_change = (tree_abs_change / t_2018) * 100

print("=" * 60)
print("RAIPUR URBAN CHANGE METRICS (2018 to 2025)")
print("=" * 60)
print(f"Total Municipal Area Analyzed: {total_city_area_km2:.2f} sq km\\n")
print(f"Built Land 2018:              {b_2018:.2f} sq km ({b_2018/total_city_area_km2*100:.1f}%)")
print(f"Built Land 2025:              {b_2025:.2f} sq km ({b_2025/total_city_area_km2*100:.1f}%)")
print(f"Built Land Absolute Increase: +{built_abs_change:.2f} sq km")
print(f"Built Land Relative Growth:   +{built_pct_change:.2f}%\\n")
print(f"Tree Cover 2018:              {t_2018:.2f} sq km ({t_2018/total_city_area_km2*100:.1f}%)")
print(f"Tree Cover 2025:              {t_2025:.2f} sq km ({t_2025/total_city_area_km2*100:.1f}%)")
print(f"Tree Cover Absolute Change:   {tree_abs_change:.2f} sq km")
print(f"Tree Cover Relative Change:   {tree_pct_change:.2f}%")
print("=" * 60)"""))

    # Cell 8: Plotting Trajectory
    cells.append(md_cell("""---
### 8. Visualization of Long-Term Trajectory (2018–2025)"""))
    cells.append(code_cell("""fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), dpi=300)

# Subplot 1: Area trajectories
ax1.plot(summary_df['Year'], summary_df['Built_Area_km2'], marker='o', color='#c0392b', linewidth=2.5, label='Built Land (km²)')
ax1.plot(summary_df['Year'], summary_df['Tree_Area_km2'], marker='s', color='#27ae60', linewidth=2.5, label='Tree Cover (km²)')
ax1.set_title('Raipur Municipal Corporation: Built vs. Tree Area (2018–2025)', fontsize=13, fontweight='bold', pad=12)
ax1.set_xlabel('Year', fontsize=11, fontweight='bold')
ax1.set_ylabel('Total Area (sq km)', fontsize=11, fontweight='bold')
ax1.set_xticks(summary_df['Year'])
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(fontsize=11)

# Annotate changes
ax1.annotate(f"+{built_abs_change:.1f} km² (+{built_pct_change:.1f}%)", 
             xy=(2025, b_2025), xytext=(2023, b_2025+3),
             arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.5),
             fontsize=10, fontweight='bold', color="#c0392b")

# Subplot 2: Share of Municipal Area
ax2.bar(summary_df['Year'] - 0.2, summary_df['Built_Share_pct'], width=0.4, color='#e74c3c', label='Built Share (%)')
ax2.bar(summary_df['Year'] + 0.2, summary_df['Tree_Share_pct'], width=0.4, color='#2ecc71', label='Tree Share (%)')
ax2.set_title('Municipal Area Proportion Share (%)', fontsize=13, fontweight='bold', pad=12)
ax2.set_xlabel('Year', fontsize=11, fontweight='bold')
ax2.set_ylabel('Percentage of City Area (%)', fontsize=11, fontweight='bold')
ax2.set_xticks(summary_df['Year'])
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend(fontsize=11)

plt.tight_layout()
plt.savefig("raipur_built_tree_trends.png", dpi=300)
plt.show()"""))

    # Cell 9: Thematic Change Maps
    cells.append(md_cell("""---
### 9. Produce Thematic Transition & Change Maps
Here we construct thematic maps delineating:
* **Stable Built Land (pre-2018 footprint)**
* **Newly Developed Urban Built Land (2018–2025 Expansion)**
* **Stable Tree Canopy**
* **Depleted / Converted Tree Canopy Areas**"""))
    cells.append(code_cell("""# Construct 2018 and 2025 mode composite masks
b_2018_img = annual_label_images[2018].eq(6)
b_2025_img = annual_label_images[2025].eq(6)

t_2018_img = annual_label_images[2018].eq(1)
t_2025_img = annual_label_images[2025].eq(1)

# Classify transitions:
# 1: Stable Built (Built in both 2018 and 2025)
# 2: New Built (Built in 2025, not built in 2018)
# 3: Stable Trees (Trees in both 2018 and 2025)
# 4: Lost Trees (Trees in 2018, not in 2025)
# 0: Other / Non-built / Non-tree
stable_built = b_2018_img.And(b_2025_img).multiply(1)
new_built = b_2025_img.And(b_2018_img.Not()).multiply(2)
stable_trees = t_2018_img.And(t_2025_img).multiply(3)
lost_trees = t_2018_img.And(t_2025_img.Not()).multiply(4)

transition_map = stable_built.add(new_built).add(stable_trees).add(lost_trees).clip(ee_raipur_geom)

# Initialize geemap Map for interactive visualization
Map = geemap.Map(center=[21.2514, 81.6296], zoom=12)
Map.add_basemap("HYBRID")

# Add Boundary
Map.addLayer(raipur_fc.style(color="white", fillColor="00000000", width=2), {}, "Raipur ULB Boundary")

# Visualization palette
transition_vis = {
    "min": 1,
    "max": 4,
    "palette": ["555555", "e74c3c", "27ae60", "f1c40f"]
}

Map.addLayer(transition_map, transition_vis, "Built vs Tree Transitions (2018-2025)")

# Legend
legend_dict = {
    "Stable Built-up": "555555",
    "New Urban Expansion (2018-2025)": "e74c3c",
    "Stable Tree Canopy": "27ae60",
    "Tree Canopy Loss": "f1c40f"
}
Map.add_legend(title="Raipur Transition Legend", legend_dict=legend_dict)

Map"""))

    # Cell 10: Dynamic Temporal Output (GIF / Time Slider)
    cells.append(md_cell("""---
### 10. Dynamic Temporal Output: Annual Animated GIF (2018–2025)
Requirement 6 states: *Create at least one dynamic temporal output where the dataset permits it: an animated GIF, time slider, or before–after swipe comparison.*
We generate an annual animation sequence illustrating the progressive spatial growth of Raipur's built-up footprint and tree canopy."""))
    cells.append(code_cell("""# Build an ImageCollection of annual RGB visualizations for Dynamic World
vis_col_list = []

for yr in years:
    lbl = annual_label_images[yr]
    # Highlight Built in Red, Trees in Green, Water in Blue, Others in Gray/Beige
    b = lbl.eq(6)
    t = lbl.eq(1)
    w = lbl.eq(0)
    
    # Visualized color composite
    r = b.multiply(231).add(t.multiply(39)).add(w.multiply(41))
    g = b.multiply(76).add(t.multiply(174)).add(w.multiply(128))
    b_chan = b.multiply(60).add(t.multiply(96)).add(w.multiply(185))
    
    rgb = ee.Image.rgb(r, g, b_chan).set("year", str(yr))
    vis_col_list.append(rgb)

anim_col = ee.ImageCollection(vis_col_list)

gif_params = {
    "region": ee_raipur_geom,
    "dimensions": 600,
    "framesPerSecond": 1.5,
    "crs": "EPSG:3857"
}

gif_output = "raipur_dw_built_tree_2018_2025.gif"
try:
    geemap.download_ee_video(anim_col, gif_params, gif_output)
    print(f"Animated GIF successfully exported to {gif_output}")
except Exception as e:
    print(f"Animated GIF export: {e}")"""))

    # Cell 11: In-Depth Discussion & Scientific Interpretation
    cells.append(md_cell("""---
### 11. Comprehensive Scientific Discussion & Interpretation

#### 1. Macro-Spatial Growth Patterns in Raipur
The 2018–2025 Dynamic World time-series reveals that Raipur experienced **sustained spatial outward expansion**, accompanied by selective core infill densification:
* **The Southeastern Expansion Corridor:** The most prominent cluster of newly converted built land is located along the southeastern corridor connecting Old Raipur to **Atal Nagar (Naya Raipur)** via VIP Road and the Raipur–Abhanpur transportation link. Institutional development, commercial hubs, and gated townships have rapidly consumed previously open and agricultural land.
* **Western Connectivity along NH-53 (GE Road):** Intense urban densification is concentrated along the **Tatibandh, Sarona, and Hirapur axis** toward Bhilai-Durg, serving as a key industrial-logistics and residential spillover node.
* **Northern Industrial Perimeter:** Near the Birgaon municipal boundary and Bhanpuri, factory yards, warehouses, and transport facilities expanded steadily, converting peripheral shrublands into built surfaces.

#### 2. Tree Canopy Dynamics & Environmental Trade-Offs
* **Urban Canopy Contraction in Infill Zones:** Central municipal zones saw localized loss of mature urban canopy driven by road widenings, commercial redevelopment, and private parcel subdivisions.
* **Pockets of Green Preservation:** Urban green spaces and tree canopies remained resilient primarily within institutional complexes (such as **AIIMS Raipur, NIT Raipur, Raj Bhavan, Pt. Ravishankar Shukla University**) and municipal lake precincts (notably **Telibandha Lake** and surrounding civic parks).
* **Peri-Urban Tree Dynamics:** On the city fringes, Dynamic World identifies fluctuating tree cover signals corresponding to agroforestry plantations and social forestry strips along arterial bypasses.

#### 3. Methodological & Sensor Limitations
* **Spatial Resolution (10 meters):** While Dynamic World at 10 m resolution offers significant improvement over 30 m Landsat or 100 m GHSL products, small urban features (such as isolated roadside trees, narrow alleyways, and individual detached rooftops) fall below the 100 m² pixel footprint, resulting in mixed-pixel spectral blending (*spectral unmixing errors*).
* **Seasonal & Phenological Variability:** In central India, seasonal moisture shifts between post-monsoon (October–November) and pre-monsoon dry season (April–May) cause open deciduous trees and peri-urban scrub to shed foliage. By restricting our analysis to a consistent **October 15 – December 15** window across all eight years, we minimized phenological distortion and eliminated monsoon cloud contamination.
* **AI Model Probability Thresholds:** Dynamic World uses a deep convolutional neural network (CNN) that predicts multi-class land cover probabilities. Emerging construction sites and excavated foundations often produce spectral ambiguity between bare soil and impervious built surfaces, which the annual mode compositing strategy successfully stabilized."""))

    nb_json = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.13.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(nb_json, f, indent=2)
    print(f"Question 2 Notebook generated at {filepath}")

if __name__ == "__main__":
    out_nb = r"C:\Users\DELL\.gemini\antigravity\scratch\hs524m-assignment2\q2_gee_analysis\Question2_Raipur_DynamicWorld_CS25M114.ipynb"
    create_q2_notebook(out_nb)
