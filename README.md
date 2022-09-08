<div>
<img src="docs/images/logo.png" align="left" width="300"/>
<img src="docs/images/huygenslogo.png" align="right" width="200"/>
<img src="docs/images/tf.png" align="right" width="200"/>
<img src="docs/images/dans.png" align="right" width="100"/>
<img src="docs/images/huc.png" align="right" width="100"/>
</div>

# General Missives

[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/Nino-cunei/oldassyrian/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/Dans-labs/clariah-gm)
[![DOI](https://zenodo.org/badge/292204502.svg)](https://zenodo.org/badge/latestdoi/292204502)
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)


# Corpus

This repo contains a structurally clean version of the data of the *General Missives*, volumes 1-14.

Read more in [about](docs/about.md).

# Rationale for this representation of the corpus

Cleaning a textual dataset is a lot of work.
If such a dataset is a standard work, it will be studied by many students/researchers from several
disciplines. 
To make life easier for those people, they should be able to start with a dataset that is readily
processable by any tool of their choice.

[Text-Fabric](https://github.com/annotation/text-fabric)
provides a
[data model](https://annotation.github.io/text-fabric/tf/about/datamodel.html)
that captures the data at the end of the cleaning process just
before it goes into other tools.
It also support the integration of subsequent annotations with the original data.

The Missiven corpus is an example how that works.

# Getting started

## Search interface to-go

For a first impression, start with
[missieven-search](https://CLARIAH.github.io/wp6-missieven-search/)
This is a static website that sends the whole corpus to your browser.
After a few seconds you can start searching.

You can do full text search via regular expressions, not only in the text,
but also in some of its attributes. For example, you can search for a word
in original letter texts or in editorial remarks.

More info in the
[manual](https://annotation.github.io/text-fabric/tf/about/clientmanual.html).

An example search is in [example.json](example.json).
Download the file, then import it in your search interface, and you see it happening.

You can save search results to excel files.

## Text-fabric browser

You get more power when you download Text-Fabric.
Text-Fabric operates in the ecosystem of Python and its libraries.

But you do not have to program in order to browse and search the corpus.
After installing Python and

```
pip3 install text-fabric
```

on the command line, say

```
text-fabric clariah/wp6-missieven
```

and a webserver on your computer is started which serves you a search-and-browse
interface on the Generale Missiven corpus.
You can search more precisely here than in the search interface-to-go above.

You can save search results to excel files.

## Jupyter notebooks

Text-Fabric is particularly suited to Jupyter notebooks.
There is a
[handy way to install](https://annotation.github.io/text-fabric/tf/about/install.html)
Python, JupyterLab in one go and Text-Fabric from there.

The next step is to consult the 
[tutorial](https://nbviewer.jupyter.org/github/CLARIAH/wp6-missieven/blob/master/tutorial/start.ipynb).
This is a series of notebooks that guides you to the computing facilities of Text-Fabric.
Text-Fabric is just a library that you import in your own Python programs,
which means that you can invoke the whole of Python and its libraries to do your job.
The only thing Text-Fabric does is to offer you a handy computing interface to the
textual data and their annotations.

See
[other corpora](https://annotation.github.io/text-fabric/tf/about/corpora.html)
for experiences with Text-Fabric as a pre-processing tool in other corpora.


# Getting the corpus data

The data of the corpus is in the `wp6-missieven` repo on GitHub:

* as simple, TEI-like XML (see the xml directory in this repo)
* as plain text-fabric files (see the tf directory in this repo)

If you use any method of working with the corpus indicated above, you do not have to
do anything special to download the data.
If you tell Text-Fabric it is in `clariah/wp6-missieven`,
it can find it and download it when needed. Automatically.


# Authors

This repo is by

*   [Dirk Roorda](https://github.com/dirkroorda) at
    [KNAW/HuC](https://huc.knaw.nl/di/text/)

## Acknowledgements

* Jesse de Does provided TEI-XML files for volumes 1-13.
* Lodewijk Petram provided textual PDFs for volume 14, bands (i) and (ii).
* Sophie Arnoult used the Text-Fabric data to perform Named Entity Recognition.

# Long term preservation and reproducibility

This repo has been archived in two independent places:

* at [Zenodo](https://zenodo.org)
* at [Software Heritage](https://archive.softwareheritage.org)

Click the respective badges above to be taken to the archives.
There you find ways to cite this work.

You can rerun the conversion programs on the source data and
regenerate the simple XML and Text-Fabric versions of the data.
See the
[reproduce](https://github.com/CLARIAH/wp6-missieven/blob/master/docs/reproduce.md).
guide.

# Status

*   2022-05-04 version 1.0: Additional volumes: Volume 14, bands (i) and (ii) have been added.
    The earlier corrections by Sophie have not been re-applied, but the conversion has been improved 
    so that they are not needed anymore.
*   2022-04-11 Additional volumes: Volume 14, bands (i) and (ii) are in the process of being converted from
    textual pdf to Text-Fabric. Most structure has been recognized, but no TF has been generated yet.

[older ...](docs/history.md)


# More interfaces
Another version of the data (less cleaned) is visible online in a
[Blacklab interface ](http://corpora.ato.ivdnt.org/corpus-frontend/Missiven/search)

A latent wish is to make the data of this repository available in a Blacklab interface.
In this repo we show how to set up a local Blacklab server and front-end and how to get the
present data into Blacklab.

**This is work in progress**, at this point follow the
[blacklab install guide for macos](https://github.com/CLARIAH/wp6-missieven/blob/master/blacklab/install.md).

Thanks to Jesse de Does (key user of Blacklab, INT) and
Jan Niestadt (main author of Blacklab, INT) for helping out with setting up and using Blacklab.
