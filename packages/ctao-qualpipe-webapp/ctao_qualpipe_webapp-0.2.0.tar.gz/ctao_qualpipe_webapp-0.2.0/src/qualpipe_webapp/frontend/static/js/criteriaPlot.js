export const allowedCriterion = [
  "TelescopeRangeCriterion",
  "RangeCriterion",
  "TelescopeThresholdCriterion",
  "ThresholdCriterion",
];

export function plotCriteria(svg, width, height, x, y, metadata, id) {
  console.info("metadata.criteriaReport:", metadata.criteriaReport);

  if (metadata.criteriaReport === undefined) {
    badgeCriteriaNone(id);
    return;
  }

  for (const criterion of allowedCriterion) {
    if (metadata.criteriaReport.hasOwnProperty(criterion)) {
      switch (criterion) {
        case "TelescopeRangeCriterion":
          plotRange(criterion, metadata, svg, width, height, x, y, id);
          break;
        case "RangeCriterion":
          plotRange(criterion, metadata, svg, width, height, x, y, id);
          break;
        case "TelescopeThresholdCriterion":
          plotThreshold(criterion, metadata, svg, width, height, x, y, id);
          break;
        case "ThresholdCriterion":
          plotThreshold(criterion, metadata, svg, width, height, x, y, id);
          break;
      }
      updateBadgeCriteria(id, metadata, criterion);
      // Only one criterion should be present, so break after handling
      break;
    }
  }
}

function plotRange(criterion, metadata, svg, width, height, x, y, id) {
  // Check if criterion contains "Telescope" (case-insensitive)
  const isTelescope = criterion.toLowerCase().includes("telescope");

  // Extract min and max values based on criterion type
  let minVal = isTelescope
    ? metadata.criteriaReport[criterion].config.min_value[0][2]
    : metadata.criteriaReport[criterion].config.min_value;

  const maxVal = isTelescope
    ? metadata.criteriaReport[criterion].config.max_value[0][2]
    : metadata.criteriaReport[criterion].config.max_value;

  const plotConfig = metadata?.plotConfiguration || {};
  const xScaleType = plotConfig.x?.scale || "linear";
  const yScaleType = plotConfig.y?.scale || "linear";
  const plotType = plotConfig.plotType || [];

  if (plotType === "histogram1d") {
    const xMin = x.domain()[0];
    if (xScaleType === "log" && minVal <= 0) {
      minVal = xMin;
      console.warn(
        `Minimum value for log scale adjusted to ${xMin} to avoid negative or zero values.`
      );
    }

    // Color region between two vertical lines
    svg
      .append("rect")
      .attr("x", x(minVal))
      .attr("y", 0)
      .attr("width", x(maxVal) - x(minVal))
      .attr("height", height)
      .attr("fill", "#28a745")
      .attr("id", "criteriaRect")
      .attr("opacity", 0.15)
      .attr("clip-path", `url(#clip-${id})`);

    // Min vertical line
    svg
      .append("line")
      .attr("x1", x(minVal))
      .attr("x2", x(minVal))
      .attr("y1", 0)
      .attr("y2", height)
      .attr("stroke", "#28a745")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "4,2")
      .attr("id", "criteriaMinLine")
      .attr("clip-path", `url(#clip-${id})`);

    // Max vertical line
    svg
      .append("line")
      .attr("x1", x(maxVal))
      .attr("x2", x(maxVal))
      .attr("y1", 0)
      .attr("y2", height)
      .attr("stroke", "#28a745")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "4,2")
      .attr("id", "criteriaMaxLine")
      .attr("clip-path", `url(#clip-${id})`);
  } else {
    const yMin = y.domain()[0];
    if (yScaleType === "log" && minVal <= 0) {
      minVal = yMin;
      console.warn(
        `Minimum value for log scale adjusted to ${yMin} to avoid negative or zero values.`
      );
    }

    // Color region between two horizontal lines
    svg
      .append("rect")
      .attr("class", "criterion")
      .attr("x", 0)
      .attr("y", y(maxVal))
      .attr("width", width)
      .attr("height", y(minVal) - y(maxVal))
      .attr("fill", "#28a745")
      .attr("id", "criteriaRect")
      .attr("opacity", 0.15)
      .attr("clip-path", `url(#clip-${id})`);

    // Min horizontal line
    svg
      .append("line")
      .attr("class", "criterion line-range-min")
      .attr("x1", 0)
      .attr("x2", width)
      .attr("y1", y(minVal))
      .attr("y2", y(minVal))
      .attr("stroke", "#28a745")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "4,2")
      .attr("id", "criteriaMinLine")
      .attr("clip-path", `url(#clip-${id})`);

    // Max horizontal line
    svg
      .append("line")
      .attr("class", "criterion line-range-max")
      .attr("x1", 0)
      .attr("x2", width)
      .attr("y1", y(maxVal))
      .attr("y2", y(maxVal))
      .attr("stroke", "#28a745")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "4,2")
      .attr("id", "criteriaMaxLine")
      .attr("clip-path", `url(#clip-${id})`);
  }
}

function plotThreshold(criterion, metadata, svg, width, height, x, y, id) {
  // Check if criterion contains "Telescope" (case-insensitive)
  const isTelescope = criterion.toLowerCase().includes("telescope");

  // Extract threshold value based on criterion type
  let threshold = isTelescope
    ? metadata.criteriaReport[criterion].config.threshold[0][2]
    : metadata.criteriaReport[criterion].config.threshold;

  const above = metadata.criteriaReport[criterion].config.above;
  const plotConfig = metadata?.plotConfiguration || {};
  const plotType = plotConfig.plotType || [];

  if (plotType === "histogram1d") {
    if (above) {
      // Color region on the right of the threshold
      svg
        .append("rect")
        .attr("x", x(threshold))
        .attr("y", 0)
        .attr("width", width - x(threshold))
        .attr("height", height)
        .attr("fill", "#28a745")
        .attr("opacity", 0.15)
        .attr("clip-path", `url(#clip-${id})`);
    } else {
      // Color region on the left of the threshold
      svg
        .append("rect")
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", width - x(threshold))
        .attr("height", height)
        .attr("fill", "#28a745")
        .attr("opacity", 0.15)
        .attr("clip-path", `url(#clip-${id})`);
    }
    // Vertical threshold line
    svg
      .append("line")
      .attr("x1", x(threshold))
      .attr("x2", x(threshold))
      .attr("y1", 0)
      .attr("y2", height)
      .attr("stroke", "#28a745")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "4,2")
      .attr("clip-path", `url(#clip-${id})`);
  } else {
    if (above) {
      // Color above threshold
      svg
        .append("rect")
        .attr("class", "criterion")
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", width)
        .attr("height", y(threshold))
        .attr("fill", "#28a745")
        .attr("opacity", 0.15)
        .attr("clip-path", `url(#clip-${id})`);
    } else {
      // Color below threshold
      svg
        .append("rect")
        .attr("class", "criterion")
        .attr("x", 0)
        .attr("y", y(threshold))
        .attr("width", width)
        .attr("height", height - y(threshold))
        .attr("fill", "#28a745")
        .attr("opacity", 0.15)
        .attr("clip-path", `url(#clip-${id})`);
    }
    // Horizontal threshold line
    svg
      .append("line")
      .attr("class", "criterion line-threshold")
      .attr("x1", 0)
      .attr("x2", width)
      .attr("y1", y(threshold))
      .attr("y2", y(threshold))
      .attr("stroke", "#28a745")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "4,2")
      .attr("clip-path", `url(#clip-${id})`);
  }
}

// --> TBD add call to function inside to update also color of table in the summary page
export function updateBadgeCriteria(id, metadata, criterion) {
  // Update criteria badge color upon criteria result
  const elem = document.getElementById(id);
  if (!elem) return;
  const badgerElem = elem.parentElement;
  if (metadata.criteriaReport[criterion].result) {
    updateBadgeClass(badgerElem, "badger-success");
  } else {
    updateBadgeClass(badgerElem, "badger-danger");
  }
}

export function badgeCriteriaNone(id) {
  const elem = document.getElementById(id);
  if (!elem) return;
  const badgerElem = elem.parentElement;
  console.debug("Badge set to NONE for plot: " + id + ".");
  updateBadgeClass(badgerElem, "badger-null");
}

function updateBadgeClass(elem, newClass) {
  const validClasses = ["badger-success", "badger-danger", "badger-null"];
  if (!elem || !validClasses.includes(newClass)) return;

  validClasses.forEach((cls) => elem.classList.remove(cls));
  elem.classList.add(newClass);

  const badgeText = {
    "badger-success": "CRITERIA: OK",
    "badger-danger": "CRITERIA: FAIL",
    "badger-null": "CRITERIA: NONE",
  };
  elem.setAttribute("data-badger-right", badgeText[newClass]);
}
