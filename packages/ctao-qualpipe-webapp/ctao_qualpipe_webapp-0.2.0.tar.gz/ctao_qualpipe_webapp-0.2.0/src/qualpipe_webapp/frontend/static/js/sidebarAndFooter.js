import { API_URL } from "./config.js";

function createOption(
  value,
  text,
  { disabled = false, selected = false } = {}
) {
  const option = document.createElement("option");
  option.value = value;
  option.textContent = text;
  option.disabled = disabled;
  option.selected = selected;
  return option;
}

function addTelIDOptions(selectTelID, start, end) {
  for (let i = start; i <= end; i++) {
    selectTelID.appendChild(createOption(i, i));
  }
}

function populateLSTs(selectTelID) {
  addTelIDOptions(selectTelID, 1, 4);
}

function populateMSTs(selectTelID, site) {
  if (site === "North") {
    addTelIDOptions(selectTelID, 5, 59);
  } else if (site === "South") {
    addTelIDOptions(selectTelID, 5, 29);
    addTelIDOptions(selectTelID, 100, 130);
  }
}

function populateSSTs(selectTelID, site) {
  if (site === "South") {
    addTelIDOptions(selectTelID, 30, 99);
    addTelIDOptions(selectTelID, 131, 179);
  }
}

function populateTelIDOptions(selectTelID, site, telType) {
  // Remove current options
  selectTelID.innerHTML = "";
  selectTelID.appendChild(
    createOption("0", "select a Tel ID", {
      disabled: true,
      selected: true,
    })
  );

  if (site !== "North" && site !== "South") {
    return;
  }

  switch (telType) {
    case "LSTs":
      populateLSTs(selectTelID);
      break;
    case "MSTs":
      populateMSTs(selectTelID, site);
      break;
    case "SSTs":
      populateSSTs(selectTelID, site);
      break;
    default:
      break;
  }
}

function populateOBOptions(selectOB, obs) {
  // Clear old options
  selectOB.innerHTML = "";
  if (!obs.length) {
    selectOB.appendChild(
      createOption("0", "No OBs available", {
        disabled: true,
        selected: true,
      })
    );
    return "No OBs available";
  }
  selectOB.appendChild(
    createOption("0", "Select an OB", {
      disabled: true,
      selected: true,
    })
  );
  obs.forEach((ob) => selectOB.appendChild(createOption(ob, ob)));
  return "Select an OB";
}

export function setupSidebarAndFooter(window, document) {
  // Wait for DOMContentLoaded to ensure elements are present
  document.addEventListener("DOMContentLoaded", async function () {
    console.log("=== SIDEBAR AND FOOTER SETUP STARTING ===");

    // Set up event listeners for mouse enter/leave sidebar
    const SIDEBAR_EL = document.getElementById("wrapper");
    const sidebarWrapper = document.getElementById("sidebar-wrapper");
    sidebarWrapper.addEventListener("mouseenter", () =>
      SIDEBAR_EL.classList.remove("collapsed")
    );
    sidebarWrapper.addEventListener("mouseleave", () =>
      SIDEBAR_EL.classList.add("collapsed")
    );

    // Helper functions to save/load state
    const STORAGE_KEY = "qualpipe_selections";

    function saveSelections() {
      const state = {
        site: selectSite.value,
        date: $("#date-picker").val(),
        ob: selectOB ? selectOB.value : null,
        telId: isTelescopeElement && selectTelID ? selectTelID.value : null,
      };

      // Only save if we have the minimum required data
      if (!state.site || !state.date) {
        console.log("Not saving - missing required fields");
        return;
      }

      // For telescope pages, require OB and telId
      if (isTelescopeElement) {
        if (!state.ob || state.ob === "0" || !state.telId || state.telId === "0") {
          console.log("Not saving - telescope page missing OB or telId");
          return;
        }
      }

      console.log("Saving selections:", state);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    }

    function loadSelections() {
      const stored = localStorage.getItem(STORAGE_KEY);
      const parsed = stored ? JSON.parse(stored) : null;
      console.log("Loaded selections:", parsed);
      return parsed;
    }

    // Datepicker initialization
    $("#date-picker").datepicker({
      format: "yyyy-mm-dd",
      autoclose: true,
      todayHighlight: true,
      todayBtn: true,
      clearBtn: true,
      calendarWeeks: true,
      orientation: "right",
    });

    function handleDatepickerMouseEnter() {
      SIDEBAR_EL.classList.remove("collapsed");
    }

    function handleDatepickerMouseLeave() {
      SIDEBAR_EL.classList.add("collapsed");
    }

    function attachDatepickerSidebarEvents() {
      const datepickerDiv = document.querySelector(
        ".datepicker.datepicker-dropdown"
      );
      if (datepickerDiv) {
        datepickerDiv.addEventListener(
          "mouseenter",
          handleDatepickerMouseEnter
        );
        datepickerDiv.addEventListener(
          "mouseleave",
          handleDatepickerMouseLeave
        );
      }
    }

    $("#date-picker").on("show", function () {
      // Wait until datepicker is actually in the DOM
      setTimeout(attachDatepickerSidebarEvents, 0);
    });

    let dateOBs = {};
    // Fetch the OB-Date mapping from the JSON file
    // It is used to populate the OB dropdown based on the selected date
    $.getJSON(`${API_URL}/v1/ob_date_map`, function (data) {
      dateOBs = data;
    }).fail(function () {
      console.error("Failed to load /data/v1/ob_date_map.json");
    });

    const path = window.location.pathname; // e.g. "/LSTs/pointings"
    const arrayElement = path.split("/").filter(Boolean)[0];
    const validTelTypes = ["LSTs", "MSTs", "SSTs"];
    const isTelescopeElement = validTelTypes.includes(arrayElement);

    // sidebar elements - declare these at top level so saveSelections can access them
    const selectSite = document.getElementById("which-Site");
    const selectOB = document.getElementById("which-OB");
    const selectTelID = document.getElementById("which-Tel-ID");

    // footer elements
    const footerSite = document.getElementById("footer-site");
    const footerDate = document.getElementById("footer-date");
    const footerOB = document.getElementById("footer-ob");
    const footerTelType = document.getElementById("footer-tel-type");
    const footerTelID = document.getElementById("footer-tel-id");

    // Set up starting value
    footerSite.textContent = selectSite.value;

    if (isTelescopeElement) {
      // Set up starting value
      footerTelType.textContent = arrayElement;

      selectSite.addEventListener("change", function () {
        populateTelIDOptions(selectTelID, selectSite.value, arrayElement);
        footerSite.textContent = selectSite.value;
        saveSelections();
      });

      selectTelID.addEventListener("change", function () {
        footerTelID.textContent = selectTelID.value;
        footerTelID.style.color = ""; // Remove any inline color style (including red)
        saveSelections();
      });
    } else {
      selectSite.addEventListener("change", function () {
        footerSite.textContent = selectSite.value;
        saveSelections();
      });
    }

    if (selectOB) {
      selectOB.addEventListener("change", function () {
        footerOB.textContent = selectOB.value;
        footerOB.style.color = ""; // Remove any inline color style (including red)
        saveSelections();
      });
    }

    // Datepicker change event to update footer date and OB dropdown
    $("#date-picker").on("changeDate", function () {
      const selectedDate = $("#date-picker").val();
      footerDate.textContent = selectedDate;
      footerDate.style.color = ""; // Remove any inline color style (including red)

      // If we remove the OB in the sidebar the following part should be revised
      if (isTelescopeElement) {
        const obs = dateOBs[selectedDate] || [];
        const firstOB = populateOBOptions(selectOB, obs);
        footerOB.textContent = firstOB;
        footerOB.style.color = "red";
      }
      // Don't save here - wait for user to select OB and telId
    });

    const buttonMakePlot = document.getElementById("makePlot");
    let makePlot;
    if (buttonMakePlot) {
      const plotModule = await import("./plot.js");
      makePlot = plotModule.makePlot;
      buttonMakePlot.addEventListener("click", () => makePlot());
    }

    // Restore previous selections
    const savedState = loadSelections();
    console.log("Attempting to restore state:", savedState);
    if (savedState) {
      // Restore site
      if (savedState.site && selectSite) {
        selectSite.value = savedState.site;
        footerSite.textContent = savedState.site;
        console.log("Restored site:", savedState.site);
      }

      // Wait for dateOBs to be loaded before restoring date/OB
      const checkDateOBsLoaded = setInterval(() => {
        if (Object.keys(dateOBs).length > 0) {
          clearInterval(checkDateOBsLoaded);
          console.log("dateOBs loaded, restoring date/OB");

          // Restore date
          if (savedState.date) {
            $("#date-picker").datepicker("setDate", savedState.date);
            footerDate.textContent = savedState.date;
            footerDate.style.color = "";
            console.log("Restored date:", savedState.date);

            // Populate OB options for the restored date
            if (isTelescopeElement) {
              const obs = dateOBs[savedState.date] || [];
              populateOBOptions(selectOB, obs);
              console.log("Available OBs for date:", obs);

              // Restore OB
              if (savedState.ob && savedState.ob !== "0" && obs.includes(parseInt(savedState.ob))) {
                selectOB.value = savedState.ob;
                footerOB.textContent = savedState.ob;
                footerOB.style.color = "";
                console.log("Restored OB:", savedState.ob);
              }
            }
          }

          // Restore telescope ID if applicable
          if (isTelescopeElement && savedState.telId && savedState.telId !== "0") {
            // Populate Tel ID options first
            populateTelIDOptions(selectTelID, savedState.site, arrayElement);

            // Then restore the saved Tel ID
            setTimeout(() => {
              if (selectTelID) {
                selectTelID.value = savedState.telId;
                if (footerTelID) {
                  footerTelID.textContent = savedState.telId;
                  footerTelID.style.color = "";
                }
                console.log("Restored Tel ID:", savedState.telId);

                // Auto-trigger plot if all parameters are valid
                if (makePlot && savedState.site && savedState.date && savedState.ob && savedState.ob !== "0") {
                  console.log("Auto-triggering makePlot");
                  setTimeout(() => makePlot(), 100);
                }
              }
            }, 100);
          } else if (!isTelescopeElement && savedState.date && savedState.site) {
            // For non-telescope pages, trigger plot if date and site are set
            if (makePlot) {
              setTimeout(() => makePlot(), 100);
            }
          } else if (isTelescopeElement) {
            // If no saved telId, still need to populate the dropdown
            populateTelIDOptions(selectTelID, savedState.site, arrayElement);
          }
        }
      }, 100);

      // Safety timeout to clear interval
      setTimeout(() => clearInterval(checkDateOBsLoaded), 5000);
    } else {
      // Initial trigger only if no saved state
      if (isTelescopeElement && selectTelID) {
        selectSite.dispatchEvent(new Event("change"));
      }
    }
  });
}

if (typeof window !== "undefined" && typeof document !== "undefined") {
  setupSidebarAndFooter(window, document);
}
