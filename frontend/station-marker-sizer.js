(function (global) {
  var DEFAULT_CONFIG = {
    layerId: "stations-circle",
    zoomStops: [
      { zoom: 8, radius: 2.2, minRadius: 1.8, maxRadius: 3.2 },
      { zoom: 10, radius: 3.2, minRadius: 2.0, maxRadius: 4.6 },
      { zoom: 12, radius: 4.8, minRadius: 2.7, maxRadius: 6.8 },
      { zoom: 14, radius: 6.4, minRadius: 3.3, maxRadius: 8.8 }
    ],
    targetDensityPer100kPixels: 12,
    minDensityMultiplier: 0.62,
    maxDensityMultiplier: 1.45,
    strokeWidthRatio: 0.24,
    minStrokeWidth: 0.8,
    maxStrokeWidth: 1.6
  };

  /**
   * Create a small controller that keeps station markers balanced against the
   * current zoom level and the number of stations visible in the viewport.
   */
  function createStationMarkerSizer(map, options) {
    var config = buildConfig(options);
    var stations = [];
    var pendingFrame = 0;
    var lastRadius = null;
    var lastStrokeWidth = null;

    map.on("move", scheduleRefresh);
    map.on("resize", scheduleRefresh);

    return {
      refresh: scheduleRefresh,
      setStations: setStations
    };

    function setStations(nextStations) {
      stations = Array.isArray(nextStations) ? nextStations.slice() : [];
      scheduleRefresh();
    }

    function scheduleRefresh() {
      if (pendingFrame || !map.getLayer(config.layerId)) {
        return;
      }

      pendingFrame = global.requestAnimationFrame(function () {
        pendingFrame = 0;
        applyMarkerStyle();
      });
    }

    function applyMarkerStyle() {
      var markerStyle = computeMarkerStyle(map, stations, config);
      if (!markerStyle) {
        return;
      }

      if (lastRadius !== markerStyle.radius) {
        map.setPaintProperty(config.layerId, "circle-radius", markerStyle.radius);
        lastRadius = markerStyle.radius;
      }

      if (lastStrokeWidth !== markerStyle.strokeWidth) {
        map.setPaintProperty(config.layerId, "circle-stroke-width", markerStyle.strokeWidth);
        lastStrokeWidth = markerStyle.strokeWidth;
      }
    }
  }

  /**
   * Convert the current viewport into a radius and stroke width that preserve
   * legibility without overwhelming the basemap in dense areas.
   */
  function computeMarkerStyle(map, stations, config) {
    var container = map.getContainer();
    var viewportArea = Math.max(container.clientWidth * container.clientHeight, 1);
    var baseStyle = interpolateZoomStyle(map.getZoom(), config.zoomStops);
    var visibleStations = countVisibleStations(stations, map.getBounds());
    var densityPer100kPixels = visibleStations / (viewportArea / 100000);
    var densityMultiplier = clamp(
      Math.sqrt(config.targetDensityPer100kPixels / Math.max(densityPer100kPixels, 1)),
      config.minDensityMultiplier,
      config.maxDensityMultiplier
    );
    var radius = roundToTenth(
      clamp(
        baseStyle.radius * densityMultiplier,
        baseStyle.minRadius,
        baseStyle.maxRadius
      )
    );

    return {
      radius: radius,
      strokeWidth: roundToTenth(
        clamp(
          radius * config.strokeWidthRatio,
          config.minStrokeWidth,
          config.maxStrokeWidth
        )
      )
    };
  }

  /** Count stations that sit within the current map viewport bounds. */
  function countVisibleStations(stations, bounds) {
    if (!bounds || !stations || stations.length === 0) {
      return 0;
    }

    var south = bounds.getSouth();
    var north = bounds.getNorth();
    var west = bounds.getWest();
    var east = bounds.getEast();

    return stations.reduce(function (visibleCount, station) {
      if (!station) {
        return visibleCount;
      }

      var isWithinLatitude = station.lat >= south && station.lat <= north;
      var isWithinLongitude = isLongitudeWithinBounds(station.lon, west, east);
      return isWithinLatitude && isWithinLongitude ? visibleCount + 1 : visibleCount;
    }, 0);
  }

  function isLongitudeWithinBounds(longitude, west, east) {
    if (west <= east) {
      return longitude >= west && longitude <= east;
    }

    return longitude >= west || longitude <= east;
  }

  function interpolateZoomStyle(zoom, zoomStops) {
    if (zoom <= zoomStops[0].zoom) {
      return zoomStops[0];
    }

    for (var index = 1; index < zoomStops.length; index += 1) {
      var nextStop = zoomStops[index];
      if (zoom <= nextStop.zoom) {
        var previousStop = zoomStops[index - 1];
        var progress = (zoom - previousStop.zoom) / (nextStop.zoom - previousStop.zoom);
        return {
          radius: interpolate(previousStop.radius, nextStop.radius, progress),
          minRadius: interpolate(previousStop.minRadius, nextStop.minRadius, progress),
          maxRadius: interpolate(previousStop.maxRadius, nextStop.maxRadius, progress)
        };
      }
    }

    return zoomStops[zoomStops.length - 1];
  }

  function buildConfig(options) {
    return {
      layerId: options && options.layerId ? options.layerId : DEFAULT_CONFIG.layerId,
      zoomStops: DEFAULT_CONFIG.zoomStops.map(function (stop) {
        return {
          zoom: stop.zoom,
          radius: stop.radius,
          minRadius: stop.minRadius,
          maxRadius: stop.maxRadius
        };
      }),
      targetDensityPer100kPixels: DEFAULT_CONFIG.targetDensityPer100kPixels,
      minDensityMultiplier: DEFAULT_CONFIG.minDensityMultiplier,
      maxDensityMultiplier: DEFAULT_CONFIG.maxDensityMultiplier,
      strokeWidthRatio: DEFAULT_CONFIG.strokeWidthRatio,
      minStrokeWidth: DEFAULT_CONFIG.minStrokeWidth,
      maxStrokeWidth: DEFAULT_CONFIG.maxStrokeWidth
    };
  }

  function interpolate(start, end, progress) {
    return start + (end - start) * progress;
  }

  function clamp(value, minimum, maximum) {
    return Math.min(Math.max(value, minimum), maximum);
  }

  function roundToTenth(value) {
    return Math.round(value * 10) / 10;
  }

  global.TubeStationMarkerSizer = {
    createStationMarkerSizer: createStationMarkerSizer
  };
})(window);
