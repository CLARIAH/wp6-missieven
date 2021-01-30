# Source format

The source data for the TF conversion is in 
[TEI format](https://tei-c.org).

The version number of the TEI set is used in the
[tfFromTrim](https://github.com/Dans-labs/clariah-gm/blob/master/programs/tfFromTrim.py)
conversion.

We have created several TF data versions out of a single source version.
The TF-App `missieven` states the TEI source version and TF version used in its metadata
in its
[config.yaml](https://github.com/annotation/app-missieven/blob/master/code/config.yaml).
That will be the latest available version.

There has been an encoding modification concerning footnotes from version 0.6 to version 0.7.
See [transcription06](transcription06.md) for details on the previous encoding.

The TEI source has been cleaned and the result is captured in a set of simplified, TEI-like XML files,
in this repo.
For an overview of the element usage in those files, see
[elementsOut.tsv](https://github.com/Dans-labs/clariah-gm/blob/master/trimreport4/elementsOut.tsv).

Here is a short explanation

element | description
--- | ---
teiTrim | top-level element
header | container of meta elements and meta elements only
meta | a key-value pair of meta data (empty, attribute key names the key, value in attribute value)
head | the heading of a letter, 1 heading per letter
subhead | headings within a letter
remark | container of editorial content (the italic bits between brackets)
lb | line break element (empty, no attributes)
pb | page break element (empty, with attributes for volume number, page number, facsimile references)
para | paragraph
table, row, cell | tabular structure of text
ref | something that looks like a reference to other literature
emph | italic text
und | underlined text
sub | subscript text
super | superscript text
special | text with special typography for whatever reason
note | footnote bodies, moved into the main text, with `mark` attribute containing the footnote number
folio | reference to original folio

This XML has been converted rather straightforwardly into Text-Fabric, which is a graph of annotated
nodes.

## Metadata

We have compared the given metadata with metadata we distill from the letter heads and resolved
all disagreements.

A complete account is in 
[metaDiagnostics.txt](https://github.com/Dans-labs/clariah-gm/blob/master/trimreport2/metaDiagnostics.txt).


## Text

The text consists of three types of text:

**original** The running, unmarked text is original letter text, written between 1610 and 1761.

**editorial** The italic paragraphs, usually but not always between brackets, are editorial comments,
written between 1960 and 2007.

**footnotes** At the bottom of the text there is explanatory text that targets words in the
running text, both original text and editorial text.

### Footnotes

There are two kind of footnotes: 

1. original footnotes, marked by `a`, `b`. 
2. editorial footnotes, marked by `1`, `2`, ...

There are very few original footnotes, less than a hand ful.
There are over 12,000 editorial footnotes.

This dataset does not make the distinction between original footnotes and editorial footnotes.

There is some complexity in the footnote numbering:

1. sometimes the numbering skips a position;
2. in the lower volumes, the numbering is by page, in the higher volumes by letter;
3. a footnote text can be referenced by multiple footnote reference with the same number;

In the case of multiple references, we have duplicated the footnote text into as many copies,
so that we can maintain a 1-1 correspondence between references and footnotes.
In such cases, we have adapted the numbering.

In the dataset, the footnote numbers are not important any more, because the footnote bodies
have moved into the running text at the exact position of their corresponding references.
Yet we have retained the footnote number in the footnote body.
Because of the remapping of multiple references, the footnote number you see in the dataset may be
one or more off w.r.t. the footnote number you see in the original.

If there are multiple footnotes to the same word, we concatenate
the material of the footnotes (including their marks).
However, this does not occur in this corpus/

## Nodes

The basic node type (*slot* type) is the word.

There are also node types for other entities, such as volume, letter, page, line,
as listed in the *otype* feature and documented below.

All non-slot nodes have a type and are linked to a subset of slots.
The linkage is stored in the *oslots* feature, which is an edge feature: it specifies a edges between
each non-slot nodes and the slots that belong to them.
This feature is hardly ever used directly, because the Text-Fabric API has functions to
move from containers to containees, the so-called
[locality](https://annotation.github.io/text-fabric/core/locality.html#tf.core.locality.Locality)
functions.

### Hierarchy

In the Text-Fabric the embeddedness of the nodes
is completely clear, and while that is not exactly the same as the tree-relation in XML,
it is sufficient, because the TEI elements encode merely a rather shallow sectional hierarchy
and not a deep linguistic hierarchy.

Should there arise the need for encoding hierarchy precisely, we can introduce other edge features
to encode the parent-child relation of the trees in question.

### Sections

Some of the node types correspond to sections, and Text-Fabric has some support for sections.

There are rigid sections in three levels: `volume`, `page`, `line`.

And there are more flexible structural sections, also three levels: `volume`, `letter`, `para`.

### node type `word` (slot type)

These are the words of the corpus, the basic units.

The text, without punctuation is stored word by word on slots, in the feature `trans`.
All punctuation, including spaces, is stored on the slot of the preceding word,
in the feature `punc`.

Whitespace will be normalized to single spaces or newlines.
Only the original letter contents and the editorial remarks are stored word by word.
The footnotes are stored one by one, as values of the feature `fnote`, see below.

Next to the `trans` and `punc` features, there are the `transo`, `punco` and `transr`, `puncr` 
and `transn` and `puncn` feature pairs.
They contain the same information as `trans` and `punc`, but only for those words
that are original text resp. editorial text, resp. footnote text,
and they are empty outside their textual scope.

The dataset defines text formats (in the *otext* feature) that make use of these features:

```
@fmt:text-orig-full={trans}{punc}
@fmt:text-orig-source={transo}{punco}
@fmt:text-orig-remark={transr}{puncr}
@fmt:text-orig-note={transn}{puncn}
```

By choosing a text format you can selectively show original text only, editorial text only,
or all text.

**Note**
Folio references also show up when selecting editorial text.

There are flag features to indicate which text type words have: `isremark`, `isnote`, `isorig`, `isfolio`.

**Note**
All words in the original letters have `isorig=1`, i.e. the word feature `isorig` has value 1 for these words.

When words have received special formatting, it is also stored in flag features.
These features have the value 1 if the word has that formatting, and are undefined for words
not having the feature.
All these flag features have a name that starts with `is`: `isemph`, `issub`, `isund`, etc.

All **word** features:

feature | type | description
--- | --- | ---
isemph | 1 or absent | whether the word is set in emphatic typography
isfolio | 1 or absent | whether the word is part of a folio reference
isnote | 1 or absent | whether the word is part of a footnote
isorig | 1 or absent | whether the word is part of a the original text of the letters
isref | 1 or absent | whether the word belongs to a reference
isremark | 1 or absent | whether the word belongs to editorial content
issub | 1 or absent | whether the word is in subscript, possibly the numerator of a fraction
issuper | 1 or absent | whether the word is in superscript, possibly the numerator of a fraction
isspecial | 1 or absent | whether the word has special typography or a strange value (possibly OCR effects)
isund | 1 or absent | whether the word is underlined, possibly the total amount in a calculation
punc | string | punctuation and or white space after the word
punco | string | as `punc`, but only for original letter content
puncr | string | as `punc`, but only for editorial content
puncn | string | as `punc`, but only for footnote content
trans | string | the value of the word
transo | string | as `trans`, but only for original letter content
transr | string | as `trans`, but only for editorial content
transn | string | as `trans`, but only for footnote content

### node type `note`

These are footnotes.
They have a mark that roughly corresponds to the footnote mark on the printed page.
Their words are slots that have been inserted just after the location of the footnote mark.

**Note**
All words in a `note` have `isnote=1`, i.e. the word feature `isfolio` has value 1 for these words.

feature | type | description
--- | --- | ---
mark | int | the footnote mark
note | edge feature | from a slot node that corresponds with the position preceding a footnote mark to a footnote node

### node type `volume`

Each of the 13 volumes corresponds with a volume node.

This is a *structure* of level 1 and a *section* of level 1.

feature | type | description
--- | --- | ---
n | integer | the number of the volume


### node type `letter`

Each of the letters corresponds with a letter node.

This is a *structure* of level 2.

feature | type | description | remarks
--- | --- | --- | ---
author | string | e.g. `De Carpentier, De Houtman, ` | comma separated list of surnames
authorFull | string | e.g. `Pieter de Carpentier, Frederick de Houtman, ` | comma separated list of surnames
day | integer | day part of a date, e.g. `25` |
month | integer | month part of a date e.g. `11` |
page | integer | e.g. `234` | page number within the volume
place | string | e.g. `Kasteel Mauritius nabij Ngofakiaha op Makéan` |
rawdate | string | full date with Dutch month names, e.g. `8 maart 1621` |
title | string | e.g. `De Carpentier, Dedel, Cornelisz. Reyersz. en Van Uffelen, Kasteel Jakatra, 9 juli 1621` |
seq | string | e.g. `XIII` | roman numeral, sequence number of letters of one set of authors in a volume
year | integer | year part of a date, e.g. `1626` |


### node type `para`

These are paragraphs.

This is a *structure* of level 3.

feature | type | description
--- | --- | ---
n | integer | the number of the paragraph within the letter


### node type `page`

These are pages from the printed work.

This is a *section* of level 2.

feature | type | description
--- | --- | ---
facs | string | variable part of a url to the online version of the facsimile of this page
n | integer | the number of the page within the volume
tpl | 1 or 2 | refers to which url template must be used to get the facsimile url 
vol | integer | the number of the volume that includes this page

There are two templates:

1.  `http://resources.huygens.knaw.nl/retroapp/service_generalemissiven/gm_` `{vol:>02}` `/images/gm_` `{facs}` `.tif`
2.  `http://resources.huygens.knaw.nl/retroapp/service_generalemissiven/gm_` `{vol:>02}` `/images/generale_missiven_gs` `{facs}` `.tif`


### node type `line`

These are lines from the print work.

This is a *section* of level 3.

feature | type | description
--- | --- | ---
n | integer | the number of the line within the page


### node type `remark`

The chunks of editorial text.

This node type has no features, it only serves to group the editorial remarks.

**Note**
All words in a `remark` have `isremark=1`, i.e. the word feature `isremark` has value 1 for these words.

Note also that that the contents of words in remarks are stored in the word features
`trans` and `transr`, but not in `transo`. 

### node type `folio`

The folio references.

This node type has no features, it only serves to group the words of the folio references.

**Note**
All words in a `folio` have `isfolio=1`, i.e. the word feature `isfolio` has value 1 for these words.

Note also that that the contents of words in folio references are stored in the word features
`trans` and `transr`, but not in `transo`. 

### node type `table`

These are pieces of text in table layout.

feature | type | description
--- | --- | ---
n | integer | the number of the table within the whole corpus


### node type `row`

These are the rows of tables

feature | type | description
--- | --- | ---
n | integer | the number of the table within the whole corpus
row | integer | the number of the row within the table


### node type `cell`

These are the cells in the rows of tables

feature | type | description
--- | --- | ---
col | integer | the number of the column within the row
n | integer | the number of the table within the whole corpus
row | integer | the number of the row within the table


### node type `head`

The letter heading.
Each letter has exactly one heading.

This node type has no features, it only serves to group the words of the headings.

### node type `subhead`

Sub headings within a letter, marked by typography.

This node type has no features, it only serves to group the words of the headings.
