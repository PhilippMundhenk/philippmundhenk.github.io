// Colour scheme: "system" (default, follows the OS), "light" or "dark".
// The choice is kept in this browser's localStorage only; nothing is sent anywhere.
(function () {
  "use strict";
  var KEY = "theme";
  var ORDER = ["system", "light", "dark"];
  var ICON = { system: "\u25D0", light: "\u2600", dark: "\u263E" };
  var LABEL = { system: "Colour theme: system", light: "Colour theme: light", dark: "Colour theme: dark" };

  function stored() {
    try { return localStorage.getItem(KEY) || "system"; } catch (e) { return "system"; }
  }
  function apply(mode) {
    if (mode === "light" || mode === "dark") { document.documentElement.setAttribute("data-theme", mode); }
    else { document.documentElement.removeAttribute("data-theme"); }
  }
  apply(stored()); // runs in <head>, before the page is painted

  document.addEventListener("DOMContentLoaded", function () {
    var button = document.getElementById("theme-toggle");
    if (!button) { return; }
    function show(mode) { button.textContent = ICON[mode]; button.title = LABEL[mode]; button.setAttribute("aria-label", LABEL[mode] + " (click to change)"); }
    button.hidden = false;
    show(stored());
    button.addEventListener("click", function () {
      var next = ORDER[(ORDER.indexOf(stored()) + 1) % ORDER.length];
      try { if (next === "system") { localStorage.removeItem(KEY); } else { localStorage.setItem(KEY, next); } } catch (e) {}
      apply(next);
      show(next);
    });
  });
})();
