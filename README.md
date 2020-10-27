<div>
<img src="docs/images/logo.png" align="left" width="300"/>
<img src="docs/images/huygenslogo.png" align="right" width="200"/>
<img src="docs/images/tf.png" align="right" width="200"/>
<img src="docs/images/dans.png" align="right" width="100"/>
</div>

General Missives
=================

[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/Nino-cunei/oldassyrian/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/Dans-labs/clariah-gm)

[![DOI](https://zenodo.org/badge/292204502.svg)](https://zenodo.org/badge/latestdoi/292204502)


Status
------

This is **work in progress!**

*   2020-10-13 A new TF version (0.3) has been delivered
    Footnote bodies are almost all checked and corrected (12247 in total),
    footnote marks have been checked
    en corrected for volumes 1-4, there remain at least (300) pages with unlinked footnotes
    out of the 5270 pages that have footnotes.
    Editorial text is now in the main text, on equal footing with the original letter content,
    but separable from it in a number of ways.
*   2020-10-13 A new TF version (0.2) has been delivered, and there is now a TF-app
    [missieven](https://github.com/annotation/app-missieven) for this corpus.
    That means that functions like the Text-Fabric browser and easy downloading of data are supported.
    There is still cleaning work to do, especially in linking the footnotes to the proper
    footnote references.
    There are also a few mis-encoded tables (from landscape format), that need manual adjustment,
    and some pages that are altoghether missing.
    See [trimTei0.py](https://github.com/Dans-labs/clariah-gm/blob/master/programs/trimTei0.py) where some of those
    pages have already been added.
*   2020-10-07 Many checks have been performed, many structural corrections
    w.r.t the TEI source have been performed,
    the metadata of all metadata has been thoroughly checked and corrected.
    See the reports in
    [trimreport2](trimreport2).
*   2020-09-16 First TF dataset created, but incomplete (notes are left out, checks needed)
    See 
    [last trimTei run](log-trimTei.txt)
    and
    [last tfFromTrim run](log-tfFromTrim.txt)
*   2020-09-02 Repository created, no content yet, start of conversion coding.

Corpus
------

This repo contains a Text-Fabric (TF) version of the data of the *General Missives*.

The *Generale Missiven* is a collection of letters from governors of the
VOC (Dutch East Indian Company) to
the *Heren 17*, the council of the governors of the 17 provinces of the Netherlands,
which was the effective
government of the Low Countries at the time of the 17th and 18th century.

The letters comprise 13 volumes and date from 1610 to 1761.

The Huygens-ING institute publishes this material:
[General Missives Website](http://resources.huygens.knaw.nl/retroboeken/generalemissiven/#page=0&accessor=toc&view=homePane),
see also
[General Missives Project](http://resources.huygens.knaw.nl/vocgeneralemissiven);
both websites are in Dutch.

The CLARIAH project uses a TEI version of this corpus in its Work Package 6 which deals with
new infrastructure for academic text processing:
[WP6-Text](https://www.clariah.nl/en/work-packages/focus-areas/text?layout=blog).
That work is conducted and carried out by

* [Lodewijk Petram](https://www.lodewijkpetram.nl)
* [Jesse de Does](https://www.researchgate.net/profile/Jesse_De_Does)
* [Sophie Arnoult](http://www.illc.uva.nl/People/person/3601/Ir-Sophie-Arnoult)

This repo does not publish the source/intermediate data as developed in CLARIAH-WP6;
they will publish their materials in due course.

Text-Fabric
--------------------------------------

The CLARIAH WP6 people kindly provided me with a TEI version of the corpus.

From there I made a conversion
[trimTei.py](https://github.com/Dans-labs/clariah-gm/blob/master/programs/trimTei.py)
to simplified pseudo TEI, leaving out all bits that do not end up in the final dataset,
and reorganizing some material to facilitate the conversion to TF.

However, this TEI version contains many inaccuracies.
There are many instances of miscategorized material: page headers and footers end up in body text and vice versa;
editorial notes and footnotes are not always properly detected; dozens of letters have not been separated;
metadata is often incoorect.

In order to produce a quality dataset, I needed to do something about it: checks and corrections.
In particular, all metadata has been freshly distilled from the letter headings, an in case of doubt the
online images of the missives have been inspected.

Then I used the
[walker module from TF](https://annotation.github.io/text-fabric/convert/walker.html#gsc.tab=0)
to turn the simple XML into TF.
See
[tfFromTrim.py](https://github.com/Dans-labs/clariah-gm/blob/master/programs/tfFromTrim.py).

Rationale
-----------------

The reason for this exercise is that Text-Fabric takes the concept of stand-off annotation
to an extreme,
and I want to see whether that approach makes it easier to pre-process this corpus
for all sorts of processing pipelines.

See
[other corpora](https://annotation.github.io/text-fabric/about/corpora.html#gsc.tab=0)
for more experiences with Text-Fabric as a corpus pre-processing tool.

Text-Fabric operates in the ecosystem of Python and its libraries
and is particularly suited to Jupyter notebooks.

TF from TEI
-----------
For details about the conversion from TEI to TF, see 
[transcription](docs/transcription.md)

Getting started
===============

**to come:**

Start with the
[tutorial](https://nbviewer.jupyter.org/github/annotation/tutorials/blob/master/generalmissives/start.ipynb).


Authors
=======

This repo is by

*   [Dirk Roorda](https://pure.knaw.nl/portal/en/persons/dirk-roorda) at
    [DANS](https://www.dans.knaw.nl)

with the help of the CLARIAH WP6 people mentioned above.

**N.B.:** Releases of this repo have been archived:

* at [Zenodo](https://zenodo.org)
* at [Software Heritage](https://archive.softwareheritage.org)

Click the respective badges above to be taken to the archives.
There you find ways to cite this work.
