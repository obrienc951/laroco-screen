"""
score.py — STEP 3: APPRAISE AND RANK
====================================
For every parcel that survived the filters:

A) CAPACITY — how many homes could it take?
     units = area x net-to-gross x density

B) RESIDUAL LAND VALUE — what's the land worth WITH permission?
   Classic developer's sum, worked backwards:
     GDV (sales value)   = units x unit size x €/sqm
   - build cost, professional fees, contributions
   - finance, sales costs, developer's profit
   = what a developer can afford to pay for the land
   Negative or thin = not viable = no deal.

C) LAROCO ECONOMICS (your promotion agreement waterfall)
     uplift          = residual value - current value
     net uplift      = uplift - promotion cost
     Laroco profit   = 30% x net uplift  (plus cost recovered first)
     Landowner gets  = current value + 70% x net uplift

D) SCORE — combine several 0-1 factors with your weights into
   one number, then rank. Weights live in config.yaml.

Unknowns (e.g. no flood layer loaded) score a neutral 0.5 so they
neither help nor hurt a parcel.
"""

import numpy as np
import pandas as pd
from common import lookup, log


def appraise(gdf, cfg):
    cap, c, lar = cfg["capacity"], cfg["costs"], cfg["laroco"]

    # A) Capacity
    gdf["units"] = np.floor(gdf["area_ha"] * cap["net_to_gross"] * cap["density_dph"]).astype(int)
    floor_area = gdf["units"] * cap["avg_unit_sqm"]

    # B) Residual land value
    sales_psqm = gdf["la"].map(lambda la: lookup(cfg["sales_value_psqm"], la))
    gdf["gdv"] = floor_area * sales_psqm
    build = floor_area * c["build_cost_psqm"]
    total_costs = (
        build
        + build * c["prof_fees_pct"]
        + gdf["units"] * c["contributions_per_unit"]
        + gdf["gdv"] * (c["finance_pct_gdv"] + c["sales_costs_pct_gdv"] + c["developer_profit_pct_gdv"])
    )
    gdf["residual_value"] = gdf["gdv"] - total_costs

    # C) Laroco waterfall
    cur_per_ha = gdf["la"].map(lambda la: lookup(cfg["current_value_per_ha"], la))
    gdf["current_value"] = gdf["area_ha"] * cur_per_ha
    gdf["uplift"] = gdf["residual_value"] - gdf["current_value"]
    gdf["promotion_cost"] = lar["promotion_cost_base"] + gdf["units"] * lar["promotion_cost_per_unit"]
    net_uplift = (gdf["uplift"] - gdf["promotion_cost"]).clip(lower=0)
    gdf["laroco_profit"] = net_uplift * lar["laroco_share"]
    gdf["landowner_proceeds"] = gdf["current_value"] + net_uplift * (1 - lar["laroco_share"])
    # How much more the landowner gets vs selling today, in %.
    # This is the number that sells the deal to them.
    gdf["landowner_gain_pct"] = (gdf["landowner_proceeds"] / gdf["current_value"] - 1) * 100
    return gdf


def score(gdf, cfg):
    w = cfg["weights"]

    # Each factor -> 0 (worst) to 1 (best)
    # fee: percentile rank within this batch (top fee = 1.0)
    f_fee = gdf["laroco_profit"].rank(pct=True)
    # margin: uplift as a multiple of current value, capped at 3x
    f_margin = (gdf["uplift"] / gdf["current_value"]).clip(0, 3) / 3
    # size fit: 1 at the sweet spot, falling to 0 at double/zero
    sweet = cfg["sweet_spot_ha"]
    f_size = (1 - (gdf["area_ha"] - sweet).abs() / sweet).clip(0, 1)
    # history: no refusals = 1, one = 0.5, two+ = 0; unknown = 0.5
    f_hist = gdf["refusal_count"].map(lambda n: 0.5 if pd.isna(n) else {0: 1.0, 1: 0.5}.get(int(n), 0.0))
    # flood: share of parcel NOT in flood zone; unknown = 0.5
    f_flood = gdf["flood_pct"].map(lambda p: 0.5 if pd.isna(p) else 1 - p / 100)

    total_w = sum(w.values())
    gdf["score"] = (
        w["fee"] * f_fee + w["margin"] * f_margin + w["size_fit"] * f_size
        + w["history"] * f_hist + w["flood"] * f_flood
    ) / total_w * 100
    gdf["score"] = gdf["score"].round(1)
    return gdf.sort_values("score", ascending=False)


def appraise_and_score(passed, cfg):
    gdf = appraise(passed, cfg)
    # Final economic filter: drop parcels that don't earn Laroco enough.
    floor = cfg["laroco"]["min_laroco_fee"]
    viable = gdf[gdf["laroco_profit"] >= floor].copy()
    unviable = gdf[gdf["laroco_profit"] < floor].copy()
    unviable["excluded_reason"] = f"Laroco profit < €{floor:,}; "
    log(f"Economics: {len(viable):,} viable, {len(unviable):,} below fee floor")
    return score(viable, cfg), unviable
