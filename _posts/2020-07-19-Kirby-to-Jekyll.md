---
layout: post
title: Kirby 2 -> Jekyll
categories: [home, web]
---

As I switched from the Kirby 2 CMS to Jekyll (see also [here](/new-website)), I needed to convert the pages. I did that in a a fairly manual way, with the help of some simple macros. This was acceptable since I did not need to convert many pages. In the following, I describe the required changes, based on the features and plugins I have used.


| Kirby 2 | Jekyll |
| --- | --- |
| Kirby Meta Information / File Format | Jekyll Meta Information / File Format |
| Kirby Tags | Jekyll Categories |
| Kirby Links | GitHub Flavored Markdown (GFM) Links |
| Markdown Links | GFM Links |
| Kirby Images | GFM Images |
| Kirby Files | GFM Links |
| [Kirby Table of Contents](/kirby-table-of-contents/) | [jekyll-toc](https://github.com/allejo/jekyll-toc/) (```{:toc}```) |
| [Kirby References](/kirby-references/) | GFM Links |
| [Kirby BibTeX](/kirby-bibtex/) | Custom BibTeX Page |
| Kirby Youtube | GFM Links |
| Kirby Shariff | Custom Links |
| Disqus | -- |
