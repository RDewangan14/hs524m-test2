import geopandas as gpd
import pandas as pd
import folium
from folium import plugins
import os
import html

def build_q1_map(gpkg_path, output_html, photo_url_prefix="assets/photos/"):
    # Read points and attachments
    points = gpd.read_file(gpkg_path, layer="notes_point")
    attachments = gpd.read_file(gpkg_path, layer="notes_attachments")
    
    if points.crs != "EPSG:4326":
        points = points.to_crs(epsg=4326)
        
    points["timestamp"] = points["timestamp"].astype(str)
    
    # Merge attachments
    att_sub = attachments[["note_uuid", "media"]].copy()
    merged = points.merge(att_sub, left_on="uuid", right_on="note_uuid", how="left")
    
    # Filter valid coordinates (campus bounds approx lat 13.5 to 14.0, lon 79.4 to 79.8)
    # Check if there are extreme outliers:
    valid_mask = (merged.geometry.y > 13.0) & (merged.geometry.y < 14.5) & \
                 (merged.geometry.x > 79.0) & (merged.geometry.x < 80.5)
    
    campus_points = merged[valid_mask].copy()
    outlier_points = merged[~valid_mask].copy()
    
    print(f"Total points: {len(merged)}, Campus points: {len(campus_points)}, Outliers: {len(outlier_points)}")
    
    center_lat = campus_points.geometry.y.mean()
    center_lon = campus_points.geometry.x.mean()
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=16,
        tiles=None,
        control_scale=True
    )
    
    # Add Basemaps
    folium.TileLayer(
        "OpenStreetMap",
        name="OpenStreetMap",
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        "CartoDB positron",
        name="CartoDB Light",
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Esri Satellite Imagery",
        control=True
    ).add_to(m)
    
    # Feature Groups
    fg_all = folium.FeatureGroup(name="All Waste Bins", show=True)
    fg_critical = folium.FeatureGroup(name="High Fill (>= 70%)", show=False)
    fg_medium = folium.FeatureGroup(name="Medium Fill (30-69%)", show=False)
    fg_low = folium.FeatureGroup(name="Low Fill (< 30%)", show=False)
    
    # Marker Cluster option
    cluster = plugins.MarkerCluster(name="Clustered Bins View", show=False)
    
    def get_color_and_status(note_val):
        try:
            val = float(str(note_val).strip())
            if val <= 1.0 and val > 0:
                val = val * 100.0
        except (ValueError, TypeError):
            val = None
            
        if val is None:
            return "#7f8c8d", "Unspecified", 0
        elif val >= 70:
            return "#e74c3c", f"{int(val)}% - High / Urgent", val
        elif val >= 30:
            return "#f39c12", f"{int(val)}% - Moderate", val
        else:
            return "#27ae60", f"{int(val)}% - Low / Normal", val

    for _, row in campus_points.iterrows():
        lat = row.geometry.y
        lon = row.geometry.x
        title = str(row.get("title", "Waste Bin"))
        note = row.get("note", "N/A")
        ts = str(row.get("timestamp", "N/A"))
        uuid = str(row.get("uuid", "N/A"))
        media = row.get("media", "")
        
        color, status_text, fill_num = get_color_and_status(note)
        
        # Photo path
        if pd.notna(media) and str(media).strip():
            photo_file = os.path.basename(str(media))
            photo_src = f"{photo_url_prefix}{photo_file}"
            photo_html = f'''
            <div style="margin-top:10px; text-align:center;">
                <img src="{photo_src}" alt="Waste Bin Photo" style="width:100%; max-height:200px; object-fit:cover; border-radius:6px; border:1px solid #ddd; box-shadow:0 2px 5px rgba(0,0,0,0.15);" loading="lazy" onerror="this.onerror=null; this.src='https://via.placeholder.com/280x180?text=Photo+Not+Found';">
            </div>
            '''
        else:
            photo_html = '<div style="margin-top:8px; color:#888; font-style:italic;">No photograph available</div>'
            
        # Progress bar
        fill_pct = min(max(fill_num, 0), 100)
        progress_bar = f'''
        <div style="background:#e0e0e0; border-radius:4px; height:10px; width:100%; margin:6px 0 10px 0; overflow:hidden;">
            <div style="background:{color}; width:{fill_pct}%; height:100%;"></div>
        </div>
        '''
        
        popup_html = f'''
        <div style="font-family:'Segoe UI',Roboto,sans-serif; width:280px; font-size:13px; line-height:1.4; color:#2c3e50;">
            <div style="border-bottom:2px solid {color}; padding-bottom:5px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:16px; font-weight:700; color:#1a252f;">{html.escape(title)}</span>
                <span style="background:{color}; color:#fff; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:600;">{html.escape(status_text)}</span>
            </div>
            <div style="margin-bottom:4px;">
                <strong>Fill Capacity:</strong> {fill_pct:.0f}%
                {progress_bar}
            </div>
            <div style="margin-bottom:4px;">
                <strong>Observer:</strong> Rahul Dewangan (CS25M114)
                <br><span style="font-size:11px; color:#7f8c8d;">Data Contributor: Raushan Vivek (CS25M115)</span>
            </div>
            <div style="margin-bottom:4px;">
                <strong>Time:</strong> <span style="font-size:11px; color:#555;">{html.escape(ts[:19])}</span>
            </div>
            <div style="margin-bottom:4px;">
                <strong>Coordinates:</strong> <span style="font-size:11px; color:#555;">{lat:.5f}° N, {lon:.5f}° E</span>
            </div>
            {photo_html}
        </div>
        '''
        
        popup = folium.Popup(popup_html, max_width=320)
        tooltip = f"{title}: {status_text}"
        
        # Marker
        marker = folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color="#2c3e50",
            weight=1.5,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=popup,
            tooltip=tooltip
        )
        marker.add_to(fg_all)
        
        # Clustered duplicate
        c_marker = folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color="#2c3e50",
            weight=1.5,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=tooltip
        )
        c_marker.add_to(cluster)
        
        # Categorized layers
        cat_marker = folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color="#2c3e50",
            weight=1.5,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=tooltip
        )
        if fill_num >= 70:
            cat_marker.add_to(fg_critical)
        elif fill_num >= 30:
            cat_marker.add_to(fg_medium)
        else:
            cat_marker.add_to(fg_low)
            
    fg_all.add_to(m)
    fg_critical.add_to(m)
    fg_medium.add_to(m)
    fg_low.add_to(m)
    cluster.add_to(m)
    
    # Map controls
    plugins.Fullscreen(position="topleft").add_to(m)
    plugins.MeasureControl(position="bottomleft", primary_length_unit="meters").add_to(m)
    folium.LayerControl(position="topright", collapsed=False).add_to(m)
    
    # Legend HTML
    legend_html = '''
    <div style="
        position: fixed; 
        bottom: 30px; right: 30px; width: 190px; height: auto; 
        background-color: rgba(255, 255, 255, 0.95);
        z-index: 9999; 
        border: 2px solid #bdc3c7;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        padding: 12px;
        font-family: 'Segoe UI', Roboto, sans-serif;
        font-size: 12px;
        color: #2c3e50;
    ">
        <h4 style="margin: 0 0 8px 0; font-size: 13px; font-weight: 700; border-bottom: 1px solid #ddd; padding-bottom: 4px;">Bin Fill Status</h4>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <span style="display:inline-block; width:14px; height:14px; background:#e74c3c; border-radius:50%; margin-right:8px; border:1px solid #333;"></span>
            <span>Critical (&ge; 70%)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <span style="display:inline-block; width:14px; height:14px; background:#f39c12; border-radius:50%; margin-right:8px; border:1px solid #333;"></span>
            <span>Moderate (30&ndash;69%)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <span style="display:inline-block; width:14px; height:14px; background:#27ae60; border-radius:50%; margin-right:8px; border:1px solid #333;"></span>
            <span>Low (&lt; 30%)</span>
        </div>
        <div style="display: flex; align-items: center;">
            <span style="display:inline-block; width:14px; height:14px; background:#7f8c8d; border-radius:50%; margin-right:8px; border:1px solid #333;"></span>
            <span>Unspecified</span>
        </div>
        <hr style="margin: 8px 0; border: 0; border-top: 1px solid #eee;">
        <div style="font-size: 10px; color: #7f8c8d; text-align: center;">
            HS524M &bull; QField &amp; Folium
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    m.save(output_html)
    print(f"Map successfully generated and saved to {output_html}")
    return m

if __name__ == "__main__":
    gpkg = r"C:\Users\DELL\.gemini\antigravity\scratch\hs524m-assignment2\data\notes.gpkg"
    out = r"C:\Users\DELL\.gemini\antigravity\scratch\hs524m-assignment2\q1_interactive_map\waste_bin_map.html"
    build_q1_map(gpkg, out)
    
    # Also save to docs for website hosting
    out_docs = r"C:\Users\DELL\.gemini\antigravity\scratch\hs524m-assignment2\docs\waste_bin_map.html"
    build_q1_map(gpkg, out_docs, photo_url_prefix="assets/photos/")
