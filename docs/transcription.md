# Source format

The source data for the TF conversion is in 
[TEI format NAF](https://tei-c.org).

## Header

The `teiHeader` header gives a the metadata.

We distil key value pairs and each key corresponds to a TF feature of the same name
with values for letter nodes.

We peel most keys and values from the `interpGrp` elements.

Here is a list of resulting TF features and where they come from:

TF feature | TEI element | type | remarks
--- | --- | --- | ---
pid | interpGrp | `pid` |
page | interpGrp | `page` |
seq | interpGrp | `n` |
title | interpGrp | `titleLevel1` |
rawdate | interpGrp | `dateLevel1` |
place | interpGrp | `localization_placeLevel1` |
yearFrom | interpGrp | `witnessYearLevel1_from` |
yearTo | interpGrp | `witnessYearLevel1_to` |
monthFrom | interpGrp | `witnessMonthLevel1_from` |
monthTo | interpGrp | `witnessMonthLevel1_to` |
dayFrom | interpGrp | `witnessDayLevel1_from` |
dayTo | interpGrp | `witnessDayLevel1_to` |
authors | interpGrp | `authorLevel1` | comma separated contents of child elements

The version number of the TEI set is used in the
[tfFromTrim](https://github.com/Dans-labs/clariah-gm/blob/master/programs/tfFromTrim.py)
conversion.

Possibly we create several TF data versions out of a single source version.
The TF-App `generalmissives` will state the TEI source version and TF version used in its metadata.

## Plain text

The plain text contains a few bits of metadata and the plain text of the letter.
Note that there may be editor's notes prepended/appended/interspersed.
We need to single them out and store them in features.
The textual data in TF will consist of the original content of the letters and that
content only.

The text, without punctuation is stored word by word on slots, in the feature `trans`.
All punctuation, including spaces, is stored on the slot of the preceding word,
in the feature `punc`.

Whitespace will be normalized to single spaces or newlines.

### node type `word`

These are the words of the corpus, the basic units, a.k.a *slots*.

Only the letter contents are stored word by word.
Editorial remarks are stored in bigger chunks, as values of features.

feature | type | description
--- | --- | ---
emph | 1 or absent | whether the word is set in emphatic typography
folio | string | an indication of an original folio at this point
punc | string | punctuation and or white space after the word
remark | string | an editorial remark at this point
super | 1 or absent | whether the word is in superscript, possibly the numerator of a fraction
special | 1 or absent | whether the word has extreme typography or a strange value (possibly OCR effects)
trans | string | the value of the word
und | 1 or absent | whether the word is underlined, possibly the total amount in a calculation

## Additonal annotations

We define several node types other than `word` that hold more complex pieces of text.

Nodes of type `word` are called slots, they are the textual positions.

All other nodes have a type and are linked to a subset of slots.

The node types can be read off from the 
[otype](https://github.com/Dans-labs/clariah-gm/blob/master/tf/0.1/otype.tf) 
feature, which lists the types together with the range of nodes of that type.

The linkage of nodes to slots is stored in the `oslots` feature, which is mostly not used directly.

Some of the node types correspond to sections, and Text-Fabric has some support for sections.

There are rigid sections in three levels: `volume`, `page`, `line`.

And there are more flexible structural sections, also three levels: `volume`, `letter`, `para`.

### node type `volume`

Each of the 13 volumes corresponds with a volume node.

This is a *structure* of level 1 and a *section* of level 1.

feature | type | description
--- | --- | ---
n | integer | the number of the volume


### node type `letter`

Each of the letters corresponds with a letter node.

This is a *structure* of level 2.

feature | type | source | description | remarks
--- | --- | --- | ---
authors | string | `authorLevel1` | e.g. `De Carpentier, De Houtman, Dedel, Sonck, Specx, Van Gorcom` | comma separated contents of child elements
dayFrom | integer | `witnessDayLevel1_from` | e.g. `25` |
dayTo | integer | `witnessDayLevel1_to` | e.g. `25` |
monthFrom | integer | `witnessMonthLevel1_from` | e.g. `11` |
monthTo | integer | `witnessMonthLevel1_to` | e.g. `11` |
page | integer | `page` | e.g. `234` | arabic page number within the volume
pid | string | `pid` | e.g. `INT_08c82040-752f-3fc2-ad50-0d3e7b37a945` | unique throughout the whole corpus
place | string | `localization_placeLevel1` | e.g. `Kasteel Mauritius nabij Ngofakiaha op Makéan` |
rawdate | string | `dateLevel1` | e.g. `8 maart 1621` |
title | string | `titleLevel1` | e.g. `De Carpentier, Dedel, Cornelisz. Reyersz. en Van Uffelen, Kasteel Jakatra, 9 juli 1621` |
seq | string | `n` | e.g. `XIII` | roman numeral, sequence number of letters of one set of authors in a volume
yearFrom | integer | `witnessYearLevel1_from` | e.g. `1626` |
yearTo | integer | `witnessYearLevel1_to` | e.g. `1626` |


### node type `para`

These are paragraphs.

This is a *structure* of level 3.

feature | type | description
--- | --- | ---
n | integer | the number of the paragraph within the letter


### node type `page`

These are pages from the print work.

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

A heading, marked by typography.

No features.

### Hierarchy

The `id` and `xpath` attributes contain the information to locate the element in the hierarchy
of XML elements in the text. We could use this to represent that hierarchy by means
of edge features.
However, we have not done that, because in the Text-Fabric the embeddedness of the nodes
is completely clear, and while that is not exactly the same as the tree-relation,
it is sufficient, because the TEI elements encode merely a rather shallow sectional hierarchy
and not a deep linguistic hierarchy.
