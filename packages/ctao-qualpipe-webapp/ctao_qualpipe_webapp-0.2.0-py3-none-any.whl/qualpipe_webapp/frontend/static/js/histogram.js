import d3 from "./d3loader.js";
import { plotCriteria } from "./criteriaPlot.js";
import { margin } from "./config.js";
import { clearPlotArea } from "./commonUtilities.js";

const COLORS = {
  DEFAULT_BAR: "#007bff",
  TOTAL_LABEL: "#333",
  OUTLIERS_LABEL: "#d9534f",
  AXIS_LABEL: "#000",
};

function getMetadataPlotConfiguration(metadata) {
  const barFill = metadata.plotConfiguration.marks?.fill || COLORS.DEFAULT_BAR;
  const barStroke = metadata.plotConfiguration.marks?.stroke || COLORS.DEFAULT_BAR;
  const barStrokeWidth = metadata.plotConfiguration.marks?.strokeWidth || 1;
  const barOpacity = metadata.plotConfiguration.marks?.opacity || 1;
  return {
    barFill,
    barStroke,
    barStrokeWidth,
    barOpacity,
  };
}

function negativeLogWarning(id) {
  console.warn(
    `Crop negative values to avoid issues with log scale representation in ${id}.`
  );
}

export function histogram1DPlot(id, dataKey) {
  const data = preprocessData(dataKey.fetchedData);
  const metadata = dataKey.fetchedMetadata;

  clearPlotArea(id);

  const { width, height, svg } = createSVGContainer(id);

  setTitle(svg, width, metadata);

  const { x, y, bins, yMin } = setScalesAndBins(
    data,
    metadata,
    width,
    height,
    svg,
    id
  );

  addClipPath(svg, id, width, height);

  drawBars({ svg, bins, x, y, id, metadata, height, yMin });

  // Draw criteria on top of the bars
  plotCriteria(svg, width, height, x, y, metadata, id);

  addXAxis(svg, x, height, width, metadata);
  addYAxis(svg, y, height, metadata);
}

// --- Helper Functions ---

function preprocessData(data) {
  // Histogram expects object with 'x' array
  if (data && typeof data === "object") {
    if (Array.isArray(data.values)) {
      return data.values.map((v) => ({ value: +v }));
    }
    if (Array.isArray(data.x)) {
      return data.x.map((v) => ({ value: +v }));
    }
  }
  return [];
}

function createSVGContainer(id) {
  const container = document.getElementById(id);
  const boundingRect = container.getBoundingClientRect();
  const width = boundingRect.width - margin.left - margin.right;
  const height = boundingRect.height - margin.top - margin.bottom;

  const svg = d3
    .select("#" + id)
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  return { width, height, svg };
}

function setTitle(svg, width, metadata) {
  svg
    .append("text")
    .attr("x", width / 2)
    .attr("y", -margin.top / 3)
    .attr("class", "histogram1d-title")
    .text(metadata.plotConfiguration.title || "Histogram1D");
}

function adjustMinForLog(min, minData, data, id, axis = 'x') {
  let adjustedMin = min;
  if (min <= 0) {
    console.warn(
      `Warning: ${axis}Min (${min}) <= 0 for log scale. Adjusting to positive minimum.`
    );
    if (data) {
      adjustedMin =
        d3.min(
          data.filter((d) => d.value > 0),
          (d) => d.value
        ) || Number.EPSILON;
    } else {
      adjustedMin = Math.max(0.1, Number.EPSILON);
    }
  }

  if (minData !== undefined && minData <= 0 && axis === 'x') {
    negativeLogWarning(id);
  }
  return adjustedMin;
}

function createScale(scaleType, domain, range) {
  return (scaleType === "log" ? d3.scaleLog() : d3.scaleLinear())
    .domain(domain)
    .range(range);
}

function generateThresholds(xScaleType, xSafeMin, xMax, numBins) {
  if (xScaleType === "log") {
    // Uniform logharitmic bins
    const logMin = Math.log10(xSafeMin);
    const logMax = Math.log10(xMax);
    return Array.from({ length: numBins + 1 }, (_, i) => {
      const logValue = logMin + (i * (logMax - logMin)) / numBins;
      return Math.pow(10, logValue);
    });
  } else {
    // Uniform linear bins
    const binWidth = (xMax - xSafeMin) / numBins;
    return Array.from(
      { length: numBins + 1 },
      (_, i) => xSafeMin + i * binWidth
    );
  }
}

function createCountLabel(svg, className, value, x, y, fill, textFn) {
  svg
    .selectAll(`.${className}`)
    .data([value])
    .join("text")
    .attr("class", className)
    .attr("x", x)
    .attr("y", y)
    .attr("text-anchor", "end")
    .attr("fill", fill)
    .attr("font-size", 16)
    .text(textFn);
}

function addCountLabels(svg, totalRendered, totalOutliers, width, id) {
  // Total count label
  createCountLabel(
    svg,
    "histogram1d-total",
    totalRendered,
    width - 8,
    -margin.top / 4 + 16,
    COLORS.TOTAL_LABEL,
    (d) => `Total: ${d}`
  );

  // Outliers count label (only show if > 0)
  if (totalOutliers > 0) {
    createCountLabel(
      svg,
      "histogram1d-outliers",
      totalOutliers,
      width + 10,
      -margin.top / 4 + 32,
      COLORS.OUTLIERS_LABEL,
      (d) => `Out of range: ${d}`
    );

    console.warn(
      `Found ${totalOutliers} outlier datapoints not rendered in the ${id}.`
    );
  } else {
    svg.selectAll(".histogram1d-outliers").remove();
  }
}

function setScalesAndBins(data, metadata, width, height, svg, id) {
  const xScaleType = metadata.plotConfiguration.x?.scale || "linear";
  const yScaleType = metadata.plotConfiguration.y?.scale || "linear";
  const xDomain = metadata.plotConfiguration.x?.domain;
  const yDomain = metadata.plotConfiguration.y?.domain;
  const numBins = metadata.plotConfiguration.bins || 20;

  const xMinData = d3.min(data, (d) => d.value);

  // X scale (value axis)
  let xMin = xDomain ? xDomain[0] : xMinData;
  const xMax = xDomain ? xDomain[1] : d3.max(data, (d) => d.value);

  // Count total data points
  const totalData = data.length;

  // Adapt xMin for logscale
  if (xScaleType === "log") {
    xMin = adjustMinForLog(xMin, xMinData, data, id, 'x');
  }

  const xSafeMin = xScaleType === "log" ? Math.max(xMin, Number.EPSILON) : xMin;

  const x = createScale(xScaleType, [xSafeMin, xMax], [0, width]);

  // Generate thresholds uniformly between xSafeMin and xMax
  const thresholds = generateThresholds(xScaleType, xSafeMin, xMax, numBins);

  const histogram = d3.bin().domain([xSafeMin, xMax]).thresholds(thresholds);

  const bins = histogram(data.map((d) => d.value));

  // Y scale (frequency/count axis)
  const yMax = yDomain ? yDomain[1] : d3.max(bins, (d) => d.length);
  let yMin = yDomain ? yDomain[0] : Number.EPSILON;

  // Adapt yMin for logscale
  if (yScaleType === "log") {
    yMin = adjustMinForLog(yMin, undefined, null, id, 'y');
  }

  const y = createScale(yScaleType, [yMin, yMax], [height, 0]);

  // Calculate rendered and outlier counts
  const totalRendered = bins.reduce((sum, b) => sum + b.length, 0);
  const totalOutliers = totalData - totalRendered;

  addCountLabels(svg, totalRendered, totalOutliers, width, id);

  return { x, y, bins, yMin };
}

function addClipPath(svg, id, width, height) {
  svg
    .append("clipPath")
    .attr("id", `clip-${id}`)
    .append("rect")
    .attr("x", 0)
    .attr("y", 0)
    .attr("width", width)
    .attr("height", height);
}

function drawBars({ svg, bins, x, y, id, metadata, height, yMin }) {
  const { barFill, barStroke, barStrokeWidth, barOpacity } =
    getMetadataPlotConfiguration(metadata);

  const barsGroup = svg.append("g").attr("clip-path", `url(#clip-${id})`);

  barsGroup
    .selectAll(".histogram1d-bar")
    .data(bins)
    .enter()
    .append("rect")
    .attr("class", "histogram1d-bar")
    .attr("x", (d) => x(d.x0))
    .attr("y", (d) => (d.length > 0 ? y(d.length) : height))
    .attr("width", (d) => Math.max(0, x(d.x1) - x(d.x0) - 1))
    .attr("height", (d) => (d.length > 0 ? y(yMin) - y(d.length) : 0))

    .attr("opacity", barOpacity)
    .attr(
      "style",
      [
        `fill: ${barFill};`,
        `stroke: ${barStroke};`,
        `stroke-width: ${barStrokeWidth}px;`,
        `} !important;`,
      ].join(" ")
    );
}

// === Tick helpers ===
function getExpScaleInfo(scale, scaleType) {
  if (!["linear", "log"].includes(scaleType)) return { use: false, k: 0 };
  const [d0, d1] = scale.domain();
  const absMax = d3.max([Math.abs(+d0 || 0), Math.abs(+d1 || 0)]);
  if (!absMax) return { use: false, k: 0 };
  const use = absMax >= 1e4 || absMax < 1e-3;
  const k = use ? Math.floor(Math.log10(absMax)) : 0;
  return { use, k };
}

function makeScaledTickFormat(k) {
  const fmt = d3.format("~g"); // no thousands separator
  const scale = Math.pow(10, k);
  return (d) => fmt(d / scale);
}

function addAxisExponentLabel(g, where, k, scale) {
  g.selectAll(".axis-exp").remove();

  const textElement = g
    .append("text")
    .attr("class", "axis-exp")
    .attr("text-anchor", "end")
    .attr("fill", COLORS.AXIS_LABEL)
    .attr("font-size", "16px");

  // Base text "×10" + superscript exponent
  textElement.append("tspan").text("×10");
  textElement
    .append("tspan")
    .attr("baseline-shift", "super")
    .attr("font-size", "12px")
    .text(k);

  // Position based on axis type
  const [x, y] = where === "x"
    ? [Array.isArray(scale.range()) ? scale.range()[1] : 0, Math.max(10, Math.floor(margin.bottom * 0.8))]
    : [0, -Math.max(10, Math.floor(margin.top * 0.4))];

  textElement.attr("x", x).attr("y", y);
}

function addAxis(svg, scale, metadata, axisType, height, width) {
  const metadataAxis = metadata.plotConfiguration[axisType] || {};
  const defaultLabel = axisType === 'x' ? 'Value' : 'None';
  let labelText = metadataAxis.label || defaultLabel;
  if (metadataAxis.unit) {
    labelText += ` [${metadataAxis.unit}]`;
  }

  const scaleType = metadata.plotConfiguration[axisType]?.scale || "linear";
  const { use, k } = getExpScaleInfo(scale, scaleType);

  const axisGenerator = axisType === 'x' ? d3.axisBottom(scale) : d3.axisLeft(scale);
  const fmt = use ? makeScaledTickFormat(k) : d3.format("~g");
  axisGenerator.tickFormat(fmt);

  const transform = axisType === 'x' ? `translate(0,${height})` : null;
  const g = svg.append("g");
  if (transform) g.attr("transform", transform);
  g.call(axisGenerator);

  // Increase tick font-size
  g.selectAll("text").attr("font-size", "16px");

  // Label ×10^k above the axis (if needed)
  if (use) addAxisExponentLabel(g, axisType, k, scale);

  // Label axis
  const labelAttrs = axisType === 'x'
    ? { y: (margin.bottom * 3) / 4, x: width / 2, class: "histogram1d-xlabel" }
    : { transform: "rotate(-90)", x: -height / 2, y: (-margin.left * 2) / 3, class: "histogram1d-ylabel" };

  const labelEl = g.append("text")
    .attr("class", labelAttrs.class)
    .attr("font-size", "18px")
    .attr("fill", COLORS.AXIS_LABEL)
    .text(labelText);

  if (labelAttrs.transform) labelEl.attr("transform", labelAttrs.transform);
  labelEl.attr("x", labelAttrs.x).attr("y", labelAttrs.y);
}

function addXAxis(svg, x, height, width, metadata) {
  addAxis(svg, x, metadata, 'x', height, width);
}

function addYAxis(svg, y, height, metadata) {
  addAxis(svg, y, metadata, 'y', height, null);
}
