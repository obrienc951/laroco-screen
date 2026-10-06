# Laroco Site Screen

Ranks RZLT-mapped land by expected value to Laroco. The output is a shortlist for site checks, folio searches and letters.

---

## 1. What you need to do

| # | Task | Time |
|---|---|---|
| 1 | Install Python, VS Code and QGIS (Section 3) | 30 min |
| 2 | Install the libraries (Section 4) | 5 min |
| 3 | Run the sample data test (Section 5) | 5 min |
| 4 | Download the real RZLT final map 2026 (Section 6) | 10 min |
| 5 | Run `inspect_data.py` and fix column names in `config.yaml` | 10 min |
| 6 | **Replace the placeholder assumptions in `config.yaml`** with your evidence: sales €/sqm, current land values, build costs, density | 1–2 hrs |
| 7 | Run the screen and review the output in Excel and QGIS | ongoing |

> **The values in `config.yaml` are placeholders, not market evidence.** The ranking is only as good as these numbers.

---

## 2. The tools: what each one does

| Tool | What it is | Why we use it |
|---|---|---|
| **Python** | A programming language | Runs the whole screen. Free, and the standard choice for data and maps work. |
| **VS Code** | A text editor for code | Lets you open, read and edit the `.py` and `.yaml` files, with a built-in terminal. |
| **Terminal** | A text window where you type commands | How you run scripts (`python src/run.py`). On Windows, use VS Code's terminal (*View → Terminal*). |
| **pip** | Python's app store | Installs the libraries below with one command. |
| **virtual environment (venv)** | A private box of libraries for this project | Keeps this project's libraries separate from anything else on your computer. |
| **pandas** | Spreadsheets in code | Tables of rows and columns: filter, calculate and sort, like Excel but repeatable. |
| **geopandas** | pandas with map shapes | Each row also has a boundary shape, so we can ask "does this parcel overlap a flood zone?" |
| **shapely** | Geometry engine (installed with geopandas) | Does the shape maths: areas, overlaps, intersections. |
| **pyogrio** | File reader (installed with geopandas) | Opens GeoJSON, Shapefile and GeoPackage map files. |
| **PyYAML** | YAML reader | Reads `config.yaml`, where all your assumptions live. |
| **openpyxl** | Excel writer | Saves the shortlist as `.xlsx`. |
| **QGIS** | Free desktop map software | Opens `screen.gpkg` so you can see parcels on a map, colour them by score and click for details. |

### Key concepts

- **GeoJSON / GeoPackage (.gpkg).** File formats for map data. GeoJSON is common for downloads. A GeoPackage holds several map layers in one file and is ideal for QGIS.
- **CRS (coordinate reference system).** How coordinates map to places. Downloads usually use latitude/longitude (EPSG:4326). The screen converts everything to **Irish Transverse Mercator (EPSG:2157)**, which measures in metres, so areas are accurate.
- **Spatial join.** Like VLOOKUP, but matching rows by location (overlapping shapes) instead of by an ID.
- **Residual land value.** Sales value of the finished scheme, minus all costs and the developer's profit, gives what the land is worth with planning permission.

---

## 3. Install the software (one-off)

1. **Python 3.11 or newer:** https://www.python.org/downloads/
   - Windows: tick **"Add Python to PATH"** on the first installer screen.
2. **VS Code:** https://code.visualstudio.com/, then install the "Python" extension inside it.
3. **QGIS (LTR version):** https://qgis.org/download/

---

## 4. Set up the project (one-off)

Open the `laroco-screen` folder in VS Code (*File → Open Folder*), then open the terminal.

```bash
# Create the private library box (virtual environment)
python -m venv .venv

# Switch it on (do this each time you open a new terminal)
#   Windows:
.venv\Scripts\activate
#   Mac:
source .venv/bin/activate

# Install the libraries listed in requirements.txt
pip install -r requirements.txt
```

You'll see `(.venv)` at the start of the terminal line when it's switched on.

---

## 5. Test with sample data

```bash
python src/make_sample_data.py
```

In `config.yaml`, temporarily set:

```yaml
inputs:
  rzlt: data/raw/sample_rzlt.geojson
  planning: data/raw/sample_planning.geojson
  flood: data/raw/sample_flood.geojson
```

Then run:

```bash
python src/run.py
```

If the screen works, `output/` will contain `shortlist.xlsx`, `excluded.csv` and `screen.gpkg`. Set the paths back to the real files afterwards.

---

## 6. Get the real data

| Layer | Where | Save as |
|---|---|---|
| **RZLT final map 2026** (required) | Department of Housing open data hub: search "Residential Zoned Land Tax Final Map 2026" on https://opendata.housing.gov.ie or data.gov.ie → *Download* → **GeoJSON** | `data/raw/rzlt_final_2026.geojson` |
| Planning applications (optional) | data.gov.ie → search "National Planning Applications" → GeoJSON | `data/raw/planning.geojson` |
| Flood Zone A (optional) | OPW, https://www.floodinfo.ie: flood map data downloads | `data/raw/flood_a.geojson` |

The national RZLT file may be large. The screen keeps only the local authorities listed in `target_las`.

---

## 7. Run it

```bash
python src/inspect_data.py   # check column names, then fix config.yaml section 2
python src/run.py            # run the full screen
```

**Outputs (`output/`):**
- `shortlist.xlsx`: the top parcels, ranked
- `excluded.csv`: every dropped parcel and the reason it was dropped
- `screen.gpkg`: drag into QGIS. Right-click the `shortlist` layer → *Properties → Symbology → Graduated* → colour by `score`.

---

## 8. How the screen works

```
ingest.py   load RZLT -> keep target LAs -> convert to metres -> area (ha)
   ↓
filter.py   drop: size outside band, Flood Zone A, live permission
            flag: past refusals (kept, but scored down)
   ↓
score.py    units -> GDV -> residual value -> uplift -> Laroco profit
            drop: Laroco profit below floor
            score: fee 40% / margin 25% / size 15% / history 10% / flood 10%
   ↓
export.py   Excel shortlist + exclusion log + QGIS map file
```

All rules and weights live in `config.yaml`. Change a number, re-run, compare.

---

## 9. Limits (read before trusting the output)

- **A filter, not a verdict.** Every shortlisted parcel still needs a desk review, a site visit and a planning check.
- **Uniform assumptions.** One density and one €/sqm per local authority. Real values vary street by street, so refine as you gather evidence.
- **RZLT polygons are not ownership boundaries.** One parcel may have several owners, or one owner may hold several parcels. The folio search settles this.
- **No owner data in this tool, by design.** Keep folio and owner details in a separate, secure file (GDPR).
- **Planning dataset coverage varies by council.** Check council portals for the shortlist.
