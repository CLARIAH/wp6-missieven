# Generale Missiven Corpus

This repo contains a structurally clean version of the data of the *General Missives*, volumes 1-14.

The *Generale Missiven* is a collection of letters from governors of the
VOC (Dutch East Indian Company) to
the *Heren 17*, the council of the governors of the 17 provinces of the Netherlands,
which was the effective
government of the Low Countries at the time of the 17th and 18th century.

The letters comprise 14 volumes and date from 1610 to 1767.

The Huygens-ING institute publishes this material:
[General Missives Website](http://resources.huygens.knaw.nl/retroboeken/generalemissiven/#page=0&accessor=toc&view=homePane),
see also
[General Missives Project](http://resources.huygens.knaw.nl/vocgeneralemissiven);
both websites are in Dutch.

The CLARIAH project works with the General Missives in its
[WP6-Text](https://www.clariah.nl/en/work-packages/focus-areas/text?layout=blog).
People involved are:

* [Lodewijk Petram](https://www.lodewijkpetram.nl) (HuygensING)
* [Jesse de Does](https://www.researchgate.net/profile/Jesse_De_Does) (INT)
* [Sophie Arnoult](http://www.illc.uva.nl/People/person/3601/Ir-Sophie-Arnoult)

The OCR of the printed pages of volumes 1-13
and the subsequent conversion from FineReader XML to TEI have been done by the INT.

Volume 14 was provided by Lodewijk Petram as textual PDFs.

Both types of data did require extensive post-processing to get many issues right.

This repo contains the
[source files](https://github.com/CLARIAH/wp6-missieven/tree/master/source)
as starting points for a battery of conversions, whose
[code](https://github.com/CLARIAH/wp6-missieven/tree/master/programs)
is included in this repository.

Consequently, all results of this repo are reproducible from the data in this repo.
There is a guide to do that in 
[reproduce.md](https://github.com/CLARIAH/wp6-missieven/tree/master/docs/reproduce.md).

# Overview of conversion issues

However, the TEI files of volumes 1-13 still contain many inaccuracies,
due to OCR errors which triggered subsequent conversion glitches.

There are several instances of miscategorized material:

*   page headers and footers end up in body text and vice versa;
*   editorial notes and footnotes are not always properly detected;
*   dozens of letters have not been separated;
*   metadata is often incorrect.

In order to produce a quality dataset, I needed to do something about it:
checks and corrections.

1.  all metadata has been freshly distilled from the letter headings,
    and in case of doubt the online images of the missives have been inspected.
2.  all footnote marks are linked to all footnote bodies.
    It is still possible that there are missed footnotes and missed footnote marks,
    but chances are slim because footnote marks and footnote bodies are detected
    independently.

Yet, most OCR errors within words and numbers are mostly untouched.
The main concern was to get a correct separation between the kinds of text:

* original letter
* editorial text
* footnotes
* page headers and footers

[trimTei.py](https://github.com/CLARIAH/wp6-missieven/blob/master/programs/trimTei.py)
consists of a battery of 4 conversions to clean the incoming TEI ,
leaving out all bits that do not end up in the final dataset,
and reorganizing some material to facilitate the conversion to TF.

The first result of the laundry is a set of XML files, which contain a clean, simplified TEI-like
encoding of the material, with all non-essential parts stripped, such as page headers and footers,
title pages, etc.
There is also an exact correspondence between files and letters.

Concerning volume 14: the pdf is the result of a much better OCR process.
We have used all typographical clues given in the pdf to infer structure.
There was quite a bit of nitty-gritty involved in this, especially for detecting table layout.
I do not claim that all table structure has been perfectly detected.
Another issue was to detect numbers and fractions properly.
Eventually, the script
[trimPdf.py](https://github.com/CLARIAH/wp6-missieven/blob/master/programs/trimPdf.py)
transforms the pdf in a sequence of stages to the same kind of XML as the trimTei.py script produced
for the volumes 1-13.

Then I used the
[walker module from TF](https://annotation.github.io/text-fabric/tf/convert/walker.html)
to turn the simple XML of all 14 volumes into Text-Fabric.
See
[tfFromTrim.py](https://github.com/CLARIAH/wp6-missieven/blob/master/programs/tfFromTrim.py).

For details about the features of the end result, see 
[transcription](docs/transcription.md)
