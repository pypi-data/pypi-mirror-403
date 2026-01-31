import d3 from "./d3loader.js";

// Map of available blindfriendly palettes from d3
const COLOR_PALETTES = {
  viridis: d3.interpolateViridis,
  plasma: d3.interpolatePlasma,
  magma: d3.interpolateMagma,
  inferno: d3.interpolateInferno,
  cividis: d3.interpolateCividis,
  turbo: d3.interpolateTurbo,
  warm: d3.interpolateWarm,
  cool: d3.interpolateCool,
};

// Default palette
let currentPalette = "viridis";

/**
 * Set palette color
 * @param {string} paletteName - Palette name (viridis, plasma, magma, etc.)
 */
export function setColorPalette(paletteName) {
  if (COLOR_PALETTES[paletteName]) {
    currentPalette = paletteName;
  } else {
    console.warn(`Palette "${paletteName}" not found, use viridis instead`);
    currentPalette = "viridis";
  }
}

/**
 * Get the color based on the normalized value using the current palette
 * @param {number} min - Minimum value of the range
 * @param {number} max - Maximum value of the range
 * @param {number} value - Value to map
 * @returns {string} Color in RGB format
 */
export function get_color(min, max, value) {
  if (value === null || value === undefined || !isFinite(value)) {
    return "#BEBEBE"; // gray color for invalid values
  }

  // Normalize value within 0 and 1
  const normalized = max > min ? (value - min) / (max - min) : 0;
  const clamped = Math.max(0, Math.min(1, normalized));

  // Use current palette color interpolator
  const interpolator = COLOR_PALETTES[currentPalette];
  return interpolator(clamped);
}

/**
 * Get the list of available color palettes
 * @returns {string[]} Array with palette names
 */
export function getAvailablePalettes() {
  return Object.keys(COLOR_PALETTES);
}
