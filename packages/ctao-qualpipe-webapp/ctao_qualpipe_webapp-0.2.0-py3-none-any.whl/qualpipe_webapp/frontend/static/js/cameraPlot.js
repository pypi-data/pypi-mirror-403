import {
  margin,
  LST_CAMERA_PIXEL_COUNT,
  lst_camera_mapping,
} from "./config.js";
import d3 from "./d3loader.js";
import { clearPlotArea } from "./commonUtilities.js";
import { updateBadgeCriteria, badgeCriteriaNone } from "./criteriaPlot.js";
import {
  get_color,
  setColorPalette,
  getAvailablePalettes,
} from "./cameraUtilities.js";

const lst_configuration = {
  hexRadius: 6,
  hexAngle: 10,
  edgeColor: "#000000", // "#ffffff",
  hexStrokeWidth: 1.3, // thickness of pixel borders
  width: 500,
  height: 580,
  legend_width: 15,
  legend_heigth: 520,
  legend_margin: 60, // extra space for legend + ticks + label
  mapping: lst_camera_mapping,
  camera_mirroring: [false, false],
  camera_rotation: 0,
};

/**
 * Render or update a camera pixel view inside a DOM container.
 *
 * This async function finds the container element by the provided `id`, reuses an existing
 * viewer if present (calling its `scale()` method), or forcefully refreshes it by destroying
 * and recreating the viewer when `forceRefresh` is true. It prepares pixel data via
 * preprocessData(dataKey.fetchedData), extracts a `gain` value from the fetched data, clears
 * the plot area, creates a new camera viewer, waits for the viewer to be ready, and finally
 * draws pixels using viewer.draw_pixels(data, sample_range, gain). The created viewer is stored
 * on the container as `container.__cameraViewer` so subsequent calls can reuse or destroy it.
 *
 * Side effects:
 * - Mutates the DOM by clearing and drawing into the plot area for `id`.
 * - Attaches a viewer instance to `container.__cameraViewer`.
 * - Calls external helpers: preprocessData, clearPlotArea, create_camera_view, and viewer methods.
 *
 * @async
 * @param {string} id - The DOM element id of the container to host the camera view (without '#').
 *                      The element is expected to exist in the document.
 * @param {Object} dataKey - An object containing the data and metadata required to draw the view.
 * @param {Object} dataKey.fetchedData - Raw data used by preprocessData; expected to include at least
 *                                       a `gain` property referenced by the viewer draw call.
 * @param {Object} [dataKey.fetchedMetadata] - Metadata that may include plotting configuration.
 * @param {Object} [dataKey.fetchedMetadata.plotConfiguration] - Plot configuration object.
 * @param {Array|Object|null} [dataKey.fetchedMetadata.plotConfiguration.x.domain] - Optional
 *                      sample range passed to viewer.draw_pixels; if absent, null is used and range is
 *                      computed taking min and max data.
 * @param {boolean} [forceRefresh=false] - When true, forces destruction and recreation of the viewer
 *                                         even if one already exists on the container.
 * @returns {Promise<void>} Resolves once the viewer is ready and pixels have been drawn.
 *
 * @throws {Error} If the container element cannot be found or if viewer creation/initialization fails.
 */

// Update colors on existing viewer
export async function updateCameraView(id, dataKey) {
  const container = document.getElementById(id);
  if (!container) throw new Error("Container not found: " + id);
  const viewer = container.__cameraViewer;
  if (!viewer) {
    console.warn("Viewer not yet initialised for:", id);
    return;
  }

  // Prepare data
  const { data, gain, sample_range } = preprocessData(
    dataKey,
    LST_CAMERA_PIXEL_COUNT
  );

  const title = dataKey?.fetchedMetadata?.plotConfiguration?.title || null;
  updateCameraTitle(id, title);

  // Wait for completed mapping and build
  await viewer.ready();
  viewer.draw_pixels(data, sample_range, gain);

  // Get criterion name
  const criterion = Object.keys(
    dataKey.fetchedMetadata?.criteriaReport || {}
  )[0];

  viewer.dataUnit = dataKey?.fetchedMetadata?.plotConfiguration?.x?.unit || "";

  if (dataKey.fetchedMetadata.criteriaReport === undefined) {
    badgeCriteriaNone(id);
    return;
  }

  updateBadgeCriteria(id, dataKey.fetchedMetadata, criterion);
}

// Scan and initialize viewers for all candidate containers
function bootstrapCameraViews() {
  const candidates = Array.from(
    document.querySelectorAll(
      'div[id^="plot-"] > div[id$="_cameraView"], div[id^="plot-"][id$="_cameraView"], div[id$="_cameraView"]'
    )
  );

  candidates.forEach((el) => {
    const id = el.id || el.parentElement.id;
    initCameraView(id);
  });
}

// Initialise single viewer (no data plotting)
function initCameraView(containerId) {
  const container = document.getElementById(containerId);
  if (!container) {
    console.warn("Container not found for initialisation:", containerId);
    return;
  }
  // Viewer already created
  if (container.__cameraViewer) return;

  clearPlotArea(containerId);

  const { width, svg } = createSVGContainer(containerId, lst_configuration);
  // Set default title (will be overwritten if specified in fetchedMetadata.plotConfiguration.title)
  setTitle(svg, width, { plotConfiguration: { title: "Camera view" } });

  const viewer = create_camera_view("#" + containerId, lst_configuration, svg);
  container.__cameraViewer = viewer;

  badgeCriteriaNone(containerId);

  // Add palette selector
  addPaletteSelector(containerId);
}

function preprocessData(dataKey, cameraPixelTot) {
  const data = dataKey.fetchedData.x;
  if (data.length !== cameraPixelTot) {
    throw new Error(
      `Data length mismatch: expected ${cameraPixelTot}, got ${data.length}`
    );
  }
  const gain = dataKey.fetchedData.gain || [];
  const sample_range =
    dataKey.fetchedMetadata?.plotConfiguration?.x?.domain ?? null;

  return { data, gain, sample_range };
}

// Create a responsive SVG with viewBox based on configuration
function createSVGContainer(id, configuration) {
  // Extend width to include right legend space
  const legendSpace = configuration.legend_width + configuration.legend_margin;
  const totalWidth =
    configuration.width + margin.left + margin.right + legendSpace;
  const totalHeight = configuration.height + margin.top + margin.bottom;

  const outerSvg = d3
    .select("#" + id)
    .append("svg")
    .attr("width", totalWidth) // starting point, then adapted by scale()
    .attr("height", totalHeight)
    .attr("preserveAspectRatio", "xMidYMid meet")
    .attr("viewBox", `0 0 ${totalWidth} ${totalHeight}`)
    .style("display", "block"); // avoid extra spacing in inline SVG

  const svg = outerSvg
    .append("g")
    .attr("transform", `translate(${margin.left}, ${margin.top + 40})`);

  return { width: configuration.width, svg };
}

function setTitle(svg, width, metadata) {
  let title = metadata.plotConfiguration.title
    ? metadata.plotConfiguration.title
    : "Camera view";

  svg
    .append("text")
    .attr("x", width / 2)
    .attr("y", -margin.top / 3)
    .attr("class", "cameraview-title")
    .attr("text-anchor", "middle")
    .attr("dy", "-30px")
    .style("pointer-events", "none") // avoid interference with mouse events
    .text(title);
}

function create_camera_view(selector, configuration, existingSvg = null) {
  let camera_view = Object.create(CameraViewer);
  camera_view.build(selector, configuration, existingSvg);
  return camera_view;
}

const CameraViewer = {
  // Always initialize state to avoid undefined
  pixels_mapping: {},
  pixels: [],
  pixels_value: null,
  pixels_count: 0,
  svg: null,
  svgContainer: null,
  baseTransform: "",
  resizeObserver: null,
  _readyPromise: null,
  currentRange: null,
  normal_pixels: [], // this can be used to highlight special pixels (e.g. dead pixels or pixel with different gain selection)

  build(div, configuration = null, existingSvg = null) {
    this.div = div;
    if (configuration) this.configuration = configuration;

    if (existingSvg) {
      this.svg = existingSvg;
      this.svgContainer = existingSvg.node().ownerSVGElement;
      this.baseTransform = this.svg.attr("transform") || "";
      if (this.svgContainer) {
        const legendSpace =
          this.configuration.legend_width + this.configuration.legend_margin;
        const totalW =
          this.configuration.width + margin.left + margin.right + legendSpace;
        const totalH = this.configuration.height + margin.top + margin.bottom;
        if (!this.svgContainer.getAttribute("viewBox")) {
          this.svgContainer.setAttribute("viewBox", `0 0 ${totalW} ${totalH}`);
        }
        this.svgContainer.setAttribute("preserveAspectRatio", "xMidYMid meet");
        this.svgContainer.style.display = "block";
      }
    }

    this._readyPromise = new Promise((r) => (this._resolveReady = r));

    this.get_mapping();
    this.build_camera();
  },

  // Waiting function until viewer is ready
  ready() {
    return this._readyPromise;
  },

  build_camera() {
    const wait_mapping = () => {
      const ready = Array.isArray(this.pixels) && this.pixels.length > 0;
      // Wait until mapping is ready
      if (!ready) return window.setTimeout(wait_mapping, 50);

      const cameraHexbin = d3.hexbin().radius(this.configuration.hexRadius);

      // If not existing, create a responsive SVG entirely contained in the div
      if (!this.svg) {
        const legendSpace =
          this.configuration.legend_width + this.configuration.legend_margin;
        const totalW =
          this.configuration.width + margin.left + margin.right + legendSpace;
        const totalH = this.configuration.height + margin.top + margin.bottom;

        const outerSvg = d3
          .select(this.div)
          .append("svg")
          .attr("width", totalW)
          .attr("height", totalH)
          .attr("viewBox", `0 0 ${totalW} ${totalH}`)
          .attr("preserveAspectRatio", "xMidYMid meet")
          .style("display", "block");

        this.svg = outerSvg
          .append("g")
          .attr("transform", `translate(${margin.left}, ${margin.top + 40})`);
        this.baseTransform = this.svg.attr("transform") || "";
        this.svgContainer = outerSvg.node();
      }

      // Tooltip div (created once per viewer)
      const tooltip = d3
        .select("body")
        .append("div")
        .attr("class", "hex-tooltip")
        .style("position", "absolute")
        .style("background", "#fff")
        .style("border", "1px solid #888")
        .style("padding", "4px 8px")
        .style("border-radius", "4px")
        .style("pointer-events", "none")
        .style("font-size", "14px")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
        .style("opacity", 0)
        .style("z-index", 9999);

      // Handler to show tooltip (accesses pixels_mapping and pixels_value)
      const showTooltip = (event, d) => {
        const pixelId = d?.[0]?.[2] ?? null;
        if (pixelId == null) return;

        // Get pixel value (if available)
        const pixelValue = this.pixels_value
          ? this.pixels_value[pixelId]
          : null;
        const unit = this.dataUnit || ""; // saved in updateCameraView
        let valueText;
        if (pixelValue != null) {
          const unitText = unit ? " [" + unit + "]" : "";
          valueText = `${pixelValue.toFixed(2)}${unitText}`;
        } else {
          valueText = "N/A";
        }

        tooltip
          .style("opacity", 1)
          .html(`<strong>Pixel #${pixelId}</strong><br>Value: ${valueText}`)
          .style("left", event.pageX + 10 + "px")
          .style("top", event.pageY - 10 + "px");
      };

      const hideTooltip = () => {
        tooltip.style("opacity", 0);
      };

      // TBD: pixel selection handler
      const select_pixel = (event, d) => {
        const pixelId = d?.[0]?.[2] ?? null;
        if (pixelId != null) {
          console.debug(
            "Selected pixel id:",
            pixelId,
            "mapping:",
            this.pixels_mapping[pixelId],
            "value:",
            this.pixels_value ? this.pixels_value[pixelId] : "N/A"
          );
        }
      };

      const rotate_hexagon = (d) =>
        `rotate(${this.configuration.hexAngle} ${d.x} ${d.y})`;

      // Always use an array in .data(...)
      this.svg
        .append("g")
        .selectAll(".hexagon")
        .data(this.pixels || [])
        .enter()
        .append("path")
        .attr("class", "hexagon")
        .attr("d", (d) => "M" + d.x + "," + d.y + cameraHexbin.hexagon())
        .attr("ID", (d) => d?.[0]?.[2] ?? null)
        .attr("transform", rotate_hexagon)
        .style("stroke", this.configuration.edgeColor)
        .style("stroke-width", this.configuration.hexStrokeWidth)
        .style("fill", "#BEBEBE")
        .on("click", select_pixel)
        .on("mousemove", showTooltip)
        .on("mouseleave", hideTooltip);

      // Vertical legend gradient (range placeholder 0-100)
      const grad = this.svg
        .append("defs")
        .append("linearGradient")
        .attr("id", "grad")
        .attr("x1", "0%")
        .attr("x2", "0%")
        .attr("y1", "0%")
        .attr("y2", "100%");

      const placeholderColors = [];
      for (let val = 0; val < 25; val++) {
        placeholderColors.push("#BEBEBE");
      }

      grad
        .selectAll("stop")
        .data(placeholderColors)
        .enter()
        .append("stop")
        .style("stop-color", (d) => d)
        .attr(
          "offset",
          (d, i) => 100 * (i / (placeholderColors.length - 1)) + "%"
        );

      // Place color legend to the right of the camera
      const legendHeight = this.configuration.legend_heigth;
      const legendWidth = this.configuration.legend_width;
      const legendX = this.configuration.width + 10;
      const legendY = (this.configuration.height - legendHeight) / 2;

      this.svg
        .append("rect")
        .attr("class", "legend-rect")
        .attr("x", legendX)
        .attr("y", legendY)
        .attr("width", legendWidth)
        .attr("height", legendHeight)
        .style("fill", "url(#grad)");

      this.svg
        .append("text")
        .attr("class", "legend-label")
        .attr("x", legendX + legendWidth / 2) // horizontally centered above legend
        .attr("y", legendY - 30) // 10px above legend
        .attr("text-anchor", "middle")
        .attr("dy", "0") // no vertical offset
        .style("font-size", "20px")
        .text("");

      this.svg.selectAll(".cameraview-title").raise();
      this.svg.attr("transform", this.baseTransform);
      this.scale();
      this.setupResizeObserver();

      if (this._resolveReady) this._resolveReady();
    };

    wait_mapping();
  },

  setupResizeObserver() {
    // Remove previous observer if existing
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
    const container = document.querySelector(this.div);
    if (!container) return;
    this.resizeObserver = new ResizeObserver(() => {
      // Call scale() only, DO NOT recreate the SVG
      this.scale();
    });
    this.resizeObserver.observe(container);
  },

  parsePixelLine(line, mapping) {
    if (!line || line.length < 3) return null;

    const ip = parseInt(line[mapping["format"]["id"]]);
    const xp = parseFloat(line[mapping["format"]["x"]]);
    const yp = parseFloat(line[mapping["format"]["y"]]);

    if (!isFinite(ip) || !isFinite(xp) || !isFinite(yp)) return null;

    return { ip, xp, yp };
  },

  applyCoordinateTransforms(xp, yp, config) {
    let x = config.camera_mirroring[0] ? -xp : xp;
    let y = config.camera_mirroring[1] ? -yp : yp;

    if (config.camera_rotation !== 0) {
      const angle = (config.camera_rotation * Math.PI) / 180;
      const rotX = x * Math.cos(angle) + y * Math.sin(angle);
      const rotY = -x * Math.sin(angle) + y * Math.cos(angle);
      x = rotX;
      y = rotY;
    }

    return { x, y };
  },

  updateBounds(bounds, x, y) {
    return {
      xm: bounds.xm === null || bounds.xm >= x ? x : bounds.xm,
      xM: bounds.xM === null || bounds.xM <= x ? x : bounds.xM,
      ym: bounds.ym === null || bounds.ym >= y ? y : bounds.ym,
      yM: bounds.yM === null || bounds.yM <= y ? y : bounds.yM,
    };
  },

  normalizeAndCreatePixels(data, bounds, config) {
    const { xm, xM, ym, yM } = bounds;
    const pixels = new Array(data.length);
    const ratio = (xM - xm) / (yM - ym);
    const pixels_mapping = {};

    for (let i = 0; i < data.length; i++) {
      const ip = data[i][0];
      const xp = (xM - data[i][1]) / (xM - xm);
      const yp = (yM - data[i][2]) / (yM - ym) / ratio;
      pixels_mapping[ip] = [data[i][1], data[i][2]];

      const x =
        config.width -
        (config.width - 2 * config.hexRadius) * xp -
        config.hexRadius;
      const y = (config.width - 2 * config.hexRadius) * yp + config.hexRadius;

      pixels[i] = new Array(2);
      pixels[i][0] = [x, y, ip];
      pixels[i]["x"] = x;
      pixels[i]["y"] = y;
    }

    return { pixels, pixels_mapping, count: data.length };
  },

  async get_mapping() {
    const arrange_pixels = (input) => {
      let bounds = { xm: null, xM: null, ym: null, yM: null };
      const data = [];

      const lines = input.split(/\n/);
      for (let i = 0; i < lines.length; i++) {
        if (i < this.configuration.mapping["skiplines"]) continue;

        const line = lines[i].match(/\S+/g);
        const parsed = this.parsePixelLine(line, this.configuration.mapping);
        if (!parsed) continue;

        const { x, y } = this.applyCoordinateTransforms(
          parsed.xp,
          parsed.yp,
          this.configuration
        );

        data.push([parsed.ip, x, y]);
        bounds = this.updateBounds(bounds, x, y);
      }

      // Avoid undefined if no pixels found
      if (data.length === 0) {
        this.pixels = [];
        this.pixels_count = 0;
        return;
      }

      const result = this.normalizeAndCreatePixels(
        data,
        bounds,
        this.configuration
      );
      this.pixels = result.pixels;
      this.pixels_mapping = result.pixels_mapping;
      this.pixels_count = result.count;
    };

    const res = await fetch(this.configuration.mapping["url"]);
    const text = await res.text();
    arrange_pixels(text);
  },

  scale() {
    if (this.svg === null) {
      setTimeout(() => this.scale(), 100);
      return false;
    }

    const container = document.querySelector(this.div);
    if (!container) return false;

    const svgElement =
      this.svgContainer || document.querySelector(this.div + " svg");
    if (!svgElement) return false;

    // Get viewBox size (coherent with configuration + margins + legend)
    const legendSpace =
      this.configuration.legend_width + this.configuration.legend_margin;
    const vb = (svgElement.getAttribute("viewBox") || "0 0 0 0").split(/\s+/);
    const vbW =
      parseFloat(vb[2]) ||
      this.configuration.width + margin.left + margin.right + legendSpace;
    const vbH =
      parseFloat(vb[3]) ||
      this.configuration.height + margin.top + margin.bottom;

    const { width: cw, height: ch } = container.getBoundingClientRect();

    // Fit-contained inside container
    const s = Math.min(cw / vbW, ch / vbH);
    const newW = Math.max(0, vbW * s);
    const newH = Math.max(0, vbH * s);

    svgElement.setAttribute("width", String(newW));
    svgElement.setAttribute("height", String(newH));

    // Keep base translate (for margins)
    if (this.baseTransform) {
      this.svg.attr("transform", this.baseTransform);
    } else {
      this.svg.attr("transform", null);
    }
    return true;
  },

  paint_pixels(data, pixels_range, normal_pixels) {
    if (this.svg !== null) {
      this.pixels_value = {};
      this.normal_pixels = normal_pixels;
      this.currentRange = pixels_range;

      const pixels_location = this.svg.selectAll("path").nodes();
      for (let i = 0; i < data.length; i++) {
        const pixel = pixels_location[i];
        const pixelId = pixel.getAttribute("ID");
        // Save values for tooltip
        this.pixels_value[pixelId] = data[i];
        pixel.style.fill =
          data[i] === null
            ? "#BEBEBE"
            : get_color(pixels_range[0], pixels_range[1], data[i]);
        if (normal_pixels[i] == 0) {
          pixel.classList.add("special_hexagon");
        } else {
          pixel.classList.remove("special_hexagon");
        }
      }
    }
  },

  paint_legend(pixels_range) {
    // Remove existing legend axis (and any previous exponent label)
    this.svg.selectAll(".z.axis.legend").remove();

    // Place color legend to the right of the camera
    const legendHeight = this.configuration.legend_heigth;
    const legendWidth = this.configuration.legend_width;
    const legendX = this.configuration.width + 10;
    const legendY = (this.configuration.height - legendHeight) / 2;

    const z = d3
      .scaleLinear()
      .range([legendHeight, 0]) // high values on top, low values at the bottom
      .domain([pixels_range[0], pixels_range[1]])
      .nice();

    const ticksCount =
      Number.isInteger(pixels_range[0]) &&
        Number.isInteger(pixels_range[1]) &&
        pixels_range[0] === 0 &&
        pixels_range[1] === 1
        ? 2
        : 5;

    // Apply formatter with ×10^k factor if needed
    const { use, k } = getExpScaleInfo(z, "linear");
    const zAxis = d3.axisRight(z).ticks(ticksCount);
    const fmt = use ? makeScaledTickFormat(k) : d3.format("~g");
    zAxis.tickFormat(fmt);

    const g = this.svg
      .append("g")
      .attr("class", "z axis legend")
      .attr(
        "transform",
        `translate(${legendX + legendWidth}, ${legendY})` // ticks on the right side
      )
      .call(zAxis);

    // Increase size of tick font
    g.selectAll("text").style("font-size", "28px");

    const legendAxis = d3.select(this.div + " .legend");

    if (legendAxis.empty()) {
      console.warn("Legend axis not found");
      return;
    }

    // Update legend axis with new scale values and gradient colors
    legendAxis
      .attr("transform", `translate(${legendX + legendWidth}, ${legendY})`)
      .call(zAxis);

    if (use) addAxisExponentLabel(g, "y", k, z);

    // Update gradient
    this.updateGradient(pixels_range);
  },

  updateGradient(pixels_range) {
    // Select existing gradient
    const grad = d3.select(this.div + " #grad");

    if (grad.empty()) {
      console.warn("Gradient not found");
      return;
    }

    // Generate new colors based on the current range
    const colors = [];
    const numSteps = 25;
    for (let val = numSteps - 1; val >= 0; val--) {
      // inverted for vertical gradient
      const normalizedValue =
        pixels_range[0] +
        (val / (numSteps - 1)) * (pixels_range[1] - pixels_range[0]);
      colors.push(get_color(pixels_range[0], pixels_range[1], normalizedValue));
    }

    // Update gradient stop
    grad.selectAll("stop").remove();
    grad
      .selectAll("stop")
      .data(colors)
      .enter()
      .append("stop")
      .style("stop-color", (d) => d)
      .attr("offset", (d, i) => 100 * (i / (colors.length - 1)) + "%");
  },

  draw_pixels(pixels_value, pixels_range, normal_pixels) {
    pixels_range =
      pixels_range === null
        ? [d3.min(pixels_value), d3.max(pixels_value)]
        : pixels_range;

    this.paint_legend(pixels_range);
    this.paint_pixels(pixels_value, pixels_range, normal_pixels || []);
  },
};

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
    .attr("text-anchor", where === "x" ? "end" : "start")
    .attr("fill", "#000")
    .attr("font-size", "28px");

  // Base text "×10"
  textElement.append("tspan").text("×10");

  // Superscript exponent
  textElement
    .append("tspan")
    .attr("baseline-shift", "super")
    .attr("font-size", "20px") // Smaller for the exponent
    .text(k);

  if (where === "x") {
    const maxX = Array.isArray(scale.range()) ? scale.range()[1] : 0;
    textElement
      .attr("x", maxX)
      .attr("y", -Math.max(10, Math.floor(margin.bottom * 0.6)));
  } else {
    textElement
      .attr("x", -20)
      .attr("y", -Math.max(10, Math.floor(margin.top * 0.7)));
  }
}

// Update camera title
function updateCameraTitle(containerId, title) {
  if (!title) title = "Camera view";

  const container = document.getElementById(containerId);
  if (!container) return;

  const svgEl = container.querySelector("svg");
  if (!svgEl) return;

  // Compute width from viewBox or attributes
  const getInnerWidth = (svg) => {
    const vb = svg.getAttribute("viewBox");
    if (vb) {
      const parts = vb.trim().split(/\s+/).map(Number);
      if (parts.length === 4 && !parts.some(Number.isNaN)) {
        return parts[2] - margin.left - margin.right;
      }
    }
    const wAttr = parseFloat(svg.getAttribute("width"));
    if (!Number.isNaN(wAttr)) return wAttr - margin.left - margin.right;
    return Math.max(
      0,
      svg.getBoundingClientRect().width - margin.left - margin.right
    );
  };

  const innerWidth = getInnerWidth(svgEl);
  const g = d3.select(svgEl).select("g");

  // Select title element (or create if not existing)
  let t = g.select("text.cameraview-title");
  if (t.empty()) {
    t = g
      .append("text")
      .attr("class", "cameraview-title")
      .attr("text-anchor", "middle")
      .attr("dy", "-0.35em");
  }

  // Set title position and text
  t.attr("x", innerWidth / 2)
    .attr("y", -margin.top / 3)
    .text(title);
}

// Add palette selector UI to the camera view container
function addPaletteSelector(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  // Remove existing selector if present
  const existing = container.querySelector(".palette-selector-container");
  if (existing) existing.remove();

  const selectorDiv = document.createElement("div");
  selectorDiv.className = "palette-selector-container";

  const label = document.createElement("label");
  label.className = "label-palette";
  label.textContent = "Palette: ";

  const select = document.createElement("select");
  select.className = "palette-selector";

  // Populate options
  getAvailablePalettes().forEach((palette) => {
    const option = document.createElement("option");
    option.value = palette;
    option.textContent = palette.charAt(0).toUpperCase() + palette.slice(1);
    if (palette === "viridis") option.selected = true;
    select.appendChild(option);
  });

  // Change handler
  select.addEventListener("change", (e) => {
    setColorPalette(e.target.value);
    const viewer = container.__cameraViewer;
    if (viewer?.pixels_value && viewer?.pixels) {
      // Redraw pixels with new palette
      const currentRange = viewer.currentRange || [
        d3.min(Object.values(viewer.pixels_value)),
        d3.max(Object.values(viewer.pixels_value)),
      ];

      // Reconstruct data array in correct pixel order (same as DOM elements)
      const orderedPixelData = [];
      for (let i = 0; i < viewer.pixels.length; i++) {
        const pixelId = viewer.pixels[i][0][2]; // Extract pixel ID from geometry
        orderedPixelData[i] = viewer.pixels_value[pixelId] || null;
      }

      viewer.paint_pixels(
        orderedPixelData,
        currentRange,
        viewer.normal_pixels || []
      );
      viewer.updateGradient(currentRange);
    }
  });

  selectorDiv.appendChild(label);
  selectorDiv.appendChild(select);
  container.style.position = "relative";
  container.insertBefore(selectorDiv, container.firstChild);
}

// Export public API
export { bootstrapCameraViews };

// Expose internal helpers for unit testing (kept separate from public API)
export const __test__ = {
  CameraViewer,
  getExpScaleInfo,
  makeScaledTickFormat,
  addAxisExponentLabel,
  updateCameraTitle,
  addPaletteSelector,
  bootstrapCameraViews,
  initCameraView,
  preprocessData,
};
