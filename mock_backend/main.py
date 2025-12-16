# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may not obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import base64
import zipfile
import io
import random

app = FastAPI(title="RetailVista Mock Backend")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_response(data: dict):
    return {"code": "200", "message": "OK", "data": data}

def generate_zip(filename: str, content: dict) -> str:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(filename, json.dumps(content))
    zip_buffer.seek(0)
    return base64.b64encode(zip_buffer.read()).decode('utf-8')

# --- API Implementations ---

@app.post("/location-aggregate/v1/location-aggregates")
async def location_aggregate(request: Request):
    body = await request.json()
    print(f"MOCK: Aggregate Request: {body}")
    return create_response({
        "demographics": {"population": "1,250,000", "households": "300,000"},
        "storeNetwork": {"count": 42}
    })

@app.post("/store/v1/store-cluster")
async def store_cluster(request: Request):
    body = await request.json()
    print(f"MOCK: Cluster Request: {body}")
    
    clusters = [{"name": f"Cluster {i}", "lat": random.uniform(18, 20), "lon": random.uniform(72, 74)} for i in range(5)]
    data_b64 = generate_zip("clusters.json", {"clusterData": clusters})
    return create_response({"data": data_b64})

@app.post("/store-list/v1/retail-assets")
async def retail_assets(request: Request):
    body = await request.json()
    print(f"MOCK: Assets Request: {body}")
    
    stores = [{"storeName": f"Store {i}", "lat": random.uniform(18, 20), "lon": random.uniform(72, 74)} for i in range(15)]
    data_b64 = generate_zip("stores.json", {"stores": stores})
    return create_response({"data": data_b64})

@app.post("/store/v1/assets-list")
async def asset_list(request: Request):
    return create_response({"assets": ["Store A", "Store B"]})

@app.post("/store-search/v1/asset-search")
async def asset_search(request: Request):
    return create_response({"results": ["Match 1", "Match 2"]})

@app.post("/hex-analysis/v1/state-city-hex-analysis")
async def hex_analysis(request: Request):
    data_b64 = generate_zip("hex.json", {"hexagons": []})
    return create_response({"data": data_b64})

@app.post("/admin-boundry/v1/polygon/boundary")
async def polygon_boundary(request: Request):
    data_b64 = generate_zip("boundary.geojson", {"type": "FeatureCollection", "features": []})
    return create_response({"data": data_b64})

@app.post("/auth/v1/auth/logout")
async def logout(request: Request):
    return create_response({"status": "Logged Out"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
