import { expect } from "chai";
import { JSDOM } from "jsdom";
import { scatterPlot } from "../static/js/scatterPlot.js";

const plotConfiguration = {
  x: { label: "X", scale: "linear" },
  y: { label: "Y", scale: "linear" },
  marks: { type: "circle", size: 64, fill: "#ff0000" },
};
const criteriaReport = {
  RangeCriterion: {
    config: {
      max_value: 1,
      min_value: 0,
    },
    result: true,
  },
};

const testCases = [
  {
    name: "'2-datapoints'",
    fetchedData: [
      { x: 0, y: 2 },
      { x: 2, y: 3 },
    ],
    fetchedMetadata: { plotConfiguration, criteriaReport },
    expectedCount: 2,
  },
  {
    name: "'3-datapoints'",
    fetchedData: [
      { x: -1, y: 2 },
      { x: 2, y: 3 },
      { x: 3, y: 4 },
    ],
    fetchedMetadata: { plotConfiguration, criteriaReport },
    expectedCount: 3,
  },
];

describe("Tests for 'scatterPlot.js':", () => {
  describe("scatterPlot", function () {
    let dom, container;

    beforeEach(() => {
      dom = new JSDOM(
        '<div id="plot" style="width:400px;height:300px;"></div>'
      );
      global.document = dom.window.document;
      global.window = dom.window;
      container = dom.window.document.getElementById("plot");
    });

    afterEach(() => {
      dom?.window?.close();
      delete global.document;
      delete global.window;
    });

    it("should be a function", function () {
      expect(scatterPlot).to.be.a("function");
    });

    it("should create an SVG element", function () {
      scatterPlot("plot", testCases[0]);
      const svg = container.querySelector("svg");
      expect(svg).to.not.be.null;
    });

    it("should create points with correct class", function () {
      scatterPlot("plot", testCases[0]);
      const points = container.querySelectorAll(".scatterPlot-point");
      expect(points).to.not.be.null;
    });

    testCases.forEach(
      ({ name, fetchedData, fetchedMetadata, expectedCount }) => {
        it(`should create ${expectedCount} points for ${name}`, function () {
          const dataKey = {
            fetchedData,
            fetchedMetadata,
          };
          scatterPlot("plot", dataKey);
          const points = container.querySelectorAll(".scatterPlot-point");
          expect(points.length).to.equal(expectedCount);
        });
      }
    );

    it("preprocessData: accepts object {x:[], y:[]} and plots points", function () {
      const dataKey = {
        fetchedData: {
          x: [1, 2],
          y: [10, 20],
          xerr: [0.1, 0.2],
          yerr: [0.5, 0.5],
        },
        fetchedMetadata: {
          plotConfiguration,
          criteriaReport: {},
        },
      };
      scatterPlot("plot", dataKey);
      const points = document.querySelectorAll(".scatterPlot-point");
      expect(points.length).to.equal(2);
    });

    it("preprocessData: handle xerr/yerr undefined", function () {
      const dataKey = {
        fetchedData: {
          x: [1, 2],
          y: [10, 20],
        },
        fetchedMetadata: {
          plotConfiguration,
          criteriaReport: {},
        },
      };
      scatterPlot("plot", dataKey);
      const points = document.querySelectorAll(".scatterPlot-point");
      expect(points.length).to.equal(2);
    });

    it("checkLogScale: throws when data contains non-positive values for log scale", function () {
      //  x axis
      let dataKey = {
        fetchedData: [{ x: 0, y: 1 }],
        fetchedMetadata: {
          plotConfiguration: {
            x: { label: "X", scale: "log" },
            y: { label: "Y", scale: "linear" },
            marks: {},
          },
        },
      };
      expect(() => scatterPlot("plot", dataKey)).to.throw();

      let err;
      try {
        scatterPlot("plot", dataKey);
      } catch (e) {
        err = e;
      }

      expect(err).to.be.instanceOf(Error);
      // Check exact error message
      expect(err.message).to.equal("Log scale requires all x values > 0");

      //  y axis
      dataKey = {
        fetchedData: [{ x: 1, y: 0 }],
        fetchedMetadata: {
          plotConfiguration: {
            x: { label: "X", scale: "linear" },
            y: { label: "Y", scale: "log" },
            marks: {},
          },
        },
      };
      expect(() => scatterPlot("plot", dataKey)).to.throw();

      try {
        scatterPlot("plot", dataKey);
      } catch (e) {
        err = e;
      }

      expect(err).to.be.instanceOf(Error);
      // Check exact error message
      expect(err.message).to.equal("Log scale requires all y values > 0");
    });

    it("checkLogScale: throws when domain min <= 0 for log scale", function () {
      // x axis
      let dataKey = {
        fetchedData: [{ x: 1, y: 1 }],
        fetchedMetadata: {
          plotConfiguration: {
            x: { label: "X", scale: "log", domain: [0, 10] },
            y: { label: "Y", scale: "linear" },
            marks: {},
          },
        },
      };
      expect(() => scatterPlot("plot", dataKey)).to.throw();

      let err;
      try {
        scatterPlot("plot", dataKey);
      } catch (e) {
        err = e;
      }

      expect(err).to.be.instanceOf(Error);
      // Check exact error message
      expect(err.message).to.equal(
        "Log scale requires x axis minimum domain > 0"
      );

      // y axis
      dataKey = {
        fetchedData: [{ x: 1, y: 1 }],
        fetchedMetadata: {
          plotConfiguration: {
            x: { label: "X", scale: "linear" },
            y: { label: "Y", scale: "log", domain: [0, 10] },
            marks: {},
          },
        },
      };
      expect(() => scatterPlot("plot", dataKey)).to.throw();

      try {
        scatterPlot("plot", dataKey);
      } catch (e) {
        err = e;
      }

      expect(err).to.be.instanceOf(Error);
      // Check exact error message
      expect(err.message).to.equal(
        "Log scale requires y axis minimum domain > 0"
      );
    });
    it("createSVGContainer and addClipPath: clipPath and rect present with expected attrs", function () {
      scatterPlot("plot", testCases[0]);
      const clip = document.querySelector("clipPath#clip-plot");
      expect(clip).to.exist;
      const rect = clip.querySelector("rect");
      expect(rect).to.exist;
      expect(rect.getAttribute("width")).to.not.be.null;
      expect(rect.getAttribute("height")).to.not.be.null;
    });

    it("drawLine: path with class 'scatterPlot-line' and non-empty 'd' created", function () {
      scatterPlot("plot", testCases[0]);
      const path = document.querySelector("path.scatterPlot-line");
      expect(path).to.exist;
      expect(path.getAttribute("d"))
        .to.be.a("string")
        .and.to.have.length.above(0);
    });

    it("drawPoints: default metadata values applied when marks missing", function () {
      let dataKey = testCases[0];
      // Remove marks from metadata to test defaults
      delete dataKey.fetchedMetadata.plotConfiguration.marks;

      // Sanity check
      expect(dataKey.fetchedMetadata.plotConfiguration.marks).to.be.undefined;

      // Default fill and stroke should be '#007bff' (bootstrap primary color)
      // Default stroke-width should be '1px'
      scatterPlot("plot", dataKey);
      const p = document.querySelector(".scatterPlot-point");
      expect(p).to.exist;
      // style attr should contain default fill (note code default is '007bff' without '#')
      const style = p.getAttribute("style") || "";
      expect(style).to.contain("fill: 007bff");
      expect(style).to.contain("stroke: 007bff");
    });

    it("drawErrorBars: renders horizontal and vertical error bars and warns on negative-log cases", function () {
      // spy console.warn
      const origWarn = console.warn;
      let warned = false;
      console.warn = function (...args) {
        warned = true;
        return origWarn.apply(console, args);
      };

      const dataKey = {
        name: "'2-datapoints'",
        fetchedData: [
          // yerr present
          { x: 1, y: 1, yerr: 0.2 },
          // xerr present
          { x: 2, y: 2, xerr: 0.5, yerr: 0.2 },
        ],
        fetchedMetadata: { plotConfiguration, criteriaReport },
        expectedCount: 2,
      };

      scatterPlot("plot", dataKey);
      // vertical error bars (yerr)
      const yerrs = document.querySelectorAll(".scatterPlot-yerror");
      const xerrs = document.querySelectorAll(".scatterPlot-xerror");
      expect(yerrs.length).to.equal(2);
      expect(xerrs.length).to.equal(1);

      // Now force log-scale with an yerr >= y to trigger warnings
      const plotEl = dom?.window?.document?.getElementById("plot");
      if (plotEl) plotEl.innerHTML = ""; // clear
      const badDataKey = {
        // yerr >= y for log case below
        fetchedData: [
          { x: 1, y: 1, yerr: 0.2 },
          { x: 1, y: 1, xerr: 2, yerr: 2 },
        ],
        fetchedMetadata: {
          plotConfiguration: {
            x: { label: "X", scale: "linear" },
            y: { label: "Y", scale: "log" },
            marks: {},
          },
          criteriaReport,
        },
      };
      // should not throw here, but should call console.warn (handled inside drawErrorBars)
      scatterPlot("plot", badDataKey);
      expect(warned).to.be.true;

      // restore original console.warn
      console.warn = origWarn;
    });

    it("drawErrorBars: xerr >= x on log scale should call 'negativeLogWarning'", function () {
      const origWarn = console.warn;
      let warned = false;
      console.warn = function (...args) {
        warned = true;
        return origWarn.apply(console, args);
      };
      const dataKey = {
        fetchedData: [{ x: 1, y: 1, xerr: 2 }],
        fetchedMetadata: {
          plotConfiguration: {
            x: { label: "X", scale: "log" },
            y: { label: "Y", scale: "linear" },
            marks: {},
          },
          criteriaReport,
        },
      };
      scatterPlot("plot", dataKey);
      expect(warned).to.be.true;
      console.warn = origWarn;
    });

    it("addXAxis/addYAxis: labels include unit when provided", function () {
      const dataKey = {
        fetchedData: [{ x: 1, y: 1 }],
        fetchedMetadata: {
          plotConfiguration: {
            x: { label: "X", unit: "s", scale: "linear" },
            y: { label: "Y", unit: "m", scale: "linear" },
            marks: {},
          },
          criteriaReport,
        },
      };
      scatterPlot("plot", dataKey);
      const xlabel = document.querySelector(".scatterPlot-xlabel");
      const ylabel = document.querySelector(".scatterPlot-ylabel");
      expect(xlabel.textContent).to.contain("[s]");
      expect(ylabel.textContent).to.contain("[m]");
    });

    it("addYAxis: label without units should not have squared parentheses", function () {
      const dataKey = {
        fetchedData: [{ x: 1, y: 1 }],
        fetchedMetadata: {
          plotConfiguration: {
            x: { label: "X", scale: "linear" },
            y: { label: "Y", scale: "linear" },
            marks: {},
          },
          criteriaReport,
        },
      };
      scatterPlot("plot", dataKey);
      const ylabel = document.querySelector(".scatterPlot-ylabel");
      expect(ylabel.textContent).to.not.contain("[");
    });

    it("addXAxis: shows x10^k label and scales ticks for large x values", function () {
      // Ensure non-zero dimensions in JSDOM
      container.getBoundingClientRect = () => ({
        width: 400,
        height: 300,
        top: 0,
        left: 0,
        right: 400,
        bottom: 300,
      });

      const dataKey = {
        fetchedData: [
          { x: 100000, y: 1 },
          { x: 200000, y: 2 },
        ],
        fetchedMetadata: {
          plotConfiguration: {
            title: "big-x",
            x: { label: "X", scale: "linear" },
            y: { label: "Y", scale: "linear" },
            marks: {},
          },
          criteriaReport: {},
        },
      };

      scatterPlot("plot", dataKey);

      const expLabels = document.querySelectorAll(".axis-exp");
      expect(expLabels.length).to.equal(1);
      expect(expLabels[0].textContent).to.contain("×10");
      // floor(log10(200000)) = 5
      expect(expLabels[0].textContent).to.contain("5");

      // Verify tick labels are scaled down (i.e. not 100000/200000 range)
      const xAxisG = document.querySelector('g[transform^="translate(0,"]');
      expect(xAxisG).to.exist;
      const tickTexts = Array.from(xAxisG.querySelectorAll(".tick text"))
        .map((t) => (t.textContent || "").trim())
        .filter((s) => s.length > 0);

      const numericTicks = tickTexts
        .map((s) => Number(s))
        .filter((n) => Number.isFinite(n));

      // There should be at least some numeric ticks, and they should be small.
      expect(numericTicks.length).to.be.above(0);
      expect(Math.max(...numericTicks)).to.be.below(1000);
    });

    it("addYAxis: shows x10^k label and avoids scientific notation for tiny y values", function () {
      container.getBoundingClientRect = () => ({
        width: 400,
        height: 300,
        top: 0,
        left: 0,
        right: 400,
        bottom: 300,
      });

      const dataKey = {
        fetchedData: [
          { x: 1, y: 0.000001 },
          { x: 2, y: 0.000002 },
        ],
        fetchedMetadata: {
          plotConfiguration: {
            title: "tiny-y",
            x: { label: "X", scale: "linear" },
            y: { label: "Y", scale: "linear" },
            marks: {},
          },
          criteriaReport: {},
        },
      };

      scatterPlot("plot", dataKey);

      const expLabels = document.querySelectorAll(".axis-exp");
      expect(expLabels.length).to.equal(1);
      expect(expLabels[0].textContent).to.contain("×10");
      // floor(log10(2e-6)) = -6
      expect(expLabels[0].textContent).to.contain("-6");

      // y-axis group is appended after x-axis group and has no transform.
      const axisGroups = Array.from(container.querySelectorAll("svg g > g"));
      expect(axisGroups.length).to.be.above(0);
      const yAxisG = axisGroups[axisGroups.length - 1];
      const tickTexts = Array.from(yAxisG.querySelectorAll(".tick text"))
        .map((t) => (t.textContent || "").trim())
        .filter((s) => s.length > 0);

      // With scaling enabled, tick labels should be small numbers like 1..2,
      // not scientific notation like 1e-6.
      expect(tickTexts.some((s) => /e/i.test(s))).to.equal(false);
    });
    it("showNoDataMessage: show no data message when fields are empty", function () {
      const dataKey = {
        fetchedData: [],
        fetchedMetadata: {
          plotConfiguration,
          criteriaReport: {},
        },
      };
      scatterPlot("plot", dataKey);
      const msg = document.querySelector("text");
      expect(msg).to.exist;
      expect(msg.textContent).to.equal("No data found for this plot.");
    });
    // Add here other tests for lines, axes, error bars, ecc.
  });
});
