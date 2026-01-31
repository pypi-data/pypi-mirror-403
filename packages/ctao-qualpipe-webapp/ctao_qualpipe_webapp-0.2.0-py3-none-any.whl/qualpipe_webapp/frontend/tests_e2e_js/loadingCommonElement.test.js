import { test, expect } from "@playwright/test";

const scopes = [{ scope: "LSTs" }, { scope: "MSTs" }, { scope: "SSTs" }];

const pages = [
  { endpoint: "", keyword: "Home" },
  { endpoint: "/pointings", keyword: "Pointings" },
  { endpoint: "/event_rates", keyword: "Event rates" },
  { endpoint: "/trigger_tags", keyword: "Trigger tags" },
  { endpoint: "/interleaved_pedestals", keyword: "Interleaved pedestals" },
  {
    endpoint: "/interleaved_flat_field_charge",
    keyword: "Interleaved flat field charge",
  },
  {
    endpoint: "/interleaved_flat_field_time",
    keyword: "Interleaved flat field time",
  },
  { endpoint: "/cosmics", keyword: "Cosmics" },
  { endpoint: "/pixel_problems", keyword: "Pixel problems" },
  { endpoint: "/muons", keyword: "Muons" },
  {
    endpoint: "/interleaved_pedestals_averages",
    keyword: "Interleaved pedestals averages",
  },
  { endpoint: "/interleaved_FF_averages", keyword: "Interleaved FF averages" },
  { endpoint: "/cosmics_averages", keyword: "Cosmics averages" },
];

function checkCommonElements({
  wrapper,
  sidebarWrapper,
  pageContentWrapper,
  firstNav,
  secondNav,
  footer,
  relativePath,
  errors,
}) {
  expect(wrapper).not.toBeNull();
  expect(sidebarWrapper).not.toBeNull();
  expect(pageContentWrapper).not.toBeNull();
  expect(firstNav).not.toBeNull();
  expect(footer).not.toBeNull();
  if (relativePath === "/home") {
    expect(secondNav).toBeNull();
  } else {
    expect(secondNav).not.toBeNull();
  }
  expect(errors, `Console errors: ${errors.join("\n")}`).toEqual([]);
}

async function runCommonElementTest({ page, relativePath }) {
  const errors = [];
  page.on("pageerror", (err) => errors.push(err));
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(msg.text());
  });

  // Use networkidle for more reliable page loading, especially in Firefox
  await page.goto(relativePath, {
    waitUntil: "networkidle",
    timeout: 60000  // Increase timeout to 60s for Firefox module loading issues
  });

  const wrapper = await page.$("#wrapper");
  const sidebarWrapper = await page.$("#sidebar-wrapper");
  const pageContentWrapper = await page.$("#page-content-wrapper");
  const firstNav = await page.$("#first-nav");
  const secondNav = await page.$("#second-nav");
  const footer = await page.$("footer");

  checkCommonElements({
    wrapper,
    sidebarWrapper,
    pageContentWrapper,
    firstNav,
    secondNav,
    footer,
    relativePath,
    errors,
  });
  // Further DOM check can be added here
}

for (const { scope } of scopes) {
  for (const { endpoint, keyword } of pages) {
    const relativePath = `/${scope}${endpoint}`;
    test(`'${scope}': '${keyword}' page loads with 2 navigation-bars, side-bar and footer`, async ({
      page,
    }) => {
      await runCommonElementTest({ page, relativePath });
    });
  }
}

test("'Home': summary page loads with 1 navigation-bar, side-bar and footer", async ({
  page,
}) => {
  await runCommonElementTest({
    page,
    relativePath: "/home",
  });
});
