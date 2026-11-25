---
layout: page
title: Search
permalink: /search/
hide_title: true
---

<div id="search-container">
    <input type="text" id="search-input" placeholder="Search through the blog posts..." data-index="{{ site.baseurl }}/search.json" autofocus>
    <ul id="results-container" style="text-align: left; list-style: none; padding-left: 0;"></ul>
</div>

<script src="{{ site.baseurl }}/assets/search.js?v={{ site.time | date: '%s' }}"></script>
