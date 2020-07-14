---
layout: post
title: Kirby Table of Contents
categories: [home, kirby, tech]
---

For longer blog entries, it would be nice to be able to divide them into different sections and show a table of contents, such as done on this site. While Kirby, the CMS I am using for this site, allows to add different levels of headlines by adding one or multiple # in front of text, it does not automatically create anchors, which can be linked to. Additionally, there is no option to automatically create a table of contents of a page.

> This is for Kirby 2. It might work for Kirby 1 as [Kirbytext Extension Plugin](http://getkirby.com/blog/kirbytext), but I have not tested that.
> It is untested for Kirby 3.

## Installation
To install the script, [download it](https://github.com/PhilippMundhenk/Kirby-Table-of-Contents) and simply place it in the *site/tags* folder within your Kirby installation.

## Usage
### Headlines
As I required the above functions, I implemented these myself, by using [Kirby Tags](http://getkirby.com/docs/advanced/kirbytext), thus extending the underlying Markdown specification of Kirby. I added tags for different level headlines (e.g. l1, l2, ...), which automatically generate an anchor, with the same name as the text of the headline:
```
conventional: #Headline1
new: (l1: Headline1)

conventional: ##Headline2
new: (l2: Headline2)

conventional: ###Headline3
new: (l3: Headline3)

conventional: ####Headline4
new: (l4: Headline4)

conventional: #####Headline5
new: (l5: Headline5)

conventional: ######Headline6
new: (l6: Headline6)
```

### Table of Contents
I created an additional tag, which allows to automatically create a table of contents, based on the above headline definitions:
```
(toc: 6)
```
The parameter given to the table of contents tag is the number of levels that shall be shown in the table. I do not always want to show a full table, but maybe only the first one, two or three levels. This can be accomplished by setting the parameter to the respective value.

Further, the script only selects headlines from level 2 onwards, as I am using level 1 headlines for pages or higher-level ordering.

## Issues
The table of contents currently does not implement all special characters. If used in a headline, the link might not work.

In the future a nicer or adaptable design of the table of contents could be nice. For now, this needs to be adapted manually by replacing the connector in the PHP code.

## Download
The script is available on [GitHub](https://github.com/PhilippMundhenk/bib-publication-list)