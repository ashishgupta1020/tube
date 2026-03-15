(function () {
  var DEFAULT_CAMERA = {
    center: { lat: 51.5074, lon: -0.1278 },
    zoom: 10
  };
  var STATION_SOURCE_ID = "stations";
  var STATION_LAYER_ID = "stations-circle";
  var BASEMAP_STYLE_URL = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";
  var appState = {
    dataset: null,
    map: null,
    mapLoaded: false,
    pendingDataset: null,
    selectedStationId: null
  };

  var elements = {
    datasetStatus: document.getElementById("dataset-status"),
    generatedAt: document.getElementById("generated-at"),
    stationCount: document.getElementById("station-count"),
    selectionName: document.getElementById("selection-name"),
    selectionCopy: document.getElementById("selection-copy"),
    stateOverlay: document.getElementById("state-overlay"),
    stateKicker: document.getElementById("state-kicker"),
    stateTitle: document.getElementById("state-title"),
    stateCopy: document.getElementById("state-copy"),
    retryButton: document.getElementById("retry-button")
  };

  function init() {
    elements.retryButton.addEventListener("click", loadDataset);
    initMap();
    loadDataset();
  }

  function initMap() {
    var map = new maplibregl.Map({
      container: "map",
      style: BASEMAP_STYLE_URL,
      center: [DEFAULT_CAMERA.center.lon, DEFAULT_CAMERA.center.lat],
      zoom: DEFAULT_CAMERA.zoom,
      attributionControl: true,
      dragRotate: false,
      cooperativeGestures: true,
      doubleClickZoom: true,
      touchZoomRotate: false
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    map.on("load", function () {
      appState.mapLoaded = true;
      ensureStationLayer(map);
      if (appState.pendingDataset) {
        applyDatasetToMap(appState.pendingDataset);
        appState.pendingDataset = null;
      }
    });

    map.on("click", STATION_LAYER_ID, function (event) {
      var feature = event.features && event.features[0];
      if (!feature || !feature.properties) {
        return;
      }

      var station = {
        id: String(feature.properties.id || ""),
        name: String(feature.properties.name || "Unknown station"),
        modes: parseModes(feature.properties.modes)
      };

      appState.selectedStationId = station.id;
      renderSelection(station);
    });

    map.on("mouseenter", STATION_LAYER_ID, function () {
      map.getCanvas().style.cursor = "pointer";
    });

    map.on("mouseleave", STATION_LAYER_ID, function () {
      map.getCanvas().style.cursor = "";
    });

    appState.map = map;
  }

  function ensureStationLayer(map) {
    if (!map.getSource(STATION_SOURCE_ID)) {
      map.addSource(STATION_SOURCE_ID, {
        type: "geojson",
        data: emptyFeatureCollection()
      });
    }

    if (!map.getLayer(STATION_LAYER_ID)) {
      map.addLayer({
        id: STATION_LAYER_ID,
        type: "circle",
        source: STATION_SOURCE_ID,
        paint: {
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            8, 3.4,
            10, 4.8,
            12, 6.4
          ],
          "circle-color": "#132126",
          "circle-stroke-color": "#fff9ef",
          "circle-stroke-width": 1.3,
          "circle-opacity": 0.92
        }
      });
    }
  }

  async function loadDataset() {
    setOverlayState({
      visible: true,
      kicker: "Loading map",
      title: "Fetching station data from the backend.",
      copy: "The map will render as soon as the current dataset arrives.",
      showRetry: false
    });
    elements.datasetStatus.textContent = "Refreshing station dataset…";

    try {
      var response = await fetch("/api/map/stations", {
        headers: { Accept: "application/json" }
      });

      if (!response.ok) {
        throw new Error(await formatError(response));
      }

      var payload = await response.json();
      var dataset = validateAndMapResponse(payload);
      appState.dataset = dataset;
      appState.selectedStationId = null;
      renderDatasetMeta(dataset);

      if (appState.mapLoaded) {
        applyDatasetToMap(dataset);
      } else {
        appState.pendingDataset = dataset;
      }

      setOverlayState({ visible: false });
    } catch (error) {
      renderError(error);
    }
  }

  async function formatError(response) {
    try {
      var payload = await response.json();
      if (payload && payload.error) {
        return payload.error;
      }
    } catch (error) {
      return "Map data is temporarily unavailable.";
    }

    return "Map data is temporarily unavailable.";
  }

  function validateAndMapResponse(payload) {
    if (!payload || payload.version !== "v1") {
      throw new Error("Map response version was not supported.");
    }

    if (!payload.camera || !payload.camera.center || !payload.camera.maxBounds || !Array.isArray(payload.stations)) {
      throw new Error("Map response was missing required camera or station data.");
    }

    var stations = payload.stations.map(function (station) {
      if (
        !station ||
        typeof station.id !== "string" ||
        typeof station.name !== "string" ||
        !station.location ||
        typeof station.location.lat !== "number" ||
        typeof station.location.lon !== "number" ||
        !Array.isArray(station.modes)
      ) {
        throw new Error("Map response contained an invalid station record.");
      }

      return {
        id: station.id,
        name: station.name,
        lat: station.location.lat,
        lon: station.location.lon,
        modes: station.modes.slice()
      };
    });

    if (stations.length === 0) {
      throw new Error("Map response contained no stations.");
    }

    return {
      version: payload.version,
      generatedAt: String(payload.generatedAt || ""),
      camera: {
        center: {
          lat: numberOrThrow(payload.camera.center.lat, "camera center latitude"),
          lon: numberOrThrow(payload.camera.center.lon, "camera center longitude")
        },
        zoom: numberOrThrow(payload.camera.zoom, "camera zoom"),
        maxBounds: {
          southWest: {
            lat: numberOrThrow(payload.camera.maxBounds.southWest && payload.camera.maxBounds.southWest.lat, "south-west latitude"),
            lon: numberOrThrow(payload.camera.maxBounds.southWest && payload.camera.maxBounds.southWest.lon, "south-west longitude")
          },
          northEast: {
            lat: numberOrThrow(payload.camera.maxBounds.northEast && payload.camera.maxBounds.northEast.lat, "north-east latitude"),
            lon: numberOrThrow(payload.camera.maxBounds.northEast && payload.camera.maxBounds.northEast.lon, "north-east longitude")
          }
        }
      },
      stations: stations
    };
  }

  function numberOrThrow(value, label) {
    if (typeof value !== "number" || !isFinite(value)) {
      throw new Error("Map response field was invalid: " + label + ".");
    }
    return value;
  }

  function applyDatasetToMap(dataset) {
    var map = appState.map;
    if (!map) {
      return;
    }

    ensureStationLayer(map);

    var source = map.getSource(STATION_SOURCE_ID);
    if (!source) {
      throw new Error("Station layer source was not available.");
    }

    source.setData(toFeatureCollection(dataset.stations));
    map.setMaxBounds([
      [dataset.camera.maxBounds.southWest.lon, dataset.camera.maxBounds.southWest.lat],
      [dataset.camera.maxBounds.northEast.lon, dataset.camera.maxBounds.northEast.lat]
    ]);
    map.jumpTo({
      center: [dataset.camera.center.lon, dataset.camera.center.lat],
      zoom: dataset.camera.zoom
    });

    renderSelection(null);
  }

  function renderDatasetMeta(dataset) {
    var stationLabel = dataset.stations.length + " stations";
    elements.datasetStatus.textContent = stationLabel;
    elements.stationCount.textContent = stationLabel;
    elements.generatedAt.textContent = formatGeneratedAt(dataset.generatedAt);
  }

  function renderSelection(station) {
    if (!station) {
      elements.selectionName.textContent = "None";
      elements.selectionCopy.textContent = "Select a station to inspect its modes.";
      return;
    }

    elements.selectionName.textContent = station.name;
    elements.selectionCopy.textContent = humanizeModes(station.modes);
  }

  function renderError(error) {
    console.error(error);
    elements.datasetStatus.textContent = "Backend unavailable";
    elements.generatedAt.textContent = "No usable dataset";
    elements.stationCount.textContent = "Unavailable";
    renderSelection(null);
    setOverlayState({
      visible: true,
      kicker: "Map unavailable",
      title: "Station data could not be loaded right now.",
      copy: error && error.message ? error.message : "Map data is temporarily unavailable.",
      showRetry: true
    });
  }

  function setOverlayState(config) {
    if (!config.visible) {
      elements.stateOverlay.classList.add("is-hidden");
      elements.retryButton.hidden = true;
      return;
    }

    elements.stateOverlay.classList.remove("is-hidden");
    elements.stateKicker.textContent = config.kicker;
    elements.stateTitle.textContent = config.title;
    elements.stateCopy.textContent = config.copy;
    elements.retryButton.hidden = !config.showRetry;
  }

  function toFeatureCollection(stations) {
    return {
      type: "FeatureCollection",
      features: stations.map(function (station) {
        return {
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: [station.lon, station.lat]
          },
          properties: {
            id: station.id,
            name: station.name,
            modes: station.modes.join("|")
          }
        };
      })
    };
  }

  function emptyFeatureCollection() {
    return { type: "FeatureCollection", features: [] };
  }

  function parseModes(rawModes) {
    if (!rawModes) {
      return [];
    }

    return String(rawModes)
      .split("|")
      .filter(Boolean);
  }

  function humanizeModes(modes) {
    if (!modes || modes.length === 0) {
      return "No supported rail modes were attached to this station.";
    }

    return modes
      .map(function (mode) {
        if (mode === "elizabeth-line") {
          return "Elizabeth line";
        }
        if (mode === "dlr") {
          return "DLR";
        }
        if (mode === "overground") {
          return "London Overground";
        }
        if (mode === "tube") {
          return "Underground";
        }
        return mode;
      })
      .join(", ");
  }

  function formatGeneratedAt(rawTimestamp) {
    if (!rawTimestamp) {
      return "Timestamp unavailable";
    }

    var date = new Date(rawTimestamp);
    if (isNaN(date.getTime())) {
      return "Timestamp unavailable";
    }

    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short"
    }).format(date);
  }

  init();
})();
