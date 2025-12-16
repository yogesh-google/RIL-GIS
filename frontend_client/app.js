// Copyright 2025 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may not obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

var app = angular.module('retailVistaApp', []);

app.controller('ChatController', ['$scope', '$http', '$timeout', '$sce', 'ActionService', function ($scope, $http, $timeout, $sce, ActionService) {
    $scope.messages = [];
    $scope.userInput = "";
    $scope.processing = false;
    $scope.dashboardData = null;

    // Welcome
    $scope.messages.push({
        sender: 'bot',
        text: $sce.trustAsHtml('Hello! I am ready to translate your queries into UI Events.')
    });

    $scope.sendMessage = function () {
        if (!$scope.userInput.trim()) return;

        var userText = $scope.userInput;
        $scope.messages.push({ sender: 'user', text: userText });
        $scope.userInput = "";
        $scope.processing = true;

        // 1. Call Agent Service
        // Ideally these IDs come from your AuthService/UserSession
        var payload = {
            message: userText,
            session_id: "demo_session_" + Math.floor(Math.random() * 1000),
            user_id: "demo_user"
        };

        $http.post('http://localhost:8000/chat', payload)
            .then(function (response) {
                var data = response.data;

                var msgIndex = $scope.messages.push({
                    sender: 'bot',
                    type: 'agent-response',
                    reasoning: data.reasoning,
                    command: data.command,
                    friendlyText: "Processing Event..."
                }) - 1;

                if (data.command && data.command.action && data.command.action !== 'UNKNOWN') {
                    // 2. Consume Event (Bridge to Real App)
                    ActionService.consumeEvent(data.command).then(function (result) {
                        $scope.messages[msgIndex].friendlyText = result.friendlyMessage;
                        $scope.dashboardData = result.visualData;
                    }, function (errMsg) {
                        $scope.messages[msgIndex].friendlyText = "Event Error: " + errMsg;
                    });
                } else if (data.command && data.command.action === 'UNKNOWN') {
                    $scope.messages[msgIndex].friendlyText = data.command.message;
                }
            })
            .catch(function (err) {
                $scope.messages.push({ sender: 'bot', text: 'Agent Service Unreachable: ' + (err.data ? err.data.message : 'Unknown') });
            })
            .finally(function () {
                $scope.processing = false;
                $timeout(function () {
                    var chatDiv = document.getElementById("chatMessages");
                    if (chatDiv) chatDiv.scrollTop = chatDiv.scrollHeight;
                }, 0);
            });
    };
}]);

/**
 * ActionService - The Bridge
 * In Production, this Service maps the Agent's "Events" (JSON) to Real Application Logic.
 */
app.service('ActionService', ['$q', function ($q) {
    // NOTE: This Service is the BRIDGE.

    this.consumeEvent = function (command) {
        var deferred = $q.defer();
        var action = command.action;
        var payload = command.payload;

        console.log("%c[ActionService] Received Event:", "color: blue; font-weight: bold;", action, payload);

        // --- INTEGRATION PATTERN ---
        switch (action) {

            // SCENARIO 1: DASHBOARD LOAD (INDIA)
            case 'CALL_LOCATION_AGGREGATE':
                if (payload.locationType === 'INDIA') {
                    console.log("👉 TRIGGERING: DashboardComponent.ngOnInit()");
                    // REAL CODE: DashboardComponent.ngOnInit();
                } else {
                    console.log("👉 TRIGGERING: DashboardComponent.loadData() for " + payload.locationId);
                    // REAL CODE: DashboardComponent.loadData(payload);
                }
                break;

            // SCENARIO 2: STATE SELECTION
            case 'CALL_RETAIL_ASSETS':
            case 'CALL_STORE_CLUSTER':
                if (payload.locationType === 'STATE') {
                    console.log("👉 TRIGGERING: DashboardComponent.onStateSelected(" + payload.locationId + ")");
                    // REAL CODE: DashboardComponent.onStateSelected({ id: payload.locationId });
                }
                break;

            // SCENARIO 3: SEARCH
            case 'CALL_ASSET_SEARCH':
                console.log("👉 TRIGGERING: SearchComponent.onSearch(" + payload.searchString + ")");
                // REAL CODE: SearchComponent.onSearch(payload.searchString);
                break;

            // SCENARIO 4: AUTH
            case 'CALL_LOGOUT':
                console.log("👉 TRIGGERING: AuthComponent.logout()");
                // REAL CODE: AuthComponent.logout();
                break;

            // OTHER LAYERS
            case 'CALL_HEX_ANALYSIS':
                console.log("👉 TRIGGERING: MapComponent.showHexLayer(" + payload.locationId + ")");
                break;

            case 'CALL_POLYGON_BOUNDARY':
                console.log("👉 TRIGGERING: MapComponent.drawBoundary(" + payload.locationId + ")");
                break;

            default:
                console.warn("Unknown Action:", action);
        }

        // Simulate success for the chat UI
        deferred.resolve({
            friendlyMessage: "Triggered " + action + " for " + (payload.locationId || "India")
        });

        return deferred.promise;
    };
}]);

// Helper to simulate visuals (Optional, for demo purposes if needed)
function processVisuals() { return {}; }
