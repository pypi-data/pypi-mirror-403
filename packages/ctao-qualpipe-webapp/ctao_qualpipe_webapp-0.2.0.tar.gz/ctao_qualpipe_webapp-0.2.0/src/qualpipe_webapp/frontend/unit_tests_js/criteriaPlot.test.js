import { expect } from "chai";
import { JSDOM } from "jsdom";
import d3 from "../static/js/d3loader.js";
import { plotCriteria, allowedCriterion } from "../static/js/criteriaPlot.js";
import fs from "fs";
import { setScales } from "../static/js/commonUtilities.js";

// Helper functions
const SVG_W = 100;
const SVG_H = 100;

const basePlotConf = (scale = "linear", domain = undefined) => ({
  plotConfiguration: { y: { scale, ...(domain ? { domain } : {}) } },
});

const mkRangeConfig = (min, max) => ({ min_value: min, max_value: max });
const mkThresholdConfig = (above, thr) => ({ above: above, threshold: thr });

const mkMetadata = ({
  scale = "linear",
  domain,
  criterion,
  config,
  result,
}) => ({
  ...basePlotConf(scale, domain),
  criteriaReport: {
    [criterion]: {
      config,
      ...(result !== undefined ? { result: result } : {}),
    },
  },
});

const mkData = (criterion) => {
  return [
    { x: 1, y: 6 },
    { x: 2, y: 4 },
  ];
};

const mkConfigForCriterion = (criterion, { above = true } = {}) => {
  if (criterion === "TelescopeRangeCriterion") {
    return mkRangeConfig([["type", "*", 3]], [["type", "*", 7]]);
  }
  if (criterion === "RangeCriterion") {
    return mkRangeConfig(3, 7);
  }
  if (criterion === "TelescopeThresholdCriterion") {
    return mkThresholdConfig(above, [["type", "*", 5]]);
  }
  return mkThresholdConfig(above, 5); // ThresholdCriterion
};

const readBadgerBg = () => {
  let BADGER_BG = "#ddecfd";
  try {
    const css = fs.readFileSync(
      new URL("../static/css/badger.css", import.meta.url),
      "utf8"
    );
    // Match ".badger > div" rule with background-color using specific character class
    const badgerDivMatch = css.match(
      /\.badger\s*>\s*div\s*\{[^}]*background-color:\s*([#\w]+)/
    );
    if (badgerDivMatch) {
      BADGER_BG = badgerDivMatch[1].trim();
      return BADGER_BG;
    }
  } catch (e) {
    console.debug(
      "Encountered an error while reading '../static/css/badger.css': ",
      e
    );
  }

  // Fallback: read from _color.scss
  try {
    const scss = fs.readFileSync(
      new URL("../static/css/_color.scss", import.meta.url),
      "utf8"
    );
    const secondaryMatch = scss.match(/\$secondary:\s*([#\w]+)/);
    if (secondaryMatch) {
      BADGER_BG = secondaryMatch[1].trim();
    }
  } catch (e) {
    console.debug(
      "Encountered an error while reading '../static/css/_color.scss': ",
      e
    );
  }

  return BADGER_BG;
};

describe("Testing 'criteriaPlot.js'", function () {
  let dom, container, svg, id;
  const BADGER_BG = readBadgerBg();

  beforeEach(() => {
    dom = new JSDOM('<div id="plot"><div id="parent"></div></div>');
    global.document = dom.window.document;
    global.window = dom.window;
    id = "plot";
    container = dom.window.document.getElementById(id);
    container.parentElement.setAttribute("class", ""); // Simulate parent for badge
    svg = d3.select(container).append("svg").append("g");
  });

  afterEach(() => {
    dom?.window?.close();
    delete global.document;
    delete global.window;
  });

  // --- Suite: Verify creation of 'rect' and 'line' regardless of the criteria ---
  describe("'rect' and 'line' creation for:", function () {
    allowedCriterion.forEach((criterion) => {
      it(`${criterion}`, function () {
        const config = mkConfigForCriterion(criterion);
        const metadata = mkMetadata({ criterion, config });
        const data = mkData(criterion);
        const { x, y } = setScales(data, metadata, SVG_W, SVG_H);
        plotCriteria(svg, SVG_W, SVG_H, x, y, metadata, id);

        expect(container.querySelectorAll("rect.criterion").length).to.be.above(
          0
        );
        expect(container.querySelectorAll("line.criterion").length).to.be.above(
          0
        );
      });
    });
  });

  // --- Verify colored rectangle for Range/Threshold ---
  it("range-like criteria: colored rectangle within min and max", function () {
    let criterion = "RangeCriterion";
    let config = mkConfigForCriterion(criterion);
    let metadata = mkMetadata({ criterion, config });
    let data = mkData(criterion);

    let { x, y } = setScales(data, metadata, SVG_W, SVG_H);
    plotCriteria(svg, SVG_W, SVG_H, x, y, metadata, id);
    let rect = container.querySelector("rect.criterion");
    expect(rect).to.exist;
    let fill = rect.getAttribute("fill");
    expect(fill === "#28a745" || fill.toLowerCase() !== BADGER_BG.toLowerCase())
      .to.be.true;

    // TelescopeRangeCriterion
    dom.window.document
      .getElementById(id)
      .parentElement.setAttribute("class", "");

    criterion = "TelescopeRangeCriterion";
    config = mkConfigForCriterion(criterion);
    metadata = mkMetadata({ criterion, config });
    data = mkData(criterion);
    ({ x, y } = setScales(data, metadata, SVG_W, SVG_H));
    plotCriteria(svg, SVG_W, SVG_H, x, y, metadata, id);
    rect = container.querySelector("rect.criterion");
    expect(rect).to.exist;
    fill = rect.getAttribute("fill");
    expect(fill === "#28a745" || fill.toLowerCase() !== BADGER_BG.toLowerCase())
      .to.be.true;
  });

  it("threshold-like criteria: colored rectangle above/below threshold", function () {
    const threshold = 5;

    // above:true
    let criterion = "ThresholdCriterion";
    let config = mkThresholdConfig(true, threshold);
    let metadata = mkMetadata({ criterion, config });
    let data = mkData(criterion);
    let { x, y } = setScales(data, metadata, SVG_W, SVG_H);

    plotCriteria(svg, SVG_W, SVG_H, x, y, metadata, id);

    let line = container.querySelector("line.criterion");
    let rect = container.querySelector("rect.criterion");
    expect(line).to.exist;
    expect(rect).to.exist;

    let thresholdY = y(threshold);
    let lineY1 = Number(line.getAttribute("y1"));
    let lineY2 = Number(line.getAttribute("y2"));
    let rectH = Number(rect.getAttribute("height"));
    let rectY = Number(rect.getAttribute("y"));
    expect(lineY1).to.equal(lineY2);
    expect(lineY1).to.equal(thresholdY);
    expect(rectY).to.equal(0);
    expect(rectH).to.equal(thresholdY);

    // reset SVG elements
    svg.selectAll("*").remove();

    // above:false
    metadata.criteriaReport.ThresholdCriterion.config.above = false;
    dom.window.document
      .getElementById(id)
      .parentElement.setAttribute("class", "");

    plotCriteria(svg, SVG_W, SVG_H, x, y, metadata, id);

    line = container.querySelector("line.criterion");
    rect = container.querySelector("rect.criterion");
    expect(line).to.exist;
    expect(rect).to.exist;

    thresholdY = y(threshold);
    lineY1 = Number(line.getAttribute("y1"));
    lineY2 = Number(line.getAttribute("y2"));
    rectH = Number(rect.getAttribute("height"));
    rectY = Number(rect.getAttribute("y"));
    expect(lineY1).to.equal(lineY2);
    expect(lineY1).to.equal(thresholdY);
    expect(rectY).to.equal(thresholdY);
    expect(rectH).to.equal(thresholdY);
  });

  it("threshold outside domain should not draw line nor rect edge", function () {
    const metadata = {
      ...basePlotConf("linear", [0, 10]),
      criteriaReport: {
        ThresholdCriterion: { config: mkThresholdConfig(true, 20) },
      },
    };
    const data = mkData("ThresholdCriterion");

    const { x, y } = setScales(data, metadata, SVG_W, SVG_H);
    plotCriteria(svg, SVG_W, SVG_H, x, y, metadata, id);

    // Despite being outside the domain range 'line' and 'rectangle' should exist.
    // Line and rectangle's edge should not be visible; instead rectangle should
    // cover all the plot area or should not be visible at all.
    const line = container.querySelector("line.criterion");
    const rect = container.querySelector("rect.criterion");
    expect(line).to.exist;
    expect(rect).to.exist;
    const y1 = Number(line.getAttribute("y1"));
    const y2 = Number(line.getAttribute("y2"));
    const rectH = Number(rect.getAttribute("height"));
    expect(y2).to.equal(y1);
    expect(y1 < 0 || y1 > SVG_H).to.be.true;
    expect(rectH < 0 || rectH > SVG_H).to.be.true;
  });

  // --- Suite: Badge class show result value ---
  describe("badge class updates upon result 'value' for:", function () {
    allowedCriterion.forEach((criterion) => {
      it(`${criterion}`, function () {
        // result: true
        let metadata = mkMetadata({
          criterion,
          config: mkConfigForCriterion(criterion, { above: true }),
          result: true,
        });
        let data = mkData(criterion);
        let { x, y } = setScales(data, metadata, SVG_W, SVG_H);
        plotCriteria(svg, SVG_W, SVG_H, x, y, metadata, id);
        expect(container.parentElement.classList.contains("badger-success")).to
          .be.true;
        expect(container.parentElement.classList.contains("badger-danger")).to
          .be.false;
        expect(container.parentElement.classList.contains("badger-null")).to.be
          .false;
        expect(
          container.parentElement.getAttribute("data-badger-right")
        ).to.equal("CRITERIA: OK");

        // result: false
        dom.window.document
          .getElementById(id)
          .parentElement.setAttribute("class", "");
        metadata.criteriaReport[criterion].result = false;
        ({ x, y } = setScales(data, metadata, SVG_W, SVG_H));
        plotCriteria(svg, SVG_W, SVG_H, x, y, metadata, id);
        expect(container.parentElement.classList.contains("badger-danger")).to
          .be.true;
        expect(container.parentElement.classList.contains("badger-success")).to
          .be.false;
        expect(container.parentElement.classList.contains("badger-null")).to.be
          .false;
        expect(
          container.parentElement.getAttribute("data-badger-right")
        ).to.equal("CRITERIA: FAIL");
      });
    });
  });

  it("raise error when using log scale with minVal <= 0", function () {
    // Simulate log scale and negative minVal
    const metadata = {
      plotConfiguration: { y: { scale: "log" } },
      criteriaReport: {
        RangeCriterion: {
          config: { min_value: -1, max_value: 3 },
          result: true,
        },
      },
    };
    const data = [
      { x: 1, y: -1 },
      { x: 2, y: 3 },
    ];
    expect(() => setScales(data, metadata, SVG_W, SVG_H)).to.throw(
      "Log scale requires all y values > 0"
    );
  });
});
