---
layout: post
title: TeX, TikZ, Cache
categories: [work, TeX, TikZ, tech]
---

When working in academia or writing your final thesis, you will come across TeX. While this is a great tool to write papers or a thesis, it has its caveats, one of these being performance. This especially holds when using TikZ or PGFPlots (which uses TikZ). When using these, every diagram and plot is redrawn every time you start your build process. To cache images, there is the function *\tikzexternalize*. This caches images, usually via automatically generated file names. This can lead to issues when you place a figure in the middle of your documents and do not clean the TikZ cache. Then, your figures might be confused by TeX. This is especially annoying when using the package *todonotes*, as every *\todo* is a TikZ image, resulting in confusion of ToDos whenever a new one is created.
However, there is a way around this, shown here.

This work has been created in cooperation with [Matthias Kauer](http://www.matthiaskauer.com/).

## Commands
Here, we define a hand full of commands that help us with this:
```tex
\newcommand*\execute[1]{\csname#1\endcsname}
\newcommand*\tikzprefix{figures/}

\tikzexternalize
\tikzexternaldisable

\newcommand*{\inputtikz}[1]{
    \tikzexternalenable
    \tikzsetnextfilename{#1}
    \input{#1.tex}
    \tikzexternaldisable
}

\newcommand*{\calltikz}[1]{
    \tikzexternalenable
    \tikzsetnextfilename{\tikzprefix#1}
    \execute{#1}
    \tikzexternaldisable
}
```

## Explanations
First, we define a helper macro *\execute*. This macro can take in any string and execute it like a TeX command. Thus, *\execute{test}* becomes *\test*.
Then, we define the command *\tikzprefix*, which I use to set the directory, where I want my TikZ cache for figures defined as commands to be (in this case in the subfolder *figures*).

After this, *\tikzexternalize* initiates the TikZ cache and *\tikzexternaldisable* directly disables it again. We do this so that only selected figures are affected by the cache and not others, such as ToDo notes.

Now comes the interesting part: Two commands (*\inputtikz* and *\calltikz*) are taking care of using external files with TikZ cache and using TikZ figures defined as commands somewhere in your document. Both work somewhat the same way, first enabling the TikZ cache for the current figure, before setting a file name where to figure is to be stored. In case of a TikZ file, the cache files are stored in the same directory as the original file, in case of a TikZ figure as command, the cache files are stored in the folder *figures*. Afterwards the figure is either read with *\input* or, in case of a figure as command, executed with our helper macro *\execute*. Finally, the TikZ cache is disabled again, so it does not affect any other figures.

## Example
Let me show you a minimal example:

File miniFig2.tex:
```tex
\begin{tikzpicture}
	\node[ellipse,draw] (test) {TestImage2};
\end{tikzpicture}
```

File minimal.tex:
```tex
\documentclass{book}

\usepackage{tikz}
\usetikzlibrary{shapes}
\usetikzlibrary{external}

\newcommand*\execute[1]{\csname#1\endcsname}
\newcommand*\tikzprefix{figures/}

\tikzexternalize
\tikzexternaldisable
\newcommand{\inputtikz}[1]{
	\tikzexternalenable
    \tikzsetnextfilename{#1}
    \input{#1.tex}
    \tikzexternaldisable
}

\newcommand*{\calltikz}[1]{
	\tikzexternalenable
    \tikzsetnextfilename{\tikzprefix#1}
    \execute{#1}
    \tikzexternaldisable
}

\newcommand*{\miniFig}{
	\begin{tikzpicture}
		\node[ellipse,draw] (test) {TestImage1};
	\end{tikzpicture}
}

\begin{document}

\begin{figure}
	\calltikz{miniFig}
	\caption{TestImage1}
\end{figure}

\begin{figure}
	\inputtikz{miniFig2}
	\caption{TestImage2}
\end{figure}

\end{document}
```

## Files
Files before running TeX (don't forget to create your cache folder!):
```
.
├── figures
├── miniFig2.tex
└── minimal.tex
```

Files after running TeX:
```
.
├── figures
│   ├── miniFig.dpth
│   ├── miniFig.log
│   ├── miniFig.md5
│   └── miniFig.pdf
├── miniFig2.dpth
├── miniFig2.log
├── miniFig2.md5
├── miniFig2.pdf
├── miniFig2.tex
├── minimal.aux
├── minimal.auxlock
├── minimal.fdb_latexmk
├── minimal.fls
├── minimal.log
├── minimal.pdf
├── minimal.synctex.gz
└── minimal.tex
```

Note the *.pdf outputs for the separate figures. These are your cache files, the actual figures as PDF. They are also great for presentations, in case you need to present your paper or thesis somewhere.

## Output
The final output file looks like this:
![Example output](/images/tikz/minimal.png)