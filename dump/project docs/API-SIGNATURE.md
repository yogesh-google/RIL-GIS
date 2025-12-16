# API Signature Reference

This document provides a concise reference for all API request/response signatures used in the RetailVista Portal application.

## Base Configuration

**Base URL**:

**Common Headers**:

```
JTOKEN: <authentication_token>
Content-Type: application/json
X-Request-ID: <uuid>
```

**Request Encryption**: Optional (via `environment.httpEnableEncryption`) **Response Format**: JSON (some endpoints return zip files that are automatically extracted)

---

## API Endpoints

### 1\. Location Aggregates

**Endpoint**: `POST /location-aggregate/v1/location-aggregates`

**Request Signature**:

```ts
{
  locationType: 'INDIA' | 'STATE' | 'CITY' | 'VILLAGE';  // Required
  locationId?: string;      // Optional, required for STATE/CITY/VILLAGE
  datapoints?: string[];    // Optional
  categories?: string[];    // Optional
}
```

**Response Signature**:

```ts
{
  code: string;
  message: string;
  data: StateApiResponse | GeographyLocationData | CompetitorsLocationData 
       | DemographicsLocationData | PlanningLocationData | StoreNetworkLocationData;
  requestId?: string;
  inTime?: string;
  outTime?: string;
  latency?: number;
}
```

**Service Method**: `ApiService.getLocationAggregates()`

---

### 2\. Store Cluster

**Endpoint**: `POST /store/v1/store-cluster`

**Request Signature**:

```ts
// For INDIA
{
  locationType: 'INDIA'
}

// For STATE
{
  locationType: 'STATE';
  locationId: string;      // Required (e.g., "MH", "GJ")
  subType: 'CITY' | 'VILLAGE';  // Required
}
```

**Response Signature**:

```ts
{
  code: string;
  message: string;
  data: {
    locationType: 'INDIA' | 'STATE' | 'CITY' | 'VILLAGE' | 'TOWN';
    locationName: string;
    locationId?: string;
    subType?: string;
    clusterData: Array<{
      name: string;
      id: string;
      lat: number;
      lon: number;
      storeCount: number;
      categoryCounts?: { [category: string]: number };
    }>;
  };
  requestId?: string;
  inTime?: string;
  outTime?: string;
  latency?: number;
}
```

**Response Format**: ZIP file (Blob) \- automatically extracted by interceptor

**Service Method**: `ApiService.getStoreClusterZipped()`

**Validation Rules**:

- `locationType` must be 'INDIA' or 'STATE'  
- When `locationType = 'STATE'`: `locationId` and `subType` are mandatory  
- When `locationType = 'INDIA'`: `locationId` and `subType` should not be included

---

### 3\. Retail Assets

**Endpoint**: `POST /store-list/v1/retail-assets`

**Request Signature**:

```ts
{
  locationType: 'STATE' | 'CITY' | 'VILLAGE';  // Required
  locationId: string;                         // Required (e.g., "MH" for state)
}
```

**Raw Response Signature** (before zip extraction):

```ts
{
  code: string;                  // "200"
  message: string;               // "Success"
  data: string;                  // Base64-encoded zip file
  requestId?: string;
  inTime?: string;               // ISO timestamp
  outTime?: string;              // ISO timestamp
  latency?: number;              // milliseconds
}
```

**Extracted Response Signature** (after zip extraction): The extracted JSON can be one of the following structures:

```ts
// Structure 1: Direct Array
Array<StoreItem>

// Structure 2: Stores Property
{
  stores: Array<StoreItem>
}

// Structure 3: Nested Data
{
  data: {
    stores: Array<StoreItem>
  }
}

// Structure 4: Deeply Nested
{
  data: {
    data: {
      stores: Array<StoreItem>
    }
  }
}

// Structure 5: Data Array
{
  data: Array<StoreItem>
}

// Structure 6: Cluster Data (backward compatibility)
{
  clusterData: Array<StoreItem>
}
```

**StoreItem Signature**:

```ts
{
  // Core Identification
  storeName?: string;
  name?: string;                 // Alternative name field
  storeId?: string;
  id?: string;                   // Alternative ID field
  
  // Location (Required)
  lat: number;                   // Latitude
  lon: number;                   // Longitude
  address?: string;              // Format: "State - City - Village - Store ID"
  
  // Category Information
  assetCategory?: string;        // e.g., "Dark Store", "Retail Store", "SCM"
  storeFormat?: string;          // e.g., "DIGITAL", "PHYSICAL"
  siteCategory?: string;         // e.g., "DARK STORE", "RETAIL STORE"
  subCategory?: string;
  
  // Geographic Details
  stateCode?: string;            // e.g., "MH", "GJ"
  stateName?: string;            // e.g., "Maharashtra"
  cityCode?: string;
  cityname?: string;
  villageRjid?: string;
  villagename?: string;
  
  // Store Metrics (Optional)
  area?: number;
  dailyFootfall?: number;
  daily_footfall?: number;       // Alternative field name
  dailyOrders?: number;
  daily_orders?: number;         // Alternative field name
  
  // Supply Chain
  supplyType?: string;
  supply_type?: string;         // Alternative field name
  
  // Internal Fields (added during processing)
  _stateCode?: string;
  _stateName?: string;
}
```

**Response Format**: JSON with base64-encoded zip in `data` field \- automatically extracted by interceptor

**Service Method**: `ApiService.getRetailAssets()`

**Zip Extraction**: HTTP interceptor automatically extracts JSON file from zip archive

---

### 4\. Asset List

**Endpoint**: `POST /store/v1/assets-list`

**Request Signature**:

```ts
{
  locationType: 'CITY' | 'VILLAGE';  // Required
  locationId: string;                 // Required
}
```

**Response Signature**:

```ts
{
  code: string;
  message: string;
  data: {
    assets: Array<{
      assetId?: string;
      assetName?: string;
      storeName?: string;
      storeNo?: string;
      lat: number;
      lon: number;
      address?: string;
      city?: string;
      cityName?: string;
      cityCode?: string;
      villageName?: string;
      villageRjid?: string;
      assetCategory?: string;
      formatDesc?: string;
      siteCategoryDesc?: string;
      stateName?: string;
      stateCode?: string;
      storePinCode?: string;
      storeFormat?: string;
      latitude?: number;        // Alternative field name
      longitude?: number;       // Alternative field name
    }>;
  };
  requestId?: string;
  inTime?: string;
  outTime?: string;
  latency?: number;
}
```

**Service Method**: `ApiService.getAssetList()`

---

### 5\. Asset Search

**Endpoint**: `POST /store-search/v1/asset-search`

**Request Signature**:

```ts
{
  searchString: string;      // Required
  stateCode?: string;        // Optional
}
```

**Response Signature**:

```ts
{
  code: string;
  message: string;
  data: {
    totalResults: number;
    assets: Array<{
      assetId?: string;
      assetName?: string;
      storeName?: string;
      storeNo?: string;
      lat: number;
      lon: number;
      address?: string;
      city?: string;
      cityName?: string;
      cityCode?: string;
      villageName?: string;
      villageRjid?: string;
      assetCategory?: string;
      formatDesc?: string;
      siteCategoryDesc?: string;
      stateName?: string;
      stateCode?: string;
      storePinCode?: string;
      storeFormat?: string;
      latitude?: number;
      longitude?: number;
    }>;
  };
  requestId?: string;
  inTime?: string;
  outTime?: string;
  latency?: number;
}
```

**Service Method**: `DashboardService.searchAssets()`

**Search Fields**: Searches across CITYNAME, ASSET\_CATEGORY, FORMAT\_DESC, VILLAGENAME, SITE\_CATEGORY\_DESC, STORENAME, STATENAME, ADDRESS

---

### 6\. Hex Analysis

**Endpoint**: `POST /hex-analysis/v1/state-city-hex-analysis`

**Request Signature**:

```ts
{
  locationId: string;  // Required (state code, city code, or village ID)
}
```

**Raw Response Signature** (before zip extraction):

```ts
{
  code: string;
  message: string;
  data: string;         // Base64-encoded zip file
  requestId?: string;
  inTime?: string;
  outTime?: string;
  latency?: number;
}
```

**Extracted Response Signature** (after zip extraction):

```ts
{
  code: string;
  message: string;
  data: {
    hexAnalysisData: Array<{
      h3Index: string;        // H3 hexagon index
      level: number;          // H3 resolution level
      signals: {
        cityCode?: string;
        cityName?: string;
        noOfBuilding?: number;
        noOfHousehold?: number;
        noOfPoi?: number;
        noOfRetailCustomer?: number;
        noOfJioCustomer?: number;
      };
    }>;
  };
  requestId?: string;
  inTime?: string;
  outTime?: string;
  latency?: number;
}
```

**Response Format**: JSON with base64-encoded zip in `data` field \- automatically extracted by interceptor

**Service Method**: `ApiService.runHexAnalysisZipped()`

---

### 7\. Polygon Boundary

**Endpoint**: `POST /admin-boundry/v1/polygon/boundary`

**Request Signature**:

```ts
{
  locationType: 'STATE';              // Required (currently only supports 'STATE')
  locationId: string[];               // Required - Array of location IDs
  locationSubType?: 'CITY' | 'VILLAGE';  // Optional
  stateCode?: string;                 // Optional
}
```

**Raw Response Signature** (before zip extraction):

```ts
{
  code: string;
  message: string;
  data: string;         // Base64-encoded zip file containing GeoJSON
  requestId?: string;
  inTime?: string;
  outTime?: string;
  latency?: number;
}
```

**Extracted Response Signature** (after zip extraction \- GeoJSON):

```ts
{
  type: "FeatureCollection",
  features: Array<{
    type: "Feature",
    geometry: {
      type: "Polygon" | "MultiPolygon",
      coordinates: number[][][]
    },
    properties: {
      [key: string]: any;
    }
  }>
}
```

**Response Format**: JSON with base64-encoded zip in `data` field \- automatically extracted by interceptor

**Service Method**: `DashboardService.getPolygonBoundary()`

---

### 8\. Logout

**Endpoint**: `POST /auth/v1/auth/logout`

**Request Signature**:

```ts
{}  // Empty body
```

**Response Signature**:

```ts
{
  code: string;
  message: string;
  data?: any;
  requestId?: string;
}
```

**Service Method**: `ApiService.logout()`

---

## Zip File Handling

The following endpoints return zip files that are automatically extracted by the HTTP interceptor:

| Endpoint | Zip Format | Extraction Method |
| :---- | :---- | :---- |
| `/store/v1/store-cluster` | Direct Blob | Extracted from Blob response |
| `/store-list/v1/retail-assets` | Base64 in JSON `data` field | Decoded and extracted |
| `/hex-analysis/v1/state-city-hex-analysis` | Base64 in JSON `data` field | Decoded and extracted |
| `/admin-boundry/v1/polygon/boundary` | Base64 in JSON `data` field | Decoded and extracted |

**Extraction Process**:

1. For Blob responses: Directly extract zip from Blob  
2. For JSON responses: Decode base64 `data` field → Extract zip → Find JSON file → Parse JSON

**JSON File Detection** (in zip):

- Searches for files with `.json` extension  
- Searches for files containing "retail", "assets", "stores", "data", "hex", "analysis" in filename  
- Falls back to any `.json` file found

---

## Common Response Wrapper

All API responses follow this wrapper structure:

```ts
interface ApiResponseWrapper<T> {
  code: string;           // Response code (e.g., "200", "400", "500")
  message: string;        // Human-readable message
  data: T;                // Response payload (type varies by endpoint)
  requestId?: string;     // Correlation ID for request tracking
  inTime?: string;        // Request received timestamp (ISO format)
  outTime?: string;       // Response sent timestamp (ISO format)
  latency?: number;       // Response latency in milliseconds
}
```

---

## Error Response Signature

```ts
{
  status: number;         // HTTP status code
  message: string;        // Error message
  error?: {
    code?: string;        // API error code
    message?: string;     // API error message
    // ... other error details
  };
}
```

**Error Handling**:

- **401 Unauthorized**: Redirects to `/auth` page  
- **500+ Server Errors**: Shows toast notification  
- **Network Errors**: Automatic retry (3 attempts, 500ms delay)  
- **Timeout Errors**: Automatic retry (5 second timeout)

---

## Request/Response Flow

```
Client Request
    ↓
HTTP Interceptor (Request)
    ↓
[Optional] Encryption
    ↓
Add Headers (JTOKEN, X-Request-ID)
    ↓
API Server
    ↓
HTTP Interceptor (Response)
    ↓
[If Zip] Extract Zip → Parse JSON
    ↓
[Optional] Decryption
    ↓
Service Layer
    ↓
Component Layer
```

---

## Quick Reference Table

| \# | Endpoint | Method | Request Body | Response Format | Zip? |
| :---- | :---- | :---- | :---- | :---- | :---- |
| 1 | `/location-aggregate/v1/location-aggregates` | POST | `{ locationType, locationId?, datapoints?, categories? }` | JSON | No |
| 2 | `/store/v1/store-cluster` | POST | `{ locationType, locationId?, subType? }` | ZIP → JSON | Yes |
| 3 | `/store-list/v1/retail-assets` | POST | `{ locationType, locationId }` | ZIP → JSON | Yes |
| 4 | `/store/v1/assets-list` | POST | `{ locationType, locationId }` | JSON | No |
| 5 | `/store-search/v1/asset-search` | POST | `{ searchString, stateCode? }` | JSON | No |
| 6 | `/hex-analysis/v1/state-city-hex-analysis` | POST | `{ locationId }` | ZIP → JSON | Yes |
| 7 | `/admin-boundry/v1/polygon/boundary` | POST | `{ locationType, locationId[], locationSubType?, stateCode? }` | ZIP → GeoJSON | Yes |
| 8 | `/auth/v1/auth/logout` | POST | `{}` | JSON | No |

---

## Version

**v1.0** \- Initial API Signature Reference

- Documents 8 API endpoints  
- Includes request/response signatures  
- Documents zip extraction process  
- Includes error handling signatures

---

## Notes

- All POST requests use JSON body  
- Zip responses are automatically extracted by HTTP interceptor  
- Base64-encoded zip data is in the `data` field of JSON responses  
- Request encryption is optional and configured via environment  
- All endpoints require `JTOKEN` authentication header  
- Correlation ID (`X-Request-ID`) is auto-generated for all requests

