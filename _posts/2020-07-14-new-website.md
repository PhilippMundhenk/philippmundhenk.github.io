---
layout: post
title: New Website
categories: [home, web]
---

Since my server provider is upgrading his systems, this means I will have to move to a newer server. Since the old version of Kirby will no longer run without problems on the newer PHP versions (7+) of the new server, I decided to go with a new website instead of re-licensing the new version of [Kirby](https://getkirby.com/).

Back when I chose Kirby I was sure that I will need server-side dynamic behavior at some point. As it turns out, I have never needed it and my website for years has been a static one, enhanced with JavaScript. Since this is also achievable without a CMS, I decided to give [Jekyll](https://jekyllrb.com/) a try. Instead of dynamically generating websites from Markdown text, whenever a website is accessed (like Kirby), or cache the requests to optimize the performance (like [Grav](https://getgrav.org/)), Jekyll generates static pages, which can be served from any simple server without the need for PHP (in the correct version). Often, Jekyll is used in combination with GitHub Pages, allowing easy serving of web-content, in modern looks, generated from Markdown automatically. This alleviates the configuration effort (e.g., for webserver) and thus increases performance, stability and availability.

For a modern look, I went with the [Reverie](https://github.com/amitmerchant1990/reverie) template. I made only minor adjustments. The website is publicly available on [GitHub](https://github.com/PhilippMundhenk/philippmundhenk.github.io).