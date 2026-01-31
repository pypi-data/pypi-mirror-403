import { JSDOM } from "jsdom";
import { expect } from "chai";
import jquery from "jquery";
import d3 from "../static/js/d3loader.js";
import { setupSidebarAndFooter } from "../static/js/sidebarAndFooter.js";

// DOM creation helper
function createDomWithPath(urlPath = "") {
  const segments = urlPath.split("/").filter(Boolean);
  const basePath = segments[0] || "";
  return new JSDOM(
    `
      <body>
        <header>
          <nav id="first-nav" class="first-nav fixed-top"></nav>
          <nav id="second-nav" class="second-nav fixed-top"></nav>
        </header>
        <main role="main">
          <div id="wrapper" class="collapsed">
            <div id="sidebar-wrapper">
              <ul class="sidebar-nav nav-pills nav-stacked mt-1" id="menu">

                <li>
                  <a href="#"><span class="fa-stack fa-lg"><i class="fa fa-globe fa-stack-1x"></i></span>
                    <label for="which-Site"></label>
                    <select id="which-Site" name="which-Site-list">
                      <option value="North">North</option>
                      <option value="South">South</option>
                    </select></a>
                </li>

                <li>
                  <a href="#"><span class="fa-stack fa-lg">
                      <i class="fa fa-calendar fa-stack-1x"></i>
                    </span><label for="which-date"></label>
                    <input id="date-picker" class="form-control no-focus" placeholder="Choose a date" style="text-align-last: center; display: inline; font-weight: bold;">
                  </a>
                </li>

                <li>
                  <a href="#">
                    <span class="fa-stack fa-lg">
                      <strong> OB
                      </strong></span>
                    <label for="which-OB"></label>
                    <select class="form-control no-focus" id="which-OB" name="which-OB-list" style="
                            text-align-last: center;
                            display: inline;
                            font-weight: bold;
                          ">
                      <option disabled="">choose date first</option>
                    </select></a>
                </li>

                <li>
                  <a href="#">
                    <span class="fa-stack fa-lg">
                      <i class="fa fa-hashtag fa-stack-1x"></i>
                    </span>
                    <label for="which-Tel-ID"></label>
                    <select class="form-control no-focus" id="which-Tel-ID" name="which-Tel-ID-list" style="
                            text-align-last: center;
                            display: inline;
                            font-weight: bold;
                          "><option value="0" disabled selected>select a Tel ID</option>

                          </select></a>
                </li>

                <li>
                  <a href="#">
                    <span class="fa-stack fa-lg">
                      <i class="fa fa-line-chart fa-stack-1x"></i>
                    </span>
                    <button type="button" id="makePlot" class="btn btn-primary">
                      Make Plot
                    </button>
                  </a>
                </li>

                <li>
                  <span id="missingInfo" style="display: block; text-align: center; color: white;"></span>
                </li>
              </ul>
            </div>
            <div id="page-content-wrapper">
              <div class="container-flex"></div>
            </div>
          </div>
        </main>
        <footer class="footer fixed-bottom text-center">
          <div class="row">
            <div class="col-4 text-center">
              <nav aria-label="breadcrumb">
                <ol class="breadcrumb">
                  <li class="breadcrumb-item">
                    <a href="/${basePath}">${basePath}</a>
                  </li>
                  <li class="breadcrumb-item active" aria-current="page">
                    <a href="${urlPath}">event rates</a>
                  </li>
                </ol>
              </nav>
            </div>
            <div class="col-8 text-center">
              <i>Selected:</i> &nbsp
              Site: <strong><span id="footer-site">North</span></strong> |
              Tel. type: <strong><span id="footer-tel-type">${basePath}</span></strong> |
              Tel ID: <strong><span id="footer-tel-id" style="color: red;">Not selected</span></strong> |
              Date: <strong><span id="footer-date" style="color: red;">Not selected</span></strong> |
              OB ID: <strong><span id="footer-ob" style="color: red;">Not selected</span></strong>
            </div>
          </div>
        </footer>
      </body>
      `,
    {
      url: `http://localhost${urlPath}`,
      runScripts: "dangerously",
      resources: "usable",
    }
  );
}

// Minimal OB-date mapping fixture for tests.
// The backend now generates this mapping dynamically, so tests should not rely
// on a file under src/qualpipe_webapp/backend/data/.
const obDateMap = {
  "2025-10-22": [1, 2],
};

// reusable setup/cleanup helpers
async function setup(urlPath = "/LSTs/event_rates") {
  const dom = createDomWithPath(urlPath);
  const window = dom.window;
  const document = window.document;

  // globals
  global.window = window;
  global.document = document;
  global.Event = window.Event;
  global.d3 = d3;

  // Link jQuery to JSDOM window
  const $ = jquery(window);
  global.$ = $;

  // minimal datepicker mock (do not override $.fn.on)
  $.fn.datepicker = function () {
    return this;
  };

  // mock getJSON with .fail
  $.getJSON = (url, cb) => {
    cb(obDateMap);
    return { fail: () => { } };
  };

  // initialize module on this window/document
  setupSidebarAndFooter(window, document);

  // 'DOMContentLoaded' is automatically triggered at the end of "beforeEach"
  // allow any microtasks / setTimeout(0) to run
  await new Promise((r) => setTimeout(r, 5));

  return { dom, window, document, $ };
}

function cleanup(context) {
  try {
    context?.dom?.window?.close();
  } catch (e) {
    // Log the error for debugging purposes
    console.error("Error during cleanup:", e);
  }
  // Remove existing globals
  if (global.window) delete global.window;
  if (global.document) delete global.document;
  if (global.Event) delete global.Event;
  if (global.$) delete global.$;
}

describe("Tests for 'sidebarAndFooter.js':", () => {
  describe("Sidebar tests:", () => {
    let context;
    beforeEach(async () => {
      context = await setup("/LSTs/event_rates");
    });
    afterEach(() => cleanup(context));

    it("should expand/collapse sidebar on mouseenter/mouseleave", async () => {
      const { document, window } = context;
      const sidebar = document.getElementById("sidebar-wrapper");
      const wrapper = document.getElementById("wrapper");
      sidebar.dispatchEvent(new window.Event("mouseenter"));
      expect(wrapper.classList.contains("collapsed")).to.be.false;
      sidebar.dispatchEvent(new window.Event("mouseleave"));
      expect(wrapper.classList.contains("collapsed")).to.be.true;
    });

    it("should populate OB options on Date change", async () => {
      // Default OB value is "choose date first"
      const { document } = context;
      const selectOB = document.getElementById("which-OB");
      expect(selectOB.options[0].textContent).to.equal("choose date first");

      // Select a date with known OBs from ob_date_map.json
      global.$("#date-picker").val("2025-10-22");
      global.$("#date-picker").trigger("changeDate");
      expect(selectOB.options.length).to.be.above(1);
      expect(selectOB.options[0].value).to.equal("0");
      expect(selectOB.options[0].textContent).to.equal("Select an OB");
      expect(selectOB.options[1].value).to.equal("1");

      // Handle date with no OBs
      global.$("#date-picker").val("1900-01-01");
      global.$("#date-picker").trigger("changeDate");
      expect(selectOB.options.length).to.be.equal(1);
      expect(selectOB.options[0].value).to.equal("0");
      expect(selectOB.options[0].textContent).to.equal("No OBs available");
    });

    it("datepicker 'show' attaches hover listeners to datepicker dropdown", async () => {
      const { document, window } = context;
      const wrapper = document.getElementById("wrapper");

      // create a fake datepicker dropdown element that attachDatepickerSidebarEvents will find
      const dp = document.createElement("div");
      dp.className = "datepicker datepicker-dropdown";
      document.body.appendChild(dp);

      // trigger show -> handler uses setTimeout(...,0) to attach events
      global.$("#date-picker").trigger("show");
      await new Promise((r) => setTimeout(r, 10));

      // simulate hover events on the created datepickerDiv and verify wrapper collapsed state changes
      wrapper.classList.add("collapsed");
      dp.dispatchEvent(new window.Event("mouseenter"));
      expect(wrapper.classList.contains("collapsed")).to.be.false;

      dp.dispatchEvent(new window.Event("mouseleave"));
      expect(wrapper.classList.contains("collapsed")).to.be.true;

      // cleanup created element
      dp.remove();
    });
  });

  describe("Footer tests:", () => {
    let context;
    beforeEach(async () => {
      context = await setup("/LSTs/event_rates");
    });
    afterEach(() => cleanup(context));

    it("should update footer Site on Site change", async () => {
      // default footer "Site" is "North"
      const { document, window } = context;
      const selectSite = document.getElementById("which-Site");
      const footerSite = document.getElementById("footer-site");
      expect(footerSite.textContent).to.equal(selectSite.value);
      // change Site to South
      selectSite.value = "South";
      selectSite.dispatchEvent(new window.Event("change"));
      expect(footerSite.textContent).to.equal("South");
    });

    it("should update footer Tel-ID on Tel-ID sidebar change", async () => {
      const { document, window } = context;
      const selectTelID = document.getElementById("which-Tel-ID");
      const footerTelID = document.getElementById("footer-tel-id");
      // initial state
      expect(footerTelID.textContent).to.equal("Not selected");
      expect(footerTelID.style.color).to.equal("red");
      // ensure the options exist (avoid dependency on the order of other tests)
      const ensureOption = (val) => {
        if (!selectTelID.querySelector(`option[value="${val}"]`)) {
          const opt = document.createElement("option");
          opt.value = val;
          opt.textContent = val;
          selectTelID.appendChild(opt);
        }
      };
      ensureOption("2");
      ensureOption("4");
      // Simulate selection of Tel-ID 2
      selectTelID.value = "2";
      selectTelID.dispatchEvent(new window.Event("change"));
      expect(footerTelID.textContent).to.equal("2");
      expect(footerTelID.style.color).to.equal("");
      // Simulate selection of Tel-ID 4
      selectTelID.value = "4";
      selectTelID.dispatchEvent(new window.Event("change"));
      expect(footerTelID.textContent).to.equal("4");
    });

    it("should update footer Date on Date change", async () => {
      // Default footer "Date" is "Not selected"
      const { document } = context;
      const footerDate = document.getElementById("footer-date");
      expect(footerDate.textContent).to.equal("Not selected");
      expect(footerDate.style.color).to.equal("red");
      global.$("#date-picker").val("2024-01-01");
      global.$("#date-picker").trigger("changeDate");
      expect(footerDate.textContent).to.equal("2024-01-01");
      expect(footerDate.style.color).to.equal("");
    });

    it("should update footer OB on OB sidebar change", async () => {
      // Default footer "OB" is "Not selected"
      const { document, window } = context;
      const selectOB = document.getElementById("which-OB");
      const footerOB = document.getElementById("footer-ob");

      // Change date helper
      const changeDate = (date) => {
        global.$("#date-picker").val(date);
        global.$("#date-picker").trigger("changeDate");
      };

      // Expectation helper
      const expectFooter = (text, isRed) => {
        expect(footerOB.textContent).to.equal(text);
        expect(footerOB.style.color).to.equal(isRed ? "red" : "");
      };

      // Default footer OB state
      expectFooter("Not selected", true);

      // Select a date with known OBs and select OB 1
      changeDate("2025-10-22");
      expectFooter("Select an OB", true);
      selectOB.value = "1";
      selectOB.dispatchEvent(new window.Event("change"));
      expectFooter("1", false);

      // Handle date with no OBs
      changeDate("1900-01-01");
      expectFooter("No OBs available", true);

      // Reselect a date with known OBs and select OB 2
      changeDate("2025-10-22");
      expectFooter("Select an OB", true);
      selectOB.value = "2";
      selectOB.dispatchEvent(new window.Event("change"));
      expectFooter("2", false);
    });
  });

  describe("Footer tests for non-telescope page:", () => {
    it("path parsing sets isTelescopeElement false for non-telescope pages", async () => {
      context = await setup("/home");
      const { document, window } = context;
      const selectSite = document.getElementById("which-Site");
      const footerSite = document.getElementById("footer-site");
      const selectTelID = document.getElementById("which-Tel-ID");

      // change site should only update footerSite (no Tel-ID population for non-telescope)
      selectSite.value = "South";
      selectSite.dispatchEvent(new window.Event("change"));
      expect(footerSite.textContent).to.equal("South");

      // Tel-ID should remain with placeholder only
      expect(selectTelID.options.length).to.equal(1);
      expect(selectTelID.options[0].textContent).to.equal("select a Tel ID");

      cleanup(context);
    });
  });

  // Generic parametrized suite creator to avoid repeating the same setup/teardown
  function makeTelTypeSuite(telTypePath, expectations) {
    const telType = telTypePath.split("/").filter(Boolean)[0];
    describe(`${telType} sidebar and footer tests`, () => {
      let context;
      beforeEach(async () => {
        context = await setup(telTypePath);
      });
      afterEach(() => cleanup(context));

      it("populates Tel-ID ranges for expected values", async () => {
        const { document, window } = context;
        const selectSite = document.getElementById("which-Site");
        const selectTelID = document.getElementById("which-Tel-ID");

        // default placeholder
        expect(selectTelID.options[0].textContent).to.equal("select a Tel ID");

        // test North expectations if provided
        if (expectations.north) {
          selectSite.value = "North";
          selectSite.dispatchEvent(new window.Event("change"));
          for (const val of expectations.north.exists) {
            expect(selectTelID.querySelector(`option[value="${val}"]`)).to
              .exist;
          }
          for (const val of expectations.north.notExists || []) {
            expect(selectTelID.querySelector(`option[value="${val}"]`)).to.not
              .exist;
          }
        }

        // test South expectations if provided
        if (expectations.south) {
          selectSite.value = "South";
          selectSite.dispatchEvent(new window.Event("change"));
          for (const val of expectations.south.exists) {
            expect(selectTelID.querySelector(`option[value="${val}"]`)).to
              .exist;
          }
          for (const val of expectations.south.notExists || []) {
            expect(selectTelID.querySelector(`option[value="${val}"]`)).to.not
              .exist;
          }
        }
      });

      it("should update footer Tel-Type based on url page", async () => {
        const { document } = context;
        const footerTelType = document.getElementById("footer-tel-type");
        expect(footerTelType.textContent).to.equal(telType);
      });
    });
  }

  // LST expectations
  makeTelTypeSuite("/LSTs/event_rates", {
    north: { exists: ["1", "4"], notExists: ["5"] },
    south: { exists: ["1", "4"], notExists: ["5"] },
    unknown: { exists: ["0", "2"], notExists: ["1"] },
  });

  // MST expectations
  makeTelTypeSuite("/MSTs/event_rates", {
    north: { exists: ["5", "59"], notExists: ["2"] },
    south: { exists: ["5", "29", "100", "130"], notExists: ["2", "59"] },
  });

  // SST expectations
  makeTelTypeSuite("/SSTs/event_rates", {
    south: { exists: ["30", "99", "131", "179"], notExists: ["2", "100"] },
  });
});

describe("localStorage persistence", () => {
  let dom, window, document, $;
  const STORAGE_KEY = "qualpipe_selections";

  beforeEach(() => {
    dom = createDomWithPath("/LSTs/event_rates");
    window = dom.window;
    document = window.document;
    $ = jquery(window);
    window.$ = $;
    window.d3 = d3;

    // Mock localStorage
    const storage = {};
    window.localStorage = {
      getItem: (key) => storage[key] || null,
      setItem: (key, value) => { storage[key] = value; },
      removeItem: (key) => { delete storage[key]; },
      clear: () => { for (const key in storage) delete storage[key]; }
    };
  });

  it("should have localStorage available in window", () => {
    expect(window.localStorage).to.exist;
    expect(window.localStorage.setItem).to.be.a("function");
    expect(window.localStorage.getItem).to.be.a("function");
  });

  it("should accept valid JSON in localStorage", () => {
    const testData = {
      site: "North",
      date: "2025-10-22",
      ob: "239",
      telId: "1"
    };

    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(testData));
    const retrieved = JSON.parse(window.localStorage.getItem(STORAGE_KEY));

    expect(retrieved).to.deep.equal(testData);
  });

  it("should handle localStorage setItem and getItem", () => {
    window.localStorage.setItem("test", "value");
    expect(window.localStorage.getItem("test")).to.equal("value");
  });

  it("should return null for non-existent keys", () => {
    expect(window.localStorage.getItem("nonexistent")).to.be.null;
  });

  it("should allow clearing storage", () => {
    window.localStorage.setItem("test", "value");
    window.localStorage.clear();
    expect(window.localStorage.getItem("test")).to.be.null;
  });
});
