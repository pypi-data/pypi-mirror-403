import { JSDOM } from "jsdom";
import { expect } from "chai";

// Import function only where needed to avoid it being executed before the mock:
// The 'event listener registration' should be executed first, before any other import of base.js
// When you import ../static/js/base.js, the module immediately runs:
//    if (typeof window !== "undefined") {
//       window.addEventListener("DOMContentLoaded", adjustContentPadding);
//       window.addEventListener("resize", adjustContentPadding);
//    }
// If 'global.window' already exists at the time of import, the module will use that object.
// If 'global.window' doesn't exist, the module doesn't register event listeners.
// After import, if you try to override global.window with 'global.window = dom.window;',
// the module has already used the old window object and doesn't reread the variable:
// event listeners have already been registered and aren't re-registered.
// Similarly, if you try to override global.window.addEventListener after import,
// the module has already called the previous version of addEventListener, so your mock isn't used.

describe("Tests for 'base.js':", () => {
  describe("event listener registration", function () {
    it("should register DOMContentLoaded and resize event listeners in browser", async function () {
      // Create JSDOM and mock window
      const dom = new JSDOM("<body></body>", { url: "http://localhost" });
      const mockWindow = dom.window;
      let calledEvents = [];
      mockWindow.addEventListener = (event, fn) => {
        calledEvents.push(event);
      };
      // Import module and explicitly call registerAdjustContentPadding
      const { registerAdjustContentPadding } = await import("../static/js/base.js");
      registerAdjustContentPadding(mockWindow);
      expect(calledEvents).to.include("DOMContentLoaded");
      expect(calledEvents).to.include("resize");
    });
  });

  function expectContentStyles(
    document,
    {
      paddingTop = "50px",
      minHeight = "720px",
      maxHeight = "720px",
      paddingBottom = "30px",
      wrapperSelector = "#wrapper",
      secondarySelector = "#sidebar-wrapper",
      pageContentSelector = "#page-content-wrapper",
      pageContentDivSelector = "#page-content-wrapper div",
    } = {}
  ) {
    expect(document.body.style.paddingTop).to.equal(paddingTop);
    expect(document.querySelector(wrapperSelector).style.minHeight).to.equal(
      minHeight
    );
    expect(document.querySelector(secondarySelector).style.maxHeight).to.equal(
      maxHeight
    );
    expect(
      document.querySelector(pageContentSelector).style.maxHeight
    ).to.equal(maxHeight);
    expect(
      document.querySelector(pageContentDivSelector).style.paddingBottom
    ).to.equal(paddingBottom);
  }

  describe("adjustContentPadding", function () {
    let dom, document;

    beforeEach(() => {
      dom = new JSDOM(
        `
      <body>
        <main role="main" class="flex-shrink-0">
          <div id="wrapper"></div>
          <div id="sidebar-wrapper"></div>
          <div id="page-content-wrapper"><div></div></div>
          <nav class="first-nav navbar fixed-top"></nav>
          <footer class="footer fixed-bottom"></footer>
          <button id="navbarToggler"></button>
        </main>
      </body>
    `,
        { url: "http://localhost" }
      );
      document = dom.window.document;

      // Mock offsetHeight for all elements used in the function
      Object.defineProperty(
        document.querySelector(".first-nav.navbar.fixed-top"),
        "offsetHeight",
        { value: 50 }
      );
      Object.defineProperty(
        document.querySelector(".footer.fixed-bottom"),
        "offsetHeight",
        { value: 30 }
      );
      Object.defineProperty(document.querySelector("#navbarToggler"), "style", {
        value: {},
      });
      document.querySelector("#wrapper").style = {};
      document.querySelector("#sidebar-wrapper").style = {};
      document.querySelector("#page-content-wrapper").style = {};
      document.querySelector("#page-content-wrapper div").style = {};
      document.body.style = {};
    });

    it("should adjust padding and minHeight for elements", async function () {
      // Simulate the global functions and properties
      global.document = document;
      global.window = dom.window;
      global.window.innerHeight = 800;

      // Import and call the function to test
      const { adjustContentPadding } = await import("../static/js/base.js");
      adjustContentPadding();

      expectContentStyles(document, {});
    });

    it("should handle presence of second navbar", async function () {
      dom = new JSDOM(
        `
      <body>
        <main role="main" class="flex-shrink-0">
          <div id="wrapper"></div>
          <div id="sidebar-wrapper"></div>
          <div id="page-content-wrapper"><div></div></div>
          <nav class="first-nav navbar fixed-top"></nav>
          <nav class="second-nav navbar"></nav>
          <footer class="footer fixed-bottom"></footer>
          <button id="navbarToggler"></button>
          <button id="navbarToggler2"></button>
        </main>
      </body>
    `,
        { url: "http://localhost/home" }
      );
      document = dom.window.document;

      Object.defineProperty(
        document.querySelector(".first-nav.navbar.fixed-top"),
        "offsetHeight",
        { value: 50 }
      );
      Object.defineProperty(
        document.querySelector(".second-nav.navbar"),
        "offsetHeight",
        { value: 20 }
      );
      Object.defineProperty(
        document.querySelector(".footer.fixed-bottom"),
        "offsetHeight",
        { value: 30 }
      );
      document.querySelector("#navbarToggler2").style = {};
      document.querySelector("#wrapper").style = {};
      document.body.style = {};
      global.document = document;
      global.window = dom.window;
      global.window.innerHeight = 800;

      const { adjustContentPadding } = await import("../static/js/base.js");
      adjustContentPadding();

      expect(document.body.style.paddingTop).to.equal("70px");
      expect(document.querySelector("#wrapper").style.minHeight).to.equal(
        "700px"
      );
      expect(
        document.querySelector("#navbarToggler2").style.maxHeight
      ).to.equal("700px");

      expectContentStyles(document, {
        paddingTop: "70px",
        minHeight: "700px",
        maxHeight: "700px",
        secondarySelector: "#navbarToggler2",
      });
    });

    it("should not throw if some elements are missing (footer, navbarToggler)", async function () {
      dom = new JSDOM(
        `
        <body>
          <main role="main" class="flex-shrink-0">
            <div id="wrapper"></div>
            <div id="sidebar-wrapper"></div>
            <div id="page-content-wrapper"><div></div></div>
            <nav class="first-nav navbar fixed-top"></nav>
          </main>
        </body>
      `,
        { url: "http://localhost/LSTs" }
      );
      document = dom.window.document;

      Object.defineProperty(
        document.querySelector(".first-nav.navbar.fixed-top"),
        "offsetHeight",
        { value: 40 }
      );
      document.querySelector("#wrapper").style = {};
      document.body.style = {};
      global.document = document;
      global.window = dom.window;
      global.window.innerHeight = 600;

      const { adjustContentPadding } = await import("../static/js/base.js");
      expect(() => adjustContentPadding()).to.not.throw();
      expect(document.body.style.paddingTop).to.equal("40px");
      expect(document.querySelector("#wrapper").style.minHeight).to.match(
        /^\d+px$/
      );
    });

    it("should compute correct values for different window.innerHeight", async function () {
      global.document = document;
      global.window = dom.window;
      global.window.innerHeight = 1000;

      const { adjustContentPadding } = await import("../static/js/base.js");
      adjustContentPadding();

      expectContentStyles(document, {
        minHeight: "920px",
        maxHeight: "920px",
      });
    });

    it("should not throw with minimal DOM", async function () {
      dom = new JSDOM(`<body></body>`, { url: "http://localhost" });
      document = dom.window.document;
      global.document = document;
      global.window = dom.window;
      global.window.innerHeight = 500;

      const { adjustContentPadding } = await import("../static/js/base.js");
      expect(() => adjustContentPadding()).to.not.throw();
    });
  });
});
