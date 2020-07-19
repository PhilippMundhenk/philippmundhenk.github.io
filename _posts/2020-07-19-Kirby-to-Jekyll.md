---
layout: post
title: Kirby 2 -> Jekyll
categories: [home, web]
---

As I switched my website from the Kirby 2 to Jekyll (see also [here](/new-website)), I needed to convert the pages. I did that in a a fairly manual way, with the help of some simple macros. This was acceptable since I did not need to convert many pages. In the following, I describe the required changes, based on the features and plugins I have used.


| Kirby 2 | Jekyll |
| --- | --- |
| Kirby Meta Information / File Format | Jekyll Meta Information / File Format |
| Kirby Tags | Jekyll Categories |
| Kirby Links | GitHub Flavored Markdown (GFM) Links |
| Markdown Links | GFM Links |
| Kirby Images | GFM Images |
| Kirby Files | GFM Links |
| [Kirby Table of Contents](/kirby-table-of-contents/) | [jekyll-toc](https://github.com/allejo/jekyll-toc/) |
| [Kirby References](/kirby-references/) | GFM Links |
| [Kirby BibTeX](/kirby-bibtex/) | Custom BibTeX Page |
| Kirby YouTube | GFM Links |
| Kirby Shariff | Custom Links |
| Disqus | -- |

In the following, I want to explain some of the above items in more detail:

## Meta Information, File Format & Tags/Categories
To generate the pages from Markdown files, both Kirby and Jekyll need some information. This includes the title of the page, the date to be published and tags in Kirby or categories in Jekyll. In Kirby all of this data is added inside the file as a header, while in Jekyll, the date is contained in the filename, while the rest of the information is contained in slightly different format inside the file. Overall no big deal to change, I did that manually. For my 20 or so posts, this was no problem.

## Links & Files
In Kirby, one can use a separate tag for links, e.g., also specifying the target (e.g., new window/tab). I had made heavy use of that, usually opening external links in a new tab. This is not possible in GFM. Instead, I just rely on plain GFM links. Since there is a large number of links in my blog, I used a small macro I created in Notepad++ to convert the format from Kirby to GFM. I used almost exclusively the same order and even spacing in my blog, which made conversion with a macro very easy. I did afterward manually had to shift the oder of text and link brackets though, which I would automate also (e.g., by using sed), if I were to do it again.

Kirby also has a dedicated tag for files. I completely replaced that with GFM links.

## Images
Kirby uses a dedicated tag for images, I manually replaced this with the GFM format for images. Also I had to move the images from Kirby's one folder per post, to a a central image storage. I am not a big fan of that new structure and maybe it can be done in different ways, but seeing the few images I use, there is no point making a fuzz.

## Table of Contents
Some time ago I built a [table of contents plugin for Kirby}(/kirby-table-of-contents/) posts that has become quite popular in the community and has been used by many people. It replaced the default Markdown headlines with a dedicated Kirby tag (for each level) and allows to automatically generate a table of contents for a post. While I hate giving that up, Jekyll of course brings such functionality along already. You can either use the ```{:toc}``` tag on every page, which did not work for me out of the box, or use a [Jekyll plugin](https://github.com/allejo/jekyll-toc/) to add the table of contents to your layout. Since I wanted a table of contents on every page that contains headlines automatically, I went with that.

## References
Having an academic education, reference management is something that I wanted to use also in Kirby. I wrote [a small plugin](/kirby-references/) for that as well. I have however, not used this in many posts, since it is more customary to use links directly on the text in websites. Both systems have advantages and disadvantages, but I can live with normal links. Converting these references was not easy though, since the style of writing is slightly different when using references versus links. I thus manually went through the posts containing references and added the links in the appropriate places.

## BibTeX
My publications and patents list was always an important part of my website. And while I don't publish as regularly as I used to (in industry patents are just more common, but also rather seldom), I still want to keep this list on my page. Obviously, my [Kirby BibTeX plugin](/kirby-bibtex/) no longer works, so I had to add it in a different way. Luckily, the BibTeX generator I use is based on JavaScript and running fully in the browser, thus there is no issue using it with Jekyll and GitHub Pages. I simply had to move the required scripts and CSS files, as well as the BibTeX library into the new folder structure of Jekyll, create a new layout, where I add the BibTeX plugin and use this for a page. Now of course, this could be enhanced into a proper configurable Jekyll plugin, and I might do that at some point, but it works for me for now.

This is the layout I used:
{% raw %}
```html
---
layout: default
---

<article class="page">

  <h1>{{ page.title }}</h1>

  <div class="entry">
    <div class="content">
        <div>
			<link rel="stylesheet" href="/assets/bibtex/bib-publication-list.css">
			<div class="publications">
				<table id="pubTable" class="display"></table>
			</div>
			<script type="text/javascript" src="https://code.jquery.com/jquery-2.1.4.min.js"></script>
			<script type="text/javascript" src="https://cdn.datatables.net/1.6.2/js/jquery.dataTables.min.js"></script>
			<script type="text/javascript" src="/assets/bibtex/BibTex-0.1.2.js"></script>
			<script type="text/javascript" src="/assets/bibtex/bib-publication-list.js"></script>
			<script type="text/javascript">$(document).ready(function() {bibtexify('/files/library.bib', 'pubTable');});</script>
		</div>
	</div>
	
	{{ content }}
  </div>
</article>
```{% endraw %}

I had to do some minor tweaks to the CSS, as I did not like the table borders it inherited from the Jekyll theme, but this is a matter of personal taste.

## YouTube
In Kirby, it is possible to directly embed YouTube videos via dedicated tag. While this is very neat, I decided that I will go the easy way and replace these videos with simple links to YouTube. Not quite as neat, but works.

## Shariff
I used the [Shariff buttons](https://github.com/heiseonline/shariff) via a [Kirby plugin](https://github.com/SpicyWeb-de/kirby-plugin-shariff). These buttons, developed by Heise, allow simple sharing of pages through social networks without integrating tracking cookies, etc. on my website. These are great, but I found that sharing for the most common networks is also possible with simple links. Some of those where already integrated with the theme I use, I additionally added the sharing link for LinkedIn. These are the links to use in your layout:

{% raw %}
```html
<a href="http://twitter.com/share?text={{page.title}}&url={{site.url}}{{page.url}}" target="_blank">Twitter</a>
<a href="https://www.facebook.com/sharer.php?u={{site.url}}{{page.url}}" target="_blank">Facebook</a>
<a href="https://www.linkedin.com/shareArticle?mini=true&url={{site.url}}{{page.url}}" target="_blank">LinkedIn</a>
```
{% endraw %}

## Disqus
I had been using Disqus for comments on my website. While this is JavaScript based and support for it is available in Jekyll and the [Reverie Theme](https://github.com/amitmerchant1990/reverie) I use, I decided to drop it. Most readers contact my directly via mail and I had very few comments over the years.

## Conclusion
Depending on which plugins you use, your migration might differ of course, but since Markdown is the basis for both Kirby 2 and Jekyll with GFM, it is fairly easy to convert pages from one to another, even in a manual fashion. The whole process took in the area of single-digit hours, with most time spent on re-building BibTeX and integrating the references into the text. Certainly a doable effort.