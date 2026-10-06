"""
filter.py — STEP 2: HARD FILTERS (DEAL-BREAKERS)
================================================
Each parcel is checked against rules that make it a non-starter.
Rather than silently deleting parcels, every exclusion gets a
written reason in an 'excluded_reason' column. At the end the
script splits the data into:
  - passed   -> goes on to scoring
  - excluded -> saved to output/excluded.csv so you can audit
                what the screen threw away (and spot bad rules)

Checks:
  1. Size band        — too small = fixed costs eat the fee;
                        too big = outside Laroco's budget/thesis
  2. Flood Zone A     — % of parcel overlapping high flood risk
  3. Live permission  — someone already has planning; no role for us
Plus a non-excluding flag:
  4. Refusal history  — a past refusal isn't fatal, but it's
                        recorded because the reasons are diagnostic
"""

import pandas as pd
import geopandas as gpd
from common import log


def add_reason(gdf, mask, reason):
    """Append a reason to every row where mask is True.
    (A parcel can fail several checks; all reasons are kept.)"""
    gdf.loc[mask, "excluded_reason"] = (
        gdf.loc[mask, "excluded_reason"].fillna("") + reason + "; "
    )


def flood_overlap_pct(parcels, flood):
    """For each parcel, what % of its area lies inside Flood Zone A?
    overlay(how='intersection') cuts parcels into the pieces that sit
    inside flood polygons; we then add up those pieces' area."""
    pieces = gpd.overlay(
        parcels[["parcel_id", "geometry"]], flood[["geometry"]], how="intersection"
    )
    pieces["flood_m2"] = pieces.geometry.area
    flooded = pieces.groupby("parcel_id")["flood_m2"].sum()
    pct = flooded / (parcels.set_index("parcel_id")["area_ha"] * 10_000) * 100
    return parcels["parcel_id"].map(pct).fillna(0).round(1)


def planning_history(parcels, planning, cfg):
    """Spatial join: attach every planning application that touches
    each parcel, then summarise per parcel."""
    cols = cfg["columns"]
    p = planning.copy()
    p["decision"] = p[cols["planning_decision"]].astype(str).str.upper()
    p["date"] = pd.to_datetime(p[cols["planning_date"]], errors="coerce", dayfirst=True)
    p["ref"] = p[cols["planning_ref"]].astype(str)

    # sjoin = "spatial join": like VLOOKUP, but matching on location
    # (does the application shape intersect the parcel?) instead of an id.
    hits = gpd.sjoin(
        parcels[["parcel_id", "geometry"]],
        p[["decision", "date", "ref", "geometry"]],
        how="inner", predicate="intersects",
    )

    cutoff = pd.Timestamp.today() - pd.DateOffset(years=cfg["filters"]["permission_lookback_years"])
    recent_grant = hits[hits["decision"].str.contains("GRANT") & (hits["date"] >= cutoff)]
    refused = hits[hits["decision"].str.contains("REFUS")]

    out = pd.DataFrame(index=parcels["parcel_id"])
    out["live_permission"] = out.index.isin(recent_grant["parcel_id"])
    out["refusal_count"] = refused.groupby("parcel_id").size().reindex(out.index).fillna(0).astype(int)
    out["planning_refs"] = hits.groupby("parcel_id")["ref"].apply(lambda s: ", ".join(sorted(set(s)))).reindex(out.index)
    return out.reset_index()


def apply_filters(layers, cfg):
    gdf = layers["rzlt"].copy()
    f = cfg["filters"]
    gdf["excluded_reason"] = pd.NA

    # 1. Size band
    add_reason(gdf, gdf["area_ha"] < f["min_area_ha"], f"under {f['min_area_ha']} ha")
    add_reason(gdf, gdf["area_ha"] > f["max_area_ha"], f"over {f['max_area_ha']} ha")

    # 2. Flood
    if layers["flood"] is not None:
        log("Checking flood overlap...")
        gdf["flood_pct"] = flood_overlap_pct(gdf, layers["flood"])
        if f["exclude_flood_zone_a"]:
            add_reason(gdf, gdf["flood_pct"] > f["flood_overlap_max_pct"], "flood zone A")
    else:
        gdf["flood_pct"] = pd.NA

    # 3 & 4. Planning history
    if layers["planning"] is not None:
        log("Checking planning history...")
        hist = planning_history(gdf, layers["planning"], cfg)
        gdf = gdf.merge(hist, on="parcel_id", how="left")
        if f["exclude_live_permission"]:
            add_reason(gdf, gdf["live_permission"], "live permission")
    else:
        gdf["live_permission"] = pd.NA
        gdf["refusal_count"] = pd.NA
        gdf["planning_refs"] = pd.NA

    passed = gdf[gdf["excluded_reason"].isna()].copy()
    excluded = gdf[gdf["excluded_reason"].notna()].copy()
    log(f"Filters: {len(passed):,} passed, {len(excluded):,} excluded")
    return passed, excluded
