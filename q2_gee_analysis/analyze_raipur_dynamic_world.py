import ee
import json
import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def run_raipur_analysis(project_id, geojson_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print(f"Initializing Earth Engine with project: {project_id}...")
    ee.Initialize(project=project_id)
    print("Earth Engine successfully initialized!")

    # 1. Load Raipur Boundary
    with open(geojson_path, "r") as f:
        geojson_data = json.load(f)
    
    # Extract features / geometry
    features = geojson_data["features"]
    ee_geom = ee.Geometry(features[0]["geometry"])
    raipur_fc = ee.FeatureCollection([ee.Feature(ee_geom, {"name": "Raipur ULB"})])
    
    # 2. Dynamic World Collection Setup
    dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
    
    years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
    results = []
    
    # Seasonal window: Post-Monsoon / Early Winter (October 15 to December 15)
    # This provides cloud-free imagery and consistent phenological baseline across years
    for y in years:
        start_date = f"{y}-10-15"
        end_date = f"{y}-12-15"
        
        # Filter collection
        dw_filtered = (dw_col
                       .filterBounds(ee_geom)
                       .filterDate(start_date, end_date))
        
        # Mode composite of the 'label' band
        label_mode = dw_filtered.select("label").reduce(ee.Reducer.mode()).clip(ee_geom)
        
        # Built land: label == 6
        built_mask = label_mode.eq(6)
        # Tree cover: label == 1
        tree_mask = label_mode.eq(1)
        
        pixel_area_sqkm = ee.Image.pixelArea().divide(1e6)
        
        built_area_img = built_mask.multiply(pixel_area_sqkm)
        tree_area_img = tree_mask.multiply(pixel_area_sqkm)
        
        stats = built_area_img.addBands(tree_area_img).reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=ee_geom,
            scale=10,
            maxPixels=1e9
        ).getInfo()
        
        built_km2 = stats.get("label_mode", 0) # first band
        tree_km2 = stats.get("label_mode_1", 0) # second band
        
        print(f"Year {y}: Built = {built_km2:.2f} sq km, Trees = {tree_km2:.2f} sq km")
        results.append({
            "year": y,
            "built_area_sqkm": round(built_km2, 2),
            "tree_area_sqkm": round(tree_km2, 2)
        })
        
    df = pd.DataFrame(results)
    df["total_reported_sqkm"] = df["built_area_sqkm"] + df["tree_area_sqkm"]
    df["built_pct"] = (df["built_area_sqkm"] / 173.64) * 100
    df["tree_pct"] = (df["tree_area_sqkm"] / 173.64) * 100
    
    csv_path = os.path.join(output_dir, "raipur_dw_statistics.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved statistics to {csv_path}")
    
    # 3. Generate Time Series Plot
    fig, ax1 = plt.subplots(figsize=(10, 6), dpi=300)
    ax1.set_title("Raipur Municipal Corporation (2018–2025)\nDynamic World: Built Land vs. Tree Cover Trajectory", fontsize=14, fontweight="bold", pad=15)
    
    ax1.plot(df["year"], df["built_area_sqkm"], marker="o", color="#d35400", linewidth=2.5, label="Built Land ($km^2$)")
    ax1.plot(df["year"], df["tree_area_sqkm"], marker="s", color="#27ae60", linewidth=2.5, label="Tree Cover ($km^2$)")
    
    ax1.set_xlabel("Year", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Area ($km^2$)", fontsize=12, fontweight="bold")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="center right", fontsize=11, framealpha=0.9)
    ax1.set_xticks(years)
    
    plot_path = os.path.join(output_dir, "raipur_built_tree_trends.png")
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()
    print(f"Saved trend chart to {plot_path}")
    
    return df

if __name__ == "__main__":
    import sys
    proj = sys.argv[1] if len(sys.argv) > 1 else "ee-rahuldewangan"
    geo = r"C:\Users\DELL\.gemini\antigravity\scratch\hs524m-assignment2\data\raipur_ulb.geojson"
    out = r"C:\Users\DELL\.gemini\antigravity\scratch\hs524m-assignment2\q2_gee_analysis"
    run_raipur_analysis(proj, geo, out)
