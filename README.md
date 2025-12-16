# RetailVista Assistant - Release Package

This package contains the production-ready components for the RetailVista Chatbot Assistant.

## Architecture: "Agent as a Bridge"

The system follows a bridge pattern where the Agent interprets user intent and creates UI Events, which the Frontend then consumes to drive the application state.

### Components

1.  **Agent Service** (`agent_service/`)
    *   **Tech**: Python, FastAPI, Google ADK, Gemini 3.0 Thinking.
    *   **Role**: Accepts Natural Language -> Returns JSON "UI Events".
    *   **Deployment**: Docker-ready.
    *   **Testing**: Includes `test_client.py` for easy CLI testing without Postman.

2.  **Frontend Client** (`frontend_client/`)
    *   **Tech**: AngularJS (v1.x) Reference Implementation.
    *   **Role**: Consumes the "UI Events" from the Agent and executes them.
    *   **Integration**: The `ActionService` class maps Events to App Logic.

---

## 🚀 Deployment Guide

### Option A: Docker (Recommended)

1.  **Build Image**:
    ```bash
    cd agent_service
    docker build -t retailvista-agent .
    ```

2.  **Run Container**:
    ```bash
    docker run -d -p 8000:8000 \
      -e GOOGLE_API_KEY="your_key" \
      -e GOOGLE_CLOUD_PROJECT="your_project" \
      retailvista-agent
    ```

### Option B: Local Python Execution

1.  **Install Dependencies**: `cd agent_service && pip install -r requirements.txt`
2.  **Configure**: Create `.env` from `.env.example`.
3.  **Run**: `python -m app.main`

---

## 🧪 Testing the API

You can test the running Agent using our included helper script or standard tools.

### Option 1: Python Helper (Easiest)
We include a script that formats the request and pretty-prints the JSON response.
```bash
cd agent_service
python test_client.py "Show stores in Maharashtra"
```

### Option 2: cURL
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Show India stores"}'
```

---

## 📡 API Reference for Release

Once deployed, the Agent exposes a single primary endpoint logic.

### **Endpoint**: `POST /chat`

**URL Format**:
- **Local**: `http://localhost:8000/chat`
- **Deployed (Example)**: `https://<YOUR-SERVER-IP-OR-DOMAIN>/chat`

**Request Body (JSON)**:
```json
{
  "message": "Show map of Maharashtra",
  "session_id": "analytics_session_123",  // Optional (For maintaining conversation context)
  "user_id": "alice_doe"                  // Optional (For user-specific logging)
}
```

**Response Body (JSON)**:
```json
{
  "reasoning": "**Interpretation**\nThe user wants...", // Thinking process (display in UI if desired)
  "command": {
    "action": "CALL_RETAIL_ASSETS",
    "payload": {
      "locationType": "STATE",
      "locationId": "MH"
    }
  }
}
```


---

## 🛠️ Frontend Integration Guide

This section explains how to integrate the Chatbot into your existing RetailVista Web Application.

### The "ActionService" Wrapper

You will implement an `ActionService` that maps Agent Commands to your existing **Component Flows** (Scenarios).

#### Mapping Actions to Component Scenarios

| Agent Action | Context | Frontend Trigger (The "Scenario") |
| :--- | :--- | :--- |
| `CALL_LOCATION_AGGREGATE` | `INDIA` | **Scenario 1: Dashboard Load**<br>Trigger `ngOnInit()` / `loadData()` logic to reset view to India. |
| `CALL_RETAIL_ASSETS` | `STATE` | **Scenario 2: State Selection**<br>Trigger `onStateSelected(stateObj)` to zoom and load state data. |
| `CALL_STORE_CLUSTER` | `STATE` | **Scenario 2: State Selection**<br>(Same as above) |

#### Implementation Example

```javascript
// frontend/services/action.service.js
app.service('ActionService', function(DashboardComponent) {
    
    this.consumeEvent = function(command) {
        switch(command.action) {
            
            // --- SCENARIO 2: STATE SELECTION ---
            case 'CALL_RETAIL_ASSETS': 
            case 'CALL_STORE_CLUSTER':
                if (command.payload.locationType === 'STATE') {
                    // Trigger the flow defined in 'onStateSelected'
                    DashboardComponent.onStateSelected({
                        id: command.payload.locationId
                    });
                }
                break;

            // --- SCENARIO 1: DASHBOARD LOAD (INDIA) ---
            case 'CALL_LOCATION_AGGREGATE':
                 if (command.payload.locationType === 'INDIA') {
                     // Trigger the flow defined in 'ngOnInit' / 'loadData'
                     DashboardComponent.ngOnInit(); 
                     // OR specific sub-methods if you don't want full reload:
                     // DashboardComponent.loadData();
                 }
                 break;

            // ... other cases (Search, Logout)
        }
    };
});
```

### Protocol for Response Capture
To integrate this into your Chat UI Component:

```javascript
// chat.component.ts
sendMessage(userText) {
    this.http.post(CONFIG.AGENT_URL + '/chat', { message: userText }).subscribe(response => {
        // 1. Show "Thinking" Bubble (Optional)
        if (response.reasoning) this.showReasoning(response.reasoning);
        
        // 2. Execute the Command
        if (response.command.action !== 'UNKNOWN') {
             this.actionService.consumeEvent(response.command); // <--- Delegation
        }
    });
}
```

---

## 📊 Event Schema Reference

| Agent Action | Payload | Expected Trigger |
| :--- | :--- | :--- |
| `CALL_LOCATION_AGGREGATE` (India) | `{ locationType: "INDIA" }` | `ngOnInit()` flow (Reset to Home) |
| `CALL_RETAIL_ASSETS` (State) | `{ locationType: "STATE", locationId: "MH" }` | `onStateSelected()` flow |
| `CALL_ASSET_SEARCH` | `{ searchString: "Reliance" }` | `SearchComponent.onSearch()` flow |
| `CALL_LOGOUT` | `{}` | `AuthComponent.logout()` flow |

---

## 🛡️ Production Considerations

Things to keep in mind before going live:

### 1. Security & Authentication
*   **CORS**: The current `main.py` allows ALL origins (`[*]`). In production, restrict this to your specific frontend domain.
    ```python
    allow_origins=["https://your-retailvista-app.com"]
    ```
*   **Endpoint Protection**: The `/chat` endpoint behaves like an internal microservice. It is recommended to put it behind your **API Gateway** (e.g., Nginx, Apigee) to handle authentication (OAuth/JWT) before the request reaches the Agent.

### 2. Maintenance (State Mapping)
*   The Agent uses a dictionary (`STATE_MAPPING` in `tools.py`) to convert "Maharashtra" -> "MH".
*   **Task**: Ensure this mapping is synced with your Master Data Management system. If you add new regions, update `tools.py`.

### 3. Error Handling
*   **Frontend Logic**: Ensure your UI handles this gracefully (e.g., "I didn't understand that. Try asking for 'India Stats'").

### 4. Session Management (In-Memory vs. Persistent)
*   **Current Setup**: The release uses `InMemorySessionService`. This stores conversation history in RAM.
    *   ⚠️ **Warning**: If you deploy multiple container instances (horizontal scaling), users might hit different servers and lose context. History is also lost on restart.
*   **Production Upgrade**: Switch to a persistent store like **Redis** or **Firestore**.
    *   *How*: Replace `InMemorySessionService` in `main.py` with `RedisSessionService` (available in Google ADK) or a custom implementation connected to your specific DB.
