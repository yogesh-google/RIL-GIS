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

# Load env vars
load_dotenv()

app = FastAPI(title="RetailVista Agent Server")

# --- Configuration ---
# You must set these environment variables!
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

if not GOOGLE_API_KEY and not GOOGLE_CLOUD_PROJECT:
    print("WARNING: Neither GOOGLE_API_KEY nor GOOGLE_CLOUD_PROJECT is set. Agent execution will likely fail.")


app = FastAPI(title="RetailVista Agent Server")

# Enable CORS (Critical Fix)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Tools ---
from tools import (
    formulate_location_aggregate,
    formulate_store_cluster,
    formulate_retail_assets,
    formulate_asset_list,
    formulate_asset_search,
    formulate_hex_analysis,
    formulate_polygon_boundary,
    formulate_logout
)

# --- Agent Configuration ---

MODEL_NAME = "gemini-3-pro-preview" 
APP_NAME = "retailvista_poc"
USER_ID = "poc_user"

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
    
    1. **Aggregates/Stats**: "Show stats for India", "Demographics of Maharashtra"
       -> `formulate_location_aggregate`
    
    2. **Store Clusters**: "Show clusters in Maharashtra", "Cluster map of Gujarat"
       -> `formulate_store_cluster`
    
    3. **Retail Assets (All)**: "Show all stores in Mumbai", "Retail assets in MH", "Map of stores"
       -> `formulate_retail_assets`
    
    4. **Asset List (Simple)**: "List assets in Pune", "Show list of stores"
       -> `formulate_asset_list`
    
    5. **Search**: "Find Reliance Digital", "Search for Fresh stores", "Where is store 001?"
       -> `formulate_asset_search`
    
    6. **Hex Analysis**: "Analyze hex data for Mumbai", "Hexagon view of Pune"
       -> `formulate_hex_analysis`
    
    7. **Boundaries**: "Show boundary of Mumbai", "Polygon for Pune"
       -> `formulate_polygon_boundary`
    
    8. **Logout**: "Log me out", "Sign out"
       -> `formulate_logout`

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

@app.post("/chat")
async def chat(request: ChatRequest):
    session_id = "session_1" # TODO: In production app, generate/manage this
    
    try:
        await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)
    except Exception:
        pass # Session might already exist

    user_msg = types.Content(role="user", parts=[types.Part(text=request.message)])
    
    print(f"DEBUG: Processing message: {request.message}")
    final_text = ""
    reasoning_text = ""
    
    try:
        async for event in runner.run_async(user_id=USER_ID, session_id=session_id, new_message=user_msg):
            # Capture thoughts/reasoning if available
            if event.content and event.content.parts:
                for part in event.content.parts:
                    # Check for 'thought' attribute (Gemini 2.0 Flash Thinking)
                    if hasattr(part, 'thought') and part.thought and isinstance(part.thought, str):
                        reasoning_text += part.thought
                    
                    # Fallback or additional text
                    try:
                        # part.text might fail if it's a function call part sometimes
                        if part.text:
                            final_text += part.text
                    except Exception:
                        # Ignore parts that don't have text (like function calls)
                        pass
        
        print(f"DEBUG: Agent raw output: {final_text}")
        print(f"DEBUG: Agent reasoning: {reasoning_text}")

        # Improved JSON Extraction for mixed output (Text + JSON)
                # Improved JSON Extraction for mixed output (Text + JSON)
        try:
             json_str = ""
             # Strategy 1: Look for the specific "action" key to find the start of our command
             action_marker = '"action":'
             action_index = final_text.find(action_marker)
             
             if action_index != -1:
                 # Find thebrace before "action"
                 json_start = final_text.rfind('{', 0, action_index)
                 if json_start != -1:
                     # Now find the matching closing brace (basic counter or just rfind '}')
                     # Simple heuristics: extract from here to the end and try to parse
                     candidate = final_text[json_start:].strip()
                     
                     # Clean up any trailing chars like "}" or "```" if extra
                     # Finding the last '}'
                     json_end = candidate.rfind('}')
                     if json_end != -1:
                         json_str = candidate[:json_end+1]
                         
                     if not reasoning_text:
                         reasoning_text = final_text[:json_start].strip()
            
             # Strategy 2: Fallback to finding outermost brackets if Strategy 1 failed
             if not json_str:
                 json_start = final_text.find('{')
                 json_end = final_text.rfind('}') + 1
                 if json_start != -1 and json_end != 0:
                     json_str = final_text[json_start:json_end]
                     if not reasoning_text:
                        reasoning_text = final_text[:json_start].strip()

             # Cleanup Markdown
             json_str = json_str.replace("```json", "").replace("```", "").strip()
             
             command_json = json.loads(json_str)
             
             # Unpack if wrapped in "result" or "data" (common model behavior)
             if "result" in command_json and isinstance(command_json["result"], str):
                 try:
                    command_json = json.loads(command_json["result"])
                 except:
                    pass # Maybe result is just the object?

             return {
                 "reasoning": reasoning_text if reasoning_text else "No reasoning provided.",
                 "command": command_json
             }
        except Exception as decode_err:
             print(f"DEBUG: JSON Parse Error: {decode_err} | Text: {final_text}")
             return {
                 "reasoning": reasoning_text if reasoning_text else final_text, # Return full text as reasoning if parse fails
                 "command": {
                     "action": "UNKNOWN",
                     "message": final_text,
                     "error": "The agent behavior was unexpected. See reasoning."
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
