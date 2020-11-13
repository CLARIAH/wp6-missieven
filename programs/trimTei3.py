import re
import collections

from distill import MONTH_DETECT_PAT
from lib import (
    REPORT_DIR,
    WHITE_RE,
    LT,
    GT,
    AMP,
    ADD_LB_ELEMENTS,
    applyCorrections,
    docSummary,
    summarize,
)

corpusPre = None
trimVolume = None
trimDocBefore = None
trimDocPrep = None
trimDocPost = None

STAGE = 3
REP = f"{REPORT_DIR}{STAGE}"

"""
Main function of this stage: move pieces of remarks and footnotes
across page boundaries to the page where their main fragment is.

"""

CORRECTIONS_DEF = {
    "01:p0004-0004": (
        (r"""<super>4J</super> \.<lb/>\s*(</remark>)""", r"""⌊4⌋\1"""),
        (r"""®\)""", r"⌊6⌋"),
    ),
    "01:p0021-0023": ((r"""Ghresik""", r"Gresik⌊5⌋"),),
    "01:p0046-0047": ((r"""(Mataran)""", r"\1⌊1⌋"),),
    "01:p0077-0078": ((r"""(4j)""", r"⌊4⌋"),),
    "01:p0087-0087": ((r"""(5Ï)""", r"⌊5⌋"),),
    "01:p0087-0089": (
        (r"""4\)( Versta: krissen.*?</note>)""", r"<lb/>\n</note>\n<note>⌊4⌋\1"),
    ),
    "01:p0129-0129": ((r"""(sockels)""", r"\1⌊1⌋"),),
    "01:p0131-0146": ((r"""(boratchos)""", r"\1⌊1⌋"),),
    "01:p0152-0152": ((r"""(Dabulders) \*•\)""", r"\1⌊1⌋"),),
    "01:p0184-0202": ((r"""<ref>2\)</ref>""", r"2)"),),
    "01:p0204-0224": ((r"""(<super>3\)</super>)""", r"""\1 ⌊4⌋"""),),
    "01:p0279-0279": ((r"""(baey )(\*)\)""", r"\1⌊1⌋"),),
    "01:p0393-0405": ((r"""(Corangie)(1)\)""", r"\1⌊1⌋"),),
    "01:p0482-0485": ((r"""(Cawaitsedonne)""", r"\1⌊1⌋"),),
    "01:p0507-0514": ((r"""(pelings)""", r"\1⌊3⌋"),),
    "01:p0554-0593": ((r""" n(<lb/>)""", r"\1⌊1⌋"),),
    "01:p0596-0638": (
        (r"""(</note>\s*)$""", r"\1\n<note>⌊5⌋ Verloren gegaan.<lb/>\n</note>\n"),
    ),
    "01:p0596-0655": ((r"""\) (Payementen)""", r"⌊1⌋ \1"),),
    "01:p0663-0671": ((r"""<super>(5)\)</super>""", r"⌊\1⌋"),),
    "01:p0663-0683": ((r"""(Hensen)(1\))""", r"\1"),),
    "01:p0663-0719": ((r"""</note>\s*<note>(72 mijl)""", r"""\1"""),),
    "01:p0663-0673": ((r"""\.41\)""", r""".<super>t</super>⌊1⌋"""),),
    "02:p0007-0018": (
        (r"""l°\)""", r"""⌊10⌋"""),
        (r"""(Herman)\s*<super>3\)</super>""", r"""\1 ⌊5⌋,"""),
        (
            r"""(<note>)5\)( Tot de vier.*?</note>\s*)""",
            r"""\1⌊5⌋ Mij niet bekend.<lb/>\n</note>\n\1⌊6⌋ \2""",
        ),
    ),
    "02:p0007-0019": ((r"""<super>a\)</super>""", r"""⌊2⌋."""),),
    "02:p0007-0031": ((r"""<super>c\)</super>""", r"""⌊6⌋"""),),
    "02:p0007-0039": ((r"""<super>T\)</super>""", r"""⌊1⌋"""),),
    "02:p0007-0040": ((r"""(intervallen)1""", r"""\1⌊1⌋"""),),
    "02:p0007-0059": ((r"""(betilli’s)(2)""", r"""\1⌊\2⌋"""),),
    "02:p0007-0075": (
        (r"""(<note>)2\)( Mij verder.*?</note>\s*)""", r"""\1⌊2⌋\2<note>⌊3⌋ \2"""),
    ),
    "02:p0109-0118": ((r"""<super>x\)</super>""", r"""⌊1⌋"""),),
    "02:p0135-0136": ((r"""(affleggen)1""", r"""\1⌊1⌋"""),),
    "02:p0155-0183": (
        (r"""<note>(Op ’t aengetogen.*?)</note>""", r"""<para>\1</para>"""),
    ),
    "02:p0267-0269": (
        (
            r"""<para><emph>\((Gegevens over Tonkin.*?)</emph>.*?j\.(.*?)</para>""",
            r"""<remark>«\1 \2»</remark>""",
        ),
    ),
    "02:p0283-0288": (
        (
            r"""(3\.12<lb/>)""",
            r"""<folio>Fol. 31r-v</folio>
<para>comt als vooren ƒ 46 497. 6.14.⌊2⌋<lb/></para>""",
        ),
    ),
    "02:p0232-0234": (
        (r"""l\(F\.""", r"""10r"""),
        (r"""<note>(Soowel.*?)</note>""", r"""<para>\1</para>"""),
    ),
    "02:p0403-0438": (
        (r"""ö\)""", r"""⌊9⌋"""),
        (r"""u\)""", r"""⌊11⌋"""),
    ),
    "02:p0445-0465": (
        (
            r"""<note>43672 picol .*</note>""",
            r"""
<para>43672 picol 37 catty off ® 5328329 costen . ƒ 908408.14.11,<lb/>
</para>
<para>welcke, beswaert wesende met d’ongelden der schepen als volcksmaentgelden, dan<lb/>
costelijcke peper soude vallen, in comparatie van die op Batavia ingecocht wert,<lb/>
</para>
            """,
        ),
    ),
    "02:p0445-0446": ((r"""<ref>2\)</ref>""", r"2)"),),
    "02:p0445-0466": (
        (r"""<note>(9392741 .*?)</note>\s*""", r"""</para><para>\1"""),
        (r"""<note>(Verminderinge .*?)</note>\s*""", r"""</para><para>\1"""),
        (r"""<note>(Wat quantiteyt .*?)</note>\s*""", r"""</para><para>\1"""),
    ),
    "02:p0480-0480": ((r"""<note>(Van varent volck.*?)</note>""", r"<para>\1</para>"),),
    "02:p0480-0484": (
        (r"""<super>a\)""", r"""<super>⌊1⌋"""),
        (r"""<note>a\)""", r"""<note>1)"""),
        (r"""<note>I\)""", r"""<note>2)"""),
    ),
    "02:p0480-0498": ((r"""(memorie gemaect)""", r"\1⌊1⌋"),),
    "02:p0585-0615": ((r"""(Borth)1\)""", r"\1⌊1⌋"),),
    "02:p0585-0624": ((r"""(gen\.)11\)""", r"\1<super>t</super>⌊1⌋"),),
    "02:p0585-0636": ((r"""(den Signaty)""", r"\1⌊1⌋"),),
    "02:p0640-0640": ((r"""(col="3">)3\)""", r"\1„"),),
    "02:p0640-0651": ((r"""• • ■\)""", r"...)"),),
    "02:p0640-0660": ((r"""(quadreren)1\)""", r"\1⌊1⌋"),),
    "02:p0673-0718": ((r"""<note>6\) (Bandel,)""", r"<note>5) \1"),),
    "02:p0739-0743": ((r"""<note>(2 .*?)</note>""", r"<para>\1</para>"),),
    "02:p0770-0806": ((r"""<note>21 """, r"<note>2)"),),
    "02:p0770-0813": (
        (
            r"""<note>(ƒ 1 .*)</note>""",
            r"""
<para>ƒ 1 268266.17.3<lb/>
</para>
<para>Met ’t fluytschip den Reyger, van Palliacatas rhede 19 october<lb/>
1653 verdreven en met volck en al in zee verongeluckt,<lb/>
aen Cormandels linnewaten als anders verloren,<lb/>
</para>
<para>comt . ƒ 39 201. 8.12<lb/>
</para>
<para>Item met ’t fluytschip Overschie aan Bengalse<lb/>
suykeren, gommelacq etc. voor<lb/>
Persia, tusschen Narsapour ende Coringa<lb/>
niet verre van Masulipatam op<lb/>
een rif verongelukt<lb/>
</para>
<para>48 697. 1.—<lb/>
</para>
            """,
        ),
    ),
    "03:p0004-0014": ((r"""(onsen cap\.tn Verheyden)""", r"\1⌊1⌋"),),
    "03:p0004-0018": ((r"""(coopman Van Voorst)""", r"\1⌊1⌋"),),
    "03:p0004-0040": ((r"""(Mam et Amienbeeck)""", r"\1⌊1⌋"),),
    "03:p0004-0041": ((r"""(Lala)\s*<super>!\)</super>""", r"\1⌊1⌋"),),
    "03:p0047-0049": ((r"""(Moesaffar)\s*\*\)""", r"\1⌊1⌋"),),
    "03:p0047-0058": ((r"""(daerdoor alle)""", r"\1⌊1⌋"),),
    "03:p0079-0081": (
        (r"""ellendig!\)""", r"ellendigh"),
        (r"""<note>ö<lb/>\s*</note>\s*""", r""),
    ),
    "03:p0085-0086": ((r"""(<lb/>\s*Diego Sarria Lascano)""", r"\1⌊1⌋"),),
    "03:p0085-0098": ((r"""(comitgies)""", r"\1⌊1⌋"),),
    "03:p0085-0102": ((r"""(omtrent Calecoulan)""", r"\1⌊1⌋"),),
    "03:p0108-0125": ((r"""<ref>aves ende</ref>""", r"aves⌊1⌋"),),
    "03:p0108-0129": ((r"""(Grinhil)""", r"\1⌊1⌋"),),
    "03:p0108-0130": ((r"""(Sayadabatse)""", r"\1⌊1⌋"),),
    "03:p0147-0156": ((r"""(<note>)G\) (Maharadja Lelo)""", r"\1⌊6⌋ \2"),),
    "03:p0210-0238": (
        (r"""(<note>)1\)( Mij niet nader.*?</note>\s*)""", r"""\1⌊1⌋\2<note>⌊2⌋ \2"""),
    ),
    "03:p0247-0256": ((r"""(Mr\. Willam Courtes)""", r"\1⌊1⌋"),),
    "03:p0247-0260": ((r"""(ghanghanna)\s*<super>!\)</super>""", r"\1⌊1⌋"),),
    "03:p0247-0273": ((r"""(Pieter Vertange)\s*\^""", r"\1⌊1⌋"),),
    "03:p0247-0279": ((r"""(opperhooft Nicolaes Loenius)""", r"\1⌊1⌋"),),
    "03:p0247-0280": ((r"""(in Ontingpoy)""", r"\1⌊1⌋"),),
    "03:p0292-0297": ((r"""(Trimmelepatam)""", r"\1⌊1⌋"),),
    "03:p0292-0300": ((r"""(q)1 \)""", r"\1⌊1⌋"),),
    "03:p0292-0312": ((r"""(Gosy Aly)""", r"\1⌊1⌋"),),
    "03:p0314-0340": ((r"""</note>\s*<note>(88° O\.L\.<lb/>\s*)""", r"\1"),),
    "03:p0314-0341": ((r"""(tot Doget)""", r"\1⌊1⌋"),),
    "03:p0314-0342": ((r"""(toetvelden)""", r"\1⌊1⌋"),),
    "03:p0383-0383": ((r"""(Mette Spangards is sijn e\.)""", r"\1⌊1⌋"),),
    "03:p0383-0387": ((r"""(<note>)D """, r"\1⌊1⌋"),),
    "03:p0354-0356": ((r"""(Tritsiampille) (onthoudt)""", r"\1⌊1⌋ \2"),),
    "03:p0393-0394": ((r"""(dughten, dat hij)""", r"\1⌊1⌋"),),
    "03:p0403-0420": ((r"""(baey) (door)""", r"\1⌊1⌋ \2"),),
    "03:p0403-0430": ((r"""(bancksael)""", r"\1⌊1⌋"),),
    "03:p0484-0506": ((r"""(cap\.n Maerten Scholten)""", r"\1⌊1⌋"),),
    "03:p0525-0533": ((r"""<super>3\)\)</super>""", r"⌊3⌋)"),),
    "03:p0525-0537": ((r"""(<ref>Ecrot)""", r"\1⌊1⌋"),),
    "03:p0525-0538": ((r"""(<ref>Lipovi)""", r"\1⌊1⌋"),),
    "03:p0525-0557": ((r"""<super>2\)\)</super>""", r"⌊2⌋)"),),
    "03:p0581-0586": (
        (r"""<super>z\)</super>""", r"\)"),
        (r"""<note>I\)""", r"""<note>1)"""),
        (r"""<note>!\)""", r"""<note>2)"""),
    ),
    "03:p0641-0644": ((r"""<super>A\)</super>""", r"⌊1⌋)"),),
    "03:p0676-0687": ((r"""(gouverneur Syra Radja Oelebalangh)""", r"\1⌊1⌋"),),
    "03:p0722-0726": ((r"""(Sampoera)""", r"\1⌊1⌋"),),
    "03:p0739-0742": ((r"""<super>fl\)</super>""", r"⌊6⌋)"),),
    "03:p0750-0769": (
        (r"""(<note>)2\)( Bedoeld is: .*?</note>\s*)""", r"""\1⌊2⌋\2<note>⌊3⌋ \2"""),
    ),
    "03:p0779-0781": ((r"""L (menschen)""", r"⌊1⌋ \1"),),
    "03:p0835-0843": ((r"""<super>A\)</super>""", r"⌊1⌋)"),),
    "03:p0835-0866": ((r"""(Tinnekon)""", r"\1⌊1⌋"),),
    "03:p0877-0880": ((r"""(<note>)1 1 \)""", r"\1⌊11⌋"),),
    "03:p0877-0885": ((r"""(dito reede) \*\)""", r"\1⌊1⌋"),),
    "03:p0877-0887": (
        (
            r"""(<note>)5\)( Dit bericht is onjuist.*?</note>\s*)""",
            r"""\1⌊5⌋\2<note>⌊6⌋ \2""",
        ),
    ),
    "03:p0924-0940": ((r"""(miserabel Suckelenburgh )""", r"\1⌊1⌋"),),
    "04:p0001-0002": (
        (
            r"""(<note>)1\)( Van den Koning van Bima.*?</note>\s*)(<note>.*?</note>\s*)""",
            r"""\1⌊1⌋\2\3<note>⌊3⌋ \2""",
        ),
    ),
    "04:p0001-0005": ((r"""(4)1\)""", r"\1⌊1⌋"),),
    "04:p0001-0007": (
        (
            r"""(<note>)1\)( Bedoeld is Radja.*?</note>\s*)""",
            r"""\1⌊1⌋\2<note>⌊2⌋ \2""",
        ),
    ),
    "04:p0001-0008": ((r"""(annae)""", r"\1⌊1⌋"),),
    "04:p0021-0037": ((r"""(telle quelle)""", r"\1⌊1⌋"),),
    "04:p0043-0049": (
        (
            r"""(<note>1\) Bedoeld: zowel als.*?</note>\s*)""",
            r"""\1\1""",
        ),
    ),
    "04:p0043-0050": ((r"""(van den p\.le)""", r"\1⌊1⌋"),),
    "04:p0083-0083": ((r"""<emph>A\)</emph>""", r"⌊1⌋"),),
    "04:p0101-0101": ((r"""<super>a\)</super>""", r"⌊2⌋,"),),
    "04:p0101-0117": (
        (
            r"""(<note>)2\)( Gouverneur en raden.*?</note>\s*)""",
            r"""\1⌊2⌋\2<note>⌊3⌋ \2""",
        ),
    ),
    "04:p0125-0136": ((r"""(Battabatta)""", r"\1⌊1⌋"),),
    "04:p0125-0141": ((r"""(1\.101\))""", r"\1⌊1⌋"),),
    "04:p0171-0171": ((r"""(Balante)""", r"\1⌊1⌋"),),
    "04:p0183-0197": ((r"""(Jan de Graaf f)""", r"\1⌊1⌋"),),
    "04:p0218-0223": ((r"""<super>5\)</super>""", r"⌊5⌋),"),),
    "04:p0218-0227": (
        (
            r"""<para>huyshuyren\b.*?f\. 507641\. 9\. 6<lb/>\n</para>\n""",
            """
<table>
    <row>
        <cell>huyshuyren</cell>
        <cell></cell>
        <cell>f. 3430.—.—</cell>
    </row>
    <row>
        <cell>brieffloonen </cell>
        <cell></cell>
        <cell>1572.19. 4</cell>
    </row>
    <row>
        <cell>intresten</cell>
        <cell></cell>
        <cell>29887. 3.12</cell>
    </row>
    <row>
        <cell></cell>
        <cell>Somma</cell>
        <cell>f. 1474621. 5. 5⌊1⌋</cell>
    </row>
    <row>
        <cell>d’ Advancen daerentegen bedragen :</cell>
    </row>
    <row>
        <cell>op Colombo</cell>
        <cell>f. 170492. 1.15</cell>
    </row>
    <row>
        <cell>Gale</cell>
        <cell>247520. 8.—</cell>
    </row>
    <row>
        <cell>Tutucoryn</cell>
        <cell>52782.18.11</cell>
    </row>
    <row>
        <cell>Jaffanapatnam</cell>
        <cell>70176. 9.—</cell>
    </row>
    <row>
        <cell>Manaer</cell>
        <cell>23723.10. 3</cell>
    </row>
    <row>
        <cell>Calpatijn</cell>
        <cell>88676. 9.12</cell>
    </row>
    <row>
        <cell>Batticalo en Trinq.6</cell>
        <cell>45151.19. 5</cell>
    </row>
    <row>
        <cell>Negapatam etc.a</cell>
        <cell>60312. 6.11</cell>
    </row>
    <row>
        <cell>generale oncosten⌊2⌋</cell>
        <cell>208143.12. 6</cell>
    </row>
    <row>
        <cell></cell>
        <cell></cell>
        <cell>966979.15.15</cell>
    </row>
    <row>
        <cell>Ceylon comt a.° 1676 te cort</cell>
        <cell></cell>
        <cell>f. 507641. 9. 6</cell>
    </row>
</table>
<folio>Fol.564r.</folio>
            """,
        ),
    ),
    "04:p0242-0244": ((r"""(Tercolo)""", r"⌊3⌋),"),),
    "04:p0262-0269": (
        (
            "("
            + re.escape(
                r"""1 Tapa
<super>4 5)</super><lb/>
"""
            )
            + ")("
            + re.escape(
                r"""Bellambellan
<super>3)</super>, bestaande in"""
            )
            + ") ("
            + re.escape(
                r"""J Saombay
<super>6)</super> ofte Ouby Latoe<lb/>
<emph>J</emph> Aloowaloe
<super>6)</super>, bij ons Schilpaddeneylant<lb/>
"""
            )
            + ")",
            r"\2\n\1\3",
        ),
    ),
    "04:p0262-0274": (
        (r"""°\)""", r"⌊9⌋),"),
        (r"""<super>u\)</super>""", r"⌊11⌋),"),
    ),
    "04:p0262-0288": ((r"""(Sacherus de Huysser)""", r"⌊1⌋),"),),
    "04:p0312-0312": ((r"""(den prins Alam)""", r"⌊1⌋),"),),
    "04:p0318-0332": ((r"""(<note>)\[4\) """, r"\1⌊4⌋"),),
    "04:p0318-0358": ((r"""(Minauw)""", r"⌊1⌋),"),),
    "04:p0373-0373": ((r"""(oely)""", r"⌊1⌋),"),),
    "04:p0373-0382": ((r"""(r Mangocro)""", r"⌊1⌋),"),),
    "04:p0373-0392": (
        (
            r"("
            + re.escape(
                r"""<para>Daerentegen bedragen d’ongelden op d’ondergen.<lb/>
comptoiren meer als de winsten, te weten<lb/>
</para>
<para>tot Bimelepatnam . f. 140. 7.10<lb/>
</para>
<para>Nagelwanze8) . . 2189.19. 8<lb/>
</para>
"""
            )
            + ")("
            + re.escape(
                r"""<para>10 678.10.—<lb/>
377 684.15.11<lb/>
52 108.17.10<lb/>
37 837.13. 4<lb/>
59 998.11. 3<lb/>
42 641.—. 3<lb/>
14 374.11.10<lb/>
695 323.19. 9
<super>1 2 3)</super><lb/>
"""
            )
            + ")",
            r"\2\1",
        ),
    ),
    "04:p0373-0401": ((r"""(haarder)""", r"⌊1⌋),"),),
    "04:p0429-0460": ((r"""<super>u\)</super>""", r"⌊11⌋),"),),
    "04:p0429-0469": ((r"""(<note>)11""", r"\1⌊1⌋"),),
    "04:p0480-0480": ((r"""(soetelaars)""", r"⌊1⌋),"),),
    "04:p0498-0522": ((r"""<super>z\)</super>""", r"⌊3⌋"),),
    "04:p0498-0554": ((r"""(daatsgelt)""", r"⌊1⌋),"),),
    "04:p0498-0558": ((r"""(Trap)""", r"⌊7⌋),"),),
    "04:p0498-0550": (
        (r"""<super>3J</super>""", r"⌊3⌋"),
        (r"""no\}i\)""", r"noyt"),
    ),
    "04:p0498-0568": ((r"""<super>3\)</super> (verstreckinge)""", r"⌊3⌋ \1"),),
    "04:p0498-0579": (
        (r"""(r\.01)\s*<super>2</super>""", r"\1⌊1⌋"),
        (r"""(r c\.t0)\s*<super>2</super>""", r"\1⌊2⌋"),
    ),
    "04:p0498-0586": ((r"""(<note>)J\)""", r"\1⌊1⌋"),),
    "04:p0498-0588": (
        (r"""<super>a\)</super>""", r"⌊8⌋, ⌊9⌋, "),
        (
            r"""(<note>а\).*?</note>\s*)((?:<note>.*?</note>\s*){8})"""
            r"""(<note>.*?</note>\s*)(<note>.*?</note>\s*)""",
            r"\2\1\4\3",
        ),
        # this a is unicode x430
        (r"""(<note>)б\)""", r"\1⌊5⌋"),
        (r"""(<note>)а\)""", r"\1⌊8⌋"),  # this a is unicode x430
        (r"""(<note>)8\)""", r"\1⌊10⌋"),
    ),
    "04:p0498-0589": (
        (
            r"""(<note>a\).*?</note>\s*)(<note>b\).*?</note>\s*)"""
            r"""((?:<note>.*?</note>\s*){7})"""
            r"""((?:<note>.*?</note>\s*){2})""",
            r"\1\4\2\3",
        ),
        (r"""<super>a\)</super>\.""", r"⌊1⌋, ⌊2⌋, ⌊3⌋."),
        (r"""<super>b\)</super>\.""", r"⌊4⌋."),
        (r"""(<note>)a\)""", r"\1⌊1⌋"),
        (r"""(<note>)b\)""", r"\1⌊4⌋"),
        (r"""(<note>)1\)""", r"\1⌊5⌋"),
        (r"""(<note>)2\)""", r"\1⌊6⌋"),
        (r"""(<note>)3\)""", r"\1⌊7⌋"),
        (r"""(<note>)4\)""", r"\1⌊8⌋"),
        (r"""(<note>)5\)""", r"\1⌊9⌋"),
        (r"""(<note>)6\)""", r"\1⌊10⌋"),
        (r"""(<note>)7\)""", r"\1⌊11⌋"),
        (r"""(<note>)8\)""", r"\1⌊2⌋"),
        (r"""(<note>)9\)""", r"\1⌊3⌋"),
    ),
    "04:p0498-0593": ((r"""<super>x\)\)</super>""", r"⌊1⌋)"),),
    "04:p0600-0638": ((r"""(<note>)11""", r"\1⌊1⌋"),),
    "04:p0600-0640": (
        (
            r"""(<note>)2\)( Van Happel.*?</note>\s*)""",
            r"""\1⌊2⌋\2<note>⌊3⌋ \2""",
        ),
    ),
    "04:p0651-0657": ((r"""(- maght)""", r"\1⌊1⌋"),),
    "04:p0651-0664": ((r"""(6)1\)""", r"\1⌊1⌋"),),
    "04:p0651-0672": ((r"""<super>4\)</super>""", r"⌊4⌋)."),),
    "04:p0680-0683": ((r"""(minees)""", r"\1⌊1⌋"),),
    "04:p0680-0693": ((r"""(Toedjoe Cotas)""", r"\1⌊1⌋"),),
    "04:p0707-0709": ((r"""(Popoloewo)""", r"\1⌊1⌋"),),
    "04:p0753-0759": ((r"""(<ref>lant te</ref>)""", r"\1⌊1⌋"),),
    "04:p0791-0821": ((r"""<super>4\)</super>( en Anthonij)""", r"⌊1⌋\1"),),
    "04:p0791-0832": ((r"""(Wiera Goena)""", r"\1⌊1⌋"),),
    "05:p0001-0002": ((r"""<super>1</super>""", r"⌊1⌋"),),
    "05:p0077-0082": ((r"""(Kartisidana) (forte)""", r"\1⌊1⌋ \2"),),
    "05:p0099-0100": (
        (
            r"""\s*(</remark>)\s*<para>\s*<emph>(is)</emph>\s* (-) ;<lb/>\s*</para>""",
            r""" \2\3)\1""",
        ),
    ),
    "05:p0099-0103": ((r"""(Tesame 22967)1\)""", r"\1⌊1⌋"),),
    "05:p0099-0115": ((r"ö\) (Isaak Clarisse)", r"</note>\n<note>5) \1"),),
    "05:p0099-0119": ((r"<ref>(daats)( zal)</ref>", r"\1⌊1⌋\2"),),
    "05:p0099-0128": ((r"""(pimpou)\b""", r"\1⌊1⌋"),),
    "05:p0099-0135": (
        (
            r"""(Padang te vestigen\.<lb/>\s*)(</remark>)""",
            r"""\1)\2""",
        ),
    ),
    "05:p0099-0149": (
        (
            r"""(Pits vernam te Bantam,<lb/>\s*)(</remark>)"""
            r"""\s*<para>\s*(dat\s*-\s*\))<lb/>\s*</para>""",
            r"""\1\3\2""",
        ),
    ),
    "05:p0099-0150": (
        (
            r"""(</para>\n)(<remark>«De retourvloot)""",
            r"\1<folio>Fol. 361r-v.⌊1⌋</folio>\n\2",
        ),
    ),
    "05:p0195-0206": ((r"""<super>A\)</super>""", r"⌊1⌋"),),
    "05:p0195-0212": ((r"""(omgedeelt te werden) \*\)""", r"\1⌊1⌋"),),
    "05:p0195-0219": ((r"""(1664)(<lb/>)""", r"\1⌊1⌋\2"),),
    "05:p0195-0223": ((r"""(Griek)""", r"\1⌊1⌋"),),
    "05:p0195-0228": ((r"""(wakkiel)2\)""", r"\1⌊2⌋"),),
    "05:p0296-0298": ((r"""(Pessy)1\)""", r"\1⌊1⌋"),),
    "05:p0296-0335": ((r"""</note>\s*<note>(9°20' N\.B\.<lb/>\s*)""", r"\1"),),
    "05:p0296-0339": ((r"""<sub>n0g</sub> - «\)""", r"nog -----⌊4⌋"),),
    "05:p0388-0399": ((r"""(<sub>cto</sub>)""", r"\1⌊1⌋"),),
    "05:p0388-0425": ((r"""(die reyse)""", r"\1⌊1⌋"),),
    "05:p0439-0454": ((r"""(Binoan)1\n<super>2 3 4\)</super>""", r"\1⌊1⌋,"),),
    "05:p0439-0468": ((r"""(jonken) (jaarlijx)""", r"\1⌊1⌋ \2"),),
    "05:p0508-0543": ((r"""(spetie\n)<ref>(aldaar) (wiert)</ref>""", r"\1 \2⌊1⌋ \2"),),
    "05:p0567-0570": ((r"""(manocken)""", r"\1⌊1⌋"),),
    "05:p0567-0590": ((r"""(Arquaron)""", r"\1⌊1⌋"),),
    "05:p0567-0592": ((r"""(en Bantal)""", r"\1⌊1⌋"),),
    "05:p0605-0609": (
        (
            r"""</remark>\s*<note>(kruidnagelen bewaard,.*?)</note>""",
            r"\1",
        ),
        (
            r"""<note>(Tot Nova Guinea.*?)</note>""",
            r"</remark>\n<para>\1</para>",
        ),
    ),
    "05:p0605-0611": ((r"""(Mariam en haar)""", r"\1⌊1⌋"),),
    "05:p0668-0676": ((r"""(boskleetjes)""", r"\1⌊1⌋"),),
    "05:p0712-0712": ((r"""(<note>)\.1\) """, r"\1⌊1⌋"),),
    "05:p0779-0799": ((r"""(couren)""", r"\1⌊1⌋"),),
    "05:p0822-0823": ((r"""<super>10</super>""", r"⌊10⌋"),),
    "06:p0066-0072": (
        (
            r"""(<note>1\).*?</note>\n)(<note>2\).*?</note>\n<note>3\).*?</note>\n)""",
            r"\1\2\1",
        ),
    ),
    "06:p0116-0127": ((r"""\]\)(atria)""", r"p\1"),),
    "06:p0116-0132": ((r"""<ref>(Sjolias)( of)</ref>""", r"\1⌊1⌋\2"),),
    "06:p0144-0147": ((r"""<ref>(Pisang)( ende)</ref>""", r"\1⌊1⌋\2"),),
    "06:p0153-0155": ((r"""<ref>(rottingh)( aan)</ref>""", r"\1⌊1⌋\2"),),
    "06:p0177-0177": ((r"""(</folio>\n)<para>1\)\.(<lb/>)\n</para>""", r"⌊1⌋\2\1"),),
    "06:p0290-0303": ((r"""<ref>(Sam) (bouwer)( de)</ref>""", r"\1\2⌊1⌋\3"),),
    "06:p0329-0329": ((r"""<super>1\)</super>""", r"⌊1⌋"),),
    "06:p0346-0376": ((r"""(alsook de bediende)""", r"\1⌊1⌋"),),
    "06:p0346-0378": (
        (
            r"""(</remark>\n)(<note>1\) Gekrakeel)""",
            r"\1<folio>Fol. 333r-v. ⌊3⌋</folio>\n\2",
        ),
    ),
    "06:p0390-0400": ((r"""p\.Ql\)""", r"p.<super>o</super> ⌊1⌋"),),
    "06:p0415-0435": (
        (r"""Pélgrom""", r"Pelgrom", 4),
        (r"""(directeur Pelgrom)""", r"\1⌊1⌋"),
    ),
    "06:p0415-0456": ((r"""(Onderkoning)""", r"\1⌊1⌋"),),
    "06:p0466-0467": ((r"""(Radja Bea)""", r"\1⌊1⌋"),),
    "06:p0477-0493": ((r"""</note>\s*<note>(22° N\.B\. stromende)""", r"\1"),),
    "06:p0514-0519": ((r"""(appriseering)""", r"\1⌊1⌋"),),
    "06:p0575-0578": ((r"""<super>1\)</super>""", r"⌊1⌋"),),
    "06:p0587-0591": (
        (
            r"""(</remark>\n)(<note>1\) Het)""",
            r"\1<folio>Fol. 1471v-1472r. ⌊5⌋</folio>\n\2",
        ),
    ),
    "06:p0587-0595": ((r"""(capitain Sergeant)""", r"\1⌊1⌋"),),
    "06:p0601-0603": ((r"""<super>1 \*</super>""", r"⌊1⌋"),),
    "06:p0601-0604": ((r"""(Bira)2\n<super>3 4\)</super>""", r"\1⌊2⌋,"),),
    "06:p0601-0607": ((r"""</note>\s*<note>(25 april 1729.*?)""", r"\1"),),
    "06:p0601-0618": (
        (
            r"""(<note>1\) Niet in\n<emph>Corpus</emph>.*?</note>\n)""",
            r"\1\1",
        ),
    ),
    "06:p0601-0629": ((r"""(Pandelekoerse) \*\)""", r"\1⌊1⌋"),),
    "06:p0601-0634": ((r"""<ref>(mandament)( met)</ref>""", r"\1⌊1⌋\2"),),
    "06:p0658-0658": (
        (fr"""(</folio>\n)<para>{GT}\)\.(<lb/>)\n</para>""", r"⌊1⌋\2\1"),
    ),
    "06:p0663-0691": ((r"""<ref>(China)( Tamby)</ref>""", r"\1⌊1⌋\2"),),
    "06:p0663-0701": ((r"""\.s1\)""", r"<super>gt</super>)"),),
    "06:p0663-0705": ((r"""(Suwagie)""", r"\1⌊1⌋"),),
    "06:p0663-0710": ((r"""vullen\n<ref>(aandoen)( en)</ref>""", r"willen \1⌊1⌋\2"),),
    "06:p0732-0732": ((r"""(</folio>\n)<para>»\)\.(<lb/>)\n</para>""", r"⌊1⌋\2\1"),),
    "06:p0732-0735": (
        (r"""(klinket)(<lb/>\n)<super>3\)\)</super>""", r"\1⌊3⌋\2"),
        (r"""<super>4\)</super>""", r"⌊4⌋"),
    ),
    "06:p0750-0773": ((r"""(doorgestoocken)""", r"\1⌊1⌋"),),
    "06:p0750-0791": ((r"""(Chanaan Badur) \^""", r"\1⌊1⌋"),),
    "06:p0750-0795": ((r"""(jun\.r)""", r"\1 ⌊1⌋"),),
    "06:p0810-0814": ((r"""(atlassen)""", r"\1⌊1⌋"),),
    "06:p0844-0858": (
        (r"""(eyland S\.)1\n<super>\*</super> (Jan)""", r"\1<super>t</super> \2⌊1⌋"),
    ),
    "06:p0844-0878": ((r"""(6500\.- de jo\.) \*\)""", r"\1⌊1⌋"),),
    "07:p0003-0004": (
        (r"""(Tuaha')""", r"\1⌊1⌋"),
        (r"""(Aly)""", r"\1⌊4⌋"),
        (
            r"""(<note>3\) Het woord.*?</note>\n)""",
            r"\1<note>4) Ten rechte: Ali.</note>",
        ),
    ),
    "07:p0003-0006": ((r"""<note>1\) Ten rechte: Ali.<lb/>\n</note>""", r""),),
    "07:p0003-0019": ((r"""(geb\.)"\)""", r"\1⌊1⌋"),),
    "07:p0045-0057": ((fr"""{GT}\)""", r"⌊1⌋"),),
    "07:p0078-0080": ((r"""(brie)P\)""", r"\1f⌊3⌋"),),
    "07:p0078-0094": ((r"""(naturelijke<lb/>\nsoon)""", r"\1⌊1⌋"),),
    "07:p0078-0084": ((r"""(Tonsaronson)2\n<super>3\)</super>""", r"\1⌊2⌋"),),
    "07:p0078-0130": ((r"""(Valentijn)1""", r"\1⌊1⌋"),),
    "07:p0136-0144": ((r"""Gemetchanï\)""", r"Gerrietchan⌊3⌋"),),
    "07:p0166-0171": ((r"""(Uhman)""", r"\1⌊1⌋"),),
    "07:p0166-0186": ((r"""(Aatsjen)""", r"\1⌊1⌋"),),
    "07:p0166-0194": (
        (r"""(<note>2\) Tenrechte: Ngoera=Ngurah\.<lb/>\n</note>\n)""", r"\1\1"),
    ),
    "07:p0202-0204": ((r"""(Niatlang)""", r"\1⌊1⌋"),),
    "07:p0226-0234": ((r"""<super>x\)</super>""", r"⌊1⌋"),),
    "07:p0226-0237": ((r"""<super>x\)</super>""", r"⌊1⌋"),),
    "07:p0226-0243": (
        (
            r"""(<note>)1\.(<lb/>\s*</note>\s*)""",
            r"\g<1>3). Weligamma, vgl. dl. III, p. 268, noot 1.\2",
        ),
    ),
    "07:p0226-0247": ((r"""'\)\)""", r"⌊1⌋"),),
    "07:p0226-0254": ((r"""<super>l\)</super>""", r"⌊1⌋"),),
    "07:p0226-0263": ((r"""Karei de 6C\|\)""", r"Karel de 6<super>e</super> ⌊1⌋"),),
    "07:p0278-0278": ((r"""(<remark>«Het betrof)""", r"<folio>1973v ⌊1⌋</folio>\n\1"),),
    "07:p0290-0309": ((r"""(Maprana)""", r"\1⌊1⌋"),),
    "07:p0325-0330": ((r"""(haar) '\)""", r"\1⌊1⌋"),),
    "07:p0336-0349": ((r"""<super>3\)</super>""", r"⌊3⌋"),),
    "07:p0413-0439": ((r"""<super>l\)</super>""", r"⌊1⌋"),),
    "07:p0479-0479": ((r"""(derselver)'\)""", r"\1⌊1⌋"),),
    "07:p0479-0483": (
        (r"""(Draak)1\n<super>2\)</super>""", r"\1⌊1⌋,"),
        (r"""(slaaf)P\)""", r"\1f⌊2⌋,"),
    ),
    "07:p0485-0499": ((r"""(scheepsstrijd)\n<super>1</super>""", r"\1⌊1⌋"),),
    "07:p0517-0533": (
        (
            r"""(<remark>winnende en.*?):\)(.*?)(</remark>)""",
            r"\1:»<lb/>\n\3\n<para>\2<lb/>\n</para>",
        ),
    ),
    "07:p0552-0557": ((r"""(Manuel) ‘j""", r"\1⌊1⌋"),),
    "07:p0552-0560": ((r"""(van)3\)""", r"\1⌊3⌋"),),
    "07:p0552-0573": ((r"""(salueeren)1\n<super>2\.\)</super>""", r"\1⌊2⌋."),),
    "07:p0552-0581": ((r"""(abord)""", r"\1⌊1⌋"),),
    "07:p0552-0574": ((r"""' \)""", r"⌊1⌋"),),
    "07:p0610-0616": ((r"""(Poelopangang) ‘\)""", r"\1⌊1⌋"),),
    "07:p0610-0639": ((r"""(<remark>)6 ml\.""", r"\1(vnl."),),
    "07:p0640-0648": (
        (r"""(<remark>«Dubbeldekop)""", r"<folio>Fol. 1921r-v ⌊1⌋</folio>\n\1"),
    ),
    "07:p0661-0662": (
        (
            r"""(</note>)\s*$""",
            r"\1\n<note>2)"
            r"This note is missing on the facsimile (Dirk Roorda, converter)</note>",
        ),
    ),
    "07:p0661-0670": ((r"""(Tondeman)""", r"\1⌊1⌋"),),
    "07:p0661-0671": ((r"""<super>l\)</super>""", r"⌊3⌋"),),
    "07:p0684-0689": ((r"""<note>0 """, r"<note>1) "),),
    "07:p0710-0713": ((r"""(”)\n<super>2\)</super>""", r"\1⌊2⌋"),),
    "07:p0710-0739": ((r"""(”)\n<super>x\)</super>""", r"\1⌊1⌋"),),
    "08:p0003-0004": ((r"""\b(1706)(6\))""", r"\1⌊\2⌋"),),
    "08:p0003-0005": ((r"""(70)(8)\)""", r"\1⌊\2⌋"),),
    "08:p0009-0012": ((r"""(prauwvoerder)(8) \)""", r"\1⌊\2⌋"),),
    "08:p0009-0024": ((r"""(1)(36)\)""", r"\1⌊\2⌋"),),
    "08:p0009-0027": ((r"""(allama)f(5)\)""", r"\1t⌊4\2⌋"),),
    "08:p0046-0053": ((r"""(92)9\)""", r"\1⌊9⌋"),),
    "08:p0046-0057": ((r"""(pangawas)(17)""", r"\1⌊\2⌋"),),
    "08:p0128-0130": ((r"""(ara)(5)\)""", r"\1⌊\2⌋"),),
    "08:p0128-0150": ((r"""(4)(27)\)""", r"\1⌊\2⌋"),),
    "08:p0188-0188": ((r"""(Hatihalu)\n<super>I\)</super>""", r"\1⌊1⌋"),),
    "08:p0188-0205": ((r"""(Attapitti)(32)\)""", r"\1⌊\2⌋"),),
    "08:p0235-0235": ((r"""(735)(1)\)""", r"\1⌊\2⌋"),),
    "08:p0552-0581": ((r"""(abord)""", r"\1⌊1⌋"),),
    "09:p0015-0051": ((r"""(sigh offers)'(9)""", r'\1"⌊\2⌋'),),
    "09:p0071-0081": ((r"""/i([35])""", r"/\1", 2),),
    "09:p0097-0105": ((r"""(noroos)(5)""", r"\1⌊\2⌋"),),
    "09:p0365-0387": ((r"""(ƒ 7823)""", r"(\1"),),
    "09:p0256-0274": ((r"""<super>1 1</super>""", r"⌊11⌋"),),
    "09:p0548-0549": ((r"""(<note>)(Cajatizaad)""", r"\1⌊1⌋ \2"),),
    "09:p0548-0550": (
        (r"""(<remark>«Aan de)""", r"<folio>Fol. 4235r ⌊2⌋</folio>\n\1"),
    ),
    "09:p0567-0574": ((r"""(kouwers ”)(3)""", r"\1⌊\2⌋"),),
    "09:p0597-0597": ((r"""(lawang)'""", r"\1⌊1⌋"),),
    "09:p0597-0602": (
        (r"""<super>\?</super>""", r"⌊3⌋"),
        (r"""(<remark>«David)""", r"<folio>Fol. 1219v-1220r. ⌊4⌋</folio>\n\1"),
    ),
    "09:p0597-0607": ((r"""3nli2""", r"3 11/12"),),
    "09:p0597-0610": ((r"""(etc\.,)(7)""", r"\1⌊\2⌋"),),
    "09:p0597-0611": (
        (
            r"""(kooplieden\.<lb/>\n</para>\n)""",
            r"\1<folio>Fol. 1387v-1387r.⌊8⌋</folio>\n",
        ),
    ),
    "09:p0702-0706": (
        (
            r"""(300 rds\.<lb/>\n</para>\n)""",
            r"\1<folio>Fol. 2786v-2787r.⌊1⌋</folio>\n",
        ),
    ),
    "09:p0782-0800": (
        (
            r"""(laten plegen\.<lb/>\n</para>\n)""",
            r"\1<folio>Fol. 1405r-1408r.⌊1⌋</folio>\n",
        ),
    ),
    "09:p0750-0758": (
        (r"""(<note>)(')( Tanna)""", r"\1⌊5⌋\2"),
        (r"""(<note>)(’)( Bohay)""", r"\1⌊6⌋\2"),
    ),
    "09:p0750-0761": ((r"""(i-a)(8)""", r"\1⌊\2⌋"),),
    "09:p0782-0801": ((r"""(<note>)(Zie)""", r"\1⌊2⌋ \2"),),
    "10:p0001-0035": ((r"""(\*\*\*)n""", r"\1⌊11⌋"),),
    "10:p0001-0018": ((r"""(<note>)(Dit)""", r"\1⌊8⌋ \2"),),
    "10:p0112-0115": ((r"""(<note>)(Betuyd)""", r"\1⌊4⌋ \2"),),
    "10:p0112-0125": ((r"""(<note>)(In)""", r"\1⌊8⌋ \2"),),
    "10:p0112-0131": ((r"""(<note>)(1 1)""", r"\1⌊11⌋ \2"),),
    "10:p0175-0185": ((r"""(\.\.\.)(5)""", r"\1⌊\2⌋"),),
    "10:p0175-0228": (
        (
            r"""(<remark>)<special>([^<]*)</special> \( """,
            r"<subhead>\2</subhead>\n\1( ",
        ),
    ),
    "10:p0175-0195": ((r"""(<note>)(Temeraire)""", r"\1⌊8⌋ \2"),),
    "10:p0255-0269": ((r"""(1737)(3)""", r"\1⌊\2⌋"),),
    "10:p0255-0279": ((r"""(<note>)(De)""", r"\1⌊8⌋ \2"),),
    "10:p0297-0317": ((r"""(<note>)(Het)""", r"\1⌊8⌋ \2"),),
    "10:p0297-0340": ((r"""(<note>)(Sortiados)""", r"\1⌊11⌋ \2"),),
    "10:p0399-0400": ((r"""(<note>)(Calange)""", r"\1⌊1⌋ \2"),),
    "10:p0399-0407": (
        (r"""(<cell n="168" row="25" col="2">[^<]*)(4)(</cell>)""", r"\1⌊\2⌋\3"),
        (r"""(<cell n="168" row="25" col="4">[^<]*)(5)(</cell>)""", r"\1⌊\2⌋\3"),
        (r"""(<cell n="168" row="25" col="5">[^<]*)(6)(</cell>)""", r"\1⌊\2⌋\3"),
        (r"""(<cell n="169" row="7" col="9">[^<]*)(7)(</cell>)""", r"\1⌊\2⌋\3"),
    ),
    "10:p0399-0408": (
        (r"""(<cell n="170" row="14" col="9">[^<]*)(8)(</cell>)""", r"\1⌊\2⌋\3"),
        (r"""(<cell n="170" row="16" col="2">[^<]*)(9)(</cell>)""", r"\1⌊\2⌋\3"),
        (r"""(<cell n="170" row="16" col="3">[^<]*)(10)(</cell>)""", r"\1⌊\2⌋\3"),
        (
            r"""(<cell n="170" row="16" col="5">[^<]*)<super>(11)</super>(</cell>)""",
            r"\1⌊\2⌋\3",
        ),
        (r"""(<cell n="170" row="19" col="9">[^<]*)(12)(</cell>)""", r"\1⌊\2⌋\3"),
        (r"""(<cell n="170" row="20" col="9">[^<]*)(13)(</cell>)""", r"\1⌊\2⌋\3"),
        (r"""(<cell n="170" row="22" col="9">[^<]*)(4)(</cell>)""", r"\1⌊1\2⌋\3"),
        (r"""(<cell n="170" row="31" col="9">[^<]*)(15)(</cell>)""", r"\1⌊\2⌋\3"),
        (
            r"""<note><super>8</super>.*</note>""",
            r"""
<note>⌊8⌋ De optelling levert een andere dan de aangegeven uitkomst op
op (ƒ 14.909,11<lb/>
</note>
<note>⌊9⌋ De optelling levert een andere dan de aangegeven uitkomst op
op (ƒ 1.774.698,12,9)<lb/>
</note>
<note>⌊10⌋ De optelling levert een andere dan de aangegeven uitkomst op
op (ƒ280.802,1,-).<lb/>
</note>
<note>⌊11⌋ De optelling levert een andere dan de aangegeven uitkomst op
op (ƒ2.126.374,6,2).<lb/>
</note>
<note>⌊12⌋ De optelling levert een andere dan de aangegeven uitkomst op
op (ƒ 563.828,4,8).<lb/>
</note>
<note>⌊13⌋ De optelling levert een andere dan de aangegeven uitkomst op
op  (ƒ 256.668,12,7).<lb/>
</note>
<note>⌊14⌋ De optelling levert een andere dan de aangegeven uitkomst op
op (ƒ 102.704,6,-).<lb/>
</note>
<note>⌊15⌋ De optelling levert een andere dan de aangegeven uitkomst op
op (ƒ 200.449,5,8).<lb/>
</note>
            """,
        ),
    ),
    "10:p0399-0409": (
        (r"""(<cell n="171" row="3" col="2">[^<]*)(16)(</cell>)""", r"\1⌊\2⌋\3"),
        (r"""(<cell n="171" row="3" col="3">[^<]*)(17)(</cell>)""", r"\1⌊\2⌋\3"),
        (
            r"""(<cell n="171" row="3" col="5">[^<]*)2\^8(</cell>)""",
            r"\g<1>2 1/5 ⌊18⌋\2",
        ),
        (r"""(<cell n="171" row="28" col="2">[^<]*)”(</cell>)""", r"\1⌊19⌋\2"),
        (
            r"""<note><super>16</super>.*</note>""",
            r"""
<note>⌊16⌋ De optelling levert een andere dan de aangegeven uitkomst op
(ƒ 1.821.01 1,16,6).
</note>
<note>⌊17⌋ De optelling levert een andere dan de aangegeven uitkomst op
(ƒ 293.608,17,-).
</note>
<note>⌊18⌋ De optelling levert een andere dan de aangegeven uitkomst op
(ƒ 1.892.381,17,2 1/5).
</note>
<note>⌊19⌋ De optelling levert een andere dan de aangegeven uitkomst op
(ƒ 1.764.628,16,8).
</note>
<note>⌊20⌋ De optelling levert een andere dan de aangegeven uitkomst op
(ƒ 127.000,18,8).
</note>
            """,
        ),
    ),
    "10:p0399-0410": (
        (r"""(<cell n="173" row="4" col="9">[^<]*)(21)(</cell>)""", r"\1⌊\2⌋\3"),
        (r"""(<cell n="173" row="14" col="2">[^<]*)(22)(</cell>)""", r"\1⌊\2⌋\3"),
        (r"""(<cell n="173" row="24" col="9">[^<]*)(23)(</cell>)""", r"\1⌊\2⌋\3"),
        (r"""(<cell n="173" row="28" col="9">[^<]*)(24)(</cell>)""", r"\1⌊\2⌋\3"),
        (r"""\b(3)(25)\b""", r"\1⌊\2⌋"),
    ),
    "10:p0399-0411": (
        (r"""\b(8)(26)\b""", r"\1⌊\2⌋"),
        (r"""(-)(27)\b""", r"\1⌊\2⌋"),
        (r"""(<cell n="175" row="9" col="2">[^<]*)l(28)(</cell>)""", r"\g<1>1⌊\2⌋\3"),
        (r"""(<cell n="175" row="9" col="3">[^<]*)(29)(</cell>)""", r"\1⌊\2⌋\3"),
        (
            r"""(<cell n="175" row="9" col="4">)<ref>([^<]*)</ref>(30)(</cell>)""",
            r"\1\2⌊\3⌋\4",
        ),
    ),
    "10:p0413-0418": ((r"""(<note>)(Slinken)""", r"\1⌊1⌋ \2"),),
    "10:p0413-0430": ((r"""(<note>)<super>2</super>""", r"\1⌊12⌋"),),
    "10:p0413-0455": ((r"""\b(26)(<lb/>)""", r"⌊\1⌋\2"),),
    "10:p0413-0456": ((r"""(670)(27)""", r"\1⌊\2⌋"),),
    "10:p0461-0462": ((r"""(<note>)(Peuril)""", r"\1⌊1⌋ \2"),),
    "10:p0496-0504": ((r"""(<note>)(Hier)""", r"\1⌊1⌋ \2"),),
    "10:p0496-0518": (
        (
            r"""(<remark>)<special>([^<]*)</special> \( """,
            r"<subhead>\2</subhead>\n\1( ",
        ),
    ),
    "10:p0496-0531": ((r"""(<note>)(Phaeton)""", r"\1⌊8⌋ \2"),),
    "10:p0598-0625": ((r"""(<note>)(Recusatie)""", r"\1⌊8⌋ \2"),),
    "10:p0633-0641": ((r"""(<note>)(Fachinen)""", r"\1⌊1⌋ \2"),),
    "10:p0633-0700": (
        (
            r"""(<remark>)«<special>(Bandar[^<]*)</special> """,
            r"<subhead>\2</subhead>\n\1( ",
        ),
    ),
    "10:p0633-0743": ((r"""(\.\.\.)(6)""", r"\1⌊\2⌋"),),
    "10:p0767-0769": ((r"""(73 %)\]""", r"\1 ⌊1⌋"),),
    "10:p0807-0814": (
        (
            r"""(<remark>)<special>(Menado[^<]*)</special> """,
            r"<subhead>\2</subhead>\n\1( ",
        ),
    ),
    "10:p0807-0820": (
        (
            r"""(<remark>)<special>(Bima)</special>""",
            r"<subhead>\2</subhead>\n\1",
        ),
    ),
    "10:p0857-0858": ((r"""(<note>)(14 december)""", r"\1⌊1⌋ \2"),),
    "11:p0008-0009": (
        (
            r"""\n(Djambi<lb/>)\n</para>\n""",
            r"</para>\n<folio>Fol. 140r. ⌊1⌋</folio>\n<subhead>\1</subhead>\n",
        ),
    ),
    "11:p0027-0085": (
        (
            r"""(<remark>«Batavia ondersteunt)""",
            r"<folio>Fol. [963a]r-v. ⌊10⌋</folio>\n\1",
        ),
    ),
    "11:p0027-0087": (
        (r"""(<note>)(<super>1 1</super>)""", r"\1⌊11⌋ \2"),
        (
            r"""(<remark>«Men moet zijn)""",
            r"<folio>Fol. 978ar-987br. ⌊11⌋</folio>\n\1",
        ),
    ),
    "11:p0131-0132": ((r"""(Ida Anna)'""", r"\1⌊1⌋"),),
    "11:p0131-0145": ((r"""( 8\.)(4)""", r"\1⌊\2⌋"),),
    "11:p0131-0160": (
        (
            r"""(<remark>«De rotan die Sumatra)""",
            r"<folio>Fol. 887v-889r. ⌊7⌋</folio>\n\1",
        ),
    ),
    "11:p0131-0174": ((r"""(1) (48)u""", r"\1\2⌊11⌋"),),
    "11:p0131-0198": (
        (
            r"""(<remark>«Het grote aantal vaarten)""",
            r"<folio>Fol. 1154r. ⌊14⌋</folio>\n\1",
        ),
    ),
    "11:p0207-0208": (
        (
            r"""\n(Malakka<lb/>)\n</para>\n""",
            r"</para>\n<folio>Fol. 1435r. ⌊1⌋</folio>\n<subhead>\1</subhead>\n",
        ),
    ),
    "11:p0207-0209": ((r"""(traffique )\\(<lb/>)""", r"\1)\2"),),
    "11:p0207-0213": (
        (
            r"""(<remark>«De kapers lappen)""",
            r"<folio>Fol. 1459v-1450v. ⌊4⌋</folio>\n\1",
        ),
    ),
    "11:p0226-0270": ((r"""<super>1</super>( overstromingen)""", r"'\1"),),
    "11:p0226-0307": ((r"""(<note>)(<super>1</super>)""", r"\1⌊11⌋ \2"),),
    "11:p0226-0308": ((r"""(22) (5%\.)(12)""", r"\1\2⌊\3⌋"),),
    "11:p0226-0323": ((r"""(19)( albereets)""", r"⌊\1⌋\2"),),
    "11:p0226-0325": ((r"""(<note>)(<super>2 1</super>)""", r"\1⌊21⌋ \2"),),
    "11:p0226-0326": (
        (
            r"""(<remark>«Andere justiti)""",
            r"<folio>Fol. 780r-[793a]r. ⌊27⌋</folio>\n\1",
        ),
    ),
    "11:p0363-0395": ((r"""24Ó\.(4)""", r"240.⌊\1⌋"),),
    "11:p0363-0407": (
        (
            r"""(<remark>«De lasten van Kasimbazar)""",
            r"<folio>Fol. 332v-335v. ⌊6⌋</folio>\n\1",
        ),
    ),
    "11:p0363-0409": (
        (
            r"""(<remark>)<special>(Hooghly)</special>""",
            r"<subhead>\2</subhead>\n\1",
        ),
    ),
    "11:p0363-0417": ((r"""(illipi-)(8)""", r"\1⌊\2⌋"),),
    "11:p0363-0433": (
        (
            r"""<note>ƒ 481.113,14, 8<lb/>.*</note>""",
            r"""
<para>ƒ 481.113,14, 8<lb/>
</para>
<para>inkomsten<lb/>
ƒ 94.766,15, 8<lb/>
</para>
<para>ƒ 278.574, 8, -<lb/>
</para>
<para>ƒ 58.247,18, 8<lb/>
</para>
<para>ƒ 1.431,11, -<lb/>
</para>
<para>/ 910, 8, -<lb/>
</para>
<para>ƒ 2.810,18, -<lb/>
</para>
<para>ƒ 436.741,19, 0<lb/>
</para>
<para><und>ƒ 917.855,13, 8</und><lb/>
ƒ 386.521, 5, 8<lb/>
</para>
            """,
        ),
    ),
    "11:p0363-0456": (
        (
            r"""(<remark>«Het gehele Bantamse)""",
            r"<folio>Fol. 555xr-v. ⌊13⌋</folio>\n\1",
        ),
    ),
    "11:p0363-0472": (
        (
            r"""(<remark>«Batavia stuurt de brief)""",
            r"<folio>Fol. 648v-649ar. ⌊16⌋</folio>\n\1",
        ),
    ),
    "11:p0507-0539": ((r"""(446)\/""", r"\1, ⌊3⌋"),),
    "11:p0507-0572": (
        (r"""(237)(9)""", r"\1⌊\2⌋"),
        (r"""(, 8)(10)""", r"\1⌊\2⌋"),
    ),
    "11:p0507-0577": ((r"""(-,83)\n<super>1<\/super>""", r"\1 ⌊11⌋"),),
    "11:p0507-0592": ((r"""\.\n<super>75<\/super>""", r". ⌊15⌋"),),
    "11:p0507-0600": ((r"""\. ƒ\n<super>6<\/super>""", r". ⌊16⌋"),),
    "11:p0601-0601": ((r"""(569\.)(1)""", r"\1⌊\2⌋"),),
    "11:p0641-0642": (
        (
            r"""(<remark>«Op de redenen voor)""",
            r"<folio>Fol. 163v-[163a]r. ⌊1⌋</folio>\n\1",
        ),
    ),
    "11:p0641-0644": (
        (
            r"""(<remark>«Batavia vraagt opheldering)""",
            r"<folio>Fol. [169a]r. ⌊2⌋</folio>\n\1",
        ),
    ),
    "11:p0641-0650": ((r"""(<lb/>\n)<super>\?</super>""", r"⌊3⌋\1"),),
    "11:p0641-0666": ((r"""(91) (1,)(4)""", r"\1\2⌊\3⌋"),),
    "11:p0641-0670": (
        (
            r"""(<remark>)(Kasimbazar)\n<emph>([^<]*)</emph>""",
            r"<subhead>\2</subhead>\n\1\3",
        ),
    ),
    "11:p0641-0701": (
        (r"""(versterkt\.)(6)\n<super>\*<\/super>""", r"\1⌊\2⌋"),
        (r"""(maanden)9""", r"\1’"),
    ),
    "11:p0641-0711": (
        (
            r"""(<remark>«Mochten er toch)""",
            r"<folio>Fol. [457a]r-v. ⌊7⌋</folio>\n\1",
        ),
    ),
    "11:p0641-0734": (
        (
            r"""(<remark>«Er wordt voor)""",
            r"<folio>Fol. 580bv-581v. ⌊16⌋</folio>\n\1",
        ),
    ),
    "11:p0735-0744": ((r"""(1)(</folio>)""", r"⌊\1⌋\2"),),
    "11:p0769-0789": (
        (
            r"""(<remark>«De handel in stofgoud)""",
            r"<folio>Fol. 246v-252r. ⌊2⌋</folio>\n\1",
        ),
    ),
    "11:p0769-0823": ((r"""(\.\.\.)(9)""", r"\1⌊\2⌋"),),
    "11:p0769-0833": ((r"""(<note>)(<super>1 1</super>)""", r"\1⌊11⌋ \2"),),
    "11:p0862-0866": (
        (
            r"""<note>De Bataviase versaameling.*</note>""",
            r"""
<para>De Bataviase versaameling rendeert<lb/>
</para>
<para>Het volgende als tot het rethour niet behoorende<lb/>
werd hetselve hier eenlijk binneslinies<lb/>
bekend gesteld, namentlijk:<lb/>
</para>
<para>54.000 lb. klipsteenen ƒ -, -<lb/>
</para>
<para>Van de equipagiewerff<lb/>
</para>
<para>38 pees onbequaame ankers wege 88.344<lb/>
</para>
<para><special>lb./-</special> -<lb/>
</para>
<para>Uyt ’t ambagtsquartier<lb/>
</para>
<para>3 pees aambeelden |<lb/>
</para>
<para>60 pees dommekragten I<lb/>
</para>
<para>20 pees bankschroeven /
<super>we8en</super> 60.000 lb. ƒ<lb/>
</para>
<para>4 pees speerhaken<lb/>
</para>
<para>8 kassen snaphanen en pistoollopen /<lb/>
</para>
<para>Voor 2 percento Batavia’s ongelden op<lb/>
ƒ1.978.684,14, -<lb/>
</para>
<para><und>ƒ 1.639.858, -, 8</und><lb/>
ƒ 1.978.684,14, -<lb/>
</para>
<para><und>ƒ 39.573,14, -</und><lb/>
ƒ 2.018.258, 8, -<lb/>
</para>
            """,
        ),
    ),
    "12:p0001-0002": ((r"""(<note>)""", r"<folio>Fol. 101r-v. ⌊1⌋</folio>\n\1"),),
    "12:p0003-0024": (
        (
            r"""(<remark>«Resident Nicolaas Bang)""",
            r"<folio>Fol. 244r-245r. ⌊6⌋</folio>\n\1",
        ),
    ),
    "12:p0003-0063": ((r"""(\.\.\.)I3""", r"\1⌊13⌋"),),
    "12:p0003-0068": (
        (r"""(\.\.\.),4""", r"\1⌊14⌋"),
        (r"""(<note>)(Het bedrag)""", r"\1⌊14⌋ \2"),
    ),
    "12:p0003-0071": (
        (r"""(2172)(15)""", r"\1⌊\2⌋"),
        (r"""15<lb/>\s*<note>""", r"<note>⌊15⌋ "),
    ),
    "12:p0003-0081": ((r"""(\.\.\.),6""", r"\1⌊16⌋"),),
    "12:p0096-0103": ((r"""(\.\.\.)l""", r"\1⌊1⌋"),),
    "12:p0096-0105": (
        (
            r"""\n(Bandjarmasin<lb/>)\n</para>\n""",
            r"</para>\n<folio>Fol. [318a]v. ⌊2⌋</folio>\n<subhead>\1</subhead>\n",
        ),
    ),
    "12:p0096-0107": (
        (r"""(suspect)9""", r"\1’"),
        (r"""daim(3)""", r"dalm⌊\1⌋"),
    ),
    "12:p0096-0109": ((r"""(\.\.\.)(4)""", r"\1⌊\2⌋"),),
    "12:p0096-0125": (
        (
            r"""(<remark>«Batavia verzoekt om)""",
            r"<folio>Fol. 391v-[391a]r. ⌊7⌋</folio>\n\1",
        ),
    ),
    "12:p0096-0157": ((r"""(1750)(9)""", r"\1⌊\2⌋"),),
    "12:p0181-0181": (
        (r"""<note>ï<lb/>\s*</note>\s*<note>""", r"<note>⌊1⌋ "),
        (r"""</note>\s*<note>(1752\.<lb/>)""", r"\1"),
    ),
    "12:p0196-0196": ((r"""(\.)'""", r"\1⌊1⌋"),),
    "12:p0198-0203": ((r"""(<note>)(Er is hier sprake)""", r"\1⌊1⌋ \2"),),
    "12:p0198-0267": ((r"""(,-)(4)""", r"\1⌊\2⌋"),),
    "12:p0276-0276": ((r"""(\.)(1)""", r"\1⌊\2⌋"),),
    "12:p0293-0309": ((r"""(<note>)(In de marge)""", r"\1⌊1⌋ \2"),),
    "12:p0293-0362": ((r"""(1752)(3)""", r"\1⌊\2⌋"),),
    "12:p0293-0372": ((r"""(\/52)(6)""", r"\1⌊\2⌋"),),
    "12:p0293-0373": ((r"""</note>\s*<note>(9 mei)""", r"\1"),),
    "12:p0394-0395": ((r"""(1705)'""", r"\1⌊1⌋"),),
    "12:p0403-0477": (
        (
            r"""(<remark>«Het verheugt Batavia)""",
            r"<folio>Fol. 675r-680r. ⌊4⌋</folio>\n\1",
        ),
        (r""" (5) (5)(5)""", r"\1\2⌊\3⌋"),
    ),
    "12:p0403-0480": ((r"""<para>6<lb/>\s*</para>\s*<note>""", r"<note>⌊6⌋ "),),
    "12:p0499-0499": ((r"""(\.)'""", r"\1⌊1⌋"),),
    "12:p0500-0500": (
        (r"""(8\. )(1)""", r"\1⌊\2⌋"),
        (r"""<note>i<lb/>\s*</note>\s*<note>""", r"<note>⌊1⌋ "),
    ),
    "12:p0501-0504": (
        (r"""</para>\s*<note>(<und>zijn,</und>)""", r"\1"),
        (r"""</note>\s*<note>(Den Soerats)""", r"</para>\n<para>\1"),
        (r"""</note>\s*$""", "</para>\n"),
    ),
    "12:p0509-0509": (
        (r"""(7\. )(1)""", r"\1⌊\2⌋"),
        (r"""I(754)(2)""", r"1\2⌊\2⌋ "),
    ),
    "12:p0510-0603": ((r"""(<note>)(De rijksdaalder)""", r"\1⌊8⌋ \2"),),
    "12:p0510-0608": ((r"""(3) (1)(9)""", r"\1\2⌊\3⌋"),),
    "12:p0510-0613": ((r"""(mey)'""", r"\1⌊11⌋"),),
    "13:p0008-0011": (
        (r"""<note>(Zullende.*?)</note>""", r"<para>\1</para>"),
        (r"""<note>(De.*?)</note>""", r"<para>\1</para>"),
    ),
    "13:p0014-0039": ((r"""<note>(Voorts.*)</note>""", r"</para><para>\1"),),
    "13:p0014-0098": ((r"""(12)(13)""", r"\1⌊\2⌋"),),
    "13:p0014-0059": ((r"""(<note>)(Platkoper)""", r"\1⌊8⌋ \2"),),
    "13:p0122-0167": (
        (
            r"""<note>aan silvere.*</note>""",
            r"""
<para>aan silvere speciën, als<lb/>
</para>
<para>59.000 pees nieuwe gekartelde ducatons<lb/>
</para>
<para>20.000 „ nieuwe ronde realen van agten<lb/>
</para>
<para>ƒ 936.034, -,ƒ<lb/>
2.644, 3,8<lb/>
</para>
<para>ƒ 236.000,<lb/>
ƒ 64.000,<lb/>
</para>
<para>ƒ 938.678, 3,8<lb/>
</para>
<para>ƒ 300.000,<lb/>
</para>
            """,
        ),
    ),
    "13:p0122-0205": ((r"""(983,14,)""", r"\1⌊5⌋"),),
    "13:p0122-0206": (
        (r"""(, 12)(6)""", r"\1⌊\2⌋"),
        (r"""(1, -)(7)""", r"\1⌊\2⌋"),
    ),
    "13:p0231-0261": ((r"""(563)(3)""", r"\1⌊\2⌋"),),
    "13:p0231-0263": ((r"""(,7,-\.)(4)""", r"\1⌊\2⌋"),),
    "13:p0231-0265": ((r"""(, 6,-)'""", r"\1⌊6⌋"),),
    "13:p0231-0274": (
        (r"""(firti)f""", r"\1j⌊8⌋"),
        (r"""(<note>)(Firtij)""", r"\1⌊8⌋ \2"),
    ),
    "13:p0231-0312": ((r"""(bombara)’ s1\n<super>5<\/super>""", r"\1's⌊15⌋"),),
    "13:p0231-0317": (
        (r"""(, -)(17)""", r"\1⌊\2⌋"),
        (r"""(,8)(18)""", r"\1⌊\2⌋"),
    ),
    "13:p0231-0329": ((r"""A822""", r",4,8⌊22⌋"),),
    "13:p0231-0337": ((r"""(, 2)(23)""", r"\1⌊\2⌋"),),
    "13:p0362-0370": ((r"""(337)(1)""", r"\1⌊\2⌋"),),
    "13:p0362-0453": ((r"""(<note>)(Hoe dit)""", r"\1⌊8⌋ \2"),),
    "13:p0483-0494": (
        (r"""<note>(Makassar.*?)</note>""", r"<subhead>\1</subhead>"),
        (r"""<note>(Bandjarmasin<lb/>.*?)</note>""", r"<subhead>\1</subhead>"),
        (r"""<note>(Bandjarmasin leverde.*?)</note>""", r"<remark>\1</remark>"),
        (r"""<note>(Palembang.*?)</note>""", r"<subhead>\1</subhead>"),
        (r"""<note>(Van Palembang.*?)</note>""", r"<remark>\1</remark>"),
        (r"""<note>SlAM(.*?)</note>""", r"<subhead>Siam\1</subhead>"),
        (r"""<note>(Naar Siam.*?)</note>""", r"<remark>\1</remark>"),
    ),
    "13:p0501-0517": (
        (
            r"""<note>Meede hebben.*</note>""",
            r"""
<para>Meede hebben wij voor welgedaan gehouden de besorging van 228 realen
<und>aan</und><lb/>
<und>stofgoud,</und> tegen 11^ Spaanse reaal, de reaal goud, ofschoon eenigsints boven onse<lb/>
bepaling van 13 Spaans de reaal fijn lopende, wijl na gemelde prijs van 13 Spaans de<lb/>
reaal fijn van 24 caraten ’t marcq fijn op ƒ 374,8,- te staan komt. Daar de reaal grof<lb/>
van 21 caraten, op welk gehalte ’t Banjerse goud ordinair gerekent word, teegen 11^<lb/>
Spaans ingekogt en beswaard met procent provisie wel tot ƒ 387,13,8 klimt en nog<lb/>
</para>
            """,
        ),
    ),
    "13:p0501-0534": ((r"""(1759)(6)""", r"\1⌊\2⌋"),),
    "13:p0501-0536": (
        (r"""<lb/>\n(7,-)(7)""", r"\1⌊\2⌋"),
        (r"""(<note>)(Juister)""", r"\1⌊7⌋ \2"),
    ),
    "13:p0501-0543": (
        (
            r"""<note>of te samen.*</note>""",
            r"""
<para>of te samen<lb/>
</para>
<para>ƒ 7.306.003,16,ƒ<lb/>
1.798.988,17,ƒ<lb/>
520.108,12,4<lb/>
</para>
<para>ƒ 9.625.101, 5,4<lb/>
</para>
            """,
        ),
    ),
    "13:p0501-0549": ((r"""(<note>)(Dit lijkt)""", r"\1⌊8⌋ \2"),),
    "13:p0501-0561": (
        (
            r"""<note>3\.1 13 pakken.*</note>""",
            r"""
<para>3.1 13 pakken en kisten lijwaaten te zamen.<lb/>
</para>
<para>3^ corges of 70 paren extra fijne koussen<lb/>
40 balen of 10.000 lb. saadtlack<lb/>
</para>
<para>ƒ 405,11,8<lb/>
ƒ 5.050,<lb/>
</para>
            """,
        ),
    ),
    "13:p0501-0563": (
        (
            r"""<note>9.*</note>""",
            r"""
ƒ 245.793,13,8<lb/>
ƒ 84.836, 9,8<lb/>
<para>ƒ 6.684, 5,8<lb/>
</para>
<para>ƒ 4.814, 9,-⌊9⌋<lb/>
</para>
<note>⌊9⌋ Juister is ƒ 4.815,9,-<lb/>
</note>
            """,
        ),
    ),
    "13:p0501-0575": (
        (
            r"""<note>Ceylon.*</note>""",
            r"""
<subhead>Ceylon<lb/>
</subhead>
<para>Uit Ceylon zijn gewone en aparte brieven ontvangen van 16 en 28 augustus 1759,<lb/>
23 januari, 11 en 16 februari, 17 maart en 1 en 3 april 1760 met briefjes uit Galle van<lb/>
14 november 1759, 31 januari, 25 maart en 7 april 1760. De besluiten naar aanleiding<lb/>
</para>
            """,
        ),
    ),
    "13:p0501-0578": ((r"""(<note>)(Het totaal)""", r"\1⌊11⌋ \2"),),
    "13:p0501-0581": ((r"""(535)(12)""", r"\1⌊\2⌋"),),
    "13:p0501-0598": (
        (
            r"""(<remark>«Daar de vermindering)""",
            r"<folio>Fol. 751bis r-v. ⌊16⌋</folio>\n\1",
        ),
    ),
    "13:p0620-0620": (
        (
            r"""<note>China.*</note>""",
            r"""
<subhead>Djambi<lb/>
</subhead>
<remark>( Van resident Ajax Fredrik van Solms, die met twee sloepen naar de rivier van Djambi<lb/>
werd gezonden, is slechts bekend dat hij begin januari uit Palembang is vertrokken.<lb/>
</remark>
<subhead>China<lb/>
</subhead>
<remark>Volgens het rapport van 4 februari kon er in China wegens de uitzonderlijk hoge<lb/>
prijs geen goud ingekocht worden. Wat van het meegegeven kapitaal over is, namelijk<lb/>
ƒ 298.118,-, werd met een verbeterde rekening terugontvangen. De rekening uit Kanton van<lb/>
7 januari 1761 was foutief. Voor het aanstaande jaar werd 4500 taël, of mark 685 ff , voor<lb/>
een prijs van 117 taël zilver voor 10 taël goud, wat uitkomt op ruim
ƒ 373,2,5 het mark<lb/>
fijn, aanbesteed. Er is een voorschot van f 238. 758 gegeven. Wegens het strenge toezicht<lb/>
op de uitvoer kon geen zijde of zijden stoffen, noch goud bemachtigd worden. Daarom<lb/>
zou er enige pikol zijde van wat de jonken te Batavia aanbrachten, ingekocht kunnen<lb/>
worden. Op 10 maart kreeg de directeur-generaal daarvoor vergunning, maar op 24 maart<lb/>
is er wegens in verhouding tot de kwaliteit hoge prijs vanaf gezien. Ook is op 10 maart<lb/>
besloten om bij particulieren tegen de huidige koers van rsd 20 het reaal fijn goud in te<lb/>
kopen, wat op
ƒ 432,- uitkomt, of f 32 — duurder dan normaal. Daarvoor kon echter nauwelijks<lb/>
voor
ƒ 10.000 worden ingekocht. Er wordt gevraagd aan de bestelling van het<lb/>
voorafgaande najaar van vier ton baar goud nog vier ton toe te voegen, maar om f 400.000<lb/>
van de verzochte dukaten af te trekken, omdat er anders bij een slechte verwerving van<lb/>
goud moeilijk aan de bestellingen door de kantoren die textiel leveren, voldaan kan worden.<lb/>
<lb/>
</remark>
            """,
        ),
    ),
}


def comp(ex):
    regex = re.compile(ex, re.S)
    return regex


CORRECTIONS = {
    page: tuple(
        (comp(spec[0]), spec[1], 1 if len(spec) == 2 else spec[2]) for spec in specs
    )
    for (page, specs) in CORRECTIONS_DEF.items()
}
OVERRIDE_START = {
    "02:p0770-0813": "«3\\ ton)",
    "07:p0534-0535": "«Kamer Zeeland)",
}

OVERRIDE_FIRST = {
    "01:p0247-0247": {"Inleiding afgedrukt  ... ertrek van schepen »"},
    "05:p0388-0400": {"- maar het werkt stu ... n; de Sultan heeft »"},
    "09:p0112-0116": {"De Huis te Assenburg ... e Machilipatnam af »"},
    "09:p0294-0324": {"uitrustingsgoederen                debiteuren"},
    "09:p0548-0562": {"Op 8 juli zijn nog 2 ... an de Compagnie. Wat"},
}
OVERRIDE_LAST = {
    "09:p0112-0115": {"«Het schip Linschote ... ober zou vertrekken."},
    "09:p0131-0174": {"«Ondanks deze overwe ... omst zorg te draaien"},
    "09:p0702-0731": {"«Personalia. De Midd ... oor de retourlading."},
    "11:p0217-0219": {"«Hoewel het bestuur  ... 1 745 verwacht werd."},
    "11:p0481-0494": {"Men werkt aan het we ... eper geen gebrek is."},
    "13:p0001-0001": {"«Dat uit Palembang v ... ld naartoe gezonden."},
    "13:p0217-0228": {"Naar Bengalen is rui ... rland zijn gezonden."},
    "13:p0340-0340": {"De Mossel is naar Be ... chepen zullen komen."},
    "13:p0483-0494": {"«Gouverneur Roelof B ... anten teruggezonden."},
    "13:p0501-0559": {"«Voor huishoudelijke ... en 21 augustus 1760."},
    "13:p0501-0590": {"«Het bestuur is van  ... oopman werd benoemd."},
    "13:p0620-0620": {"«Van resident Ajax F ... mbang is vertrokken."},
}
OVERRIDE_NOTE_START = {
    "08:p0003-0004": 4,
}
OVERRIDE_NOTE_MARK = {
    "01:p0021-0025": {5: "3"},
    "01:p0063-0065": {5: "6"},
    "01:p0121-0123": {1: "2 3 4"},
    "01:p0184-0188": {5: "8", 6: "5", 7: "6", 8: "7"},
    "01:p0204-0223": {1: "2"},
    "01:p0247-0255": {2: "3"},
    "01:p0279-0292": {3: "1"},
    "01:p0482-0484": {5: "6"},
    "01:p0554-0593": {3: "2"},
    "01:p0596-0638": {5: "1"},
    "01:p0663-0682": {3: "8"},
    "01:p0663-0723": {1: "2"},
    "02:p0007-0018": {6: "5", 7: "6", 8: "7", 9: "8", 10: "9", 11: "10"},
    "02:p0007-0082": {5: "6"},
    "02:p0007-0087": {3: "8"},
    "02:p0007-0075": {3: "2", 4: "3", 5: "4"},
    "02:p0128-0129": {3: "8"},
    "02:p0195-0197": {5: "6"},
    "02:p0200-0215": {2: "3"},
    "02:p0232-0242": {3: "8"},
    "02:p0283-0286": {5: "6"},
    "02:p0306-0309": {2: "3", 3: "2"},
    "02:p0311-0312": {3: "8"},
    "02:p0332-0343": {3: "8"},
    "02:p0403-0414": {3: "8"},
    "02:p0403-0415": {3: "4"},
    "02:p0480-0484": {2: "1"},
    "02:p0480-0499": {5: "6"},
    "02:p0480-0529": {1: "2"},
    "02:p0585-0617": {1: "2 3 4"},
    "02:p0585-0621": {5: "6"},
    "02:p0585-0634": {1: "2 3 4"},
    "02:p0640-0646": {1: "4"},
    "02:p0673-0711": {1: "4"},
    "03:p0047-0050": {1: "2"},
    "03:p0085-0099": {4: "5", 5: "6"},
    "03:p0147-0152": {1: "8"},
    "03:p0247-0288": {1: "2"},
    "03:p0375-0377": {3: "1"},
    "03:p0403-0410": {3: "2"},
    "03:p0484-0486": {3: "2"},
    "03:p0676-0701": {2: "1"},
    "03:p0750-0769": {3: "2"},
    "03:p0779-0796": {4: "5", 5: "6"},
    "03:p0877-0887": {6: "5"},
    "03:p0924-0925": {4: "5", 5: "6"},
    "03:p0924-0937": {4: "5", 5: "6"},
    "04:p0001-0002": {4: "3", 5: "4", 6: "5", 7: "6", 8: "7"},
    "04:p0001-0006": {5: "6", 6: "5"},
    "04:p0001-0007": {4: "8", 3: "2"},
    "04:p0043-0049": {3: "1 2", 2: "1"},
    "04:p0101-0117": {3: "2"},
    "04:p0498-0588": {10: "8"},
    "04:p0498-0589": {6: "2", 7: "3", 8: "4", 9: "5", 10: "6", 11: "7"},
    "04:p0600-0640": {4: "3", 5: "4", 6: "5"},
    "04:p0680-0693": {4: "1"},
    "05:p0024-0050": {6: "7"},
    "05:p0159-0160": {1: "2"},
    "05:p0195-0227": {1: "11"},
    "05:p0439-0441": {1: "2"},
    "05:p0668-0704": {3: "83"},
    "06:p0066-0072": {5: "4", 6: "5", 7: "6"},
    "06:p0267-0268": {4: "5", 5: "6"},
    "06:p0601-0618": {2: "1", 3: "2", 4: "3"},
    "06:p0897-0908": {4: "5", 5: "6"},
    "07:p0003-0026": {3: "1"},
    "07:p0003-0040": {2: "3", 3: "1"},
    "07:p0045-0047": {4: "3"},
    "07:p0078-0087": {2: "3", 3: "1"},
    "07:p0166-0171": {3: "1"},
    "07:p0166-0177": {5: "2"},
    "07:p0166-0194": {3: "2", 4: "3"},
    "07:p0290-0312": {2: "3"},
    "07:p0413-0453": {2: "3", 3: "1"},
    "07:p0517-0527": {3: "1"},
    "07:p0517-0528": {3: "1"},
    "07:p0583-0586": {2: "1"},
    "07:p0596-0599": {2: "3"},
    "07:p0610-0619": {1: "2"},
    "07:p0651-0655": {3: "1"},
    "08:p0009-0019": {23: "11"},
    "08:p0121-0124": {2: "3"},
    "08:p0128-0133": {11: "12", 12: "13"},
}
OVERRIDE_NOTE_BODY = {
    "01:p0184-0188": {5: "8", 6: "5", 7: "6", 8: "7"},
    "01:p0204-0224": {4: "3"},
    "01:p0482-0483": {6: "5"},
    "01:p0553-0553": {2: "1"},
    "01:p0596-0638": {5: "1"},
    "02:p0480-0484": {2: "1"},
    "02:p0007-0018": {6: "5", 7: "6", 8: "7", 9: "8", 10: "9", 11: "10"},
    "02:p0007-0075": {4: "3", 5: "4"},
    "03:p0108-0129": {5: "6"},
    "03:p0247-0270": {3: "4"},
    "03:p0484-0505": {5: "6"},
    "03:p0525-0546": {5: "6"},
    "03:p0601-0602": {5: "6"},
    "03:p0618-0620": {5: "6"},
    "03:p0641-0643": {5: "6"},
    "03:p0750-0754": {5: "6"},
    "03:p0924-0926": {5: "6"},
    "03:p0924-0932": {5: "6"},
    "03:p0924-0935": {5: "6"},
    "04:p0001-0002": {4: "3", 5: "4", 6: "5", 7: "6", 8: "7"},
    "04:p0001-0007": {4: "3", 3: "2"},
    "04:p0038-0038": {5: "6"},
    "04:p0043-0049": {3: "2", 2: "1"},
    "04:p0043-0078": {4: "3"},
    "04:p0101-0112": {5: "6"},
    "04:p0101-0114": {5: "6"},
    "04:p0101-0120": {5: "6"},
    "04:p0125-0131": {5: "6"},
    "04:p0125-0147": {5: "6"},
    "04:p0125-0148": {5: "6"},
    "04:p0183-0188": {5: "6"},
    "04:p0262-0282": {5: "6"},
    "04:p0262-0302": {5: "6"},
    "04:p0318-0320": {5: "6"},
    "04:p0373-0390": {5: "6"},
    "04:p0496-0496": {5: "6"},
    "04:p0600-0605": {5: "6"},
    "04:p0600-0633": {2: "1"},
    "04:p0600-0640": {4: "3", 5: "4", 6: "5"},
    "04:p0651-0668": {2: "1"},
    "04:p0680-0693": {5: "6"},
    "04:p0680-0703": {3: "4"},
    "04:p0707-0709": {5: "6"},
    "05:p0605-0618": {5: "6"},
    "06:p0051-0060": {5: "6"},
    "06:p0066-0072": {4: "1", 5: "4", 6: "5", 7: "6"},
    "06:p0236-0250": {5: "6"},
    "06:p0275-0278": {5: "6"},
    "06:p0383-0386": {5: "6"},
    "06:p0415-0442": {5: "6"},
    "06:p0477-0493": {5: "6"},
    "06:p0477-0497": {5: "6"},
    "06:p0514-0519": {5: "6"},
    "06:p0587-0588": {5: "6"},
    "06:p0601-0618": {2: "1", 3: "2", 4: "3"},
    "06:p0641-0652": {5: "6"},
    "06:p0750-0787": {5: "6"},
    "06:p0750-0806": {5: "6"},
    "06:p0810-0820": {5: "6"},
    "06:p0810-0830": {5: "6"},
    "06:p0844-0860": {5: "6"},
    "07:p0166-0194": {3: "2", 4: "3"},
    "07:p0610-0619": {1: "2"},
    "07:p0684-0690": {2: "3", 3: "4"},
    "07:p0710-0713": {2: "1"},
    "07:p0710-0733": {2: "1", 3: "2"},
    "08:p0128-0133": {11: "12", 12: "13"},
    "09:p0344-0355": {2: "1"},
}
SKIP_NOTE_BODY = {
    "08:p0128-0133": {11},
}
SKIP_NOTE_MARK = {
    "02:p0821-0822": {"n"},
}
REMARK_SPURIOUS_RE = re.compile(r"""<remark>(y[y ]*)</remark>""", re.S)
REMARK_END_CORR_RE = re.compile(r"""\)\s*\.\s*([*\]^])\s*(</remark>)""", re.S)

COMMENT_RE = re.compile(r"""<(fnote|remark)\b([^>]*)>(.*?)</\1>""", re.S)
REMARK_START_RE = re.compile(
    r"""
        ^
        (
            (?:
                <
                    (?:
                        special
                        |
                        ref
                        |
                        emph
                    )
                >
            )?
        )
        -*
        \s*
        \*?
        [({]
        \s*
    """,
    re.S | re.X,
)
REMARK_END_RE = re.compile(
    r"""
        [ -]*
        (?:
            [ :)}][;\]]
            |
            [:)}]
        )
        [ -]*
        \s*
        [:;.,]?
        \s*
        (
            (?:
                </
                    (?:
                        ref
                        |
                        super
                        |
                        emph
                    )>
                \s*
            )?
            (?:
                <lb/>
                \s*
            )?
        )
        $
    """,
    re.S | re.X,
)
REMARK_RE = re.compile(r"""<remark>(.*?)</remark>""", re.S)
REMARK_MULTIPLE_RE = re.compile(
    r"""
        (?:
            <remark>
                (?:
                    .
                    (?!
                        <remark
                    )
                )*
            </remark>
            \s*
        ){2,}
    """,
    re.S | re.X,
)

REMARK_FIRST_REMOVE_RE = re.compile(r"""<remark\b[^>]*>.*?</remark>""", re.S)

REMARK_LAST_REMOVE_RE = re.compile(
    r"""
        <remark\b[^>]*>
            (
                (?:
                    .
                    (?!<remark)
                )*
            )
        </remark>
        (?=
            \s*
            (?:
                (?:
                    (?:
                        <note\b[^>]*>.*?</note>
                    )
                    |
                    (?:
                        <folio\b[^>]*>.*?</folio>
                    )
                )
                \s*
            )*
            $
        )
    """,
    re.S | re.X,
)

REMARK_PRE_POST_RE = re.compile(
    r"""
        ^
        (.*?)
        <remark>
        .*
        </remark>
        (.*)
        $
    """,
    re.S | re.X,
)

REMARK_PRE_RE = re.compile(
    r"""
        <pb\b[^>]*>\s*
        (?:
            (?:
                (?:
                    <head\b[^>]*>.*?</head>
                )
                |
                (?:
                    <folio\b[^>]*>.*?</folio>
                )
            )
            \s*
        )*
        \s*
        (.*)
        $
    """,
    re.S | re.X,
)

REMARK_POST_RE = re.compile(
    r"""
        ^
        \s*
        (.*?)
        (?:
            (?:
                (?:
                    <note\b[^>]*>.*?</note>
                )
                |
                (?:
                    <folio\b[^>]*>.*?</folio>
                )
            )
            \s*
        )*
        $
    """,
    re.S | re.X,
)

PARA_END_BEFORE_NOTES_RE = re.compile(
    r"""
        (
            <fnote\b
                .*
            </fnote>
            \s*
        )
        (</para>)
    """,
    re.S | re.X,
)

EMPTY_PARA_RE = re.compile(r"""<para>\s*</para>\s*""", re.S)

NOTES_PER_PAGE = {1, 2, 3, 4, 5, 6, 7}
NOTES_BRACKET = {1, 2, 3, 4, 5, 6, 7, 8}
NOTE_START = 0

EXTRA_DIGITS = {
    "i": 1,
    "l": 1,
}

EXTRA_DIGIT_STR = "".join(EXTRA_DIGITS)

NUMBER_RE = re.compile(r"""[0-9]""")

NUMBER_SANITY_RE = re.compile(
    fr"""
    \b
    (?:
        [0-9{EXTRA_DIGIT_STR}]
        [0-9{EXTRA_DIGIT_STR}.,/-]*
        [0-9{EXTRA_DIGIT_STR}]
    )
    \b
    """,
    re.S | re.X,
)


def numberRepl(match):
    number = match.group(0)
    if not NUMBER_RE.search(number):
        return number

    for (extraDigit, value) in EXTRA_DIGITS.items():
        number = number.replace(extraDigit, str(value))
    return number


def processPage(text, previous, result, info, *args, **kwargs):
    global NOTE_START
    remarkInfo = info["remarkInfo"]
    fnoteBodyInfo = info["fnoteBodyInfo"]
    page = info["page"]
    prevRemark = previous.get("remark", None)
    prevNotes = previous.get("notes", [])
    prevPage = previous.get("page", None)

    if not text:
        if prevNotes is not None:
            for (ref, body, summary) in prevNotes:
                mark = "" if ref is None else f' ref="{ref}"'
                result.append(f"<fnote{mark}>{body}</fnote>\n")
            previous["notes"] = []
        result.append("\n\n")
        return

    vol = int(info["vol"].lstrip("0"))
    first = info["first"]
    if page in OVERRIDE_NOTE_START:
        NOTE_START = OVERRIDE_NOTE_START[page] - 1
    elif vol in NOTES_PER_PAGE or first:
        NOTE_START = 0

    (text, current) = trimPage(text, info, previous, *args, **kwargs)

    onlyRemark = current["onlyRemark"]
    firstRemark = current["firstRemark"]
    lastRemark = current["lastRemark"]
    startRemark = onlyRemark if onlyRemark else firstRemark if firstRemark else None

    if startRemark:
        (curContent, curSummary) = startRemark

    if prevRemark is None:
        if startRemark:
            remarkInfo["≮"][curSummary].append(page)
    else:
        (prevContent, prevSummary) = prevRemark
        if not startRemark:
            remarkInfo["≯"][prevSummary].append(prevPage)

    previous["remark"] = onlyRemark if onlyRemark else lastRemark

    onlyNote = current["onlyNote"]
    firstNote = current["firstNote"]
    startNote = onlyNote if onlyNote else firstNote if firstNote else None

    if startNote:
        (curRef, curBody, curSummary) = startNote

    if not prevNotes:
        if startNote:
            (curRef, curBody, curSummary) = startNote
            fnoteBodyInfo[page].insert(0, ("≮", curSummary))
            current["notes"].insert(0, startNote)
    else:
        (prevRef, prevBody, prevSummary) = prevNotes[-1]
        if startNote:
            (thisSummary, thisTrimmed) = summarize(prevSummary + curSummary)
            prevNotes[-1] = (prevRef, prevBody + curBody, thisSummary)
        for (ref, body, summary) in prevNotes:
            mark = "" if ref is None else f' ref="{ref}"'
            result.append(f"<fnote{mark}>{body}</fnote>\n")
        result.append("\n")

    previous["notes"] = current["notes"]
    previous["page"] = page

    result.append(text)
    result.append("\n")


def trimVolume(vol, letters, info, idMap, givenLid, mergeText):
    vol = info["vol"]
    info["noteBrackets"] = int(vol.lstrip("0")) in NOTES_BRACKET


ADD_LB_STR = "|".join(ADD_LB_ELEMENTS)

TAIL_LB_RE = re.compile(
    fr"""
        <lb/>
        \s*
        (
            </
                (?:
                    {ADD_LB_STR}
                )
            >
        )
        \s*
    """,
    re.S | re.X,
)

A_RE = re.compile(r"(\b|[0-9])a([0-9])", re.S)


def trimPage(text, info, previous, *args, **kwargs):
    global NOTE_START

    remarkInfo = info["remarkInfo"]
    page = info["page"]

    overrideFirst = OVERRIDE_FIRST.get(page, set())
    overrideLast = OVERRIDE_LAST.get(page, set())
    overrideStart = OVERRIDE_START.get(page, None)

    text = REMARK_SPURIOUS_RE.sub(r"<special>\1</special>", text)
    text = COMMENT_RE.sub(cleanTag, text)
    text = REMARK_END_CORR_RE.sub(r"\1).\2", text)

    text = EMPTY_PARA_RE.sub(r"", text)

    text = applyCorrections(CORRECTIONS, page, text)

    text = REMARK_MULTIPLE_RE.sub(remarkMultiplePre(info), text)

    text = NUMBER_SANITY_RE.sub(numberRepl, text)
    text = A_RE.sub(r"\1 à \2", text)

    current = {}

    onlyRemark = None
    firstRemark = None
    lastRemark = None

    ppMatch = REMARK_PRE_POST_RE.search(text)
    if ppMatch:
        (beforeFirst, afterLast) = ppMatch.group(1, 2)
        pre = REMARK_PRE_RE.match(beforeFirst)
        pre = "" if pre is None else pre.group(1).strip()
        post = REMARK_POST_RE.match(afterLast)
        post = "" if post is None else post.group(1).strip()

        matches = tuple(REMARK_RE.finditer(text))
        for (i, match) in enumerate(matches):
            content = match.group(1)
            (summary, trimmed) = summarize(cleanText(content, "remark", full=True))
            startBracket = trimmed.startswith("«")
            endBracket = trimmed.endswith("»")
            isFirst = (
                i == 0
                and not pre
                and (
                    (not startBracket and summary not in overrideFirst)
                    or (overrideStart and content.startswith(overrideStart))
                )
            )
            isLast = (
                i == len(matches) - 1
                and not post
                and (not endBracket and summary not in overrideLast)
            )
            content = cleanText(content, "remark")
            if overrideStart and content.startswith(overrideStart):
                content = "(" + content[1:]
            if isFirst and isLast:
                onlyRemark = (content, summary)
            elif isFirst:
                firstRemark = (content, summary)
            elif isLast:
                lastRemark = (content, summary)
            label = (
                "1"
                if isFirst and isLast
                else "F"
                if isFirst
                else "L"
                if isLast
                else "v"
                if startBracket and endBracket
                else "("
                if startBracket
                else ")"
                if endBracket
                else "x"
            )
            remarkInfo[label][summary].append(page)
    else:
        remarkInfo["0"][""].append(page)

    current["onlyRemark"] = onlyRemark
    current["firstRemark"] = firstRemark
    current["lastRemark"] = lastRemark

    fnoteBodyInfo = info["fnoteBodyInfo"]
    fnoteMarkInfo = info["fnoteMarkInfo"]

    thisFnoteBodyInfo = []
    thisFnoteMarkInfo = []

    (text, bodies) = formatNoteBodies(text, info, current, thisFnoteBodyInfo)

    if len(bodies) == 0:
        marks = {}
    else:
        (text, marks) = formatNoteMarks(text, info, bodies)
        for (ref, (mark, summary)) in marks.items():
            thisFnoteMarkInfo.append((ref, mark, summary))
        thisFnoteMarkInfo.append((None, len(bodies), len(marks)))
        fnoteMarkInfo[page].extend(thisFnoteMarkInfo)
        NOTE_START = max(bodies)

    if bodies:
        for (ref, (mark, summary)) in bodies.items():
            thisFnoteBodyInfo.append((ref, mark, summary))
        fnoteBodyInfo[page].extend(thisFnoteBodyInfo)
    else:
        label = "0"
        thisFnoteBodyInfo.append((label, ""))
        for x in reversed(thisFnoteBodyInfo):
            fnoteBodyInfo[page].insert(0, x)

    text = TAIL_LB_RE.sub(r"\1\n", text)

    text = text.replace(LT, "&lt;").replace(GT, "&gt;").replace(AMP, "&amp;")
    return (text, current)


LEGEND_REMARK = {
    "≮": "continuing remark without previous remark on preceding page",
    "≯": "to-be-continued remark without next remark on following page",
    "x": "remark without opening and without closing",
    "(": "remark with opening and without closing",
    ")": "remark without opening and with closing",
    "m": "multiple remarks combined into one",
    "1": "single remark continuing from previous page and extending to next page",
    "F": "first remark on page continuing from previous page",
    "L": "last remark on page continuing to next page",
    "0": "page without remarks",
    "v": "remark without issues",
}

LEGEND_NOTE = {
    "≮": (None, "continuing note without previous note on preceding page"),
    "1": (None, "single note continuing from previous page and extending to next page"),
    "F": (None, "first note on page continuing from previous page"),
    "0": (None, "page without notes"),
    "≠": (0, "mark in conflict with sequence number"),
    "↓": (0, "no mark in text"),
    "+": (20, "mark is one more than sequence number"),
    "-": (20, "mark is one less than sequence number"),
    "→": (40, "no mark in body"),
    "∉": (20, "sequence number not contained in mark"),
    "≃": (98, "sequence number corresponds to mark modulo OCR errors"),
    "∈": (99, "sequence number contained in mark"),
    "*": (100, "mark is * or x, will be filled in by sequence number"),
    "≡": (100, "mark exactly equal to sequence number"),
    "=": (100, "mark exactly equal to sequence number after overriding"),
}
LEGEND_SCORE = {x[0]: x[1][0] for x in LEGEND_NOTE.items()}

INDEF = {"*", "x"}


def corpusPost(info):
    print("REMARKS:\n")
    remarkInfo = info["remarkInfo"]
    totalPatterns = 0
    totalRemarks = 0
    with open(f"{REP}/remarks.tsv", "w") as fh:
        for (label, legend) in LEGEND_REMARK.items():
            thisRemarkInfo = remarkInfo.get(label, {})

            nPatterns = len(thisRemarkInfo)
            nRemarks = sum(len(x) for x in thisRemarkInfo.values())
            if label not in {"m", "1", "F", "L", "0"}:
                totalPatterns += nPatterns
                totalRemarks += nRemarks

            msg = f"{label}: {nPatterns:>5} in {nRemarks:>5} x {legend}"
            print(f"\t{msg}")
            fh.write(f"\n-------------------\n{msg}\n\n")

            for (summary, docs) in sorted(thisRemarkInfo.items(), key=byOcc):
                fh.write(f"{summary} {docSummary(docs).rstrip()}\n")

        msg = f"T: {totalPatterns:>5} in {totalRemarks:>5} x in total"
        print(f"\t{msg}")

    # FOOTNOTE BODIES

    fnoteBodyInfo = info["fnoteBodyInfo"]

    totalNotes = 0
    totalPages = len(fnoteBodyInfo)
    totalScore = 0
    scores = collections.defaultdict(list)

    noteLog = collections.defaultdict(dict)

    for page in sorted(fnoteBodyInfo):
        report = []
        overrideMark = OVERRIDE_NOTE_BODY.get(page, {})
        entries = fnoteBodyInfo[page]

        score = 0
        nNotes = 0

        for entry in entries:
            if len(entry) == 2:
                (label, summary) = entry
                report.append(f"\t{label} «{summary or ''}»\n")
                continue

            nNotes += 1
            (ref, mark, summary) = entry
            mark = normalize(mark)

            label = (
                "→"
                if not mark
                else "≡"
                if str(ref) == mark
                else "="
                if overrideMark.get(ref, None) == mark
                else "-"
                if str(ref - 1) == mark
                else "+"
                if str(ref + 1) == mark
                else "≠"
            )
            thisScore = LEGEND_SCORE[label]
            score += thisScore
            markRep = f"⌈{mark}⌉"
            report.append(f" {ref:>2} {label} {markRep:<4} «{summary}»\n")

        score = 100 if nNotes == 0 else int(round(score / nNotes))
        scoreThreshold = int((score // 10) * 10)
        scores[scoreThreshold].append(page)
        totalScore += score
        totalNotes += nNotes

        log = "".join(report)
        noteLog[score][page] = log

    with open(f"{REP}/footnoteBodies.tsv", "w") as fh:
        for score in sorted(noteLog):
            fh.write(f"score={score:>3}\n")
            pages = noteLog[score]
            for page in sorted(pages):
                fh.write(f"={score:>3} page={page}\n")
                fh.write(pages[page])

    minScore = min(noteLog) if noteLog else 100
    avScore = 100 if totalNotes == 0 else int(round(totalScore / totalPages))

    print(
        f"FOOTNOTE BODIES: {totalNotes} notes on {totalPages} pages"
        f" with score: average={avScore}, minimum={minScore}"
    )
    for score in sorted(scores):
        pages = scores[score]
        pagesRep = docSummary(pages)
        print(f"\tscore {score:>3} ({pagesRep})")

    # FOOTNOTE MARKS

    fnoteMarkInfo = info["fnoteMarkInfo"]

    totalNotes = 0
    totalPages = len(fnoteMarkInfo)
    totalScore = 0
    scores = collections.defaultdict(list)

    noteLog = collections.defaultdict(dict)

    for page in sorted(fnoteMarkInfo):
        report = []
        overrideMark = OVERRIDE_NOTE_MARK.get(page, {})
        entries = fnoteMarkInfo[page]

        score = 0
        nNotes = 0

        nBodies = 0
        nMarks = 0

        for (ref, mark, summary) in entries:
            if ref is None:
                nBodies = mark
                nMarks = summary
                continue

            nNotes += 1
            oldMark = mark
            mark = normalize(mark)

            parts = tuple(n for n in mark.split())
            nums = {int(n) for n in parts if n.isdigit()}
            polyNums = len(parts) > 1

            label = (
                "↓"
                if not mark
                else "≡"
                if str(ref) == mark
                else "="
                if overrideMark.get(ref, None) == mark
                else "≃"
                if str(ref) == mark.replace(" ", "")
                else "∈"
                if ref in nums
                else "∉"
                if polyNums and ref not in nums
                else "*"
                if mark in MARK_SIGNS
                else "≃"
                if (ref == 1 and (mark == "Y" or oldMark == "J" or oldMark == "z"))
                or (ref == 3 and mark in {"2", "8"})
                or (ref == 5 and mark in {"6", "8"})
                or (ref == 6 and mark in {"°", "8"})
                else "-"
                if str(ref - 1) == mark
                else "+"
                if str(ref + 1) == mark
                else "≠"
            )
            thisScore = LEGEND_SCORE[label]
            score += thisScore
            markRep = f"⌈{mark}⌉"
            report.append(f" {ref:>2} {label} {markRep:<4} «{summary}»\n")

        comment = None
        if nBodies < nMarks:
            score = 0
            comment = f"too many marks: {nMarks - nBodies}\n"
        elif nBodies > nMarks:
            score = 0
            comment = f"too few marks: {nBodies - nMarks}\n"
        else:
            score = 100 if nNotes == 0 else int(round(score / nNotes))
        if comment is not None:
            report.insert(0, comment)
        scoreThreshold = int((score // 10) * 10)
        scores[scoreThreshold].append(page)
        totalScore += score
        totalNotes += nNotes

        log = "".join(report)
        noteLog[score][page] = log

    with open(f"{REP}/footnoteMarks.tsv", "w") as fh:
        for score in sorted(noteLog):
            fh.write(f"score={score:>3}\n")
            pages = noteLog[score]
            for page in sorted(pages):
                fh.write(f"={score:>3} page={page}\n")
                fh.write(pages[page])

    minScore = min(noteLog) if noteLog else 100
    avScore = 100 if totalNotes == 0 else int(round(totalScore / totalPages))

    print(
        f"FOOTNOTE MARKS: {totalNotes} notes on {totalPages} pages"
        f" with score: average={avScore}, minimum={minScore}"
    )
    for score in sorted(scores):
        pages = scores[score]
        pagesRep = docSummary(pages)
        print(f"\tscore {score:>3} ({pagesRep})")


def byOcc(x):
    (summary, docs) = x
    return (docs[0], summary) if docs else ("", summary)


def remarkMultiplePre(info):
    return lambda match: remarkMultiple(match, info)


def remarkMultiple(match, info):
    remarkInfo = info["remarkInfo"]
    page = info["page"]
    text = match.group(0)
    result = []

    for remarks in REMARK_MULTIPLE_RE.findall(text):
        mRemarks = []
        prevClosed = False

        for match in REMARK_RE.finditer(remarks):
            content = match.group(1)
            (summary, trimmed) = summarize(cleanText(content, "remark", full=True))
            content = cleanText(content, "remark")
            thisOpen = trimmed.startswith("(")
            thisClosed = trimmed.endswith(")")

            if prevClosed or thisOpen:
                if mRemarks:
                    mText = (
                        "<remark>\n"
                        + (" ".join(r[0] for r in mRemarks))
                        + "</remark>\n"
                    )
                    result.append(mText)
                    if len(mRemarks) > 1:
                        summary = "\n\t".join(r[1] for r in mRemarks)
                        remarkInfo["m"][f"{len(mRemarks)}\t{summary}"].append(page)
                    mRemarks = []
            mRemarks.append((content, summary))
            prevClosed = thisClosed

        if mRemarks:
            mText = "<remark>\n" + (" ".join(r[0] for r in mRemarks)) + "</remark>\n"
            result.append(mText)
            if len(mRemarks) > 1:
                summary = "\n\t".join(r[1] for r in mRemarks)
                remarkInfo["m"][f"{len(mRemarks)}\t{summary}"].append(page)

    return "".join(result)


REF_RE = re.compile(
    fr"""
        (<ref>)
        ([^<]*)
        (</ref>)
        (
            (?:
                [XIVLMC]*
                \s*
                (?:
                    [0-9]{{1,2}}
                    \s+
                    {MONTH_DETECT_PAT}
                    \s+
                    1[6-8][0-9][0-9]
                    \s*
                )?
                \s*
                (?:
                    ,
                    |
                    p\.
                    |
                    [0-9rv]+
                    |
                    -
                    |
                    (?:
                        </?emph>
                        |
                        <lb/>
                    )
                    |
                    \s+
                )
            )+
        )
        (
            (?:
                [^<]*
                </emph>
            )?
        )
    """,
    re.S | re.X,
)


def refRepl(match):
    (start, inside, end, trail, tail) = match.group(1, 2, 3, 4, 5)
    trail = trail.replace("<emph>", "").replace("</emph>", "").replace("<lb/>", " ")
    tail = tail.replace("</emph>", "")
    inside = (inside + trail).replace("\n", " ")
    inside = WHITE_RE.sub(" ", inside)
    return f"{start}{inside}{end}{tail}"


NOTE_RENAME_P_RE = re.compile(r"""<fnote\b[^>]*>(.*?)</fnote>""", re.S)


def filterNotes(match):
    notes = match.group(1)
    word = match.group(2)
    if word:
        notes = NOTE_RENAME_P_RE.sub(r"""<para>\1</para>""", notes)
    return f"""{notes}{word}"""


def filterNotes2(match):
    pre = match.group(1)
    notes = match.group(2)
    notes = NOTE_RENAME_P_RE.sub(r"""<para>\1</para>""", notes)
    return f"""{pre}{notes}"""


NOTES_FILTER1 = (
    (
        re.compile(
            r"""
                (
                    </table>
                    \s*
                    (?:
                        </para>
                        \s*
                    )?
                )
                (
                    (?:
                        <fnote>
                            .*?
                        </fnote>
                        \s*
                    )+
                )
            """,
            re.S | re.X,
        ),
        filterNotes2,
    ),
)
NOTES_FILTER2 = (
    (
        re.compile(
            r"""
                (
                    (?:
                        <fnote[^>]*>
                            .*?
                        </fnote>
                        \s*
                    )+
                )
                (\S*)
            """,
            re.S | re.X,
        ),
        filterNotes,
    ),
)
NOTES_ALL_RE = re.compile(
    r"""
        ^
            (.*?)
            (
                (?:
                    <fnote.*?</fnote>
                    \s*
                )+
            )
            (.*?)
        $
    """,
    re.S | re.X,
)
NOTE_RE = re.compile(r"""<fnote\b([^>]*)>(.*?)</fnote>""", re.S)

NOTE_COLLAPSE_RE = re.compile(
    r"""
    (<fnote\ ref=[^>]*>)
    (.*?)
    (</fnote>)
    (
        (?:
            \s*
            <(
                fnote
                |
                para
            )>
            .*?
            </\5>
        )+
    )
    """,
    re.S | re.X,
)


def collapseNotes(match):
    (firstNoteStart, firstNoteText, firstNoteEnd, restNotes) = match.group(1, 2, 3, 4)
    restNotes = restNotes.replace("<fnote>", " ")
    restNotes = restNotes.replace("</fnote>", " ")
    restNotes = restNotes.replace("<para>", " ")
    restNotes = restNotes.replace("</para>", " ")
    return f"""{firstNoteStart}{firstNoteText} {restNotes}{firstNoteEnd}"""


NOTE_MARK_RE = re.compile(r"""<fnote ref="([^"]*)">""", re.S)
NOTE_ATT_REF_RE = re.compile(r"""\bref="([^"]*)["]""", re.S)

FOLIO_DWN_RE = re.compile(r"""<folio>\s*(.*?)\s*</folio>""", re.S)
MARK_DWN_RE = re.compile(r"""<fref ref="([^"]*)"/>""", re.S)
TABLE_DWN_RE = re.compile(r"""<table\b[^>]*>\s*(.*?)\s*</table>""", re.S)
ROW_DWN_RE = re.compile(r"""<row\b[^>]*>\s*(.*?)\s*</row>""", re.S)
CELL_DWN_RE = re.compile(r"""<cell\b[^>]*>\s*(.*?)\s*</cell>""", re.S)


def tableDown(match):
    text = match.group(1)
    rows = []
    for rowStr in ROW_DWN_RE.findall(text):
        rows.append(CELL_DWN_RE.findall(rowStr))
    columns = max(len(row) for row in rows)

    result = []
    result.append(
        "".join((("" if i == 0 else " | ") + f" {i + 1} ") for i in range(columns))
    )
    result.append(
        "".join((("" if i == 0 else " | ") + " --- ") for i in range(columns))
    )
    for row in rows:
        result.append(
            "".join(
                (("" if i == 0 else " | ") + f" {cell} ")
                for (i, cell) in enumerate(row)
            )
        )
    return "\\n".join(result)


def cleanTag(match):
    tag = match.group(1)
    atts = match.group(2)
    text = match.group(3)
    text = cleanText(text, tag)
    return f"<{tag}{atts}>{text}</{tag}>"


def cleanText(text, tag, full=False):
    if full:
        text = text.replace("<lb/>", " ")
        text = text.replace("<emph>", "*")
        text = text.replace("</emph>", "*")
        text = text.replace("<subhead>", "**")
        text = text.replace("</subhead>", "**")
        text = text.replace("<und>", "_")
        text = text.replace("</und>", "_")
        text = text.replace("<sub>", "^")
        text = text.replace("</sub>", "^")
        text = text.replace("<super>", "^")
        text = text.replace("</super>", "^")
        text = text.replace("<special>", "`")
        text = text.replace("</special>", "`")
        text = text.replace("<ref>", "[")
        text = text.replace("</ref>", "]")
        text = MARK_DWN_RE.sub(r"[=\1]", text)
        text = FOLIO_DWN_RE.sub(r" {\1} ", text)
        text = text.replace("\n", " ")
        text = text.strip()
        text = WHITE_RE.sub(" ", text)
        text = TABLE_DWN_RE.sub(tableDown, text)

    if tag == "remark":
        text = REMARK_START_RE.sub(r"«\1", text)
        text = REMARK_END_RE.sub(r"\1»", text)
    text = REF_RE.sub(refRepl, text)

    if full:
        if "<" in text:
            print(f"\nunclean {tag}")
            print(f"\t==={text}===")
    return text


MARK_MAPPING = {
    "‘": "1",
    "’": "1",
    "'": "1",
    "i": "1",
    "I": "1",
    "l": "1",
    "il": "1",
    "[il": "1",
    "<ref>il</ref>": "1",
    "ï": "1",
    "]": "1",
    "!": "1",
    "L": "1",
    "r": "1",
    "s": "2",
    "J": "3",
    "z": "3",
    "}": "3",
    "ö": "5",
    "b": "6",
    "fl": "6",
    "K": "8",
    "y": "9",
    "n": "11",
    "<emph>2</emph> Q": "20",
}


def normalize(text):
    n = MARK_MAPPING.get(text, None)
    if n is not None:
        return n

    return text


def markedUnNote(match):
    parts = match.groups()
    if len(parts) > 1:
        (num, trail) = parts
    else:
        num = parts[0]
        trail = ""
    num = normalize(num)
    return f"""<note ref="{num}">{trail}"""


def markedUnNoteRepl(match):
    (pre, num, text) = match.group(1, 2, 3)
    num = normalize(num)
    pre = pre.replace("<lb/>", "")
    text = text.strip()
    if text.endswith("<lb/>"):
        text = text[0:-5].rstrip()
    if text and num == "0":
        print(f"X {pre=}, {num=} {text=}")
    return f"{pre}\n<note>{num}) {text}</note>\n" if text else match.group(0)


MARKED_NOTE_DBL_RE = re.compile(r"""(<lb/></note>)(<note>)""", re.S)
MARK_BODY = r"""
    (?:
        \[il
        |
        il\b
        |
        [ïöKbyn]\b
        |
        \]
        |
        <ref>il</ref>
        |
        <emph>2</emph>\ Q
        |
        [0-9]{1,2}\b
    )
"""
MARKED_NOTE = (
    (
        re.compile(
            r"""
                <note>
                \s*
                ⌊([0-9]+)⌋
                \s*
                \)?
                \s*
            """,
            re.S | re.X,
        ),
        markedUnNote,
    ),
    (
        re.compile(
            fr"""
                <note>
                \s*
                <super>
                \s*
                (
                    {MARK_BODY}
                )
                \s*
                \)?
                </super>
                \s*
                \)?
                \s*
            """,
            re.S | re.X,
        ),
        markedUnNote,
    ),
    (
        re.compile(
            fr"""
                <note>
                \s*
                (
                    {MARK_BODY}
                )
                \s*
                \)?
                \s*
            """,
            re.S | re.X,
        ),
        markedUnNote,
    ),
    (
        re.compile(
            fr"""
                <note>
                \s*
                <emph>
                (
                    {MARK_BODY}
                )
                \s*
                \)?
                ([^<]*)
                </emph>
                \s*
            """,
            re.S | re.X,
        ),
        markedUnNote,
    ),
    (
        re.compile(
            r"""
                <note>
                \s*
                (
                    I
                )
                \s*
                \)
                \s*
            """,
            re.S | re.X,
        ),
        markedUnNote,
    ),
)

MARKED_UN_NOTE = (
    (
        re.compile(
            fr"""
            \s*
            (
                (?:
                    <lb/>
                    |
                    <para>
                )
            )
            \s*
            (
                {MARK_BODY}
            )
            \s*
            \)
            \s*
            (.*?)
            (?=
                (?:
                    <lb/>
                    \s*
                    (?:
                        {MARK_BODY}
                    )
                    \s*
                    \)
                )
                |
                (?:
                    (?:
                        <lb/>
                    )?
                    (?:
                        <note\b
                        |<para
                        |</para
                        |<remark
                        |$
                    )
                )
            )
        """,
            re.S | re.X,
        ),
        markedUnNoteRepl,
    ),
    (
        re.compile(
            r"""
                <para\b[^>]*>
                \s*
                (
                    <note\b[^>]*>
                    (?:
                        .
                        (?!
                            <para\b
                        )
                    )*
                    </note>
                )
                \s*
                </para>
                \s*
            """,
            re.S | re.X,
        ),
        r"\1\n",
    ),
    (
        re.compile(
            r"""
                (
                    <note\b[^>]*>
                    (?:
                        .
                        (?!
                            <para\b
                        )
                    )*
                    </note>
                )
                \s*
                (</para>)
                \s*
            """,
            re.S | re.X,
        ),
        r"\2\n\1\n",
    ),
)

# MARK_LETTERS_TEXT_BR = "xyziLlbn"

MARK_NUM = r"""
    (?:
        [0-9]{1,2}
        (?:
            \s+
            [0-9]{1,2}
        )*
    )
"""

MARK_SIGN_STR = r"’‘°ö•■®*xBJ':!\]}"
MARK_LETTER = r"[ilLYrzsn]"
MARK_SIGNS = set(MARK_SIGN_STR)
MARK_SIGN_PAT = f"[{MARK_SIGN_STR}]"
MARK_TRAIL = ".,;: "

MARK_PLAIN_BR_RE = re.compile(
    fr"""
        (
            (?:
                <super>
                (?:
                    {MARK_NUM}
                    |
                    {MARK_LETTER}
                    |
                    {MARK_SIGN_PAT}
                    |
                    fl
                )
                \s*
                \)
                ([{MARK_TRAIL}]*)
                </super>
            )
            |
            (?:
                <super>
                (?:
                    {MARK_NUM}
                    |
                    {MARK_LETTER}
                    |
                    {MARK_SIGN_PAT}
                    |
                    fl
                )
                </super>
                \s*
                \)
            )
            |
            (?:
                ⌊
                [0-9]{{1,2}}
                ⌋
            )
            |
            (?:
                (?:
                    (?:
                        (?:
                            \b
                            |
                            (?<=
                                1[6-8][0-9]{{2}}
                            )
                        )
                        {MARK_NUM}
                    )
                    |
                    {MARK_SIGN_PAT}
                    |
                    (?:
                        \b
                        (?:
                            fl
                            |
                            {MARK_LETTER}
                        )
                    )
                )
                \)
            )
            |
            (?:
                (?<=[a-zéA-Z])
                {MARK_NUM}
                \)
            )
        )
    """,
    re.S | re.X,
)

# Lots of <super>1</super> are really apostrophes.
# But they can also be frefs. Sigh
# We can try to weed them out at the moment when we know the note bodies.
# If then the number in the super element does not correspond to a note body
# we turn it into an apostrophe

MARK_PLAIN_RE = re.compile(
    fr"""
        (
            (?:
                <super>
                {MARK_NUM}
                </super>
            )
            |
            (?:
                ⌊
                [0-9]{{1,2}}
                ⌋
            )
            |
            (?:
                (?<=[a-zé])
                [0-9]{{1,2}}
                \b
            )
            |
            (?:
                (?<=[a-zé][;.’'])
                [0-9]{{1,2}}
                \b
            )
        )
    """,
    re.S | re.X,
)


NOTE_RENAME_RE = re.compile(r"""<note\b([^>]*)>(.*?)</note>""", re.S)
SPURIOUS_PARA_RE = re.compile(
    fr"""
        (
            <lb/>
            \s*
        )
        </para>
        \s*
        <para>
        \s*
        (
            {MARK_BODY}
        )
        \s*
        \)
        \s*
    """,
    re.S | re.X,
)
DEL_LB_RE = re.compile(r"""(</note>)\s*<lb/>\s*""", re.S)

NOTE_REF_BODY_RE = re.compile(
    r"""
        (<note>)
        <ref>
        (
            [0-9]{1,2}
            \)
        )
        </ref>
        \s*
    """,
    re.S | re.X,
)


def showPage(text, label):
    (tb, te) = (400, 1000)
    show = False and 'n="41"' in text
    if show:
        print(
            f"=== [ {label} ] ========================================================"
        )
        print(text[tb:te])


def formatNoteBodies(text, info, current, thisFnoteBodyInfo):
    showPage(text, "BODY AAAA")
    text = NOTE_REF_BODY_RE.sub(r"""\1\2 """, text)
    showPage(text, "BODY AABB")
    text = SPURIOUS_PARA_RE.sub(r"""\1\2) """, text)
    showPage(text, "BODY BBBB")
    text = MARKED_NOTE_DBL_RE.sub(r"""\1\n\2""", text)
    showPage(text, "BODY CCCC")
    for (convertRe, convertRepl) in MARKED_UN_NOTE:
        text = convertRe.sub(convertRepl, text)
    showPage(text, "BODY DDDD")
    text = DEL_LB_RE.sub(r"""\1\n""", text)
    showPage(text, "BODY EEEE")
    for (trimRe, trimRepl) in MARKED_NOTE:
        text = trimRe.sub(trimRepl, text)
    showPage(text, "BODY FFFF")
    text = NOTE_RENAME_RE.sub(r"""<fnote\1>\2</fnote>""", text)
    showPage(text, "BODY GGGG")
    text = PARA_END_BEFORE_NOTES_RE.sub(r"\2\n\1", text)
    showPage(text, "BODY HHHH")
    for (trimRe, trimRepl) in NOTES_FILTER1:
        text = trimRe.sub(trimRepl, text)
    showPage(text, "BODY IIII")
    text = NOTE_COLLAPSE_RE.sub(collapseNotes, text)
    showPage(text, "BODY JJJJ")
    for (trimRe, trimRepl) in NOTES_FILTER2:
        text = trimRe.sub(trimRepl, text)
    showPage(text, "BODY KKKK")
    text = COMMENT_RE.sub(cleanTag, text)
    showPage(text, "BODY LLLL")
    nmatch = NOTES_ALL_RE.match(text)
    if nmatch:
        (text, notesStr, post) = nmatch.group(1, 2, 3)

        if post:
            print("\nMaterial after footnotes:")
            print(f"\tNOTES==={notesStr}")
            print(f"\tPOST ==={post}")
    else:
        notesStr = ""

    notes = []
    onlyNote = None
    firstNote = None

    bodies = {}
    page = info["page"]

    if notesStr:
        matches = tuple(NOTE_RE.finditer(notesStr))
        ref = NOTE_START
        for (i, match) in enumerate(matches):
            atts = match.group(1)
            body = match.group(2)
            mmatch = NOTE_ATT_REF_RE.search(atts)
            mark = mmatch.group(1) if mmatch else ""
            (summary, trimmed) = summarize(cleanText(body, "fnote", full=True))
            isFirst = True if i == 0 and not mmatch else False
            isLast = i == len(matches) - 1
            body = cleanText(body, "fnote")
            if isFirst:
                firstNote = (ref, body, summary)
                if isLast:
                    onlyNote = firstNote
                    firstNote = None
                    label = "1"
                else:
                    label = "F"
                thisFnoteBodyInfo.append((label, summary))
            else:
                ref += 1
                if page in SKIP_NOTE_BODY:
                    while ref in SKIP_NOTE_BODY[page]:
                        ref += 1
                notes.append((ref, body, summary))
                bodies[ref] = (mark, summary)

    current["notes"] = notes
    current["onlyNote"] = onlyNote
    current["firstNote"] = firstNote
    return (text, bodies)


SUPER_PRE_RE = re.compile(
    r"""
    ([.,:-])
    (</super>)
    """,
    re.S | re.X,
)
SUPER_RE = re.compile(
    r"""
        <super>
        ([0-9u]{1,2})
        \)\)
        </super>
    """,
    re.S | re.X,
)


def formatNoteMarks(text, info, bodies):
    noteBrackets = info["noteBrackets"]
    markDetectRe = MARK_PLAIN_BR_RE if noteBrackets else MARK_PLAIN_RE
    page = info["page"]
    skipMarks = SKIP_NOTE_MARK.get(page, set())

    showPage(text, "MARK AAAA")
    text = SUPER_PRE_RE.sub(r"\2\1", text)
    text = SUPER_RE.sub(r"⌊\1⌋)", text)
    text = CL_BR_ESCAPE_RE.sub(r"←\1→", text)
    text = FL_RE.sub(r"ƒ \1", text)
    for (sanRe, sanRepl) in MARK_SANITIZE:
        text = sanRe.sub(sanRepl, text)

    if not noteBrackets:
        for (escRe, escRepl) in CL_BR_NO:
            text = escRe.sub(escRepl, text)

    showPage(text, "MARK BBBB")
    matches = tuple(markDetectRe.finditer(text))
    replacements = []
    marks = {}
    ref = NOTE_START
    for (i, match) in enumerate(matches):
        if noteBrackets:
            (mark, trail) = match.group(1, 2)
            if trail is None:
                trail = ""
        else:
            mark = match.group(1)
            trail = ""
        if noteBrackets:
            mark = MARK_TRAIL_RE.sub(r"", mark)
            mark = (
                mark.replace("<super>", "")
                .replace("</super>", "")
                .replace(" )", "")
                .replace(")", "")
            )
        else:
            mark = mark.replace("<super>", "").replace("</super>", "")
        mark = mark.replace("⌊", "").replace("⌋", "")
        if mark in skipMarks:
            continue
        (b, e) = match.span()
        ref += 1
        pre = max(b - 20, 0)
        post = min(e + 20, len(text))
        summary = f"{text[pre:b]}⌈{mark}⌉{text[e:post]}".replace("\n", " ")
        marks[ref] = (mark, summary)
        replacement = f"""<fref ref="{ref}"/> {trail}"""
        replacements.append((b, e, replacement))
    for (b, e, r) in reversed(replacements):
        text = text[0:b] + r + text[e:]
    showPage(text, "MARK CCCC")
    text = CL_BR_RESTORE_RE.sub(r"(\1)", text)
    showPage(text, "MARK DDDD")
    return (text, marks)


MARK_TRAIL_RE = re.compile(r"""\)[^>]*</super>""")

MARK_SANITIZE = ((re.compile(r"""\*j\b""", re.S), r"*)"),)
CL_BR_ESCAPE_RE = re.compile(
    r"""
        \(
        (
            (?:
                <super>[^<]*</super>
                |
                (?:
                    [^)]
                    (?!
                        </?para>
                    )
                )
            )*
        )
        \)
    """,
    re.S | re.X,
)
CL_BR_RESTORE_RE = re.compile(r"""←([^→]*)→""", re.S)

CL_BR_NO = (
    (
        re.compile(
            r"""
                ([a-z”,]{3,})
                ([0-9]{1,2})
                \b
            """,
            re.S | re.X,
        ),
        r"\1⌊\2⌋",
    ),
    (
        re.compile(
            r"""
                <super>
                ([0-9]{1,2})
                </super>
            """,
            re.S | re.X,
        ),
        r"⌊\1⌋",
    ),
)

FL_RE = re.compile(r"""\bf([0-9]+)""", re.S)


MARK_PLAIN_AFTER_RE = re.compile(
    r"""
        <super>
        \s*
        (
            <fref[^>]*/>
            .*?
        )
        </super>
    """,
    re.S | re.X,
)
