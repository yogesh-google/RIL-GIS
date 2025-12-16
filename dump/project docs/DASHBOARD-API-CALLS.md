# Dashboard API Calls Documentation

This document details all API calls that occur when landing on the dashboard and when clicking on state cards.

---

## Table of Contents

1. [API Calls on Dashboard Load](#api-calls-on-dashboard-load)
2. [API Calls on State Card Click](#api-calls-on-state-card-click)
3. [API Endpoints Reference](#api-endpoints-reference)

---

## API Calls on Dashboard Load

When the dashboard component initializes, the following API calls are made:

<!-- ===================================================================================== -->
### 1. Preload India Retail Assets (Background)  - INDIA LOADING DEAFULKT SCREEN
**Trigger:** `ngOnInit()` - Line 626  
**Service Method:** `RetailAssetsClusterService.preloadIndiaAssets()`  
**Endpoint:** `POST /store-list/v1/retail-assets`  
**Request Body:**
```typescript
{
  locationType: 'INDIA'
}
```
**Purpose:** Preloads retail assets data for India in the background for faster state-level loading  
**Timing:** Runs asynchronously without blocking UI  
**Note:** This data is cached and used when showing clusters for individual states (no additional API call needed)

---

### 2. Load Location Aggregates for All States
**Trigger:** `loadData()` - Called from `ngOnInit()` - Line 628  
**Service Method:** `DashboardService.getLocationAggregates()`  
**Endpoint:** `POST /location-aggregate/v1/location-aggregates`  
**Request Body:**
```typescript
{
  locationType: 'STATE',
  locationId: string,  // State code (e.g., 'MH', 'GJ')
  categories: ['CUSTOMERS', 'BUILDINGS', 'POIS', 'STORENETWORK', 'SUPPLYCHAIN', 'COMPETITORS']
}
```
**Purpose:** Loads aggregated statistics for each state (demographics, store network, competitors, etc.)  
**Behavior:** 
- Makes parallel API calls for all states found in `authorizedPlaces` from sessionStorage
- Updates state cards as each response arrives (progressive loading)
- Each state card shows skeleton data initially, then updates with real data

**Response Structure:**
```typescript
{
  code: string;
  message: string;
  data: {
    geography: {
      cities: number;
      villages: number;
    };
    demographics: {
      population: number;
      households: number;
      customers: {
        total: number;
        retail: number;
        jio: number;
        hotstar: number;
      };
    };
    planning: {
      buildings: {
        total: number;
        categories: Array<{ name: string; count: number }>;
      };
      pois: {
        total: number;
        categories: Array<{ name: string; count: number }>;
      };
    };
    storeNetwork: {
      retail: {
        total: number;
      };
      darkStores: number;
      competitors: {
        total: number;
      };
    };
    competitors: {
      total: number;
    };
  };
}
```

---

### 3. Load India Store Cluster Data
**Trigger:** `loadDashboardClusterData()` - Called from `ngAfterViewInit()` after map initialization - Line 932  
**Service Method:** `ApiService.getStoreClusterZipped()`  
**Endpoint:** `POST /store/v1/store-cluster`  
**Request Body:**
```typescript
{
  locationType: 'INDIA'
}
```
**Purpose:** Loads store cluster markers for India view (state-level markers on map)  
**Response:** ZIP file containing JSON with cluster data  
**Response Structure:**
```typescript
{
  locationType: 'INDIA';
  locationName: string;
  clusterData: Array<{
    name: string;        // State name
    id: string;          // State code
    lat: number;         // Latitude
    lon: number;         // Longitude
    storeCount: number;  // Number of stores in state
  }>;
}
```
**Note:** This API call is made after the map is initialized in `ngAfterViewInit()`

---

<!-- ================================================================================== -->
## API Calls on State Card Click

When a user clicks on a state card, the `onStateSelected()` method is triggered (Line 2627), which makes the following API calls:

### 1. Load Cities for Selected State
**Trigger:** `onStateSelected()` - Line 2761  
**Service Method:** `ApiService.getStoreClusterZipped()`  
**Endpoint:** `POST /store/v1/store-cluster`  
**Request Body:**
```typescript
{
  locationType: 'STATE',
  locationId: string,  // State code (e.g., 'MH', 'GJ')
  subType: 'CITY'
}
```
**Purpose:** Loads city cluster data for the selected state (for left panel list display)  
**Response:** ZIP file containing JSON with city cluster data  
**Response Structure:**
```typescript
{
  locationType: 'STATE';
  locationName: string;
  locationId: string;
  subType: 'CITY';
  clusterData: Array<{
    name: string;        // City name
    id: string;          // City ID
    lat: number;         // Latitude
    lon: number;         // Longitude
    storeCount: number;  // Number of stores in city
  }>;
}
```
**Note:** This data is used to populate the cities list in the left panel. City clusters are NOT displayed on the map (replaced by retail asset clusters).

---

### 2. Load Villages for Selected State
**Trigger:** `onStateSelected()` - Line 2809 (calls `loadVillagesForState()`)  
**Service Method:** `ApiService.getStoreClusterZipped()`  
**Endpoint:** `POST /store/v1/store-cluster`  
**Request Body:**
```typescript
{
  locationType: 'STATE',
  locationId: string,  // State code (e.g., 'MH', 'GJ')
  subType: 'VILLAGE'
}
```
**Purpose:** Loads village cluster data for the selected state (for left panel list display)  
**Response:** ZIP file containing JSON with village cluster data  
**Response Structure:**
```typescript
{
  locationType: 'STATE';
  locationName: string;
  locationId: string;
  subType: 'VILLAGE';
  clusterData: Array<{
    name: string;        // Village name
    id: string;          // Village ID
    lat: number;         // Latitude
    lon: number;         // Longitude
    storeCount: number;  // Number of stores in village
  }>;
}
```
**Note:** This data is used to populate the villages list in the left panel. Village clusters are NOT displayed on the map (replaced by retail asset clusters).

---

### 3. Draw State Boundary
**Trigger:** `onStateSelected()` - Line 2757 (calls `drawStateBoundary()`)  
**Service Method:** `DashboardService.getPolygonBoundary()`  
**Endpoint:** `POST /admin-boundry/v1/polygon/boundary`  
**Request Body:**
```typescript
{
  locationType: 'STATE',
  locationId: [string]  // Array with state code (e.g., ['MH'])
}
```
**Purpose:** Fetches GeoJSON boundary data for the selected state and draws it on the map  
**Response:** GeoJSON format containing polygon coordinates for state boundary  
**Behavior:** 
- Draws state boundary polygon on map
- Automatically fits map bounds to show entire state
- Adjusts padding based on left panel state (open/closed)

---

### 4. Show Retail Asset Clusters for State
**Trigger:** `onStateSelected()` - Line 2814-2825  
**Service Method:** `RetailAssetsClusterService.showClustersForState()`  
**API Call:** ❌ **NO API CALL** - Uses preloaded data only  
**Purpose:** Displays retail asset clusters on the map for the selected state by filtering preloaded data  
**Behavior:**
- Filters and displays assets from the cache loaded during initialization (`preloadIndiaAssets()`)
- If data not yet loaded, waits for the initialization API call to complete
- Replaces old city/village cluster markers with retail asset clusters

**Note:** This method does NOT make an API call. It only filters and displays the retail assets that were preloaded during dashboard initialization.

---

## Execution Flow Summary

### On Dashboard Load:
1. **Background:** Preload India retail assets (non-blocking)
2. **Parallel:** Load location aggregates for all states (multiple API calls)
3. **After Map Init:** Load India store cluster data for map markers

### On State Card Click:
All operations run **in parallel** (no coordination - all independent):

1. **Immediate:** Draw state boundary (API call)
2. **Immediate:** Load cities for state (API call)
3. **Immediate:** Load villages for state (API call)
4. **Immediate:** Show retail asset clusters (NO API call - filters preloaded data)

---

## API Endpoints Reference

### Base URL
All endpoints use the base URL from `environment.apiUrl`

### Endpoints Used

| Endpoint | Method | Purpose | Returns ZIP? |
|----------|--------|---------|--------------|
| `/location-aggregate/v1/location-aggregates` | POST | Get location statistics | No |
| `/store/v1/store-cluster` | POST | Get store cluster data | Yes |
| `/admin-boundry/v1/polygon/boundary` | POST | Get polygon boundaries | Yes |
| `/store-list/v1/retail-assets` | POST | Get retail assets | Yes |

### Authentication
All API calls require `JTOKEN` header (automatically added by HTTP interceptor)

### Encryption
All endpoints (except those in `SKIP_ENCRYPTION_URLS`) are automatically encrypted/decrypted by the HTTP interceptor when `httpEnableEncryption` is enabled.

---

## Notes

1. **ZIP File Handling:** Endpoints marked as "Returns ZIP?" return ZIP files that are automatically extracted by the HTTP interceptor. The extracted JSON is then processed.

2. **Error Handling:** 
   - Missing file errors are handled gracefully
   - When `environment.useApiData` is `false`, navigation waits for API success
   - Failed API calls don't block other parallel operations

3. **Performance Optimizations:**
   - India retail assets are preloaded in background
   - State aggregates load in parallel
   - State card click operations run independently in parallel
   - Progressive UI updates as data arrives

4. **State Card Display:**
   - Shows skeleton data immediately
   - Updates progressively as location aggregates arrive
   - Store counts updated from cluster data when available

---

## Related Files

- **Component:** `src/app/components/dashboard/dashboard.component.ts`
- **API Service:** `src/app/services/api.service.ts`
- **Dashboard Service:** `src/app/services/dashboard.service.ts`
- **API Endpoints:** `src/app/constants/api-endpoints.constants.ts`
- **Environment Config:** `src/environments/environment.ts`

