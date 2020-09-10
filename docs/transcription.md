# Source format

The source data for the TF conversion is in 
[NLP annotation format NAF](http://wordpress.let.vupr.nl/naf/).

See this
[example source file](https://github.com/Dans-labs/clariah-gm/blob/master/source/example.naf).

Here are the important bits:

## Header

The NAF header gives a bit of metadata.

    <nafHeader>
        <fileDesc title="Bantam, 10 nov. 1614" filename="INT_f2f7d1c3-2ce6-3b91-aca6-d3db04f25f83"/>
        <public publicId="INT_f2f7d1c3-2ce6-3b91-aca6-d3db04f25f83.naf"/>
        <linguisticProcessors layer="raw">
            <lp name="tei2naf-vu" version="0.1.1" timestamp="2020-08-26T18:05:43+0200"/>
        </linguisticProcessors>
        <linguisticProcessors layer="tunits">
            <lp name="tei2naf-vu" version="0.1.1" timestamp="2020-08-26T18:05:43+0200"/>
        </linguisticProcessors>
    </nafHeader>

We store the following pieces of metadata in the following text-fabric features:

element | example | tf-feature
--- | --- | ---
`fileDesc` | Bantam, 10 nov. 1614 | `fileDesc`
parse `fileDesc` | Bantam | `location`
parse `fileDesc` | 1614-11-10 | `date`
`fileName` | `INT_f2f7d1c3-2ce6-3b91-aca6-d3db04f25f83` | `fileId`

The fact that this is source version `0.1.1` will be reflected in the TF data version.

Possibly we create several TF data versions out of a single source version.
The TF-App `generalmissives` will state the source version used in its metadata.

## Plain text

The plain text contains a few bits of metadata and the plain text of the letter.
Note that there may be editor's notes prepended/appended/interspersed.
We need to single them out and store them in features.
The textual data in TF will consist of the original content of the letters and that
content only.

    <raw><![CDATA[28Both XVIII, 10 november 1614XVIII. PIETER BOTH. BANTAM 10 november 1614.969, fol. 13-19.
    Mijn héeren. Ick en can mij niet genouchsaem verwonderen, dat U Ed.
    (die alhier hebt te dirigeren een saeck van staet ende royaell.)
    soo weynich acht (onder correctie) sijt nemende in ’t aennemen van dengenen,
    die herwerts werden gesonden. Sommige van dien sijn banekerottiers,
    andere die ’t door quade menage niet langer aen de wal en connen houden,
    alsmede capiteyns, die van den vijandt zijn overgecomen ende meer bedreven sijn
    omme den coopman in den buyll te rijden als anders. Het schijnt dat het landt
    van ervaren landtsaten gepri veert is ende alsoo gaet het met alle de reste.
    Men brenght er in de schepen sommige met de boeyen aen de benen om herwerts te comen;
    van andere wert de schippers belast haer aen landt niet meer te laten keren ;
    eenige geheel van haer verstandt gepriveertende alsoo onbequaem tot eenigen dienst -
    ( De rest van deze brief, handelende over de slechte kwaliteit van het
    'personeel en over uitreding van schepen, is niet van groot belang).]]></raw>

The first line needs to be parsed in order to get metadata.
We store the following pieces of metadata in the following text-fabric features:

example | tf-feature
 --- | ---
28Both XVIII | `label`
10 november 1614 | redundant, will be skipped
XVIII | `numeral`
PIETER BOTH | `author` (converted to `Pieter Both`)
BANTAM 10 november 1614 | redundant, will be skipped
969 | `number`
fol. 13-19 | `folio` (converted to `13-19`)

Then the plain text follows until `- ( De rest van deze brief ...)`.

The text, without punctuation is stored word by word on slots, in the feature `trans`.
All punctuation, including spaces, is stored on the slot of the preceding word,
in the feature `punc`.

Whitespace will be normalized to single spaces or newlines.

## Additonal annotations

The source contains stand-off markup in the form of `<tunit>` elements.

    <tunits>
        <tunit
            id="INT_f2f7d1c3-2ce6-3b91-aca6-d3db04f25f83.TEI.1.text.1"
            type="text" xpath="/TEI/text[1]" offset="0" length="1091"/>
        <tunit
            id="INT_f2f7d1c3-2ce6-3b91-aca6-d3db04f25f83.TEI.1.text.1.body.1"
            type="body" xpath="/TEI/text[1]/body[1]" offset="0" length="1091"/>
        <tunit
            id="INT_f2f7d1c3-2ce6-3b91-aca6-d3db04f25f83.TEI.1.text.1.body.1.div.1"
            type="div" xpath="/TEI/text[1]/body[1]/div[1]" offset="0" length="1091"/>
        ...
        <tunit
            id="INT_f2f7d1c3-2ce6-3b91-aca6-d3db04f25f83.TEI.1.text.1.body.1.div.1.note.1.lb.1"
            type="lb" xpath="/TEI/text[1]/body[1]/div[1]/note[1]/lb[1]"
            offset="1036" length="0"/>
        <tunit
            id="INT_f2f7d1c3-2ce6-3b91-aca6-d3db04f25f83.TEI.1.text.1.body.1.div.1.note.1.lb.2"
            type="lb" xpath="/TEI/text[1]/body[1]/div[1]/note[1]/lb[2]"
            offset="1091" length="0"/>
    </tunits>

These elements specify TEI-element markup that has been encoded inside the text and is
now represented in a stand-off way.
Here is what we do with the information in these elements.
In general, the TEI elements correspond to nodes in TF of a node type that carries the
same name as the TEI element.

However, we will not convert the empty break elements (`lb` line, `pb` page)
in this way.
Instead, we introduce the node types `line` and `page` in TF,
and use the break elements to determine the extent of the lines and pages.

Some elements contain material that is not the primary text.
The `note` elements contain notes by later editors.
We will detach these notes from the main text, and store their contents in feature values.
We will ignore any markup inside notes, except that we translate `lb` elements into newlines,
and that we record `pb` elements in order to keep the sequence of pages intact.


attribute | example | node type | feature | remarks
--- | --- | --- | --- | ---
`id` | `INT_f2f7d1c3-2ce6-3b91-aca6-d3db04f25f83.TEI.1.text.1` | skipped | none | TF has its own local identifiers: nodes
`type` | `text`, `body`, `div`, | `text`, `body`, `div` | `otype` | the type of all nodes ends up in the standard `otype` feature
`type` | `lb`, `pb` | `line`, `page` | `otype` | the type of all nodes ends up in the standard `otype` feature
`type` | `note` | `note` | `otype`, `text` | plain text of the note
`xpath` | `/TEI/text[1]` | skipped | none | TF has its own local identifiers: nodes
`offset`, `length` | `0`, `1091` | none | `oslots` | the text location of all nodes ends up in the standard `oslots` feature 

### Hierarchy

The `id` and `xpath` attributes contain the information to locate the element in the hierarchy
of XML elements in the text. We could use this to represent that hierarchy by means
of edge features.
However, we have not done that, because in the Text-Fabric the embeddedness of the nodes
is completely clear, and while that is not exactly the same as the tree-relation,
it is sufficient, because the TEI elements encode merely a rather shallow sectional hierarchy
and not a deep linguistic hierarchy.
