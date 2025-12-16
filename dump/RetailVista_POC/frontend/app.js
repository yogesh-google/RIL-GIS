var app = angular.module('retailVistaApp', []);

app.controller('ChatController', ['$scope', '$http', '$timeout', '$sce', 'ActionService', function ($scope, $http, $timeout, $sce, ActionService) {
  $scope.messages = [];
  $scope.userInput = "";
  $scope.processing = false;
  $scope.dashboardData = null; // Data for the right pane

  // Welcome
  $scope.messages.push({
    sender: 'bot',
    text: $sce.trustAsHtml('Hello! I can help you analyze location data. Try asking:<br><em>"Show India stats"</em> or <em>"Show map of Maharashtra"</em>.'),
    isHtml: true
  });

  $scope.sendMessage = function () {
    if (!$scope.userInput.trim()) return;

    var userText = $scope.userInput;
    $scope.messages.push({ sender: 'user', text: userText });
    $scope.userInput = "";
    $scope.processing = true;

    // 1. Call Agent
    $http.post('http://localhost:8000/chat', { message: userText })
      .then(function (response) {
        var data = response.data;

        // Add Agent Entry with Reasoning (Friendly text added later)
        var msgIndex = $scope.messages.push({
          sender: 'bot',
          type: 'agent-response',
          reasoning: data.reasoning,
          command: data.command,
          friendlyText: "Executing command..."
        }) - 1;

        if (data.command && data.command.action && data.command.action !== 'UNKNOWN') {
          // 2. Execute Command
          ActionService.execute(data.command).then(function (result) {
            // Success: Update UI
            $scope.messages[msgIndex].friendlyText = result.friendlyMessage;
            $scope.dashboardData = result.visualData;
          }, function (errMsg) {
            $scope.messages[msgIndex].friendlyText = "Error: " + errMsg;
          });
        } else if (data.command && data.command.action === 'UNKNOWN') {
          $scope.messages[msgIndex].friendlyText = data.command.message;
        }
      })
      .catch(function (err) {
        $scope.messages.push({ sender: 'bot', text: 'Connection Error: ' + (err.data ? err.data.message : 'Unknown') });
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

app.service('ActionService', ['$http', '$q', '$sce', function ($http, $q, $sce) {
  var BACKEND_URL = "http://localhost:8001";

  this.execute = function (command) {
    var deferred = $q.defer();
    var endpoint = "";
    var isZip = false;

    // --- 1. Map Action to Endpoint ---
    switch (command.action) {
      case 'CALL_LOCATION_AGGREGATE': endpoint = "/location-aggregate/v1/location-aggregates"; break;
      case 'CALL_STORE_CLUSTER': endpoint = "/store/v1/store-cluster"; isZip = true; break;
      case 'CALL_RETAIL_ASSETS': endpoint = "/store-list/v1/retail-assets"; isZip = true; break;
      case 'CALL_ASSET_LIST': endpoint = "/store/v1/assets-list"; break;
      case 'CALL_ASSET_SEARCH': endpoint = "/store-search/v1/asset-search"; break;
      case 'CALL_HEX_ANALYSIS': endpoint = "/hex-analysis/v1/state-city-hex-analysis"; isZip = true; break;
      case 'CALL_POLYGON_BOUNDARY': endpoint = "/admin-boundry/v1/polygon/boundary"; isZip = true; break;
      case 'CALL_LOGOUT': endpoint = "/auth/v1/auth/logout"; break;
      default: deferred.reject("Unknown Action"); return deferred.promise;
    }

    // --- 2. Call Backend ---
    $http.post(BACKEND_URL + endpoint, command.payload).then(function (response) {
      var resData = response.data;
      if (resData.code != "200") { deferred.reject(resData.message); return; }

      // --- 3. Process Data (Zip or JSON) ---
      if (isZip) {
        handleZip(resData.data).then(function (jsonData) {
          processVisuals(command.action, jsonData, deferred, $sce, command.payload);
        }, deferred.reject);
      } else {
        processVisuals(command.action, resData.data, deferred, $sce, command.payload);
      }
    }).catch(function () { deferred.reject("API Request Failed"); });

    return deferred.promise;
  };

  // --- Helper: Generate Visuals & Text ---
  function processVisuals(action, data, deferred, $sce, payload) {
    var result = { friendlyMessage: "", visualData: null };

    var actionName = action;
    var payloadStr = JSON.stringify(payload);
    var scenarioText = "";

    // --- Scenario Mapping ---
    if (action === 'CALL_LOCATION_AGGREGATE' && payload.locationType === 'INDIA') {
      scenarioText = "Scenario 1: Dashboard Load (ngOnInit)";
    } else if (action === 'CALL_RETAIL_ASSETS' && payload.locationType === 'STATE') {
      scenarioText = "Scenario 2: State Selection (onStateSelected)";
    } else if (action === 'CALL_STORE_CLUSTER' && payload.locationType === 'STATE') {
      scenarioText = "Scenario 2: State Selection (onStateSelected)";
    } else {
      scenarioText = "Component Trigger: " + action;
    }

    // Dynamic Friendly Message
    result.friendlyMessage = "Triggering " + scenarioText + " | Payload: " + payloadStr;

    if (action === 'CALL_LOCATION_AGGREGATE') {
      result.visualData = {
        type: 'STATS',
        stats: {
          'Population': data.demographics ? data.demographics.population : 'N/A',
          'Households': data.demographics ? data.demographics.households : 'N/A',
          'Stores': data.storeNetwork ? data.storeNetwork.count : 'N/A'
        }
      };
    }
    else if (action === 'CALL_RETAIL_ASSETS' || action === 'CALL_STORE_CLUSTER') {
      var count = (data.stores || data.clusterData || []).length;
      var loc = payload.locationId || "the area";

      // Update message for clarity on map plot
      result.friendlyMessage += " (Plotting " + count + " points for " + loc + ")";

      // Generate Mock Points for Visualizer
      var points = (data.stores || data.clusterData || []).map(function (s, i) {
        // Mock generic coordinates for the visualizer box (0-100%)
        // In a real app we'd map lat/lon to canvas pixels.
        // Randomize slightly for demo effect if lat/lon static
        return { x: (Math.abs(s.lon) % 1 * 100), y: (Math.abs(s.lat) % 1 * 100), name: s.storeName || s.name };
      });

      result.visualData = {
        type: 'MAP',
        title: 'Map View: ' + loc,
        points: points
      };
    }
    else {
      result.visualData = {
        type: 'JSON',
        content: $sce.trustAsHtml("<pre>" + JSON.stringify(data, null, 2) + "</pre>")
      };
    }

    deferred.resolve(result);
  }

  function handleZip(base64Data) {
    var deferred = $q.defer();
    var zip = new JSZip();
    zip.loadAsync(base64Data, { base64: true }).then(function (zipContent) {
      var fileNames = Object.keys(zipContent.files);
      var targetFile = fileNames.find(function (n) { return n.endsWith(".json") || n.endsWith(".geojson"); });
      if (targetFile) {
        zipContent.files[targetFile].async("string").then(function (c) { deferred.resolve(JSON.parse(c)); });
      } else { deferred.reject("No Data in Zip"); }
    }).catch(function (e) { deferred.reject("Zip Error"); });
    return deferred.promise;
  }
}]);
