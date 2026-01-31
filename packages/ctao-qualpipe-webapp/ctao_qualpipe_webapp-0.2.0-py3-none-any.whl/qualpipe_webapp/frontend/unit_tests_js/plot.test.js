import { expect } from "chai";
import { JSDOM } from "jsdom";
import sinon from "sinon";
import * as plotModule from "../static/js/plot.js";
import esmock from "esmock";

// Mock modules
const mockValidation = {
  isValidMetadata: sinon.stub().resolves(true),
  isValidData: sinon.stub().resolves(true),
};

const mockScatterPlot = sinon.stub();
const mockBadgeCriteriaNone = sinon.stub();
const mockResizeListeners = {};

// Helper function to build minimal plot data with metadata
function makePlotData(key = "test") {
  return {
    [key]: {
      fetchedData: { x: [1, 2, 3], y: [4, 5, 6] },
      fetchedMetadata: { plotConfiguration: { title: "t" } },
    },
  };
}

// Helper functions to avoid deep nesting in tests
const alwaysTrue = () => true;
const asyncTextFn = (value) => async () => value;
function FakeAjv() {
  this.addSchema = sinon.stub();
  this.compile = sinon.stub().returns(alwaysTrue);
}

function setupMissingInfoDom(initialText = "") {
  document.body.innerHTML = `<div id="missingInfo"></div>`;
  const missingInfo = document.getElementById("missingInfo");
  if (initialText) {
    missingInfo.textContent = initialText;
  }
  return missingInfo;
}

// Helper to test validation functions with consistent pattern
function testValidation(description, validationFn, value, expectedResult) {
  it(description, function () {
    setupMissingInfoDom();
    const result = validationFn(value);
    expect(result).to.equal(expectedResult);
  });
}

// Helper to set up DOM for requestData tests
function setupRequestDom({
  site = "North",
  date = "2025-12-16",
  ob = "123",
  telId = "1",
} = {}) {
  document.body.innerHTML = `
    <div id="missingInfo"></div>
    <div id="which-Site"></div>
    <input id="date-picker" value="${date}" />
    <div id="which-OB"></div>
    <div id="which-Tel-ID"></div>
  `;

  document.getElementById("which-Site").value = site;
  document.getElementById("which-OB").value = ob;
  document.getElementById("which-Tel-ID").value = telId;
}

// Setup JSDOM
let dom;
let window;
let document;
let fetchStub;

describe("Testing 'plot.js'", function () {
  beforeEach(() => {
    dom = new JSDOM(
      `
      <html>
        <body>
          <div id="missingInfo"></div>
          <div id="which-Site">
            <option value="North">North</option>
            <option value="South">South</option>
          </div>
          <input id="date-picker" value="" />
          <div id="which-OB"></div>
          <div id="which-Tel-ID"></div>
        </body>
      </html>
    `,
      { url: "http://qualpipe.local:8080/LSTs/test" }
    );
    window = dom.window;
    document = window.document;
    global.window = window;
    global.document = document;
    global.fetch = sinon.stub();
    fetchStub = global.fetch;

    // Mock jQuery
    global.$ = function (selector) {
      return {
        val: function () {
          const element = document.querySelector(selector);
          return element ? element.value : "";
        },
      };
    };
  });

  afterEach(() => {
    sinon.restore();
    dom?.window?.close();
    delete global.window;
    delete global.document;
    delete global.fetch;
    delete global.$;
  });

  describe("plotAndCreateResizeListener", function () {
    it("should return a resize handler function", function () {
      const elementId = "plot-test";
      const data = makePlotData();
      const key = "test";
      const plotType = "scatterplot";

      const handler = plotModule.plotAndCreateResizeListener(
        elementId,
        data,
        key,
        plotType
      );

      expect(handler).to.be.a("function");
    });

    it("should reset plot container color to black on resize", async function () {
      const elementId = "plot-test";
      document.body.innerHTML = `<div id="${elementId}" style="color: red;"></div>`;

      // Ensure scatterPlot sees non-zero dimensions
      document.getElementById(elementId).getBoundingClientRect = () => ({
        width: 200,
        height: 200,
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
      });

      // Use esmock to replace scatterPlot with a no-op for this test
      const scatterAbs = new URL("../static/js/scatterPlot.js", import.meta.url)
        .pathname;
      const plotModuleMocked = await esmock(
        "../static/js/plot.js",
        { [scatterAbs]: { scatterPlot: () => { } } },
        { url: import.meta.url }
      );

      // Provide minimal metadata so handler runs
      const data = makePlotData();
      const key = "test";

      const handler = plotModuleMocked.plotAndCreateResizeListener(
        elementId,
        data,
        key,
        "scatterplot"
      );

      const plotContainer = document.getElementById(elementId);
      // invoke the resize handler to trigger color reset
      handler();
      expect(plotContainer.style.color).to.equal("black");
    });

    it("should use scatterPlot as default plotting function", function () {
      const elementId = "plot-test";
      document.body.innerHTML = `<div id="${elementId}"></div>`;

      const data = makePlotData();
      const key = "test";

      const handler = plotModule.plotAndCreateResizeListener(
        elementId,
        data,
        key,
        "unknown-plot-type"
      );

      expect(handler).to.be.a("function");
    });
  });

  describe("handleInvalidData", function () {
    it("should clear the plot and display error message", function () {
      const elementId = "plot-test";
      const message = "Test error message";
      document.body.innerHTML = `<div id="${elementId}"></div>`;

      plotModule.handleInvalidData(message, elementId);

      const container = document.getElementById(elementId);
      const errorDiv = container.querySelector(".plot-error");
      expect(errorDiv).to.exist;
      expect(errorDiv.textContent).to.equal(message);
      expect(container.style.color).to.equal("red");
    });

    it("should handle null elementId gracefully", function () {
      const message = "Test error message";
      expect(() => plotModule.handleInvalidData(message, null)).to.not.throw();
    });

    it("should broadcast message to all plot-* containers when elementId is null", function () {
      document.body.innerHTML = `
        <div id="plot-a"></div>
        <div id="plot-b"></div>
      `;

      const warnStub = sinon.stub(console, "warn");
      const message = "Broadcast error";

      plotModule.handleInvalidData(message, null, true);

      ["plot-a", "plot-b"].forEach((id) => {
        const container = document.getElementById(id);
        const errorDiv = container.querySelector(".plot-error");
        expect(errorDiv).to.exist;
        expect(errorDiv.textContent).to.equal(message);
        expect(container.style.color).to.equal("red");
      });

      expect(warnStub.called).to.equal(true);
    });
  });

  describe("validateScatterplot", function () {
    it("should return true for valid scatterplot data", function () {
      const data = makePlotData();
      data["test"]["fetchedData"]["xerr"] = [0.1, 0.1, 0.1];
      data["test"]["fetchedData"]["yerr"] = [0.2, 0.2, 0.2];

      const customError = sinon.stub().returns(false);

      const result = plotModule.validateScatterplot(
        data["test"]["fetchedData"],
        "test-key",
        "plot-test",
        "scatterplot",
        customError
      );

      expect(result).to.be.true;
      expect(customError.called).to.be.false;
    });

    it("should reject when x and y lengths do not match", function () {
      const data = {
        x: [1, 2],
        y: [4, 5, 6],
      };
      const customError = sinon.stub().returns(false);

      plotModule.validateScatterplot(
        data,
        "test-key",
        "plot-test",
        "scatterplot",
        customError
      );

      expect(customError.called).to.be.true;
      expect(customError.firstCall.args[0]).to.include(
        "x and y must have the same length"
      );
    });

    it("should reject when xerr length does not match x", function () {
      const data = makePlotData();
      data["test"]["fetchedData"]["xerr"] = [0.1, 0.1];

      const customError = sinon.stub().returns(false);

      plotModule.validateScatterplot(
        data["test"]["fetchedData"],
        "test-key",
        "plot-test",
        "scatterplot",
        customError
      );

      expect(customError.called).to.be.true;
      expect(customError.firstCall.args[0]).to.include(
        "xerr exists but does not match x length"
      );
    });

    it("should reject when yerr length does not match y", function () {
      const data = makePlotData();
      data["test"]["fetchedData"]["yerr"] = [0.2];
      const customError = sinon.stub().returns(false);

      plotModule.validateScatterplot(
        data["test"]["fetchedData"],
        "test-key",
        "plot-test",
        "scatterplot",
        customError
      );

      expect(customError.called).to.be.true;
      expect(customError.firstCall.args[0]).to.include(
        "yerr exists but does not match y length"
      );
    });

    it("should handle missing xerr and yerr gracefully", function () {
      const data = makePlotData();
      const customError = sinon.stub().returns(false);

      const result = plotModule.validateScatterplot(
        data["test"]["fetchedData"],
        "test-key",
        "plot-test",
        "scatterplot",
        customError
      );

      expect(result).to.be.true;
      expect(customError.called).to.be.false;
    });
  });

  describe("checkXYLength", function () {
    it("should call validator for known plot types", function () {
      const data = makePlotData();

      const result = plotModule.checkXYLength(
        data["test"],
        "test-key",
        "plot-test",
        "scatterplot"
      );

      expect(result).to.be.true;
    });

    it("should handle unknown plot types", function () {
      document.body.innerHTML = `<div id="plot-test"></div>`;
      const data = makePlotData();

      const result = plotModule.checkXYLength(
        data["test"],
        "test-key",
        "plot-test",
        "unknown-type"
      );

      expect(result).to.be.undefined;
    });

    it("should reject mismatched x and y lengths", function () {
      document.body.innerHTML = `<div id="plot-test"></div>`;
      const data = {
        fetchedData: {
          x: [1, 2],
          y: [4, 5, 6],
        },
      };

      const result = plotModule.checkXYLength(
        data,
        "test-key",
        "plot-test",
        "scatterplot"
      );

      expect(result).to.be.false;
    });
  });

  describe("clearPlotArea", function () {
    it("should clear a single plot by ID", function () {
      document.body.innerHTML = `<div id="plot-test"></div>`;
      const container = document.getElementById("plot-test");
      container.innerHTML = "<svg></svg>";

      plotModule.clearPlotArea("plot-test");

      expect(container.querySelector("svg")).to.not.exist;
      expect(container.textContent).to.equal("");
      expect(container.style.color).to.equal("black");
    });

    it("should clear all plots when plotId is omitted or null", function () {
      document.body.innerHTML = `
        <div id="plot-test1"></div>
        <div id="plot-test2"></div>
      `;
      const plots = document.querySelectorAll('[id^="plot-"]');

      // Add some content to clear
      plots.forEach((plot) => (plot.innerHTML = "<svg></svg><h5>t</h5>old"));

      plotModule.clearPlotArea();

      plots.forEach((plot) => {
        expect(plot.querySelector("svg")).to.not.exist;
        expect(plot.textContent).to.equal("");
        expect(plot.style.color).to.equal("black");
      });
    });

    it("should handle non-existent plot ID gracefully", function () {
      document.body.innerHTML = "";
      expect(() =>
        plotModule.clearPlotArea("Error", "non-existent")
      ).to.not.throw();
    });
  });

  describe("Query parameters validation", function () {
    describe("isValidSite", function () {
      it("should accept 'North' as valid site", function () {
        const result = plotModule.isValidSite("North");
        expect(result).to.be.true;
      });

      it("should accept 'South' as valid site", function () {
        const result = plotModule.isValidSite("South");
        expect(result).to.be.true;
      });

      it("should reject invalid sites", function () {
        setupMissingInfoDom();
        const result = plotModule.isValidSite("Invalid");
        expect(result).to.be.false;
        expect(document.getElementById("missingInfo").textContent).to.include(
          "Site must be either 'North' or 'South'"
        );
      });
    });

    describe("isValidDate", function () {
      testValidation(
        "should accept valid date format YYYY-MM-DD",
        plotModule.isValidDate,
        "2025-12-16",
        true
      );

      [
        { label: "missing date", value: "" },
        { label: "'Choose a date' placeholder", value: "Choose a date" },
        { label: "invalid date format", value: "12/16/2025" },
      ].forEach(({ label, value }) => {
        testValidation(
          `should reject ${label}`,
          plotModule.isValidDate,
          value,
          false
        );
      });
    });

    describe("isValidOB", function () {
      testValidation(
        "should accept valid OB number",
        plotModule.isValidOB,
        "12345",
        true
      );

      [
        { label: "missing OB", value: "" },
        {
          label: "'choose date first' placeholder",
          value: "choose date first",
        },
        { label: "'No OBs available' status", value: "No OBs available" },
        { label: "'Select an OB' placeholder", value: "Select an OB" },
        { label: "non-numeric OB", value: "OB-123" },
      ].forEach(({ label, value }) => {
        testValidation(
          `should reject ${label}`,
          plotModule.isValidOB,
          value,
          false
        );
      });
    });

    describe("isValidTelType", function () {
      const validTelTypes = ["LST", "MST", "SST"];
      for (const telType of validTelTypes) {
        testValidation(
          `should accept '${telType}' as valid telescope type`,
          plotModule.isValidTelType,
          telType,
          true
        );
      }

      const invalidTelTypes = [
        { value: "INVALID", label: "invalid telescope type" },
        { value: "", label: "missing telescope type" },
      ];
      for (const { value, label } of invalidTelTypes) {
        testValidation(
          `should reject ${label}`,
          plotModule.isValidTelType,
          value,
          false
        );
      }
    });

    describe("isValidTelID", function () {
      testValidation(
        "should accept valid numeric Telescope ID",
        plotModule.isValidTelID,
        "123",
        true
      );

      [
        { label: "missing Telescope ID", value: "" },
        { label: "'select a Tel ID' placeholder", value: "select a Tel ID" },
        { label: "non-numeric Telescope ID", value: "TEL-123" },
      ].forEach(({ label, value }) => {
        testValidation(
          `should reject ${label}`,
          plotModule.isValidTelID,
          value,
          false
        );
      });
    });

    describe("checkQueryParams", function () {
      it("should return true for all valid parameters", function () {
        setupMissingInfoDom();
        const result = plotModule.checkQueryParams(
          "LST",
          "North",
          "2025-12-16",
          "123",
          "1"
        );
        expect(result).to.be.true;
      });

      it("should return false for invalid site", function () {
        setupMissingInfoDom();
        const result = plotModule.checkQueryParams(
          "LST",
          "Invalid",
          "2025-12-16",
          "123",
          "1"
        );
        expect(result).to.be.false;
      });

      it("should return false for invalid date", function () {
        setupMissingInfoDom();
        const result = plotModule.checkQueryParams(
          "LST",
          "North",
          "invalid",
          "123",
          "1"
        );
        expect(result).to.be.false;
      });

      it("should clear missingInfo when all parameters are valid", function () {
        setupMissingInfoDom("Some error");
        plotModule.checkQueryParams("LST", "North", "2025-12-16", "123", "1");
        expect(document.getElementById("missingInfo").textContent).to.equal("");
      });
    });
  });

  describe("requestData", function () {
    it("should return data for valid parameters", async function () {
      setupRequestDom();

      const mockData = { test: "data" };
      fetchStub.resolves({
        status: 200,
        json: sinon.stub().resolves(mockData),
      });

      const result = await plotModule.requestData();

      expect(result).to.deep.equal(mockData);
      expect(fetchStub.called).to.be.true;
    });

    it("should handle 404 response", async function () {
      setupRequestDom();

      fetchStub.resolves({
        status: 404,
        json: sinon.stub().resolves({}),
      });

      const result = await plotModule.requestData();

      expect(result).to.be.undefined;
      expect(document.getElementById("missingInfo").textContent).to.include(
        "404"
      );
    });

    it("should return false for invalid parameters", async function () {
      setupRequestDom({ site: "Invalid", date: "", ob: "123", telId: "1" });

      const result = await plotModule.requestData();

      expect(result).to.be.false;
      expect(fetchStub.called).to.be.false;
    });

    it("should handle fetch errors gracefully", async function () {
      setupRequestDom();

      fetchStub.rejects(new Error("Network error"));

      const result = await plotModule.requestData();

      expect(result).to.be.undefined;
    });
  });

  describe("missingInfo", function () {
    it("should set missingInfo element text and background", function () {
      setupMissingInfoDom();
      plotModule.missingInfo("Test error");

      const element = document.getElementById("missingInfo");
      expect(element.textContent).to.equal("Test error");
      expect(element.style.background).to.equal("red");
    });

    it("should handle missing missingInfo element gracefully", function () {
      document.body.innerHTML = "";
      expect(() => plotModule.missingInfo("Test error")).to.not.throw();
    });
  });

  describe("validateAndPlotElement", function () {
    it("should show error when key data is missing", async function () {
      document.body.innerHTML = `<div id="plot-foo"></div>`;

      await plotModule.validateAndPlotElement("plot-foo", { other: {} }, "foo");

      const el = document.getElementById("plot-foo");
      const errorDiv = el.querySelector(".plot-error");
      expect(errorDiv).to.exist;
      expect(errorDiv.textContent).to.equal("No data found for key: foo");
      expect(el.style.color).to.equal("red");
    });

    it("should report invalid metadata when schema fetch fails", async function () {
      document.body.innerHTML = `<div id="plot-foo"></div>`;

      // First two fetch calls are for metadata and criteria schemas
      fetchStub.onFirstCall().resolves({ ok: false, status: 404 });
      fetchStub.onSecondCall().resolves({ ok: false, status: 404 });

      const data = {
        foo: {
          fetchedMetadata: { plotConfiguration: { plotType: "scatterplot" } },
          fetchedData: { x: [1, 2], y: [1, 2] },
        },
      };

      await plotModule.validateAndPlotElement("plot-foo", data, "foo");

      const el = document.getElementById("plot-foo");
      const errorDiv = el.querySelector(".plot-error");
      expect(errorDiv).to.exist;
      expect(errorDiv.textContent).to.equal("Invalid metadata for key: foo");
      expect(el.style.color).to.equal("red");
    });

    it("should stop with length error when validations pass but x/y mismatch", async function () {
      document.body.innerHTML = `<div id="plot-foo"></div>`;

      // Mock globals required by validators
      window.jsyaml = { load: sinon.stub().returns({}) };
      window.Ajv = FakeAjv;

      // metadata schema and criteria schema
      fetchStub.onCall(0).resolves({ ok: true, text: asyncTextFn("meta") });
      fetchStub.onCall(1).resolves({ ok: true, text: asyncTextFn("crit") });
      // data schema for scatterplot
      fetchStub.onCall(2).resolves({ ok: true, text: asyncTextFn("data") });

      const data = {
        foo: {
          fetchedMetadata: { plotConfiguration: { plotType: "scatterplot" } },
          fetchedData: { x: [1, 2], y: [1] }, // mismatch to trigger length error
        },
      };

      await plotModule.validateAndPlotElement("plot-foo", data, "foo");

      const el = document.getElementById("plot-foo");
      const errorDiv = el.querySelector(".plot-error");
      expect(errorDiv).to.exist;
      expect(errorDiv.textContent).to.match(/Data length error for key: 'foo'/);
      expect(el.style.color).to.equal("red");
    });
  });

  describe("makePlot", function () {
    it("should clear plot containers when no data is returned", async function () {
      // Invalid params to force requestData to return false
      document.body.innerHTML = `
        <div id="missingInfo"></div>
        <div id="which-Site"></div>
        <input id="date-picker" value="" />
        <div id="which-OB"></div>
        <div id="which-Tel-ID"></div>
        <div id="plot-foo">old</div>
      `;
      document.getElementById("which-Site").value = "Invalid";

      plotModule.makePlot();
      await new Promise((r) => setTimeout(r, 0));

      const el = document.getElementById("plot-foo");
      const errorDiv = el.querySelector(".plot-error");
      expect(errorDiv).to.exist;
      expect(errorDiv.textContent).to.equal("No data received.");
      expect(el.style.color).to.equal("red");
    });

    it("should request data successfully and do nothing if no plot-* elements", async function () {
      document.body.innerHTML = `
        <div id="missingInfo"></div>
        <div id="which-Site"></div>
        <input id="date-picker" value="2025-12-16" />
        <div id="which-OB"></div>
        <div id="which-Tel-ID"></div>
      `;
      document.getElementById("which-Site").value = "North";
      document.getElementById("which-OB").value = "123";
      document.getElementById("which-Tel-ID").value = "1";

      fetchStub.resolves({ status: 200, json: async () => ({ ok: true }) });

      plotModule.makePlot();
      await new Promise((r) => setTimeout(r, 0));

      expect(fetchStub.called).to.be.true;
      // No plot-* divs, so nothing else to assert beyond no throw
    });

    it("logs error in catch when requestData throws", async function () {
      // Force requestData to throw synchronously by making getElementById blow up
      const docErr = new Error("boom");
      const originalWindow = global.window;
      const originalDocument = global.document;

      global.window = { location: { pathname: "/LSTs/foo" } };
      global.document = {
        getElementById: () => {
          throw docErr;
        },
        querySelectorAll: () => [],
      };

      const consoleSpy = sinon.spy(console, "error");

      plotModule.makePlot();
      await new Promise((r) => setTimeout(r, 0));

      expect(consoleSpy.called).to.be.true;
      expect(consoleSpy.firstCall.args[0]).to.equal(
        "Error while requesting data:"
      );
      expect(consoleSpy.firstCall.args[1]).to.equal(docErr);

      consoleSpy.restore();
      global.window = originalWindow;
      global.document = originalDocument;
    });

    it("logs error in catch when requestData rejects asynchronously", async function () {
      const asyncErr = new Error("async boom");

      // Keep DOM minimal to avoid plotting loop
      const originalQuerySelectorAll = document.querySelectorAll;
      document.querySelectorAll = () => [];

      const consoleSpy = sinon.spy(console, "error");

      plotModule.makePlot(() => Promise.reject(asyncErr));
      await new Promise((r) => setTimeout(r, 0));

      expect(consoleSpy.called).to.be.true;
      expect(consoleSpy.firstCall.args[0]).to.equal(
        "Error while requesting data:"
      );
      expect(consoleSpy.firstCall.args[1]).to.equal(asyncErr);

      consoleSpy.restore();
      document.querySelectorAll = originalQuerySelectorAll;
    });
  });

  describe("validateAndPlotElement (success path)", function () {
    const validationAbs = new URL("../static/js/validation.js", import.meta.url)
      .pathname;
    const scatterAbs = new URL("../static/js/scatterPlot.js", import.meta.url)
      .pathname;
    const baseAbs = new URL("../static/js/base.js", import.meta.url).pathname;

    async function setupValidateAndPlotTest({ withOldListener = false } = {}) {
      document.body.innerHTML = `<div id="plot-foo" style="color: red;"></div>`;

      const mockedResizeListeners = {};
      const scatterSpy = sinon.spy();

      if (withOldListener) {
        mockedResizeListeners["plot-foo"] = sinon.spy();
      }

      const plotModuleMocked = await esmock(
        "../static/js/plot.js",
        {
          [validationAbs]: {
            isValidMetadata: async () => true,
            isValidData: async () => true,
          },
          [scatterAbs]: { scatterPlot: scatterSpy },
          [baseAbs]: { resizeListeners: mockedResizeListeners },
        },
        { url: import.meta.url }
      );

      const data = {
        foo: {
          fetchedMetadata: { plotConfiguration: { plotType: "scatterplot" } },
          fetchedData: { x: [1, 2], y: [3, 4] },
        },
      };

      return { plotModuleMocked, mockedResizeListeners, scatterSpy, data };
    }

    it("calls scatterPlot, registers resize listener, and resets color", async function () {
      const { plotModuleMocked, mockedResizeListeners, scatterSpy, data } =
        await setupValidateAndPlotTest();

      await plotModuleMocked.validateAndPlotElement("plot-foo", data, "foo");

      expect(scatterSpy.calledOnce).to.be.true;
      expect(scatterSpy.firstCall.args[0]).to.equal("plot-foo");
      expect(typeof mockedResizeListeners["plot-foo"]).to.equal("function");

      const el = document.getElementById("plot-foo");
      expect(el.style.color).to.equal("black");

      window.dispatchEvent(new window.Event("resize"));
      expect(scatterSpy.calledTwice).to.be.true;
    });

    it("removes old resize listener and registers a new one", async function () {
      const { plotModuleMocked, mockedResizeListeners, data } =
        await setupValidateAndPlotTest({ withOldListener: true });

      const oldListener = mockedResizeListeners["plot-foo"];
      const removeSpy = sinon.spy(window, "removeEventListener");
      const addSpy = sinon.spy(window, "addEventListener");

      await plotModuleMocked.validateAndPlotElement("plot-foo", data, "foo");

      expect(removeSpy.calledWith("resize", oldListener)).to.be.true;
      expect(addSpy.calledWith("resize")).to.be.true;
      expect(mockedResizeListeners["plot-foo"]).to.be.a("function");
      expect(mockedResizeListeners["plot-foo"]).to.not.equal(oldListener);

      removeSpy.restore();
      addSpy.restore();
    });
  });

  describe("validateAndPlotElement (invalid data path)", function () {
    it("shows 'Invalid data for key' and stops when data validation fails", async function () {
      document.body.innerHTML = `<div id="plot-foo"></div>`;

      const mockedResizeListeners = {};

      const validationAbs = new URL(
        "../static/js/validation.js",
        import.meta.url
      ).pathname;
      const baseAbs = new URL("../static/js/base.js", import.meta.url).pathname;

      const plotModuleMocked = await esmock(
        "../static/js/plot.js",
        {
          [validationAbs]: {
            isValidMetadata: async () => true,
            isValidData: async () => false,
          },
          [baseAbs]: { resizeListeners: mockedResizeListeners },
        },
        { url: import.meta.url }
      );

      const data = {
        foo: {
          fetchedMetadata: { plotConfiguration: { plotType: "scatterplot" } },
          fetchedData: { x: [1, 2], y: [1, 2] },
        },
      };

      await plotModuleMocked.validateAndPlotElement("plot-foo", data, "foo");

      const el = document.getElementById("plot-foo");
      const errorDiv = el.querySelector(".plot-error");
      expect(errorDiv).to.exist;
      expect(errorDiv.textContent).to.equal("Invalid data for key: foo");
      expect(el.style.color).to.equal("red");
      expect(mockedResizeListeners["plot-foo"]).to.be.undefined;
    });
  });
});
