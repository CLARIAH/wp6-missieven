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

*   2020-09-02 Repository created, no content yet, start of conversion coding.

Corpus
------

This repo contains a version of the data of the *General Missives*.

The *Generale Missiven* is a collection of letters from governors of the
VOC (Dutch East Indian Company) to
the *Heren 17*, the council of the governors of the 17 provinces of the Netherlands,
which was the effective
government of the Low Countries at the time of the 17th and 18th century.

The letters comprise 13 volumes and date from 1610 to 1761.

The Huygens-ING institute publishes this material:
[General Missives Website](http://resources.huygens.knaw.nl/retroboeken/generalemissiven/#page=0&accessor=toc&view=homePane).

See also
[General Missives Project (in Dutch)](http://resources.huygens.knaw.nl/vocgeneralemissiven).

The CLARIAH project uses this material in its Work Package 6 which deals with
new infrastructure for academic text processing:
[WP6-Text](https://www.clariah.nl/en/work-packages/focus-areas/text?layout=blog).
This work is conducted and carried out by

* [Lodewijk Petram](https://www.lodewijkpetram.nl)
* [Jesse de Does](https://www.researchgate.net/profile/Jesse_De_Does)
* [Sophie Arnoult](http://www.illc.uva.nl/People/person/3601/Ir-Sophie-Arnoult)

This representation of the corpus data
--------------------------------------

The CLARIAH WP6 people kindly provided me with an intermediate version
of the text and markup of the corpus in 
[NAF](http://wordpress.let.vupr.nl/naf/) format.

From there I made a conversion
[tfFromNav.py](https://github.com/Dans-labs/clariah-gm/blob/master/programs/tfFromNaf.py)
to turn it in a Text-Fabric dataset.

The reason for this exercise is that Text-Fabric takes the concept of stand-off annotation
to an extreme,
and I want to see whether that approach makes it easier to pre-process this corpus
for all sorts of processing pipelines.

See
[other corpora](https://annotation.github.io/text-fabric/about/corpora.html#gsc.tab=0)
for more experiences with Text-Fabric as a corpus pre-processing tool.

Text-Fabric operates in the ecosystem of Python and its libraries
and is particularly suited to Jupyter notebooks.

For details about the conversion from NAF to TF, see 
[transcription](docs/transcription.md)

Getting started
===============

Start with the
[tutorial](https://nbviewer.jupyter.org/github/annotation/tutorials/blob/master/generalmissives/start.ipynb).

Authors
=======

This repo is by

*   [Dirk Roorda](https://pure.knaw.nl/portal/en/persons/dirk-roorda) at
    [DANS](https://www.dans.knaw.nl)

with the help of the CLARIAH WP6 people mentioned above.

**N.B.:** Releases of this repo have been archived at [Zenodo](https://zenodo.org).
Click the DOI badge to be taken to the archive. There you find ways to cite this work.
