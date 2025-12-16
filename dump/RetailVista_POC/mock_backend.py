import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import base64
import io
import zipfile
import json
from typing import Dict, Any, Optional

app = FastAPI(title="RetailVista Mock Backend")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper Functions ---
def generate_zip_response(filename: str, json_data: Dict[str, Any]) -> str:
    """Generates a Base64 ZIP containing a JSON file."""
    json_str = json.dumps(json_data, indent=2)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(filename, json_str)
    zip_buffer.seek(0)
    return base64.b64encode(zip_buffer.read()).decode('utf-8')

# --- 1. Location Aggregates ---
@app.post("/location-aggregate/v1/location-aggregates")
async def get_location_aggregates(request: Request):
    """Returns dummy aggregate stats."""
    body = await request.json()
    print(f"MOCK API: /location-aggregates called with {body}")
    
    return {
        "code": "200",
        "message": "Success",
        "data": {
            "locationType": body.get("locationType"),
            "locationId": body.get("locationId"),
            "demographics": {
                "population": 15000000,
                "households": 3400000,
            },
            "storeNetwork": {
                "count": 150
            }
        }
    }

# --- 2. Store Cluster (ZIP) ---
@app.post("/store/v1/store-cluster")
async def get_store_cluster(request: Request):
    """Returns clustered store data (ZIP)."""
    body = await request.json()
    print(f"MOCK API: /store-cluster called with {body}")
    
    # Dummy Cluster Data
    cluster_data = {
        "locationType": body.get("locationType", "STATE"),
        "clusterData": [
            {"name": "Cluster A", "lat": 19.1, "lon": 72.9, "storeCount": 5},
            {"name": "Cluster B", "lat": 19.2, "lon": 72.8, "storeCount": 3}
        ]
    }
    
    base64_zip = generate_zip_response("clusters.json", cluster_data)
    
    return {
        "code": "200",
        "message": "Success",
        "data": base64_zip 
    }

# --- 3. Retail Assets (ZIP) ---
@app.post("/store-list/v1/retail-assets")
async def get_retail_assets(request: Request):
    """Returns full retail asset list (ZIP)."""
    body = await request.json()
    print(f"MOCK API: /retail-assets called with {body}")
    
    location_id = body.get("locationId", "Unknown")
    
    stores_data = {
        "stores": [
            {"storeName": f"Rel Digital {location_id} 001", "assetCategory": "Retail Store", "lat": 19.0, "lon": 73.0},
            {"storeName": f"Fresh {location_id} 002", "assetCategory": "Fresh", "lat": 18.5, "lon": 73.8},
            {"storeName": f"Trends {location_id} 003", "assetCategory": "Trends", "lat": 20.0, "lon": 74.0}
        ]
    }
    
    base64_zip = generate_zip_response("stores.json", stores_data)
    
    return {
        "code": "200",
        "message": "Success",
        "data": base64_zip
    }

# --- 4. Asset List (JSON) ---
@app.post("/store/v1/assets-list")
async def get_asset_list(request: Request):
    """Returns simple asset list (JSON)."""
    body = await request.json()
    print(f"MOCK API: /assets-list called with {body}")
    
    return {
        "code": "200",
        "message": "Success",
        "data": {
            "assets": [
                {"assetName": "Store A", "city": "Pune"},
                {"assetName": "Store B", "city": "Pune"}
            ]
        }
    }

# --- 5. Asset Search (JSON) ---
@app.post("/store-search/v1/asset-search")
async def asset_search(request: Request):
    """Returns search results (JSON)."""
    body = await request.json()
    print(f"MOCK API: /asset-search called with {body}")
    query = body.get("searchString", "")
    
    return {
        "code": "200",
        "message": "Success",
        "data": {
            "totalResults": 2,
            "assets": [
                {"assetName": f"{query} Result 1", "assetCategory": "Retail"},
                {"assetName": f"{query} Result 2", "assetCategory": "Digital"}
            ]
        }
    }

# --- 6. Hex Analysis (ZIP) ---
@app.post("/hex-analysis/v1/state-city-hex-analysis")
async def get_hex_analysis(request: Request):
    """Returns Hex data (ZIP)."""
    body = await request.json()
    print(f"MOCK API: /hex-analysis called with {body}")
    
    hex_data = {
        "hexAnalysisData": [
            {"h3Index": "8928308280fffff", "level": 9, "signals": {"noOfBuilding": 100}},
            {"h3Index": "8928308283fffff", "level": 9, "signals": {"noOfBuilding": 50}}
        ]
    }
    
    base64_zip = generate_zip_response("hex_data.json", hex_data)
    return {
        "code": "200",
        "message": "Success",
        "data": base64_zip
    }

# --- 7. Polygon Boundary (ZIP) ---
@app.post("/admin-boundry/v1/polygon/boundary")
async def get_polygon_boundary(request: Request):
    """Returns GeoJSON boundary (ZIP)."""
    body = await request.json()
    print(f"MOCK API: /polygon/boundary called with {body}")
    
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [[[0,0], [0,1], [1,1], [1,0], [0,0]]]},
                "properties": {"name": "Dummy Boundary"}
            }
        ]
    }
    
    base64_zip = generate_zip_response("boundary.geojson", geojson_data)
    return {
        "code": "200",
        "message": "Success",
        "data": base64_zip
    }

# --- 8. Logout (JSON) ---
@app.post("/auth/v1/auth/logout")
async def logout(request: Request):
    """Logs out."""
    print("MOCK API: /logout called")
    return {
        "code": "200",
        "message": "Logged out successfully"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
