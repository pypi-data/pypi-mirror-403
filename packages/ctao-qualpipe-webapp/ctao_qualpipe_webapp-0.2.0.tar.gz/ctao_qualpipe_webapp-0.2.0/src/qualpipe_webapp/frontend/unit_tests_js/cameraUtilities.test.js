import { expect } from "chai";

describe("Tests for 'cameraUtilities.js':", function () {
    it("setColorPalette should accept a known palette", async function () {
        const mod = await import("../static/js/cameraUtilities.js");
        // Should not throw for known palette
        expect(() => mod.setColorPalette("plasma")).to.not.throw();

        // Should return a non-gray color for a valid number
        const c = mod.get_color(0, 10, 5);
        expect(c).to.be.a("string");
        expect(c).to.not.equal("#BEBEBE");
    });

    it("setColorPalette should fall back to viridis for unknown palette", async function () {
        const mod = await import("../static/js/cameraUtilities.js");
        // Unknown palette triggers fallback (no throw)
        expect(() => mod.setColorPalette("not-a-palette")).to.not.throw();

        // Still returns a valid color string
        const c = mod.get_color(0, 1, 0.2);
        expect(c).to.be.a("string");
    });

    it("get_color should return gray for invalid values", async function () {
        const mod = await import("../static/js/cameraUtilities.js");
        expect(mod.get_color(0, 1, null)).to.equal("#BEBEBE");
        expect(mod.get_color(0, 1, undefined)).to.equal("#BEBEBE");
        expect(mod.get_color(0, 1, NaN)).to.equal("#BEBEBE");
    });

    it("getAvailablePalettes should include viridis", async function () {
        const mod = await import("../static/js/cameraUtilities.js");
        const palettes = mod.getAvailablePalettes();
        expect(palettes).to.be.an("array");
        expect(palettes).to.include("viridis");
    });
});
