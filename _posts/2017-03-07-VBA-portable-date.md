---
layout: post
title: VBA Portable Date
categories: [home, tech, VBA]
---

In Excel, the date format depends on the locale setting of the computer, e.g., the formula =TEXT(TODAY(),"YYYY-MM-DD") only works correctly on computers set to English locales, and =TEXT(HEUTE(),"JJJJ-MM-TT") works on computers with German locale settings. This makes worksheets with such functions not portable between computers with different locale settings.

This VBA macro adds =PORTABLE_TODAY() function, which fixes this problem and works on any computer. 

## Installation
In the worksheet, where you want to add this code, press **Alt+F11**, Press **Insert > Module** and paste the below code. Then save the worksheet and add the formula =PORTABLE_TODAY() wherever you require.

## Code
<script src="https://gist.github.com/PhilippMundhenk/17e780e2cbcdc054e48a3ad3e5faa13a.js"></script>