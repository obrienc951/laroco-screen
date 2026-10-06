"""
run.py — RUN THE WHOLE SCREEN IN ONE GO
=======================================
    python src/run.py

Runs the four steps in order:
  ingest  -> load and prepare the maps
  filter  -> drop deal-breakers, recording why
  score   -> appraise each parcel and rank it
  export  -> save Excel shortlist, exclusion log, QGIS map file

Change assumptions in config.yaml and simply run it again; results
are rebuilt from scratch each time.
"""

import pandas as pd
from common import load_config, log
from ingest import ingest
from filter import apply_filters
from score import appraise_and_score
from export import export


def main():
    cfg = load_config()
    log("=== Laroco site screen ===")
    layers = ingest(cfg)
    passed, excluded = apply_filters(layers, cfg)
    ranked, unviable = appraise_and_score(passed, cfg)
    all_excluded = pd.concat([excluded, unviable])
    export(ranked, all_excluded, cfg)
    log(f"Done. {len(ranked):,} viable parcels; top {min(len(ranked), cfg['output']['top_n'])} in shortlist.")


if __name__ == "__main__":
    main()
