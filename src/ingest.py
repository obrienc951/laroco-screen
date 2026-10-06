"""
ingest.py — STEP 1: LOAD AND PREPARE THE DATA
=============================================
What it does:
  1. Reads the RZLT map (every parcel of land liable to the tax).
  2. Keeps only the local authorities you're targeting.
  3. Converts coordinates to Irish Transverse Mercator (metres) so
     areas come out in real square metres, not degrees.
  4. Calculates each parcel's area in hectares.
  5. Loads the optional planning and flood layers in the same
     coordinate system so they can be overlaid.

Key idea — a GeoDataFrame:
  Think of it as an Excel sheet where every row also has a shape
  (the parcel boundary) in a special 'geometry' column. You can
  filter rows like a spreadsheet AND do map operations like
  "which parcels overlap a flood zone?".
"""

import geopandas as gpd
from common import project_path, log


def load_layer(path, crs):
    """Read one map file and convert it to the working coordinate system."""
    gdf = gpd.read_file(project_path(path))
    if gdf.crs is None:
        # Some files don't declare a CRS; Irish open data is usually lat/long.
        log(f"  {path}: no CRS declared — assuming EPSG:4326 (lat/long)")
        gdf = gdf.set_crs(4326)
    # to_crs re-projects: same places on Earth, different coordinate numbers.
    return gdf.to_crs(crs)


def ingest(cfg):
    crs = cfg["working_crs"]
    cols = cfg["columns"]

    # --- RZLT parcels (required) ---------------------------------------
    log("Loading RZLT map...")
    rzlt = load_layer(cfg["inputs"]["rzlt"], crs)
    log(f"  {len(rzlt):,} parcels loaded")

    # Keep only target local authorities (empty list = keep all).
    if cfg["target_las"]:
        rzlt = rzlt[rzlt[cols["rzlt_la"]].isin(cfg["target_las"])].copy()
        log(f"  {len(rzlt):,} parcels in {', '.join(cfg['target_las'])}")

    # Fix broken shapes (self-intersecting boundaries are common in
    # government data and make area/overlap maths fail). make_valid
    # repairs them without changing the land covered.
    rzlt["geometry"] = rzlt.geometry.make_valid()

    # .area gives square metres (because CRS is in metres); /10,000 = hectares.
    rzlt["area_ha"] = rzlt.geometry.area / 10_000

    # A clean, consistent id and LA column for later steps.
    rzlt["parcel_id"] = rzlt[cols["rzlt_id"]].astype(str)
    rzlt["la"] = rzlt[cols["rzlt_la"]]

    # --- Optional layers ----------------------------------------------
    layers = {"rzlt": rzlt, "planning": None, "flood": None}
    for name in ("planning", "flood"):
        path = cfg["inputs"].get(name)
        if path:
            log(f"Loading {name} layer...")
            layers[name] = load_layer(path, crs)
            log(f"  {len(layers[name]):,} features")
        else:
            log(f"No {name} layer set — that check will be skipped")
    return layers
