import { API_URL } from "./config.js";
import { scatterPlot } from "./scatterPlot.js";
import { updateCameraView, bootstrapCameraViews } from "./cameraPlot.js";
import { histogram1DPlot } from "./histogram.js";
import { badgeCriteriaNone } from "./criteriaPlot.js";
import { resizeListeners } from "./base.js";
import { isValidMetadata, isValidData } from "./validation.js";
import { clearPlotArea } from "./commonUtilities.js";

function plotAndCreateResizeListener(elementId, data, key, plotType) {
  // Map between plotType and the plotting function
  const plotFunctions = {
    scatterplot: scatterPlot,
    cameraview: updateCameraView, // update (viewer already initialized)
    histogram1d: histogram1DPlot,
    // add here below other plotType and corresponding functions, e.g.
    // histogram2D: histogram2DPlot,
  };

  return function resizeHandler() {
    // Reset standard axis color after possible alerts
    const plotContainer = document.getElementById(elementId);
    plotContainer.style.color = "black";
    // Choose plotting function upon plotType, use scatterPlot as default
    const plotFunc = plotFunctions[plotType] || scatterPlot;
    plotFunc(elementId, data[key]);
  };
}

function handleInvalidData(message, elementId, warnOnly = false) {
  // Broadcast to all plot-* containers if no specific elementId
  if (!elementId) {
    const plotElements = document.querySelectorAll('[id^="plot-"]');
    plotElements.forEach((el) => handleInvalidData(message, el.id, warnOnly));
    return;
  }

  const container = document.getElementById(elementId);
  if (container) {
    clearPlotArea(elementId);

    // Create error div
    const errorDiv = document.createElement("div");
    errorDiv.className = "plot-error";
    errorDiv.textContent = message;
    container.appendChild(errorDiv);
    container.style.color = "red";

    badgeCriteriaNone(elementId);
  }

  if (warnOnly) {
    console.warn(`Warning in: '${elementId}' element`, message);
    return;
  }
  console.error(`Error in: '${elementId}' element`, message);
}

function validateScatterplot(
  { x, y, xerr, yerr },
  key,
  elementId,
  plotType,
  customError
) {
  if (x.length !== y.length)
    return customError(
      "x and y must have the same length.",
      key,
      plotType,
      elementId
    );
  if (xerr && xerr.length !== x.length)
    return customError(
      "xerr exists but does not match x length.",
      key,
      plotType,
      elementId
    );
  if (yerr && yerr.length !== y.length)
    return customError(
      "yerr exists but does not match y length.",
      key,
      plotType,
      elementId
    );
  return true;
}

function validateCameraViewPlot({ x }, key, elementId, plotType, customError) {
  const data = x;
  if (!data || !Array.isArray(data) || data.length === 0) {
    return customError(
      "CameraViewPlot requires 'x' array with at least one element.",
      key,
      plotType,
      elementId
    );
  }
  return true;
}

function validateHistogram1D({ x }, key, elementId, plotType, customError) {
  const data = x;
  if (!data || !Array.isArray(data) || data.length === 0) {
    return customError(
      "Histogram1D requires 'x' array with at least one element.",
      key,
      plotType,
      elementId
    );
  }
  return true;
}

const plotTypeValidators = {
  scatterplot: validateScatterplot,
  cameraview: validateCameraViewPlot,
  histogram1d: validateHistogram1D,
  // Add other plotType validators here, e.g. histogram2D: validateHistogram2D,
};

function checkXYLength(data, key, elementId, plotType) {
  const { x, y, xerr, yerr, z } = data.fetchedData;

  const customError = function (msg, key, plotType, elementId) {
    handleInvalidData(
      "Data length error for key: '" +
      key +
      "' and plot type: '" +
      plotType +
      "';\n" +
      msg,
      elementId
    );
    return false;
  };

  const validator = plotTypeValidators[plotType];
  if (validator) {
    return validator(
      { x, y, xerr, yerr, z },
      key,
      elementId,
      plotType,
      customError
    );
  } else {
    customError(
      `No specific 'plotType validation' defined for plot type '${plotType}'.`,
      key,
      plotType,
      elementId
    );
  }
}

async function validateAndPlotElement(elementId, data, key) {
  if (!data?.[key]) {
    const warnOnly = true;
    handleInvalidData(`No data found for key: ${key}`, elementId, warnOnly);
    return;
  }

  const validatedMetadata = await isValidMetadata(data[key], key);
  if (!validatedMetadata) {
    handleInvalidData(`Invalid metadata for key: ${key}`, elementId);
    return;
  }

  let plotType = data[key].fetchedMetadata.plotConfiguration.plotType
    ? data[key].fetchedMetadata.plotConfiguration.plotType
    : "scatterplot";

  plotType = typeof plotType === "string" ? plotType.toLowerCase() : plotType;

  const validatedData = await isValidData(data[key], key, elementId, plotType);
  if (!validatedData) {
    handleInvalidData(`Invalid data for key: ${key}`, elementId);
    return;
  }

  // Validate data length upon plot type
  if (!checkXYLength(data[key], key, elementId, plotType)) {
    return;
  }

  // Remove old listener if existing // TO BE CHECKED if still useful
  if (resizeListeners[elementId]) {
    window.removeEventListener("resize", resizeListeners[elementId]);
  }

  // Create and add the new listener
  const plotAndListen = plotAndCreateResizeListener(
    elementId,
    data,
    key,
    plotType
  );

  // First call: force refresh for cameraview
  if (plotType === "cameraview") {
    // aggiorna dati su viewer esistente
    const container = document.getElementById(elementId);
    const svg = container.querySelector("svg");
    // show back SVG if previously hidden
    if (svg) svg.style.display = "block";
    // remove any eventual previously shown errors
    container.querySelectorAll(".plot-error").forEach((el) => el.remove());

    await updateCameraView(elementId, data[key]);
  } else {
    plotAndListen();
  }

  resizeListeners[elementId] = plotAndListen;

  // For cameraview the window listener is not necessary (internal ResizeObserver)
  if (plotType !== "cameraview") {
    window.addEventListener("resize", plotAndListen);
  }
}

// requestDataFn is injectable to stub network calls during tests
function makePlot(requestDataFn = requestData) {
  const dataPromise = requestDataFn();

  dataPromise
    .then((data) => {
      console.debug("Received data:", data);
      if (!data) {
        handleInvalidData("No data received.", null);
        return;
      }
      const plotElements = document.querySelectorAll('[id^="plot-"]');
      Array.from(plotElements).forEach(async (element) => {
        const key = element.id.replace(/^plot-/, "");
        // Each element is handled asynchronously
        try {
          await validateAndPlotElement(element.id, data, key);
        } catch (error) {
          handleInvalidData(error, element.id);
        }
      });
    })
    .catch((error) => {
      console.error("Error while requesting data:", error);
    });
}

function checkQueryParams(
  selectedTelType,
  selectedSite,
  selectedDate,
  selectedOB,
  selectedTelID
) {
  if (!isValidSite(selectedSite)) return false;
  if (!isValidDate(selectedDate)) return false;
  if (!isValidOB(selectedOB)) return false;
  if (!isValidTelType(selectedTelType)) return false;
  if (!isValidTelID(selectedTelID)) return false;

  // Clear missinInfo alert
  const missingInfo = document.getElementById("missingInfo");
  if (missingInfo) {
    missingInfo.textContent = "";
  }
  return true;
}

function missingInfo(text, error = false) {
  if (error) {
    console.error(text);
  } else {
    console.warn(text);
  }
  const missingInfo = document.getElementById("missingInfo");
  if (missingInfo) {
    missingInfo.textContent = text;
    missingInfo.style.background = "red";
  }
}

function isValidSite(site) {
  if (site !== "North" && site !== "South") {
    missingInfo("Site must be either 'North' or 'South'");
    return false;
  }
  return true;
}

function isValidDate(date) {
  if (!date || date === "Choose a date") {
    missingInfo("Please select a 'date' from the dropdown menu.");
    return false;
  }
  if (!date.match(/^\d{4}-\d{2}-\d{2}$/)) {
    missingInfo("Date must be in YYYY-MM-DD format", true);
    return false;
  }
  return true;
}

function isValidOB(ob) {
  if (!ob || ob === "choose date first") {
    missingInfo("Please first choose a 'date' from the dropdown menu.");
    return false;
  }
  if (ob === "No OBs available") {
    missingInfo(
      "No Observation Blocks available for the selected date." +
      " Please select an other 'date' from the dropdown menu."
    );
    return false;
  }
  if (ob === "Select an OB") {
    missingInfo("Please select an 'Observation Block' from the dropdown menu.");
    return false;
  }
  if (!/^\d+$/.test(ob)) {
    missingInfo("Observation Block must be a valid number", true);
    return false;
  }
  return true;
}

function isValidTelType(type) {
  if (!type || !["LST", "MST", "SST"].includes(type)) {
    missingInfo("Telescope type must be 'LST', 'MST', or 'SST'", true);
    return false;
  }
  return true;
}

function isValidTelID(id) {
  if (!id || id === "select a Tel ID") {
    missingInfo("Please, select a 'Telescope ID' from the dropdown menu.");
    return false;
  }
  if (!/^\d+$/.test(id)) {
    missingInfo("Telescope ID must be a valid number", true);
    return false;
  }
  return true;
}

async function requestData() {
  const path = window.location.pathname;
  const arrayElement = path.split("/").filter(Boolean)[0];
  const selectedTelType = arrayElement ? arrayElement.slice(0, -1) : "";
  const selectedSite = document.getElementById("which-Site").value;
  const selectedDate = $("#date-picker").val();
  const selectedOB = document.getElementById("which-OB").value;
  const selectedTelID = document.getElementById("which-Tel-ID").value;

  const validParameters = checkQueryParams(
    selectedTelType,
    selectedSite,
    selectedDate,
    selectedOB,
    selectedTelID
  );

  if (validParameters) {
    console.log(
      "Query parameters are valid. Requesting data (for: Site=" +
      selectedSite +
      ", TelType=" +
      selectedTelType +
      ", Date=" +
      selectedDate +
      ", OB=" +
      selectedOB +
      ", TelID=" +
      selectedTelID +
      ")."
    );
    try {
      const response = await fetch(
        `${API_URL}/v1/data?site=${selectedSite}` +
        `&date=${selectedDate}` +
        `&ob=${selectedOB}` +
        `&telescope_type=${selectedTelType}` +
        `&telescope_id=${selectedTelID}`
      );
      const data = await response.json();
      if (response.status === 404) {
        missingInfo("Requested data not found (404).", true);
        return;
      }
      return data;
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  } else {
    console.warn("Invalid query parameters. Cannot request data.");
    return false;
  }
}

// re-export internals used in tests
export {
  makePlot,
  plotAndCreateResizeListener,
  handleInvalidData,
  validateAndPlotElement,
  validateScatterplot,
  checkXYLength,
  clearPlotArea,
  checkQueryParams,
  missingInfo,
  isValidSite,
  isValidDate,
  isValidOB,
  isValidTelType,
  isValidTelID,
  requestData,
};
export { scatterPlot } from "./scatterPlot.js";
export { histogram1DPlot } from "./histogram.js";
export { badgeCriteriaNone } from "./criteriaPlot.js";

// Initialize camera views on page load
if (typeof document !== "undefined") {
  const initCameraViews = () => {
    try {
      // Only initialize if there are camera view containers on the page
      const hasCameraViews = document.querySelector('[id$="_cameraView"]');
      if (hasCameraViews) {
        bootstrapCameraViews();
      }
    } catch (err) {
      console.error("Error initializing camera views:", err);
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCameraViews);
  } else {
    // DOM already loaded
    initCameraViews();
  }
}
