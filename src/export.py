"""
export.py — STEP 4: SAVE THE RESULTS
====================================
Writes three outputs to the output/ folder:

  shortlist.xlsx    Top N parcels, one row each, with the numbers
                    rounded and columns in a readable order. This is
                    your working list for site checks and folio searches.

  excluded.csv      Every parcel that was dropped, with the reason.
                    Skim it occasionally to check the rules aren't
                    throwing out good land.

  screen.gpkg       A GeoPackage: a single file holding map layers
                    (shortlist + all viable + excluded). Drag it into
                    QGIS to see the parcels on a map, colour them by
                    score, and click any parcel to see its numbers.
"""

import pandas as pd
from common import project_path, log

SHORTLIST_COLS = [
    "parcel_id", "la", "area_ha", "units", "gdv", "residual_value",
    "current_value", "uplift", "promotion_cost", "laroco_profit",
    "landowner_proceeds", "landowner_gain_pct", "flood_pct",
    "refusal_count", "planning_refs", "score",
]


def export(ranked, excluded, cfg):
    out = project_path(cfg["output"]["folder"])
    out.mkdir(exist_ok=True)
    top = ranked.head(cfg["output"]["top_n"])

    # 1. Excel shortlist (rounded for readability)
    sheet = top[SHORTLIST_COLS].copy()
    money = ["gdv", "residual_value", "current_value", "uplift",
             "promotion_cost", "laroco_profit", "landowner_proceeds"]
    sheet[money] = sheet[money].round(-3)          # nearest €1,000
    sheet[["area_ha", "landowner_gain_pct"]] = sheet[["area_ha", "landowner_gain_pct"]].round(2)
    sheet.insert(0, "rank", range(1, len(sheet) + 1))
    sheet.to_excel(out / "shortlist.xlsx", index=False)

    # 2. Audit trail of exclusions (drop shapes: CSV can't hold them)
    excluded.drop(columns="geometry").to_csv(out / "excluded.csv", index=False)

    # 3. Map layers for QGIS. Each call adds a named layer to one file.
    gpkg = out / "screen.gpkg"
    if gpkg.exists():
        gpkg.unlink()                              # start fresh each run
    keep = SHORTLIST_COLS + ["geometry"]
    top[keep].to_file(gpkg, layer="shortlist", driver="GPKG")
    ranked[keep].to_file(gpkg, layer="all_viable", driver="GPKG")
    excluded[["parcel_id", "la", "area_ha", "excluded_reason", "geometry"]].to_file(
        gpkg, layer="excluded", driver="GPKG")

    log(f"Saved: {out/'shortlist.xlsx'}, {out/'excluded.csv'}, {gpkg}")
