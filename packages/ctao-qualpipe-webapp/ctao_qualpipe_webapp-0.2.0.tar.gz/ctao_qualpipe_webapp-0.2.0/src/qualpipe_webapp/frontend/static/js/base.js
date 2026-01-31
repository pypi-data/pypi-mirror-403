// to avoid eventListener duplications
export const resizeListeners = {};

function getOffset(element) {
  return element ? element.offsetHeight : 0;
}

function setStyleIfExists(element, styleProp, value) {
  if (element) element.style[styleProp] = value;
}

export function adjustContentPadding() {
  const body = document.querySelector("body");
  const wrapper = document.querySelector("div#wrapper");
  const sidebarWrapper = document.querySelector("div#sidebar-wrapper");
  const pageContentWrapper = document.querySelector("div#page-content-wrapper");
  const pageContentWrapperChild = document.querySelector(
    "div#page-content-wrapper div"
  );
  const navbar1 = document.querySelector(".first-nav.navbar.fixed-top");
  const footer = document.querySelector(".footer.fixed-bottom");
  const navbar2 = document.querySelector(".second-nav.navbar");
  const navbarToggler = document.querySelector("#navbarToggler");
  const navbarToggler2 = document.querySelector("#navbarToggler2");

  const hNavbar1 = getOffset(navbar1);
  const hNavbar2 = getOffset(navbar2);
  const hFooter = getOffset(footer);

  let paddingTop = hNavbar1 + (navbar2 ? hNavbar2 : 0);
  let minHeight =
    window.innerHeight - hNavbar1 - (navbar2 ? hNavbar2 : 0) - hFooter + "px";

  setStyleIfExists(body, "paddingTop", paddingTop + "px");
  setStyleIfExists(wrapper, "minHeight", minHeight);
  setStyleIfExists(
    navbarToggler,
    "maxHeight",
    window.innerHeight - hNavbar1 - hFooter + "px"
  );
  setStyleIfExists(navbarToggler2, "maxHeight", minHeight);
  setStyleIfExists(sidebarWrapper, "maxHeight", minHeight);
  setStyleIfExists(pageContentWrapper, "maxHeight", minHeight);
  setStyleIfExists(pageContentWrapperChild, "paddingBottom", hFooter + "px");
}

// Register listeners explicitly
export function registerAdjustContentPadding(targetWindow) {
  const win =
    targetWindow ||
    (typeof window !== "undefined" && window) ||
    (typeof globalThis !== "undefined" && globalThis.window) ||
    undefined;

  if (!win || typeof win.addEventListener !== "function") return;

  // Avoid double registrations
  if (win.__qp_adjust_registered) return;
  win.__qp_adjust_registered = true;

  // Adjust at any reload and resizing
  win.addEventListener("DOMContentLoaded", adjustContentPadding);
  win.addEventListener("resize", adjustContentPadding);
}

// Auto-register only in the browser (where process is undefined)
if (typeof process === "undefined") {
  try {
    registerAdjustContentPadding();
  } catch { }
}
