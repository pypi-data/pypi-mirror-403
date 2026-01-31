import d3 from "./d3loader.js";
import { plotCriteria } from "./criteriaPlot.js";
import { setScales, clearPlotArea } from "./commonUtilities.js";
import { margin } from "./config.js";

const symbolTypes = {
  circle: d3.symbolCircle, // default
  triangle: d3.symbolTriangle,
  cross: d3.symbolCross,
  wye: d3.symbolWye,
  star: d3.symbolStar,
  square: d3.symbolSquare,
  diamond: d3.symbolDiamond,
};

function getMetadataPlotConfiguration(metadata) {
  const markType = metadata.plotConfiguration.marks?.type || "circle";
  const markSize = metadata.plotConfiguration.marks?.size || "64";
  const markFill = metadata.plotConfiguration.marks?.fill || "007bff";
  const markStroke = metadata.plotConfiguration.marks?.stroke || "007bff";
  const markStrokeWidth = metadata.plotConfiguration.marks?.strokeWidth || 1;
  const markOpacity = metadata.plotConfiguration.marks?.opacity || 1;
  return {
    markType,
    markSize,
    markFill,
    markStroke,
    markStrokeWidth,
    markOpacity,
  };
}

export function scatterPlot(id, dataKey) {
  let data = preprocessData(dataKey.fetchedData);
  const metadata = dataKey.fetchedMetadata;

  clearPlotArea(id);

  const { width, height, svg } = createSVGContainer(id);

  setTitle(svg, width, metadata);

  formatData(data);

  const { x, y } = setScales(data, metadata, width, height);

  addClipPath(svg, id, width, height);

  drawLine(svg, data, x, y, id, metadata);
  drawErrorBars(svg, data, x, y, id, metadata);
  drawPoints(svg, data, x, y, id, metadata);

  // Draw criteria on top of the points
  plotCriteria(svg, width, height, x, y, metadata, id);

  addXAxis(svg, x, height, width, metadata);
  addYAxis(svg, y, height, metadata);
}

// --- Helper Functions ---

function preprocessData(data) {
  // If data is an object with x and y arrays returns tuple for each point
  if (
    data &&
    !Array.isArray(data) &&
    typeof data === "object" &&
    Array.isArray(data.x) &&
    Array.isArray(data.y)
  ) {
    return data.x.map((xVal, i) => ({
      x: xVal,
      y: data.y[i],
      xerr: data.xerr ? data.xerr[i] : undefined,
      yerr: data.yerr ? data.yerr[i] : undefined,
    }));
  }
  return data;
}

function createSVGContainer(id) {
  const container = document.getElementById(id);
  // Dynamically retrieve container sizes
  const boundingRect = container.getBoundingClientRect();
  const width = boundingRect.width - margin.left - margin.right;
  const height = boundingRect.height - margin.top - margin.bottom;
  // Append the svg object to the body of the page
  const svg = d3
    .select("#" + id)
    .append("svg")
    .attr("width", width + margin.left + margin.right) // boundingRect.width
    .attr("height", height + margin.top + margin.bottom) // boundingRect.height
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  return { width, height, svg };
}

function setTitle(svg, width, metadata) {
  svg
    .append("text")
    .attr("x", width / 2)
    .attr("y", -margin.top / 3)
    .attr("class", "scatterplot-title")
    .text(
      metadata.plotConfiguration.title
        ? metadata.plotConfiguration.title
        : "No data found for this plot."
    );
}

function formatData(data) {
  // Coerce the strings to numbers.
  data.forEach(function (d) {
    d.x = +d.x;
    d.y = +d.y;
    if (d.xerr !== undefined) d.xerr = +d.xerr;
    if (d.yerr !== undefined) d.yerr = +d.yerr;
  });
}

function addClipPath(svg, id, width, height) {
  // Create a clipPath to restrict drawing to the plot area
  svg
    .append("clipPath")
    .attr("id", `clip-${id}`)
    .append("rect")
    .attr("x", 0)
    .attr("y", 0)
    .attr("width", width)
    .attr("height", height);
}

function drawLine(svg, data, x, y, id, metadata) {
  // define the line connecting points
  const valueline = d3
    .line()
    .x((d) => x(d.x))
    .y((d) => y(d.y))
    .curve(d3.curveLinear);

  // map metadata line names to CSS classes
  const lineStyle = (metadata?.plotConfiguration?.line || "solid")
    .toString()
    .toLowerCase();
  const classMap = {
    solid: "scatterplot-line",
    dashed: "scatterplot-line-dashed",
    dotted: "scatterplot-line-dotted",
    "dot-dashed": "scatterplot-line-dot-dashed",
    "dot-dashed-dashed": "scatterplot-line-dot-dashed-dashed",
    none: "scatterplot-no-line",
    "no-line": "scatterplot-no-line",
  };
  const cssClass = classMap[lineStyle.toLowerCase()] || classMap["solid"];

  // Draw the line, clipped to the plot area, using the chosen CSS class
  svg
    .append("path")
    .data([data])
    .attr("class", cssClass)
    .attr("class", "scatterPlot-line")
    .attr("d", valueline)
    .attr("clip-path", `url(#clip-${id})`)
    .style("fill", "none"); // force open path
}

function drawPoints(svg, data, x, y, id, metadata) {
  // Get mark configuration from metadata
  const {
    markType,
    markSize,
    markFill,
    markStroke,
    markStrokeWidth,
    markOpacity,
  } = getMetadataPlotConfiguration(metadata);

  const symbolType = symbolTypes[markType] || d3.symbolCircle;
  const symbol = d3.symbol().type(symbolType).size(markSize);
  // Create subgroup with clip-path, to avoid conflict with transform function
  const pointsGroup = svg.append("g").attr("clip-path", `url(#clip-${id})`);

  pointsGroup
    .selectAll(".scatterplot-point")
    .data(data)
    .enter()
    .append("path")
    .attr("transform", (d) => `translate(${x(d.x)},${y(d.y)})`)
    .attr("class", "scatterplot-point")
    .attr("d", symbol)
    .attr("opacity", markOpacity)
    // using .attr("style", ...) to enforce priority over CSS rules
    .attr(
      "style",
      [
        `fill: ${markFill};`,
        `stroke: ${markStroke};`,
        `stroke-width: ${markStrokeWidth}px;`,
        `} !important;`,
      ].join(" ")
    );
}

function negativeLogWarning(id) {
  console.warn(
    `Crop negative values to avoid issues with log scale representation in ${id}.`
  );
}

function drawErrorBars(svg, data, x, y, id, metadata) {
  const yScaleType = metadata.plotConfiguration.y.scale || "linear";
  const xScaleType = metadata.plotConfiguration.x.scale || "linear";
  const xMin = x.domain()[0];
  const yMin = y.domain()[0];

  // Vertical error bars (yerr)
  svg
    .selectAll(".scatterplot-yerror")
    .data(data.filter((d) => d.yerr !== undefined))
    .enter()
    .append("line")
    .attr("class", "scatterplot-yerror")
    .attr("x1", (d) => x(d.x))
    .attr("x2", (d) => x(d.x))
    .attr("y1", (d) => {
      if (yScaleType === "log" && d.yerr >= d.y) {
        negativeLogWarning(id);
        return y(yMin);
      }
      return y(d.y - d.yerr);
    })
    .attr("y2", (d) => y(d.y + d.yerr))
    .attr("clip-path", `url(#clip-${id})`);

  // Horizontal error bars (xerr)
  svg
    .selectAll(".scatterplot-xerror")
    .data(data.filter((d) => d.xerr !== undefined))
    .enter()
    .append("line")
    .attr("class", "scatterplot-xerror")
    .attr("y1", (d) => y(d.y))
    .attr("y2", (d) => y(d.y))
    .attr("x1", (d) => {
      if (xScaleType === "log" && d.xerr >= d.x) {
        negativeLogWarning(id);
        return x(xMin);
      }
      return x(d.x - d.xerr);
    })
    .attr("x2", (d) => x(d.x + d.xerr))
    .attr("stroke", "#333")
    .attr("stroke-width", 1)
    .attr("clip-path", `url(#clip-${id})`);
}

// Check if requires 10^k factor according to domain
function getExpScaleInfo(scale, scaleType) {
  if (!["linear", "log"].includes(scaleType)) return { use: false, k: 0 };
  const [d0, d1] = scale.domain();
  const absMax = d3.max([Math.abs(+d0 || 0), Math.abs(+d1 || 0)]);
  if (!absMax) return { use: false, k: 0 };
  const use = absMax >= 1e4 || absMax < 1e-3;
  const k = use ? Math.floor(Math.log10(absMax)) : 0;
  return { use, k };
}

// Formatter without thousand comma separator, with 10^k factor scaling
function makeScaledTickFormat(k) {
  const fmt = d3.format("~g");
  const scale = Math.pow(10, k);
  return (d) => fmt(d / scale);
}

// Add ×10^k flag above axis
function addAxisExponentLabel(g, where, k, scale) {
  g.selectAll(".axis-exp").remove();

  const textElement = g
    .append("text")
    .attr("class", "axis-exp")
    .attr("text-anchor", "end")
    .attr("fill", "#000")
    .attr("font-size", "16px");

  // Base text "×10"
  textElement.append("tspan").text("×10");

  // Superscript exponent
  textElement
    .append("tspan")
    .attr("baseline-shift", "super")
    .attr("font-size", "12px") // Smaller for the exponent
    .text(k);

  if (where === "x") {
    const maxX = Array.isArray(scale.range()) ? scale.range()[1] : 0;
    textElement
      .attr("x", maxX)
      .attr("y", Math.max(10, Math.floor(margin.bottom * 0.8)));
  } else {
    textElement
      .attr("x", 0)
      .attr("y", -Math.max(10, Math.floor(margin.top * 0.4)));
  }
}

function addXAxis(svg, x, height, width, metadata) {
  const metadataX = metadata.plotConfiguration.x || {};
  let xLabelText = metadataX.label || "Value";
  if (metadataX.unit) xLabelText += ` [${metadataX.unit}]`;

  const xScaleType = metadata.plotConfiguration.x.scale || "linear";
  const { use, k } = getExpScaleInfo(x, xScaleType);

  const axis = d3.axisBottom(x);
  // Use always formatter with no comma-thousand separator; if factor ×10^k is required, scale tick values
  const fmt = use ? makeScaledTickFormat(k) : d3.format("~g");
  axis.tickFormat(fmt);

  const g = svg
    .append("g")
    .attr("transform", "translate(0," + height + ")")
    .call(axis);

  // Increase tick font-size
  g.selectAll("text").attr("font-size", "16px");

  // Label ×10^k above the axis (if needed)
  if (use) addAxisExponentLabel(g, "x", k, x);

  // Axis label
  g.append("text")
    .attr("y", (margin.bottom * 3) / 4)
    .attr("x", width / 2)
    .attr("class", "scatterplot-xlabel")
    .attr("font-size", "18px") // Tick label larger
    .attr("fill", "#000")
    .text(xLabelText);
}

function addYAxis(svg, y, height, metadata) {
  const metadataY = metadata.plotConfiguration.y || {};
  let yLabelText = metadataY.label || "None";
  if (metadataY.unit) yLabelText += ` [${metadataY.unit}]`;

  const yScaleType = metadata.plotConfiguration.y.scale || "linear";
  const { use, k } = getExpScaleInfo(y, yScaleType);

  const axis = d3.axisLeft(y);
  // Use always formatter with no comma-thousand separator; if factor ×10^k is required, scale tick values
  const fmt = use ? makeScaledTickFormat(k) : d3.format("~g");
  axis.tickFormat(fmt);

  const g = svg.append("g").call(axis);

  // Increase tick font-size
  g.selectAll("text").attr("font-size", "16px");

  // Label ×10^k above the axis (if needed)
  if (use) addAxisExponentLabel(g, "y", k, y);

  // Axis label
  g.append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -height / 2)
    .attr("y", (-margin.left * 2) / 3)
    .attr("class", "scatterplot-ylabel")
    .attr("font-size", "18px") // Tick label larger
    .attr("fill", "#000")
    .text(yLabelText);
}
