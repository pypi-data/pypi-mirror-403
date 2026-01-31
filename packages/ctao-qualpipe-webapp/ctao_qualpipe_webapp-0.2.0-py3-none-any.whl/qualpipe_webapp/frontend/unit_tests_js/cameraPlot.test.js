import { expect } from "chai";
import { JSDOM } from "jsdom";
import sinon from "sinon";
import esmock from "esmock";

import { LST_CAMERA_PIXEL_COUNT } from "../static/js/config.js";

describe("Tests for 'cameraPlot.js':", function () {
    let dom;
    let d3;

    beforeEach(() => {
        dom = new JSDOM(
            `
      <html>
        <body>
          <div id="plot-1_cameraView"></div>
        </body>
      </html>
      `,
            { url: "http://localhost" }
        );
        global.window = dom.window;
        global.document = dom.window.document;
    });

    before(async () => {
        d3 = (await import("d3")).default || (await import("d3"));
        // d3-hexbin will be loaded via d3loader.js in cameraPlot.js
    });

    afterEach(() => {
        sinon.restore();
        dom?.window?.close();
        delete global.window;
        delete global.document;
    });

    async function importCameraPlotWithCriteriaStubs({ updateBadgeCriteria, badgeCriteriaNone }) {
        const criteriaAbs = new URL("../static/js/criteriaPlot.js", import.meta.url)
            .pathname;

        const cameraPlot = await esmock(
            "../static/js/cameraPlot.js",
            {
                [criteriaAbs]: {
                    updateBadgeCriteria,
                    badgeCriteriaNone,
                },
            },
            { url: import.meta.url }
        );

        return cameraPlot;
    }

    it("updateCameraView should throw when container is missing", async function () {
        const updateBadgeCriteria = sinon.stub();
        const badgeCriteriaNone = sinon.stub();
        const { updateCameraView } = await importCameraPlotWithCriteriaStubs({
            updateBadgeCriteria,
            badgeCriteriaNone,
        });

        try {
            await updateCameraView("does-not-exist", { fetchedData: { x: [] } });
            expect.fail("Should have thrown");
        } catch (err) {
            expect(err.message).to.include("not found");
        }
    });

    it("updateCameraView should warn and return when viewer is missing", async function () {
        const updateBadgeCriteria = sinon.stub();
        const badgeCriteriaNone = sinon.stub();
        const warnStub = sinon.stub(console, "warn");

        const { updateCameraView } = await importCameraPlotWithCriteriaStubs({
            updateBadgeCriteria,
            badgeCriteriaNone,
        });

        // No __cameraViewer attached
        await updateCameraView("plot-1_cameraView", {
            fetchedData: { x: new Array(LST_CAMERA_PIXEL_COUNT).fill(0), gain: [] },
            fetchedMetadata: { plotConfiguration: { title: "t" } },
        });

        expect(warnStub.called).to.equal(true);
        expect(updateBadgeCriteria.called).to.equal(false);
        expect(badgeCriteriaNone.called).to.equal(false);
    });

    it("updateCameraView should draw pixels, set title, set dataUnit, and badge NONE when criteriaReport is missing", async function () {
        const updateBadgeCriteria = sinon.stub();
        const badgeCriteriaNone = sinon.stub();

        const { updateCameraView } = await importCameraPlotWithCriteriaStubs({
            updateBadgeCriteria,
            badgeCriteriaNone,
        });

        const container = document.getElementById("plot-1_cameraView");
        container.innerHTML =
            '<svg width="600" height="600" viewBox="0 0 600 600"><g></g></svg>';

        const viewer = {
            ready: sinon.stub().resolves(),
            draw_pixels: sinon.spy(),
        };
        container.__cameraViewer = viewer;

        const x = Array.from({ length: LST_CAMERA_PIXEL_COUNT }, (_, i) => i + 1);
        const gain = [1, 2, 3];
        const sampleRange = [0, 10];

        await updateCameraView("plot-1_cameraView", {
            fetchedData: { x, gain },
            fetchedMetadata: {
                plotConfiguration: {
                    title: "My Camera Title",
                    x: { unit: "pe", domain: sampleRange },
                },
                // criteriaReport intentionally omitted
            },
        });

        expect(viewer.ready.calledOnce).to.equal(true);
        expect(viewer.draw_pixels.calledOnce).to.equal(true);
        const args = viewer.draw_pixels.firstCall.args;
        expect(args[0]).to.have.lengthOf(LST_CAMERA_PIXEL_COUNT);
        expect(args[1]).to.deep.equal(sampleRange);
        expect(args[2]).to.deep.equal(gain);

        expect(viewer.dataUnit).to.equal("pe");

        const titleEl = container.querySelector("text.cameraview-title");
        expect(titleEl).to.exist;
        expect(titleEl.textContent).to.equal("My Camera Title");

        expect(badgeCriteriaNone.calledOnce).to.equal(true);
        expect(updateBadgeCriteria.called).to.equal(false);
    });

    it("updateCameraView should call updateBadgeCriteria when criteriaReport is present", async function () {
        const updateBadgeCriteria = sinon.stub();
        const badgeCriteriaNone = sinon.stub();

        const { updateCameraView } = await importCameraPlotWithCriteriaStubs({
            updateBadgeCriteria,
            badgeCriteriaNone,
        });

        const container = document.getElementById("plot-1_cameraView");
        container.innerHTML =
            '<svg width="600" height="600" viewBox="0 0 600 600"><g></g></svg>';

        const viewer = {
            ready: sinon.stub().resolves(),
            draw_pixels: sinon.spy(),
        };
        container.__cameraViewer = viewer;

        const x = Array.from({ length: LST_CAMERA_PIXEL_COUNT }, (_, i) => i + 1);

        await updateCameraView("plot-1_cameraView", {
            fetchedData: { x },
            fetchedMetadata: {
                plotConfiguration: { title: "t", x: { unit: "" } },
                criteriaReport: {
                    SomeCriterion: { config: {}, result: true },
                },
            },
        });

        expect(updateBadgeCriteria.calledOnce).to.equal(true);
        const callArgs = updateBadgeCriteria.firstCall.args;
        expect(callArgs[0]).to.equal("plot-1_cameraView");
        expect(callArgs[2]).to.equal("SomeCriterion");
        expect(badgeCriteriaNone.called).to.equal(false);
    });

    describe("__test__ helpers", function () {
        it("parsePixelLine should return null for invalid input and parse valid lines", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            const mapping = { format: { id: 0, x: 1, y: 2 } };
            expect(CameraViewer.parsePixelLine([], mapping)).to.equal(null);
            expect(CameraViewer.parsePixelLine(["a", "b", "c"], mapping)).to.equal(null);

            const parsed = CameraViewer.parsePixelLine(["12", "1.5", "-2.25"], mapping);
            expect(parsed).to.deep.equal({ ip: 12, xp: 1.5, yp: -2.25 });
        });

        it("applyCoordinateTransforms should mirror and rotate", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            const cfg = {
                camera_mirroring: [true, false],
                camera_rotation: 90,
            };
            const res = CameraViewer.applyCoordinateTransforms(1, 0, cfg);
            // mirror x => -1, rotate 90deg around origin: (-1,0) -> (0,1)
            expect(res.x).to.be.closeTo(0, 1e-9);
            expect(res.y).to.be.closeTo(1, 1e-9);
        });

        it("updateBounds should track mins/maxes", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            let b = { xm: null, xM: null, ym: null, yM: null };
            b = CameraViewer.updateBounds(b, 5, 10);
            b = CameraViewer.updateBounds(b, -2, 7);
            b = CameraViewer.updateBounds(b, 3, 20);
            expect(b).to.deep.equal({ xm: -2, xM: 5, ym: 7, yM: 20 });
        });

        it("normalizeAndCreatePixels should produce pixel geometry and mapping", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            const data = [
                [1, 0, 0],
                [2, 10, 5],
            ];
            const bounds = { xm: 0, xM: 10, ym: 0, yM: 5 };
            const cfg = { width: 100, hexRadius: 6 };

            const out = CameraViewer.normalizeAndCreatePixels(data, bounds, cfg);
            expect(out.count).to.equal(2);
            expect(out.pixels).to.have.lengthOf(2);
            expect(out.pixels_mapping[1]).to.deep.equal([0, 0]);
            expect(out.pixels_mapping[2]).to.deep.equal([10, 5]);
            expect(out.pixels[0][0]).to.have.lengthOf(3);
            expect(out.pixels[0][0][2]).to.equal(1);
        });

        it("getExpScaleInfo and makeScaledTickFormat should scale large numbers", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { getExpScaleInfo, makeScaledTickFormat } = mod.__test__;

            // Minimal scale-like object
            const scale = { domain: () => [0, 1e6] };
            const info = getExpScaleInfo(scale, "linear");
            expect(info.use).to.equal(true);
            expect(info.k).to.equal(6);

            const fmt = makeScaledTickFormat(6);
            expect(fmt(1e6)).to.equal("1");
        });

        it("addAxisExponentLabel should add ×10^k label", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { addAxisExponentLabel } = mod.__test__;

            // Provide d3 via window for d3loader
            global.window.d3 = d3;

            document.body.innerHTML = `<svg id="s" viewBox="0 0 200 200"><g id="g"></g></svg>`;
            const g = d3.select("#g");
            const scale = d3.scaleLinear().range([0, 100]).domain([0, 10]);

            addAxisExponentLabel(g, "x", 3, scale);
            const label = document.querySelector(".axis-exp");
            expect(label).to.exist;
            expect(label.textContent).to.include("×10");
            expect(label.textContent).to.include("3");
        });

        it("updateCameraTitle should create/update title element", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { updateCameraTitle } = mod.__test__;

            // Provide d3 via window for d3loader
            global.window.d3 = d3;

            document.body.innerHTML = `
        <div id="c">
          <svg width="600" height="400" viewBox="0 0 600 400"><g></g></svg>
        </div>
      `;

            updateCameraTitle("c", "Hello");
            const title = document.querySelector("#c text.cameraview-title");
            expect(title).to.exist;
            expect(title.textContent).to.equal("Hello");

            // Default title when null
            updateCameraTitle("c", null);
            expect(title.textContent).to.equal("Camera view");
        });

        it("addPaletteSelector should insert selector and trigger repaint on change", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { addPaletteSelector } = mod.__test__;

            // Provide d3 via window for d3loader
            global.window.d3 = d3;

            document.body.innerHTML = `<div id="plot-1_cameraView"></div>`;
            const container = document.getElementById("plot-1_cameraView");

            const viewer = {
                pixels_value: { 1: 0.1, 2: 0.9 },
                pixels: [[[0, 0, "1"]], [[0, 0, "2"]]],
                currentRange: [0, 1],
                normal_pixels: [1, 1],
                paint_pixels: sinon.spy(),
                updateGradient: sinon.spy(),
            };
            container.__cameraViewer = viewer;

            addPaletteSelector("plot-1_cameraView");
            const select = container.querySelector("select.palette-selector");
            expect(select).to.exist;

            // Simulate selecting a different palette
            select.value = "plasma";
            select.dispatchEvent(new window.Event("change", { bubbles: true }));

            expect(viewer.paint_pixels.calledOnce).to.equal(true);
            expect(viewer.updateGradient.calledOnce).to.equal(true);
        });
    });

    describe("CameraViewer methods (integration)", function () {
        beforeEach(() => {
            // JSDOM doesn't provide ResizeObserver
            global.ResizeObserver = class {
                constructor(cb) {
                    this._cb = cb;
                }
                observe() {
                    // Stub for testing - ResizeObserver not available in JSDOM
                }
                disconnect() {
                    // Stub for testing - ResizeObserver not available in JSDOM
                }
            };
        });

        afterEach(() => {
            delete global.ResizeObserver;
        });

        function setupViewerDom() {
            // Provide d3 via window for d3loader
            global.window.d3 = d3;

            document.body.innerHTML = `
        <div id="plot-1_cameraView" style="width: 300px; height: 300px;">
          <svg viewBox="0 0 700 700">
            <defs>
              <linearGradient id="grad"></linearGradient>
            </defs>
            <g class="legend"></g>
            <g id="root"></g>
          </svg>
        </div>
      `;

            const container = document.getElementById("plot-1_cameraView");
            container.getBoundingClientRect = () => ({ width: 300, height: 300 });

            const g = d3.select("#plot-1_cameraView svg").select("#root");
            return { container, g };
        }

        it("paint_pixels should color pixels and mark special hexagons", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            setupViewerDom();

            // Create 2 pixel paths in DOM
            const g = d3.select("#plot-1_cameraView svg").select("#root");
            g.append("path").attr("ID", "1");
            g.append("path").attr("ID", "2");

            const viewer = Object.create(CameraViewer);
            viewer.svg = g;
            viewer.div = "#plot-1_cameraView";

            viewer.paint_pixels([null, 5], [0, 10], [0, 1]);

            const p1 = document.querySelector('path[ID="1"]');
            const p2 = document.querySelector('path[ID="2"]');
            expect(p1.style.fill).to.equal("#BEBEBE");
            expect(p1.classList.contains("special_hexagon")).to.equal(true);
            expect(p2.style.fill).to.not.equal("");
            expect(p2.classList.contains("special_hexagon")).to.equal(false);
        });

        it("updateGradient should create stops when gradient exists", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            setupViewerDom();

            const viewer = Object.create(CameraViewer);
            viewer.div = "#plot-1_cameraView";

            viewer.updateGradient([0, 1]);

            const stops = document.querySelectorAll("#plot-1_cameraView #grad stop");
            expect(stops.length).to.be.greaterThan(0);
        });

        it("paint_legend should build axis and exponent label for large ranges", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            const { g } = setupViewerDom();

            const viewer = Object.create(CameraViewer);
            viewer.div = "#plot-1_cameraView";
            viewer.svg = g;
            viewer.configuration = {
                width: 500,
                height: 580,
                legend_width: 15,
                legend_heigth: 520,
                legend_margin: 60,
            };

            viewer.updateGradient = CameraViewer.updateGradient;

            viewer.paint_legend([0, 1e6]);

            // Axis group created
            expect(document.querySelector(".z.axis.legend")).to.exist;
            // Exponent label present for large scale
            expect(document.querySelector(".z.axis.legend .axis-exp")).to.exist;
            // Gradient updated
            expect(document.querySelectorAll("#plot-1_cameraView #grad stop").length).to.be.greaterThan(0);
        });

        it("scale should set width/height based on container", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            setupViewerDom();
            const svg = document.querySelector("#plot-1_cameraView svg");
            const g = d3.select(svg).select("#root");

            const viewer = Object.create(CameraViewer);
            viewer.div = "#plot-1_cameraView";
            viewer.svg = g;
            viewer.svgContainer = svg;
            viewer.configuration = {
                width: 500,
                height: 580,
                legend_width: 15,
                legend_margin: 60,
            };

            const ok = viewer.scale();
            expect(ok).to.equal(true);
            expect(svg.getAttribute("width")).to.be.a("string");
            expect(svg.getAttribute("height")).to.be.a("string");
        });

        it("get_mapping should parse mapping text via fetch", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            global.fetch = sinon.stub().resolves({
                text: async () =>
                    [
                        "# header",
                        "# header2",
                        "# header3",
                        "# header4",
                        "# header5",
                        "# header6",
                        "1 0 0",
                        "2 10 5",
                    ].join("\n"),
            });

            const viewer = Object.create(CameraViewer);
            viewer.configuration = {
                width: 100,
                hexRadius: 6,
                camera_mirroring: [false, false],
                camera_rotation: 0,
                mapping: {
                    url: "/static/mapping.txt",
                    skiplines: 6,
                    format: { id: 0, x: 1, y: 2 },
                },
            };

            await viewer.get_mapping();
            expect(viewer.pixels_count).to.equal(2);
            expect(Object.keys(viewer.pixels_mapping)).to.have.lengthOf(2);
        });

        it("draw_pixels should handle empty gain array", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            setupViewerDom();
            const g = d3.select("#plot-1_cameraView svg").select("#root");
            g.append("path").attr("ID", "1");

            const viewer = Object.create(CameraViewer);
            viewer.svg = g;
            viewer.div = "#plot-1_cameraView";
            viewer.configuration = {
                width: 500,
                height: 580,
                legend_width: 15,
                legend_heigth: 520,
                legend_margin: 60,
            };
            viewer.updateGradient = CameraViewer.updateGradient;

            // Test with empty gain array (valid path)
            viewer.draw_pixels([5], [0, 10], []);
            const p1 = document.querySelector('path[ID="1"]');
            expect(p1.style.fill).to.not.equal("");
        });
    });

    describe("Initialization functions", function () {
        beforeEach(() => {
            global.ResizeObserver = class {
                constructor(cb) { this._cb = cb; }
                observe() { /* Stub - JSDOM doesn't provide ResizeObserver */ }
                disconnect() { /* Stub - JSDOM doesn't provide ResizeObserver */ }
            };
        });

        afterEach(() => {
            delete global.ResizeObserver;
        });

        it("bootstrapCameraViews should initialize all camera view containers", async function () {
            global.window.d3 = d3;
            global.fetch = sinon.stub().resolves({
                text: async () => ["# h1", "# h2", "# h3", "# h4", "# h5", "# h6", "1 0 0"].join("\n"),
            });

            document.body.innerHTML = `
                <div id="plot-1_cameraView"></div>
                <div id="plot-2_cameraView"></div>
            `;

            const mod = await import("../static/js/cameraPlot.js");
            const { bootstrapCameraViews } = mod.__test__;

            bootstrapCameraViews();

            const c1 = document.getElementById("plot-1_cameraView");
            const c2 = document.getElementById("plot-2_cameraView");
            expect(c1.__cameraViewer).to.exist;
            expect(c2.__cameraViewer).to.exist;
        });

        it("initCameraView should warn when container not found", async function () {
            const warnStub = sinon.stub(console, "warn");

            const mod = await import("../static/js/cameraPlot.js");
            const { initCameraView } = mod.__test__;

            initCameraView("nonexistent-container");
            expect(warnStub.calledWith("Container not found for initialisation:", "nonexistent-container")).to.equal(true);
            warnStub.restore();
        });

        it("initCameraView should not reinitialize existing viewer", async function () {
            global.window.d3 = d3;
            global.fetch = sinon.stub().resolves({
                text: async () => ["# h1", "# h2", "# h3", "# h4", "# h5", "# h6", "1 0 0"].join("\n"),
            });

            document.body.innerHTML = `<div id="plot-test_cameraView"></div>`;

            const mod = await import("../static/js/cameraPlot.js");
            const { initCameraView } = mod.__test__;

            const container = document.getElementById("plot-test_cameraView");
            const existingViewer = { ready: sinon.stub() };
            container.__cameraViewer = existingViewer;

            initCameraView("plot-test_cameraView");

            // Should still be the same viewer object
            expect(container.__cameraViewer).to.equal(existingViewer);
        });

        it("preprocessData should throw when data length mismatches expected pixel count", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { preprocessData } = mod.__test__;

            const dataKey = {
                fetchedData: { x: [1, 2, 3] },
                fetchedMetadata: {},
            };

            expect(() => preprocessData(dataKey, 1855)).to.throw("Data length mismatch: expected 1855, got 3");
        });

        it("preprocessData should return data, gain, and sample_range", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { preprocessData } = mod.__test__;

            const dataKey = {
                fetchedData: { x: [1, 2], gain: [0.5, 0.6] },
                fetchedMetadata: { plotConfiguration: { x: { domain: [0, 10] } } },
            };

            const result = preprocessData(dataKey, 2);
            expect(result.data).to.deep.equal([1, 2]);
            expect(result.gain).to.deep.equal([0.5, 0.6]);
            expect(result.sample_range).to.deep.equal([0, 10]);
        });

        it("setupResizeObserver should disconnect previous observer if existing", async function () {
            global.window.d3 = d3;
            document.body.innerHTML = `<div id="plot-resize_cameraView"></div>`;

            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            const viewer = Object.create(CameraViewer);
            viewer.div = "#plot-resize_cameraView";

            const oldObserver = {
                disconnect: sinon.spy(),
                observe: sinon.spy(),
            };
            viewer.resizeObserver = oldObserver;

            // ResizeObserver is already stubbed in beforeEach
            viewer.setupResizeObserver();

            expect(oldObserver.disconnect.calledOnce).to.equal(true);
        });

        it("setupResizeObserver should return early if container not found", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            const viewer = Object.create(CameraViewer);
            viewer.div = "#nonexistent-container";
            viewer.resizeObserver = null;

            // Should not throw, just return early without creating new observer
            viewer.setupResizeObserver();
            expect(viewer.resizeObserver).to.be.null;
        });

        it("get_mapping should handle empty data case", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            global.fetch = sinon.stub().resolves({
                text: async () => ["# h1", "# h2", "# h3", "# h4", "# h5", "# h6"].join("\n"),
            });

            const viewer = Object.create(CameraViewer);
            viewer.configuration = {
                width: 100,
                hexRadius: 6,
                camera_mirroring: [false, false],
                camera_rotation: 0,
                mapping: {
                    url: "/static/mapping.txt",
                    skiplines: 6,
                    format: { id: 0, x: 1, y: 2 },
                },
            };

            await viewer.get_mapping();

            expect(viewer.pixels).to.deep.equal([]);
            expect(viewer.pixels_count).to.equal(0);
        });

        it("scale should return false and schedule retry when svg is null", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            const clock = sinon.useFakeTimers();

            const viewer = Object.create(CameraViewer);
            viewer.svg = null;

            const result = viewer.scale();

            expect(result).to.equal(false);

            clock.restore();
        });

        it("scale should set transform to null when no baseTransform", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            global.window.d3 = d3;
            document.body.innerHTML = `
                <div id="plot-transform_cameraView" style="width: 300px; height: 300px;">
                    <svg viewBox="0 0 700 700"></svg>
                </div>
            `;

            const container = document.getElementById("plot-transform_cameraView");
            container.getBoundingClientRect = () => ({ width: 300, height: 300 });

            const svg = container.querySelector("svg");
            const g = d3.select(svg).append("g");

            const viewer = Object.create(CameraViewer);
            viewer.div = "#plot-transform_cameraView";
            viewer.svg = g;
            viewer.svgContainer = svg;
            viewer.configuration = {
                width: 500,
                height: 580,
                legend_width: 15,
                legend_margin: 60,
            };
            viewer.baseTransform = ""; // Empty baseTransform

            viewer.scale();

            expect(g.attr("transform")).to.be.null;
        });

        it("updateGradient should warn when gradient not found", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            global.window.d3 = d3;
            document.body.innerHTML = `<div id="plot-grad_cameraView"></div>`;

            const warnStub = sinon.stub(console, "warn");

            const viewer = Object.create(CameraViewer);
            viewer.div = "#plot-grad_cameraView";

            viewer.updateGradient([0, 100]);

            expect(warnStub.calledWith("Gradient not found")).to.equal(true);
            warnStub.restore();
        });
    });

    describe("CameraViewer build_camera and SVG creation", function () {
        beforeEach(() => {
            global.ResizeObserver = class {
                constructor(cb) { this._cb = cb; }
                observe() { /* Stub - JSDOM doesn't provide ResizeObserver */ }
                disconnect() { /* Stub - JSDOM doesn't provide ResizeObserver */ }
            };
        });

        afterEach(() => {
            delete global.ResizeObserver;
        });

        it("build_camera should create SVG when not existing", async function () {
            global.window.d3 = d3;

            document.body.innerHTML = `<div id="plot-camera_cameraView"></div>`;

            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            const viewer = Object.create(CameraViewer);
            viewer.div = "#plot-camera_cameraView";
            viewer.configuration = {
                width: 500,
                height: 580,
                hexRadius: 6,
                legend_width: 15,
                legend_margin: 60,
            };

            // Pre-populate pixels so build_camera proceeds immediately
            viewer.pixels = [[[0, 0, "1"]]];

            // Call build_camera which should create the SVG
            viewer.build_camera();

            // Wait for async timeout to complete
            await new Promise(resolve => setTimeout(resolve, 100));

            const container = document.getElementById("plot-camera_cameraView");
            const svg = container.querySelector("svg");
            expect(svg).to.exist;
            expect(svg.getAttribute("viewBox")).to.include("0 0");
        });

        it("scale should set width and height based on container size", async function () {
            const mod = await import("../static/js/cameraPlot.js");
            const { CameraViewer } = mod.__test__;

            global.window.d3 = d3;
            document.body.innerHTML = `
                <div id="plot-scale_cameraView" style="width: 300px; height: 300px;">
                    <svg viewBox="0 0 700 700"></svg>
                </div>
            `;

            const container = document.getElementById("plot-scale_cameraView");
            container.getBoundingClientRect = () => ({ width: 300, height: 300 });

            const svg = container.querySelector("svg");
            const g = d3.select(svg).append("g");

            const viewer = Object.create(CameraViewer);
            viewer.div = "#plot-scale_cameraView";
            viewer.svg = g;
            viewer.svgContainer = svg;
            viewer.configuration = {
                width: 500,
                height: 580,
                legend_width: 15,
                legend_margin: 60,
            };

            const result = viewer.scale();

            // Should set width and height attributes based on container and viewBox
            expect(result).to.equal(true);
            expect(svg.getAttribute("width")).to.not.be.null;
            expect(svg.getAttribute("height")).to.not.be.null;
        });
    });
});
