// Local blog search: loads /search.json from this site and filters it in the browser.
// No libraries, no third-party requests.
(function () {
  "use strict";
  var input = document.getElementById("search-input");
  var results = document.getElementById("results-container");
  var index = null;

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function snippet(text, term) {
    var i = text.toLowerCase().indexOf(term);
    if (i < 0) { return ""; }
    var start = Math.max(0, i - 60);
    var end = Math.min(text.length, i + term.length + 100);
    var before = escapeHtml(text.slice(start, i));
    var hit = escapeHtml(text.slice(i, i + term.length));
    var after = escapeHtml(text.slice(i + term.length, end));
    return (start > 0 ? "… " : "") + before + "<mark>" + hit + "</mark>" + after + (end < text.length ? " …" : "");
  }

  function search(query) {
    var terms = query.toLowerCase().split(/\s+/).filter(function (t) { return t.length > 1; });
    if (!terms.length) { return []; }
    var hits = [];
    index.forEach(function (post) {
      var title = post.title.toLowerCase();
      var meta = (post.category + " " + post.date).toLowerCase();
      var body = post.content.toLowerCase();
      var score = 0;
      for (var i = 0; i < terms.length; i++) {
        var t = terms[i];
        var s = (title.indexOf(t) >= 0 ? 10 : 0) + (meta.indexOf(t) >= 0 ? 3 : 0) + (body.indexOf(t) >= 0 ? 1 : 0);
        if (s === 0) { return; } // every term must match somewhere
        score += s;
      }
      hits.push({ post: post, score: score, term: terms[0] });
    });
    hits.sort(function (a, b) { return b.score - a.score; });
    return hits;
  }

  function render(query) {
    if (!index) { return; }
    var hits = search(query);
    if (!query.trim()) { results.innerHTML = ""; return; }
    if (!hits.length) { results.innerHTML = "<li>No posts found.</li>"; return; }
    results.innerHTML = hits.map(function (h) {
      return '<li><a href="' + escapeHtml(h.post.url) + '"><h1>' + escapeHtml(h.post.title) + "</h1></a>" +
        "<span>" + escapeHtml(h.post.date) + "</span>" +
        '<p class="search-snippet">' + snippet(h.post.content, h.term) + "</p></li>";
    }).join("");
  }

  fetch(input.getAttribute("data-index"))
    .then(function (r) { return r.json(); })
    .then(function (data) { index = data; render(input.value); })
    .catch(function () { results.innerHTML = "<li>The search index could not be loaded.</li>"; });

  input.addEventListener("input", function () { render(input.value); });
})();
