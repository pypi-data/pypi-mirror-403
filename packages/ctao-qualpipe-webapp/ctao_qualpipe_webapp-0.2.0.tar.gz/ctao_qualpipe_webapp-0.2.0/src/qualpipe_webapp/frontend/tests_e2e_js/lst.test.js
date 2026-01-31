import { test, expect } from "@playwright/test";

test("LST: 'event rates' page shows error if 'Make Plot' button is clicked without selecting parameters first", async ({
  page,
}) => {
  await page.goto("/LSTs/event_rates", {
    waitUntil: "networkidle",
    timeout: 60000
  });

  // Take a debug snapshot before hovering the sidebar
  await page.screenshot({
    path: "playwright-snapshot/1_event_rates_before_hovering_sidebar.png",
    fullPage: false,
  });

  // Simulate mouse movement over the sidebar to trigger sidebar expansion hover effects
  await page.hover("#sidebar-wrapper");

  // Wait 1 second to allow animation/effect
  await page.waitForTimeout(1000);

  // Take a debug snapshot after hovering the sidebar
  await page.screenshot({
    path: "playwright-snapshot/2_event_rates_after_hovering_sidebar.png",
    fullPage: false,
  });

  // Verify button existence and click
  const makePlotButton = page.locator("#makePlot");
  await expect(makePlotButton).toBeEnabled();

  // Take screenshot before clicking
  await page.screenshot({
    path: "playwright-snapshot/3_before_click.png",
    fullPage: false,
  });

  // Click on the button without selecting parameterss first
  await makePlotButton.click();

  // Wait for DOM updates and JavaScript execution
  await page.waitForTimeout(1000);

  // Take screenshot after clicking to debug
  await page.screenshot({
    path: "playwright-snapshot/4_after_click_debug.png",
    fullPage: false,
  });

  // Wait for the error message to become visible with longer timeout
  const errorMessage = page.locator("#missingInfo");
  await errorMessage.waitFor({ state: "visible", timeout: 10000 });

  // Verify content
  await expect(errorMessage).toContainText(
    "Please select a 'date' from the dropdown menu."
  );

  // Take a debug snapshot
  await page.screenshot({
    path: "playwright-snapshot/5_event_rates_error.png",
    fullPage: false,
  });
  await page.screenshot({
    path: "playwright-snapshot/6_event_rates_error_FULLPAGE.png",
    fullPage: true,
  });
});
