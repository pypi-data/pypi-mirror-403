import d3 from "./d3loader.js";

export function clearPlotArea(id) {
  // Allow clearing all plot containers in one call
  if (!id) {
    const plotElements = document.querySelectorAll('[id^="plot-"]');
    Array.from(plotElements).forEach((el) => clearPlotArea(el.id));
    return;
  }

  // Remove any precedent SVG element
  d3.select("#" + id).selectAll("svg").remove();

  // Remove placeholder title
  d3.select("#" + id + " h5").remove();

  // Clean div element if previous error was shown
  d3.select("#" + id).text("").style("color", "black");
}

// Map between scale type and d3 scale function
export const scaleMap = {
  linear: () => d3.scaleLinear(),
  log: () => d3.scaleLog(),
  time: () => d3.scaleTime(), // Not implemented yet
  ordinal: () => d3.scaleOrdinal(), // Not implemented yet
  band: () => d3.scaleBand(), // Not implemented yet
  point: () => d3.scalePoint(), // Not implemented yet
};

export function getMin(data, key, errKey, scaleType) {
  if (scaleType === "log") {
    // Only consider values where (d[key] - d[errKey]) > 0
    return d3.min(
      data
        .map((d) => {
          if (d[errKey] !== undefined) {
            return d[key] < d[errKey] ? d[key] : d[key] - d[errKey];
          }
          return d[key];
        })
        .filter((v) => v > 0)
    );
  }
  return d3.min(data, (d) =>
    d[errKey] !== undefined ? d[key] - d[errKey] : d[key]
  );
}

export function getMax(data, key, errKey) {
  return d3.max(data, (d) =>
    d[errKey] !== undefined ? d[key] + d[errKey] : d[key]
  );
}

export function checkLogScale(type, arr, domain, axisName) {
  if (type === "log") {
    if (arr.some((v) => v <= 0)) {
      throw new Error(`Log scale requires all ${axisName} values > 0`);
    }
    if (domain && domain[0] <= 0) {
      throw new Error(`Log scale requires ${axisName} axis minimum domain > 0`);
    }
  }
}

export function checkTimeScale(type, arr, axisName) {
  if (
    type === "time" &&
    arr.some((v) => !(v instanceof Date || typeof v === "number"))
  ) {
    throw new Error(
      `Time scale requires ${axisName} values to be Date objects or timestamps`
    );
  }
}

export function setScales(data, metadata, width, height) {
  // If plotConfiguration.x or y are undefined, it assumes linear by default
  const plotConfig = metadata.plotConfiguration || {};
  const xConfig = plotConfig.x || {};
  const yConfig = plotConfig.y || {};
  const xScaleType = xConfig.scale || "linear";
  const yScaleType = yConfig.scale || "linear";
  const xDomain = xConfig.domain;
  const yDomain = yConfig.domain;

  checkLogScale(
    xScaleType,
    data.map((d) => d.x),
    xDomain,
    "x"
  );
  checkLogScale(
    yScaleType,
    data.map((d) => d.y),
    yDomain,
    "y"
  );
  checkTimeScale(
    xScaleType,
    data.map((d) => d.x),
    "x"
  );
  checkTimeScale(
    yScaleType,
    data.map((d) => d.y),
    "y"
  );

  const x = scaleMap[xScaleType]
    ? scaleMap[xScaleType]().range([0, width])
    : d3.scaleLinear().range([0, width]);
  const y = scaleMap[yScaleType]
    ? scaleMap[yScaleType]().range([height, 0])
    : d3.scaleLinear().range([height, 0]);

  // Determine Min and Max for quantitative axes
  function setDomain(scaleType, domain, dataArr, key, errKey, scaleObj) {
    // Get distinct values for ordinal/band/point
    const getDistinct = (arr) => Array.from(new Set(arr));

    if (["linear", "log", "time"].includes(scaleType)) {
      const min = domain ? domain[0] : getMin(dataArr, key, errKey, scaleType);
      const max = domain ? domain[1] : getMax(dataArr, key, errKey);
      scaleObj.domain([min, max]);
    } else if (["ordinal", "point", "band"].includes(scaleType)) {
      scaleObj.domain(getDistinct(dataArr.map((d) => d[key])));
    }
  }

  setDomain(xScaleType, xDomain, data, "x", "xerr", x);
  setDomain(yScaleType, yDomain, data, "y", "yerr", y);

  return { x, y };
}
