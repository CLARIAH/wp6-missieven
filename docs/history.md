*   2021-07-22 Additional data corrections: letters that have no page break elements were
    not part of a page. That has been remedied (0.9), with the earlier corrections by Sophie on top of it (0.9.1).
*   2021-06-17 Data corrections by Sophie Arnoult have been applied (0.8.1)
*   2021-05-20 A new TF version (0.8) has been delivered.
    When multiple letters occur on one page, the words of the first line
    of some letters are not contained in line nodes.
    This has been corrected.
*   2021-01-30 A new TF version (0.7) has been delivered.
    This  version as a major encoding difference: whereas in version 0.6 footnote material ended
    up in the values of a feature, now footnotes are treated like text material.
    That means: the words in footnotes occupy slots, the footnotes themselves are nodes.
    As a consequence, footnotes and the words in it can be annotated, e.g. with named entities.
    This is a reuqirement for the kind of processing that Sophie Arnoult is currently devising.
*   2020-12-07 A new TF version (0.6) has been delivered.
    Fixed some folio references.
    Also: a simple data export has been made: a csv file with all the words, and for each
    word whether it is editorial or original, and if a word has a footnote, the footnote is
    also given. See the
    [export notebook](https://nbviewer.jupyter.org/github/Dans-labs/clariah-gm/tree/master/usage/SimpleData.ipynb).
    The
    [exported data](https://github.com/Dans-labs/clariah-gm/releases/download/v0.6/words.tsv.gz)
    is attached to this release.
*   2020-11-24 Experimenting with a [Blacklab](http://inl.github.io/BlackLab/index.html) interface.
*   2020-11-17 A new TF version (0.5) has been delivered
    Fixed the generation of spurious newlines in footnote bodies.
*   2020-11-16 A new TF version (0.4) has been delivered
    Footnote bodies and marks have been checked and corrected, all encoded footnote marks
    have been linked to all encoded footnote bodies.
    Docs have been updated, and tutorials have been written.
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



