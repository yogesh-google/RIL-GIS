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

import json
from typing import List, Optional

# --- Domain Knowledge ---
STATE_MAPPING = {
    "JAMMU & KASHMIR": "JK", "DELHI": "DL", "MAHARASHTRA": "MH",
    "GUJARAT": "GJ", "UTTAR PRADESH": "UP", "KARNATAKA": "KA",
    "TAMIL NADU": "TN", "WEST BENGAL": "WB", "TELANGANA": "TG",
    "KERALA": "KL", "RAJASTHAN": "RJ", "PUNJAB": "PB",
    "ANDHRA PRADESH": "AP", "MADHYA PRADESH": "MP", "ODISHA": "OR",
    "BIHAR": "BR", "HARYANA": "HR", "JHARKHAND": "JH", "CHHATTISGARH": "CG",
    "ASSAM": "AS", "HIMACHAL PRADESH": "HP", "UTTARAKHAND": "UK",
    "TRIPURA": "TR", "MEGHALAYA": "ML", "MANIPUR": "MN", "NAGALAND": "NL",
    "GOA": "GA", "ARUNACHAL PRADESH": "AR", "MIZORAM": "MZ", "SIKKIM": "SK"
}

def _resolve_location_id(location_id: Optional[str]) -> Optional[str]:
    """Helper to map state names to codes."""
    if not location_id:
        return None
    clean_id = location_id.upper().strip()
    return STATE_MAPPING.get(clean_id, clean_id)

# --- 1. Location Aggregates ---
def formulate_location_aggregate(location_type: str, location_id: str = None) -> str:
    """
    Get aggregated stats for a location.
    Args:
        location_type: 'INDIA', 'STATE', 'CITY', or 'VILLAGE'
        location_id: Required if type is NOT 'INDIA'. State code/city name.
    """
    command = {
        "action": "CALL_LOCATION_AGGREGATE",
        "payload": {
            "locationType": location_type,
            "locationId": _resolve_location_id(location_id),
            "datapoints": ["GEOGRAPHY", "DEMOGRAPHICS", "PLANNING", "STORE_NETWORK", "COMPETITORS"],
            "categories": ["CUSTOMERS", "BUILDINGS", "POIS", "STORENETWORK", "SUPPLYCHAIN", "COMPETITORS"]
        }
    }
    return json.dumps(command)

# --- 2. Store Cluster ---
def formulate_store_cluster(location_type: str, location_id: str = None, sub_type: str = None) -> str:
    """
    Get store clusters. Returns ZIP.
    Args:
        location_type: 'INDIA' or 'STATE'
        location_id: State code (Required if STATE)
        sub_type: 'CITY' or 'VILLAGE' (Required if STATE)
    """
    payload = {"locationType": location_type}
    if location_type == 'STATE':
        payload["locationId"] = _resolve_location_id(location_id)
        payload["subType"] = sub_type or 'CITY' # Default to CITY if not provided
        
    command = {
        "action": "CALL_STORE_CLUSTER",
        "payload": payload
    }
    return json.dumps(command)

# --- 3. Retail Assets ---
def formulate_retail_assets(location_type: str, location_id: str) -> str:
    """
    Get full list of retail assets (stores) for a State/City. Returns ZIP.
    Args:
        location_type: 'STATE', 'CITY', 'VILLAGE'
        location_id: State Name/Code or City Name.
    """
    command = {
        "action": "CALL_RETAIL_ASSETS",
        "payload": {
            "locationType": location_type,
            "locationId": _resolve_location_id(location_id)
        }
    }
    return json.dumps(command)

# --- 4. Asset List ---
def formulate_asset_list(location_type: str, location_id: str) -> str:
    """
    Get a simple list of assets (Non-Zip).
    Args:
        location_type: 'CITY' or 'VILLAGE'
        location_id: City/Village Name.
    """
    command = {
        "action": "CALL_ASSET_LIST",
        "payload": {
            "locationType": location_type,
            "locationId": location_id
        }
    }
    return json.dumps(command)

# --- 5. Asset Search ---
def formulate_asset_search(search_string: str, state_code: str = None) -> str:
    """
    Search for assets by name, category, etc.
    Args:
        search_string: Text to search (e.g. "Reliance Digital", "Mumbai")
        state_code: Optional filter.
    """
    payload = {"searchString": search_string}
    if state_code:
        payload["stateCode"] = _resolve_location_id(state_code)

    command = {
        "action": "CALL_ASSET_SEARCH",
        "payload": payload
    }
    return json.dumps(command)

# --- 6. Hex Analysis ---
def formulate_hex_analysis(location_id: str) -> str:
    """
    Get Hexagon-based analytics data. Returns ZIP.
    Args:
        location_id: State code or City name.
    """
    command = {
        "action": "CALL_HEX_ANALYSIS",
        "payload": {
            "locationId": _resolve_location_id(location_id)
        }
    }
    return json.dumps(command)

# --- 7. Polygon Boundary ---
def formulate_polygon_boundary(location_id: str, location_sub_type: str = 'CITY', state_code: str = None) -> str:
    """
    Retrieve admin boundaries (GeoJSON). Returns ZIP.
    Args:
        location_id: Name of location (e.g. "Mumbai")
        location_sub_type: 'CITY' or 'VILLAGE'
        state_code: Optional state code.
    """
    payload = {
        "locationType": "STATE", 
        "locationId": [location_id], 
        "locationSubType": location_sub_type
    }
    if state_code:
        payload["stateCode"] = _resolve_location_id(state_code)
        
    command = {
        "action": "CALL_POLYGON_BOUNDARY",
        "payload": payload
    }
    return json.dumps(command)

# --- 8. Logout ---
def formulate_logout() -> str:
    """Logs the user out."""
    command = {
        "action": "CALL_LOGOUT",
        "payload": {}
    }
    return json.dumps(command)
