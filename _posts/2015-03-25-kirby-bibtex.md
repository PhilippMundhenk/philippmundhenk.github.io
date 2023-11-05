---
layout: post
title: Kirby BibTeX
categories: [home, kirby, tech]
---

While there exist a number of publication management tools on the web, I prefer to have my publications stored locally in a BibTeX file. This BibTeX file might be easy to parse for machines, but it is neither particularly nice for humans to read nor pretty. Luckily, there exist some projects out there using JavaScript to parse a BibTeX file into HTML and show this in a pretty manner. I base my work on the work of [Ville Karavirta](http://www.villekaravirta.com/publications/) and [Martin Lukasiewycz](https://github.com/lukasiewycz/lukasiewycz.github.io). Based on this I developed a small Kirby tag which allows to easily include a publications list into a Kirby page.

> This is for Kirby 2. It might work for Kirby 1 as [Kirbytext Extension Plugin](http://getkirby.com/blog/kirbytext), but I have not tested that. 
> It is untested for Kirby 3.

## Installation
Download the files from my [repository](https://github.com/PhilippMundhenk/bib-publication-list) into your Kirby installation. Make sure all files are are in the correct folders, following the folder structure in the repository.

## Usage
Simply add the following tag to your page:
```
(BIBTEX: library.bib) *note: use small bibtex, had to use capital to avoid interpretation
```
This command expects the path to your library.bib file from the base of your domain.
You may also use subfolders of content, by adding the path here, e.g.:
```
(BIBTEX: publications/library.bib) *note: use small bibtex, had to use capital to avoid interpretation
```
You may further use a full URL:
```
(BIBTEX: http://www.mundhenk.org/content/library.bib) *note: use small bibtex, had to use capital to avoid interpretation
```

## Demo

> Note that this demo no longer works, since the website is not based on Kirby anymore.

I use this setup for my own publications [here](http://www.mundhenk.org/publications).

## Issues
As the base code uses jQuery DataTables attached to a HTML table on document load, it is currently not possible to resize the table when the window resizes. A reload is required for that. I tried to reload the page whenever a window resize event occurs, however, this leads to reloads when scrolling fast on Chrome for Android.

## Download
The script is available on [GitHub](https://github.com/PhilippMundhenk/Kirby-BibTeX)