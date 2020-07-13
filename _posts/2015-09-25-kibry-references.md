Title: Kirby Reference Management

----

Date: 2015-09-25

----

Description: 

----

Tags: home,tech,kirby

----

Text: 

(l2: Introduction)
As I often cite multiple sources in my articles here in Kirby, I built a minimal reference management, that lets me simply refer to these sources by a tag in the text. The actual URL of the source is then given at the bottom of the article in a separate section.

To make this process a little simpler, I built a mini tag for Kirby, which allows me to easily reference to sources in multiple places in the text.

(l2: Demo)
```
(Ref: PM2015) //use small r in ref
```
yields:
(ref: PM2015)

```
(Source: PM2015 url:https://www.mundhenk.org) //use small s in source
```
yields
(source: PM2015 url:https://www.mundhenk.org)

You may create links to sources which open in new windows by adding *popup:yes* or *popup:true* to your (Source: ) tag.