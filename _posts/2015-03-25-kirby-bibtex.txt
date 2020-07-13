Title: Kirby BibTeX

----

Date: 2015-03-25

----

Description: 

----

Tags: home,kirby,tech

----

Text: 

(l2: Introduction)
While there exist a number of publication management tools on the web, I prefer to have my publications stored locally in a BibTeX file. This BibTeX file might be easy to parse for machines, but it is neither particularly nice for humans to read nor pretty. Luckily, there exist some projects out there using JavaScript to parse a BibTeX file into HTML and show this in a pretty manner. I base my work on the work of (link: http://www.villekaravirta.com/publications/ text: Ville Karavirta popup:yes) and (link: https://github.com/lukasiewycz/lukasiewycz.github.io text: Martin Lukasiewycz popup:yes). Based on this I developed a small Kirby tag which allows to easily include a publications list into a Kirby page.

######NOTE:
>This is for Kirby 2. It might work for Kirby 1 as (link: http://getkirby.com/blog/kirbytext text: Kirbytext Extension Plugin popup:yes), but I have not tested that.

(l2: Installation)
Download the files from my (link: https://github.com/PhilippMundhenk/bib-publication-list text: repository popup:yes) into your Kirby installation. Make sure all files are are in the correct folders, following the folder structure in the repository.

(l2: Usage)
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

(l2: Demo)
I use this setup for my own publications (link: http://www.mundhenk.org/publications text: here).

(l2: Issues)
As the base code uses jQuery DataTables attached to a HTML table on document load, it is currently not possible to resize the table when the window resizes. A reload is required for that. I tried to reload the page whenever a window resize event occurs, however, this leads to reloads when scrolling fast on Chrome for Android.

(l2: Download)
The script is available on (link: https://github.com/PhilippMundhenk/Kirby-BibTeX text: GitHub popup:yes)