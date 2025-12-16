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

import requests
import json
import sys

# Configuration
API_URL = "http://localhost:8000/chat"

def test_chat(message):
    print(f"\n🚀 Sending Message: '{message}'")
    
    payload = {
        "message": message,
        "session_id": "test_cli_user",
        "user_id": "cli_tester"
    }

    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # Pretty Print Result
        print("-" * 50)
        print("🤖 REASONING:")
        print(data.get("reasoning", "N/A"))
        print("-" * 50)
        print("⚡ COMMAND:")
        print(json.dumps(data.get("command"), indent=2))
        print("-" * 50)
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server. Is it running on port 8000?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    msg = "Show map of Maharashtra"
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
    
    test_chat(msg)
