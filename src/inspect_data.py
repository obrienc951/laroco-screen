"""
inspect_data.py — LOOK BEFORE YOU SCREEN
========================================
Run this first, every time you download a new dataset:

    python src/inspect_data.py

It opens each input file listed in config.yaml and prints:
  - how many rows (parcels / applications / flood polygons) it has
  - its coordinate system (CRS)
  - its column names and a sample row
  - for the RZLT file, the list of local authority names

You then copy the right column names into config.yaml (section 2).
Nothing is changed or saved — this script only reads.
"""

import geopandas as gpd   # geopandas = pandas (spreadsheet-style tables) + map shapes
from common import load_config, project_path


def describe(name, path):
    print("=" * 70)
    print(f"{name.upper()}  ->  {path}")
    print("=" * 70)
    # read_file understands GeoJSON, Shapefile, GeoPackage, etc.
    gdf = gpd.read_file(project_path(path))
    print(f"Rows:        {len(gdf):,}")
    # CRS = coordinate reference system: how x/y numbers map to places on Earth.
    # EPSG:4326 = latitude/longitude; EPSG:2157 = Irish Transverse Mercator (metres).
    print(f"CRS:         {gdf.crs}")
    print(f"Geometry:    {gdf.geom_type.value_counts().to_dict()}")
    print("Columns:")
    for col in gdf.columns:
        if col == "geometry":
            continue
        sample = gdf[col].dropna().iloc[0] if gdf[col].notna().any() else "(all empty)"
        print(f"   {col:<30} e.g. {str(sample)[:50]}")
    return gdf


def main():
    cfg = load_config()
    for name, path in cfg["inputs"].items():
        if path is None:
            print(f"\n[{name}] not set in config — skipped\n")
            continue
        gdf = describe(name, path)
        # For RZLT, list the local authority names so you can copy one
        # exactly into target_las in config.yaml.
        if name == "rzlt":
            la_col = cfg["columns"]["rzlt_la"]
            if la_col in gdf.columns:
                print(f"\nLocal authorities in '{la_col}' (parcel count):")
                print(gdf[la_col].value_counts().to_string())
            else:
                print(f"\n!! Column '{la_col}' not found. Pick the LA column from the list "
                      f"above and set columns.rzlt_la in config.yaml.")
        print()


if __name__ == "__main__":
    main()
