// d3loader.js
const d3Base =
  typeof window !== "undefined" && window.d3
    ? window.d3
    : (await import("d3")).default || (await import("d3"));

// In browser, d3-hexbin is loaded separately and attaches to global d3
// In Node/tests, we need to import and wrap it
const d3 = typeof window === "undefined"
  ? { ...d3Base, hexbin: (await import("d3-hexbin")).hexbin }
  : d3Base;

export default d3;
