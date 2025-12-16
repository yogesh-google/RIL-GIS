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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import asyncio
from typing import Dict, Any, Optional

# ADK Imports
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.planners import BuiltInPlanner
from google.genai import types
from dotenv import load_dotenv

# App Imports
from app.tools import (
    formulate_location_aggregate,
    formulate_store_cluster,
    formulate_retail_assets,
    formulate_asset_list,
    formulate_asset_search,
    formulate_hex_analysis,
    formulate_polygon_boundary,
    formulate_logout
)

# Load env vars
load_dotenv()

# --- Configuration ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

if not GOOGLE_API_KEY and not GOOGLE_CLOUD_PROJECT:
    print("WARNING: Neither GOOGLE_API_KEY nor GOOGLE_CLOUD_PROJECT is set. Agent execution will likely fail.")

# Application Setup
app = FastAPI(title="RetailVista Agent Service")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "running", "service": "RetailVista Agent API", "version": "1.0.0"}

# --- Agent Configuration ---
MODEL_NAME = "gemini-3-pro-preview" # Supports Thinking Config
APP_NAME = "retailvista_prod"
USER_ID = "prod_user"

# Initialize Session Service
session_service = InMemorySessionService()

# Create Agent
agent = LlmAgent(
    model=MODEL_NAME,
    name="retailvista_agent",
    description="A helper agent for RetailVista that translates user queries into JSON commands.",
    instruction="""
    You are an intelligent router for the RetailVista dashboard.
    Your goal is to translate user natural language queries into specific JSON commands using the provided tools.
    
    Rules for Intent Classification:
    
    1. **Scenario 1: India View (Home/Reset)**
       - triggers: "Show India", "Reset view", "Back to country", "Show stats for India"
       - tool: `formulate_location_aggregate(location_type='INDIA')`
    
    2. **Scenario 2: State View (Drill Down)**
       - triggers: "Show Maharashtra", "Map of Gujarat", "Show stores in MH", "Show clusters in Karnataka", "Retail assets in Delhi"
       - tool: `formulate_retail_assets(location_type='STATE', location_id='MH')`
       - NOTE: Use `formulate_retail_assets` as the default for ANY state-level map request.
    
    3. **Specific Aggregates (State Stats)**
       - triggers: "Show only stats for MH", "Demographics of Gujarat" (without map)
       - tool: `formulate_location_aggregate(location_type='STATE', location_id='MH')`
    
    4. **Asset Search (Component)**
       - triggers: "Find Reliance Digital", "Where is store 001?", "Search for Fresh"
       - tool: `formulate_asset_search`
    
    5. **Hex Analysis (Layer)**
       - triggers: "Analyze hex data for Mumbai", "Hexagon view"
       - tool: `formulate_hex_analysis`
    
    6. **Boundaries (Layer)**
       - triggers: "Show boundary of Mumbai", "Polygon for Pune"
       - tool: `formulate_polygon_boundary`
    
    7. **Logout (Auth)**
       - triggers: "Log me out", "Sign out"
       - tool: `formulate_logout`

    **CRITICAL EXECUTION RULES**:
    1.  **ALWAYS** call the appropriate tool.
    2.  The tool will return a valid JSON string.
    3.  **YOU MUST COPY-PASTE THAT EXACT JSON STRING AS YOUR FINAL RESPONSE.**
    4.  **DO NOT** summarize what you did. **DO NOT** say "Here is the JSON".
    5.  **Output ONLY the JSON.**
    """,
    tools=[
        formulate_location_aggregate,
        formulate_store_cluster,
        formulate_retail_assets,
        formulate_asset_list,
        formulate_asset_search,
        formulate_hex_analysis,
        formulate_polygon_boundary,
        formulate_logout
    ],
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=1024,
        )
    ) 
)

# Create Runner
runner = Runner(
    agent=agent,
    app_name=APP_NAME,
    session_service=session_service
)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "session_1"
    user_id: Optional[str] = "prod_user"

@app.post("/chat")
async def chat(request: ChatRequest):
    # Use provided session/user ID or defaults
    current_session_id = request.session_id
    current_user_id = request.user_id
    
    # Ensure session exists
    try:
        await session_service.create_session(app_name=APP_NAME, user_id=current_user_id, session_id=current_session_id)
    except Exception:
        pass 

    user_msg = types.Content(role="user", parts=[types.Part(text=request.message)])
    
    final_text = ""
    reasoning_text = ""
    
    try:
        async for event in runner.run_async(user_id=current_user_id, session_id=current_session_id, new_message=user_msg):
            # Capture thoughts/reasoning if available
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'thought') and part.thought and isinstance(part.thought, str):
                        reasoning_text += part.thought
                    
                    try:
                        if part.text:
                            final_text += part.text
                    except Exception:
                        pass
        
        # JSON Extraction
        try:
             json_str = ""
             json_start = final_text.find('{')
             json_end = final_text.rfind('}') + 1
             
             if json_start != -1 and json_end != 0:
                 json_str = final_text[json_start:json_end]
                 if not reasoning_text:
                     reasoning_text = final_text[:json_start].strip()
                     reasoning_text = reasoning_text.replace("```json", "").replace("```", "").strip()
             else:
                 json_str = final_text.replace("```json", "").replace("```", "").strip()

             command_json = json.loads(json_str)
             
             return {
                 "reasoning": reasoning_text if reasoning_text else "No reasoning provided.",
                 "command": command_json
             }
        except json.JSONDecodeError as decode_err:
             print(f"JSON Parse Error: {decode_err}")
             return {
                 "reasoning": reasoning_text,
                 "command": {
                     "action": "UNKNOWN",
                     "message": final_text,
                     "error": "The agent did not return a valid JSON command."
                 }
             }

    except Exception as e:
        print(f"Error executing agent: {e}")
        return {
            "reasoning": "Error occurred.",
            "command": {
                "action": "ERROR",
                "message": str(e)
            }
        }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
