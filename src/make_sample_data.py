"""
make_sample_data.py — FAKE DATA TO TEST YOUR SETUP
==================================================
    python src/make_sample_data.py

Creates made-up parcels, planning applications and a flood zone
around north Co. Dublin, saved to data/raw/sample_*.geojson.
Use it to check everything installs and runs BEFORE downloading
real data. To use it, point config.yaml inputs at the sample files.

None of these parcels are real.
"""

import random
import geopandas as gpd
from shapely.geometry import box
from common import project_path

random.seed(1)
CRS = 2157                     # Irish Transverse Mercator (metres)
X0, Y0 = 725000, 755000        # roughly north Co. Dublin in ITM


def main():
    raw = project_path("data/raw")
    raw.mkdir(parents=True, exist_ok=True)

    # 60 square-ish parcels between ~0.1 and ~3 ha
    parcels = []
    for i in range(60):
        side = random.uniform(30, 175)                 # metres
        x, y = X0 + random.uniform(0, 8000), Y0 + random.uniform(0, 8000)
        parcels.append({"OBJECTID": i + 1, "LA_NAME": "Fingal County Council",
                        "geometry": box(x, y, x + side, y + side)})
    rz = gpd.GeoDataFrame(parcels, crs=CRS)
    rz.to_crs(4326).to_file(raw / "sample_rzlt.geojson")   # saved as lat/long like real data

    # Planning applications on a few parcels
    apps = []
    for i, row in rz.sample(12, random_state=2).iterrows():
        apps.append({"PlanningRef": f"F{20+i%6}A/{1000+i}",
                     "Decision": random.choice(["GRANTED", "REFUSED"]),
                     "DecisionDate": f"0{random.randint(1,9)}/06/20{random.randint(17,25)}",
                     "geometry": row.geometry.buffer(-5)})
    gpd.GeoDataFrame(apps, crs=CRS).to_crs(4326).to_file(raw / "sample_planning.geojson")

    # One flood zone strip across the area
    flood = gpd.GeoDataFrame([{"zone": "A", "geometry": box(X0, Y0 + 3000, X0 + 8000, Y0 + 3600)}], crs=CRS)
    flood.to_crs(4326).to_file(raw / "sample_flood.geojson")
    print("Sample data written to data/raw/")


if __name__ == "__main__":
    main()
