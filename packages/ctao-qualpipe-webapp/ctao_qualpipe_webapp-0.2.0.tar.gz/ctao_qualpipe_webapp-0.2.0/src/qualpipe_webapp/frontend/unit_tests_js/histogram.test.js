import { expect } from "chai";
import { JSDOM } from "jsdom";
import { histogram1DPlot } from "../static/js/histogram.js";

let d3;

const plotConfiguration = {
    x: { label: "Value", scale: "linear", unit: "units" },
    y: { label: "Count", scale: "linear" },
    title: "Test Histogram",
    bins: 10,
    marks: { fill: "007bff", stroke: "007bff", strokeWidth: 1, opacity: 0.8 },
};

const criteriaReport = {
    RangeCriterion: {
        config: {
            max_value: 100,
            min_value: 0,
        },
        result: true,
    },
};

describe("Tests for 'histogram.js':", () => {
    before(async () => {
        d3 = (await import("d3")).default || (await import("d3"));
    });

    describe("histogram1DPlot", function () {
        let dom, container;

        beforeEach(() => {
            dom = new JSDOM(
                '<div id="plot" style="width:800px;height:600px;"></div>'
            );
            global.document = dom.window.document;
            global.window = dom.window;
            global.window.d3 = d3;
            container = dom.window.document.getElementById("plot");
        });

        afterEach(() => {
            dom?.window?.close();
            delete global.document;
            delete global.window;
        });

        it("should be a function", function () {
            expect(histogram1DPlot).to.be.a("function");
        });

        it("should create an SVG element", function () {
            const dataKey = {
                fetchedData: { x: [1, 2, 3, 4, 5] },
                fetchedMetadata: { plotConfiguration, criteriaReport },
            };
            histogram1DPlot("plot", dataKey);
            const svg = container.querySelector("svg");
            expect(svg).to.not.be.null;
        });

        it("should create histogram bars with correct class", function () {
            const dataKey = {
                fetchedData: { x: [1, 2, 3, 4, 5] },
                fetchedMetadata: { plotConfiguration, criteriaReport },
            };
            histogram1DPlot("plot", dataKey);
            const bars = container.querySelectorAll(".histogram1d-bar");
            expect(bars).to.not.be.null;
            expect(bars.length).to.be.greaterThan(0);
        });

        it("should create histogram title", function () {
            const dataKey = {
                fetchedData: { x: [1, 2, 3, 4, 5] },
                fetchedMetadata: { plotConfiguration, criteriaReport },
            };
            histogram1DPlot("plot", dataKey);
            const title = container.querySelector(".histogram1d-title");
            expect(title).to.not.be.null;
            expect(title.textContent).to.equal("Test Histogram");
        });

        it("should handle data with 'values' property", function () {
            const dataKey = {
                fetchedData: { values: [10, 20, 30, 40, 50] },
                fetchedMetadata: { plotConfiguration, criteriaReport },
            };
            histogram1DPlot("plot", dataKey);
            const bars = container.querySelectorAll(".histogram1d-bar");
            expect(bars.length).to.be.greaterThan(0);
        });

        it("should handle data with 'x' property (array format)", function () {
            const dataKey = {
                fetchedData: { x: [5, 10, 15, 20, 25] },
                fetchedMetadata: { plotConfiguration, criteriaReport },
            };
            histogram1DPlot("plot", dataKey);
            const bars = container.querySelectorAll(".histogram1d-bar");
            expect(bars.length).to.be.greaterThan(0);
        });

        it("should create the correct number of bins", function () {
            const customConfig = {
                ...plotConfiguration,
                bins: 5,
            };
            const dataKey = {
                fetchedData: { x: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] },
                fetchedMetadata: {
                    plotConfiguration: customConfig,
                    criteriaReport,
                },
            };
            histogram1DPlot("plot", dataKey);
            const bars = container.querySelectorAll(".histogram1d-bar");
            // d3.bin() may create numBins or numBins+1 bins depending on threshold values
            expect(bars.length).to.be.within(5, 6);
        });

        it("should add x-axis with label and unit", function () {
            const dataKey = {
                fetchedData: { x: [1, 2, 3, 4, 5] },
                fetchedMetadata: { plotConfiguration, criteriaReport },
            };
            histogram1DPlot("plot", dataKey);
            const xLabel = container.querySelector(".histogram1d-xlabel");
            expect(xLabel).to.not.be.null;
            expect(xLabel.textContent).to.equal("Value [units]");
        });

        it("should add y-axis with label", function () {
            const dataKey = {
                fetchedData: { x: [1, 2, 3, 4, 5] },
                fetchedMetadata: { plotConfiguration, criteriaReport },
            };
            histogram1DPlot("plot", dataKey);
            const yLabel = container.querySelector(".histogram1d-ylabel");
            expect(yLabel).to.not.be.null;
            expect(yLabel.textContent).to.equal("Count");
        });

        it("should display total count label", function () {
            const dataKey = {
                fetchedData: { x: [1, 2, 3, 4, 5] },
                fetchedMetadata: { plotConfiguration, criteriaReport },
            };
            histogram1DPlot("plot", dataKey);
            const totalLabel = container.querySelector(".histogram1d-total");
            expect(totalLabel).to.not.be.null;
            expect(totalLabel.textContent).to.include("Total:");
        });

        it("should handle log scale on x-axis", function () {
            const logConfig = {
                ...plotConfiguration,
                x: { ...plotConfiguration.x, scale: "log" },
            };
            const dataKey = {
                fetchedData: { x: [1, 10, 100, 1000] },
                fetchedMetadata: {
                    plotConfiguration: logConfig,
                    criteriaReport,
                },
            };
            // Should not throw
            expect(() => histogram1DPlot("plot", dataKey)).to.not.throw();
            const bars = container.querySelectorAll(".histogram1d-bar");
            expect(bars.length).to.be.greaterThan(0);
        });

        it("should handle log scale on y-axis", function () {
            const logConfig = {
                ...plotConfiguration,
                y: { ...plotConfiguration.y, scale: "log" },
            };
            const dataKey = {
                fetchedData: { x: [1, 2, 3, 4, 5] },
                fetchedMetadata: {
                    plotConfiguration: logConfig,
                    criteriaReport,
                },
            };
            // Should not throw
            expect(() => histogram1DPlot("plot", dataKey)).to.not.throw();
            const bars = container.querySelectorAll(".histogram1d-bar");
            expect(bars.length).to.be.greaterThan(0);
        });

        it("should handle custom x domain", function () {
            const customConfig = {
                ...plotConfiguration,
                x: { ...plotConfiguration.x, domain: [0, 100] },
            };
            const dataKey = {
                fetchedData: { x: [10, 20, 30, 40, 50] },
                fetchedMetadata: {
                    plotConfiguration: customConfig,
                    criteriaReport,
                },
            };
            histogram1DPlot("plot", dataKey);
            const bars = container.querySelectorAll(".histogram1d-bar");
            expect(bars.length).to.be.greaterThan(0);
        });

        it("should handle custom y domain", function () {
            const customConfig = {
                ...plotConfiguration,
                y: { ...plotConfiguration.y, domain: [0, 10] },
            };
            const dataKey = {
                fetchedData: { x: [1, 2, 3, 4, 5] },
                fetchedMetadata: {
                    plotConfiguration: customConfig,
                    criteriaReport,
                },
            };
            histogram1DPlot("plot", dataKey);
            const bars = container.querySelectorAll(".histogram1d-bar");
            expect(bars.length).to.be.greaterThan(0);
        });

        it("should show outliers count when data is outside domain", function () {
            const customConfig = {
                ...plotConfiguration,
                x: { ...plotConfiguration.x, domain: [10, 50] },
            };
            const dataKey = {
                fetchedData: { x: [1, 5, 10, 20, 30, 40, 50, 60, 100] },
                fetchedMetadata: {
                    plotConfiguration: customConfig,
                    criteriaReport,
                },
            };
            histogram1DPlot("plot", dataKey);
            const outliersLabel = container.querySelector(".histogram1d-outliers");
            expect(outliersLabel).to.not.be.null;
            expect(outliersLabel.textContent).to.include("Out of range:");
        });

        it("should not show outliers label when all data is in range", function () {
            const dataKey = {
                fetchedData: { x: [1, 2, 3, 4, 5] },
                fetchedMetadata: { plotConfiguration, criteriaReport },
            };
            histogram1DPlot("plot", dataKey);
            const outliersLabel = container.querySelector(".histogram1d-outliers");
            expect(outliersLabel).to.be.null;
        });

        it("should use default title when not provided", function () {
            const configNoTitle = { ...plotConfiguration };
            delete configNoTitle.title;
            const dataKey = {
                fetchedData: { x: [1, 2, 3, 4, 5] },
                fetchedMetadata: {
                    plotConfiguration: configNoTitle,
                    criteriaReport,
                },
            };
            histogram1DPlot("plot", dataKey);
            const title = container.querySelector(".histogram1d-title");
            expect(title.textContent).to.equal("Histogram1D");
        });

        it("should use default bins (20) when not provided", function () {
            const configNoBins = { ...plotConfiguration };
            delete configNoBins.bins;
            const dataKey = {
                fetchedData: { x: Array.from({ length: 100 }, (_, i) => i) },
                fetchedMetadata: {
                    plotConfiguration: configNoBins,
                    criteriaReport,
                },
            };
            histogram1DPlot("plot", dataKey);
            const bars = container.querySelectorAll(".histogram1d-bar");
            // d3.bin() may create numBins or numBins+1 bins depending on threshold values
            expect(bars.length).to.be.within(20, 21);
        });

        it("should apply custom bar styling from metadata", function () {
            const customConfig = {
                ...plotConfiguration,
                marks: {
                    fill: "ff0000",
                    stroke: "00ff00",
                    strokeWidth: 2,
                    opacity: 0.5,
                },
            };
            const dataKey = {
                fetchedData: { x: [1, 2, 3, 4, 5] },
                fetchedMetadata: {
                    plotConfiguration: customConfig,
                    criteriaReport,
                },
            };
            histogram1DPlot("plot", dataKey);
            const bar = container.querySelector(".histogram1d-bar");
            expect(bar).to.not.be.null;
            const style = bar.getAttribute("style");
            expect(style).to.include("fill: ff0000");
            expect(style).to.include("stroke: 00ff00");
        });

        it("should use default bar styling when marks not provided", function () {
            const configNoMarks = { ...plotConfiguration };
            delete configNoMarks.marks;
            const dataKey = {
                fetchedData: { x: [1, 2, 3, 4, 5] },
                fetchedMetadata: {
                    plotConfiguration: configNoMarks,
                    criteriaReport,
                },
            };
            histogram1DPlot("plot", dataKey);
            const bar = container.querySelector(".histogram1d-bar");
            expect(bar).to.not.be.null;
            const style = bar.getAttribute("style");
            expect(style).to.include("fill: #007bff");
        });

        it("should create clipPath for the plot", function () {
            const dataKey = {
                fetchedData: { x: [1, 2, 3, 4, 5] },
                fetchedMetadata: { plotConfiguration, criteriaReport },
            };
            histogram1DPlot("plot", dataKey);
            const clipPath = container.querySelector("clipPath");
            expect(clipPath).to.not.be.null;
            expect(clipPath.getAttribute("id")).to.equal("clip-plot");
        });

        it("should handle empty data gracefully", function () {
            const dataKey = {
                fetchedData: { x: [] },
                fetchedMetadata: { plotConfiguration, criteriaReport },
            };
            // Should not throw
            expect(() => histogram1DPlot("plot", dataKey)).to.not.throw();
        });

        it("should handle single data point", function () {
            const dataKey = {
                fetchedData: { x: [42] },
                fetchedMetadata: { plotConfiguration, criteriaReport },
            };
            histogram1DPlot("plot", dataKey);
            const bars = container.querySelectorAll(".histogram1d-bar");
            expect(bars.length).to.be.greaterThan(0);
        });

        it("should handle data with negative values for linear scale", function () {
            const dataKey = {
                fetchedData: { x: [-10, -5, 0, 5, 10] },
                fetchedMetadata: { plotConfiguration, criteriaReport },
            };
            histogram1DPlot("plot", dataKey);
            const bars = container.querySelectorAll(".histogram1d-bar");
            expect(bars.length).to.be.greaterThan(0);
        });

        it("should handle very large values", function () {
            const dataKey = {
                fetchedData: { x: [1e6, 2e6, 3e6, 4e6, 5e6] },
                fetchedMetadata: { plotConfiguration, criteriaReport },
            };
            histogram1DPlot("plot", dataKey);
            const bars = container.querySelectorAll(".histogram1d-bar");
            expect(bars.length).to.be.greaterThan(0);
        });

        it("should handle very small values", function () {
            const dataKey = {
                fetchedData: { x: [1e-6, 2e-6, 3e-6, 4e-6, 5e-6] },
                fetchedMetadata: { plotConfiguration, criteriaReport },
            };
            histogram1DPlot("plot", dataKey);
            const bars = container.querySelectorAll(".histogram1d-bar");
            expect(bars.length).to.be.greaterThan(0);
        });

        it("should add exponent label for large values on x-axis", function () {
            const dataKey = {
                fetchedData: { x: [1e5, 2e5, 3e5, 4e5, 5e5] },
                fetchedMetadata: { plotConfiguration, criteriaReport },
            };
            histogram1DPlot("plot", dataKey);
            const expLabel = container.querySelector(".axis-exp");
            expect(expLabel).to.not.be.null;
            expect(expLabel.textContent).to.include("×10");
        });

        it("should handle log scale with positive values only", function () {
            const logConfig = {
                ...plotConfiguration,
                x: { ...plotConfiguration.x, scale: "log" },
            };
            const dataKey = {
                fetchedData: { x: [0.1, 1, 10, 100] },
                fetchedMetadata: {
                    plotConfiguration: logConfig,
                    criteriaReport,
                },
            };
            histogram1DPlot("plot", dataKey);
            const bars = container.querySelectorAll(".histogram1d-bar");
            expect(bars.length).to.be.greaterThan(0);
        });

        it("should clear previous plot content", function () {
            const dataKey = {
                fetchedData: { x: [1, 2, 3] },
                fetchedMetadata: { plotConfiguration, criteriaReport },
            };
            // Plot once
            histogram1DPlot("plot", dataKey);
            const firstSvg = container.querySelector("svg");
            expect(firstSvg).to.not.be.null;

            // Plot again
            histogram1DPlot("plot", dataKey);
            const allSvgs = container.querySelectorAll("svg");
            // Should only have one SVG (previous cleared)
            expect(allSvgs.length).to.equal(1);
        });
    });
});
