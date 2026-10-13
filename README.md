# HS524M – Urban Informatics and Spatial Analytics
## Test 2: Practical Assignment Submission Package
**Student:** Rahul Dewangan | **Roll No:** CS25M114 | **Date:** 13th October 2026

---

### Executive Summary & Submission Deliverables

As required by the assignment guidelines, both **Question 1** and **Question 2** have been completely solved, packaged into standalone Jupyter Notebooks, and integrated into a responsive personal portfolio website.

| Component | Deliverable | Location |
| :--- | :--- | :--- |
| **Question 1 Notebook** | Complete QField & Folium pipeline | `q1_interactive_map/Question1_WasteBin_Folium_CS25M114.ipynb` |
| **Question 1 Web Map** | Interactive Folium HTML Map | `docs/waste_bin_map.html` |
| **Question 2 Notebook** | GEE & Dynamic World Raipur Analysis | `q2_gee_analysis/Question2_Raipur_DynamicWorld_CS25M114.ipynb` |
| **Question 2 Dynamic Output**| Annual Animated GIF (2018–2025) | `docs/assets/images/raipur_dw_animation.gif` |
| **Question 2 Thematic Map** | Thematic Transition & Change Map | `docs/assets/images/raipur_change_map.png` |
| **Question 2 Statistics** | Numerical summary dataset | `docs/raipur_dynamic_world_stats.csv` |
| **Personal Webpage / Portfolio** | Complete submission website | `docs/index.html` |

---

### Question 1: Interactive Web Mapping of Waste-Bin Observations [5 Marks]

#### Key Highlights & Rubric Alignment:
1. **Interactive Point Features:** 55 spatial waste bin observations displayed across campus.
2. **Visual Encoding by Fill Level:**
   - 🟢 **Low Fill (< 30%):** 22 bins (normal operation)
   - 🟠 **Moderate Fill (30%–69%):** 20 bins (scheduled servicing)
   - 🔴 **Critical Fill (≥ 70%):** 13 bins (urgent clearance / overflow risk)
3. **Popups & Embedded Photographs:**
   - Real-world photo of each container displayed in the popup.
   - Fill capacity progress bar and exact percentage.
   - Timestamp, GPS coordinates (latitude, longitude), and observation ID.
4. **Student Attribution:**
   - Primary observer clearly identified: **Rahul Dewangan (CS25M114)**.
   - Peer collaboration explicitly acknowledged: **Raushan Vivek (CS25M115)**.
5. **Map Controls & Navigation:**
   - Multiple basemaps (OpenStreetMap, Humanitarian OSM, Esri High-Resolution Satellite).
   - Layer Control with individual category toggles and marker clustering view.
   - Fullscreen button and interactive measurement tool.

---

### Question 2: Individual GEE Urban Analysis — Raipur [15 Marks]
**Allocation No. 32 | Raipur | Dynamic World (2018–2025) | Built Land vs. Tree Cover**

#### 1. Official City Boundary
* **Source:** Indian Urban Local Body boundaries (`ramSeraph/indian_admin_boundaries`, `SBM_ULBs` dataset, ULB Code: `802034`).
* **Territory Analyzed:** **173.64 km²** (Raipur Municipal Corporation).

#### 2. Satellite Methodology
* **Dataset:** Google Earth Engine Dynamic World (`GOOGLE/DYNAMICWORLD/V1`, 10 m resolution Sentinel-2 L2A).
* **Consistent Seasonal Window:** **October 15 to December 15 (Post-Monsoon / Early Winter)** applied across all years (2018 to 2025) to prevent monsoon cloud contamination and avoid pre-monsoon dry-season vegetation shedding.
* **Compositing:** Annual `mode` composite of the discrete `label` band (`label == 6` for Built Land, `label == 1` for Tree Cover).

#### 3. Numerical Summary Statistics (2018 vs. 2025)

| Metric | 2018 Baseline | 2025 Current | Absolute Change | Relative Change (%) |
| :--- | :---: | :---: | :---: | :---: |
| **Built Land Area** | $69.42\text{ km}^2$ | $84.82\text{ km}^2$ | **$+15.40\text{ km}^2$** | **$+22.18\%$** |
| **Built Land Share** | $39.98\%$ | $48.85\%$ | $+8.87\%$ of city | — |
| **Tree Cover Area** | $29.85\text{ km}^2$ | $25.62\text{ km}^2$ | **$-4.23\text{ km}^2$** | **$-14.17\%$** |
| **Tree Cover Share** | $17.19\%$ | $14.75\%$ | $-2.44\%$ of city | — |
| **Built-to-Tree Ratio** | $2.33 : 1$ | $3.31 : 1$ | $+0.98$ shift | $+42.06\%$ |

#### 4. Spatial Pattern & Analytical Discussion
* **Southeastern Growth Corridor:** The primary expansion corridor links Old Raipur with **Atal Nagar (Naya Raipur)** along the VIP Road and Raipur–Abhanpur highway, driving rapid conversion of agricultural and peri-urban land into residential gated communities, government complexes, and logistics hubs.
* **Western Connectivity (NH-53 / GE Road):** Substantial built densification occurred around the **Tatibandh, Sarona, and Hirapur axis** toward Bhilai-Durg.
* **Northern Industrial Perimeter:** Near the Birgaon border and Bhanpuri, commercial transport hubs and factory yards expanded into former scrubland.
* **Tree Canopy Dynamics:** Urban canopy contraction occurred predominantly along widened transit corridors and core infill parcels. However, large green clusters remained resilient inside major institutional campuses (**AIIMS Raipur, NIT Raipur, Raj Bhavan / Civil Lines, Pt. Ravishankar Shukla University**) and around civic water bodies (**Telibandha Lake**).

#### 5. Sensor & Methodological Limitations
* **10 m Spatial Resolution:** Small roadside trees and narrow urban alleys fall below the $100\text{ m}^2$ pixel footprint, introducing spectral unmixing error.
* **Seasonal Phenology:** Restricting observations to the post-monsoon window eliminated cloud interference, but captures only a single seasonal snapshot per year.
* **Deep Learning Probability Thresholds:** Early-stage construction excavations produce bare earth that can exhibit transient confusion with natural bare soil before structural impervious surfaces emerge.

---

### Step-by-Step GitHub Pages Hosting Instructions

To publish your website to GitHub Pages:

1. **Create a GitHub repository:**
   * Go to [github.com/new](https://github.com/new)
   * Repository Name: `hs524m-assignment2` (or `hs524m-test2`)
   * Visibility: **Public**
   * Do **NOT** initialize with README (the repository is already initialized locally).

2. **Push your code from your terminal:**
   Open PowerShell in `C:\Users\DELL\.gemini\antigravity\scratch\hs524m-assignment2` and run:
   ```bash
   git remote add origin https://github.com/RDewangan14/hs524m-assignment2.git
   git branch -M main
   git push -u origin main
   ```

3. **Activate GitHub Pages:**
   * In your repository on GitHub, go to **Settings** → **Pages**.
   * Under **Build and deployment**:
     * Source: `Deploy from a branch`
     * Branch: `main`
     * Folder: `/docs`
   * Click **Save**.

4. **Your Live Webpage URL:**
   Your portfolio will be live in ~1 minute at:
   **`https://rdewangan14.github.io/hs524m-assignment2/`**

---

### Submission Checklist for Course Portal

* **Submission item (i): Complete Code / Notebook(s):**
  * Question 1 Notebook: `Question1_WasteBin_Folium_CS25M114.ipynb`
  * Question 2 Notebook: `Question2_Raipur_DynamicWorld_CS25M114.ipynb`
* **Submission item (ii): Webpage Link:**
  * `https://rdewangan14.github.io/hs524m-assignment2/`
