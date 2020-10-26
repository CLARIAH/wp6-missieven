import re
import collections

from distill import MONTH_DETECT_PAT
from lib import REPORT_DIR, WHITE_RE, applyCorrections, docSummary

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
        (
            r"""<super>4J</super> \.<lb/>\s*(</remark>)""",
            r"""<super>4)</super>\1""",
        ),
    ),
    "01:p0204-0224": (
        (
            r"""(<super>3\)</super>)""",
            r"""\1 <super>4)</super>""",
        ),
    ),
    "01:p0279-0279": ((r"""(baey )(\*)\)""", r"\1⌊\2⌋"),),
    "01:p0663-0683": ((r"""(Hensen)(1\))""", r"\1"),),
    "01:p0663-0719": ((r"""</note>\s*<note>(72 mijl)""", r"""\1"""),),
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
    "02:p0445-0466": (
        (r"""<note>(9392741 .*?)</note>\s*""", r"""</para><para>\1"""),
        (r"""<note>(Verminderinge .*?)</note>\s*""", r"""</para><para>\1"""),
        (r"""<note>(Wat quantiteyt .*?)</note>\s*""", r"""</para><para>\1"""),
    ),
    "02:p0480-0484": (
        (r"""<note>a\)""", r"""<note>1)"""),
        (r"""<note>I\)""", r"""<note>2)"""),
    ),
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
    "03:p0079-0081": ((r"""<note>ö<lb/>\s*</note>\s*""", r""),),
    "03:p0314-0340": ((r"""</note>\s*<note>(88° O\.L\.<lb/>\s*)""", r"\1"),),
    "03:p0581-0586": (
        (r"""<note>I\)""", r"""<note>1)"""),
        (r"""<note>!\)""", r"""<note>2)"""),
    ),
    "03:p0877-0880": ((r"""(<note>)1 1 \)""", r"\1<super>11</super>"),),
    "04:p0318-0332": ((r"""(<note>)\[4\) """, r"\1<super>4</super>"),),
    "04:p0429-0469": ((r"""(<note>)11""", r"\1<super>1</super>"),),
    "04:p0498-0586": ((r"""(<note>)J\)""", r"\1<super>1</super>"),),
    "04:p0498-0588": (
        (r"""(<note>)а\)""", r"\1<super>1</super>"),  # this a is unicode x430
        (r"""(<note>)1\)""", r"\1<super>2</super>"),
        (r"""(<note>)2\)""", r"\1<super>3</super>"),
        (r"""(<note>)3\)""", r"\1<super>4</super>"),
        (r"""(<note>)4\)""", r"\1<super>5</super>"),
        (r"""(<note>)б\)""", r"\1<super>6</super>"),
        (r"""(<note>)6\)""", r"\1<super>7</super>"),
        (r"""(<note>)7\)""", r"\1<super>8</super>"),
        (r"""(<note>)8\)""", r"\1<super>9</super>"),
        (r"""(<note>)9\)""", r"\1<super>10</super>"),
    ),
    "04:p0498-0589": (
        (r"""(<note>)a\)""", r"\1<super>1</super>"),
        (r"""(<note>)b\)""", r"\1<super>2</super>"),
        (r"""(<note>)1\)""", r"\1<super>3</super>"),
        (r"""(<note>)2\)""", r"\1<super>4</super>"),
        (r"""(<note>)3\)""", r"\1<super>5</super>"),
        (r"""(<note>)4\)""", r"\1<super>6</super>"),
        (r"""(<note>)5\)""", r"\1<super>7</super>"),
        (r"""(<note>)6\)""", r"\1<super>8</super>"),
        (r"""(<note>)7\)""", r"\1<super>9</super>"),
        (r"""(<note>)8\)""", r"\1<super>10</super>"),
        (r"""(<note>)9\)""", r"\1<super>11</super>"),
    ),
    "04:p0600-0638": ((r"""(<note>)11""", r"\1<super>1</super>"),),
    "05:p0099-0100": (
        (
            r"""\s*(</remark>)\s*<para>\s*<emph>(is)</emph>\s* (-) ;<lb/>\s*</para>""",
            r""" \2\3)\1""",
        ),
    ),
    "05:p0099-0115": ((r"ö\) (Isaak Clarisse)", r"</note>\n<note>5) \1"),),
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
    "05:p0296-0335": ((r"""</note>\s*<note>(9°20' N\.B\.<lb/>\s*)""", r"\1"),),
    "05:p0605-0609": (
        (r"""</remark>\s*<note>(kruidnagelen bewaard,.*?)</note>""", r"\1",),
        (r"""<note>(Tot Nova Guinea.*?)</note>""", r"</remark>\n<para>\1</para>",),
    ),
    "05:p0712-0712": ((r"""(<note>)\.1\) """, r"\1<super>1</super>"),),
    "06:p0477-0493": ((r"""</note>\s*<note>(22° N\.B\. stromende)""", r"\1"),),
    "06:p0601-0607": ((r"""</note>\s*<note>(25 april 1729.*?)""", r"\1"),),
    "07:p0226-0243": ((r"""<note>1\.<lb/>\s*</note>\s*""", r""),),
    "07:p0610-0639": ((r"""(<remark>)6 ml\.""", r"\1(vnl."),),
    "07:p0684-0689": ((r"""<note>0 """, r"<note>1) "),),
    "08:p0003-0004": ((r"""\b(1706)(6\))""", r"\1⌊\2⌋"),),
    "08:p0003-0005": ((r"""\b(70)(8\))""", r"\1⌊\2⌋"),),
    "09:p0365-0387": ((r"""(ƒ 7823)""", r"(\1"),),
    "09:p0548-0549": ((r"""(<note>)(Cajatizaad)""", r"\1<super>1</super> \2"),),
    "09:p0750-0758": (
        (r"""(<note>)(')( Tanna)""", r"\1<super>5</super>\2"),
        (r"""(<note>)(’)( Bohay)""", r"\1<super>6</super>\2"),
    ),
    "09:p0782-0801": ((r"""(<note>)(Zie)""", r"\1<super>2</super> \2"),),
    "10:p0001-0018": ((r"""(<note>)(Dit)""", r"\1<super>8</super> \2"),),
    "10:p0112-0115": ((r"""(<note>)(Betuyd)""", r"\1<super>4</super> \2"),),
    "10:p0112-0125": ((r"""(<note>)(In)""", r"\1<super>8</super> \2"),),
    "10:p0112-0131": ((r"""(<note>)(1 1)""", r"\1<super>11</super> \2"),),
    "10:p0175-0228": (
        (
            r"""(<remark>)<special>([^<]*)</special> \( """,
            r"<subhead>\2</subhead>\n\1( ",
        ),
    ),
    "10:p0175-0195": ((r"""(<note>)(Temeraire)""", r"\1<super>8</super> \2"),),
    "10:p0255-0279": ((r"""(<note>)(De)""", r"\1<super>8</super> \2"),),
    "10:p0297-0317": ((r"""(<note>)(Het)""", r"\1<super>8</super> \2"),),
    "10:p0297-0340": ((r"""(<note>)(Sortiados)""", r"\1<super>11</super> \2"),),
    "10:p0399-0400": ((r"""(<note>)(Calange)""", r"\1<super>1</super> \2"),),
    "10:p0399-0408": (
        (
            r"""<note><super>8</super>.*</note>""",
            r"""
<note><super>8</super> De optelling levert een andere dan de aangegeven uitkomst op
op (ƒ 14.909,11<lb/>
</note>
<note><super>9</super> De optelling levert een andere dan de aangegeven uitkomst op
op (ƒ 1.774.698,12,9)<lb/>
</note>
<note><super>10</super> De optelling levert een andere dan de aangegeven uitkomst op
op (ƒ280.802,1,-).<lb/>
</note>
<note><super>11</super> De optelling levert een andere dan de aangegeven uitkomst op
op (ƒ2.126.374,6,2).<lb/>
</note>
<note><super>12</super> De optelling levert een andere dan de aangegeven uitkomst op
op (ƒ 563.828,4,8).<lb/>
</note>
<note><super>13</super> De optelling levert een andere dan de aangegeven uitkomst op
op  (ƒ 256.668,12,7).<lb/>
</note>
<note><super>14</super> De optelling levert een andere dan de aangegeven uitkomst op
op (ƒ 102.704,6,-).<lb/>
</note>
<note><super>15</super> De optelling levert een andere dan de aangegeven uitkomst op
op (ƒ 200.449,5,8).<lb/>
</note>
            """,
        ),
    ),
    "10:p0399-0409": (
        (
            r"""<note><super>16</super>.*</note>""",
            r"""
<note><super>16</super> De optelling levert een andere dan de aangegeven uitkomst op
(ƒ 1.821.01 1,16,6).
</note>
<note><super>17</super> De optelling levert een andere dan de aangegeven uitkomst op
(ƒ 293.608,17,-).
</note>
<note><super>18</super> De optelling levert een andere dan de aangegeven uitkomst op
(ƒ 1.892.381,17,2 1/5).
</note>
<note><super>19</super> De optelling levert een andere dan de aangegeven uitkomst op
(ƒ 1.764.628,16,8).
</note>
<note><super>20</super> De optelling levert een andere dan de aangegeven uitkomst op
(ƒ 127.000,18,8).
</note>
            """,
        ),
    ),
    "10:p0413-0418": ((r"""(<note>)(Slinken)""", r"\1<super>1</super> \2"),),
    "10:p0413-0430": ((r"""(<note>)<super>2</super>""", r"\1<super>12</super>"),),
    "10:p0461-0462": ((r"""(<note>)(Peuril)""", r"\1<super>1</super> \2"),),
    "10:p0496-0504": ((r"""(<note>)(Hier)""", r"\1<super>1</super> \2"),),
    "10:p0496-0518": (
        (
            r"""(<remark>)<special>([^<]*)</special> \( """,
            r"<subhead>\2</subhead>\n\1( ",
        ),
    ),
    "10:p0496-0531": ((r"""(<note>)(Phaeton)""", r"\1<super>8</super> \2"),),
    "10:p0598-0625": ((r"""(<note>)(Recusatie)""", r"\1<super>8</super> \2"),),
    "10:p0633-0641": ((r"""(<note>)(Fachinen)""", r"\1<super>1</super> \2"),),
    "10:p0633-0700": (
        (
            r"""(<remark>)<special>\((Bandar[^<]*)</special> """,
            r"<subhead>\2</subhead>\n\1( ",
        ),
    ),
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
    "10:p0857-0858": ((r"""(<note>)(14 december)""", r"\1<super>1</super> \2"),),
    "11:p0027-0087": (
        (r"""(<note>)(<super>1 1</super>)""", r"\1<super>11</super> \2"),
    ),
    "11:p0207-0209": ((r"""(traffique )\\(<lb/>)""", r"\1)\2"),),
    "11:p0226-0270": ((r"""<super>1</super>( overstromingen)""", r"'\1"),),
    "11:p0226-0307": ((r"""(<note>)(<super>1</super>)""", r"\1<super>11</super> \2"),),
    "11:p0226-0325": (
        (r"""(<note>)(<super>2 1</super>)""", r"\1<super>21</super> \2"),
    ),
    "11:p0363-0409": (
        (
            r"""(<remark>)<special>(Hooghly)</special>""",
            r"<subhead>\2</subhead>\n\1",
        ),
    ),
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
    "11:p0641-0670": (
        (
            r"""(<remark>)(Kasimbazar)\n<emph>([^<]*)</emph>""",
            r"<subhead>\2</subhead>\n\1\3",
        ),
    ),
    "11:p0769-0833": (
        (r"""(<note>)(<super>1 1</super>)""", r"\1<super>11</super> \2"),
    ),
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
    "12:p0003-0068": ((r"""(<note>)(Het bedrag)""", r"\1<super>14</super> \2"),),
    "12:p0003-0071": ((r"""15<lb/>\s*<note>""", r"<note><super>15</super> "),),
    "12:p0181-0181": (
        (r"""<note>ï<lb/>\s*</note>\s*<note>""", r"<note><super>1</super> "),
        (r"""</note>\s*<note>(1752\.<lb/>)""", r"\1"),
    ),
    "12:p0198-0203": ((r"""(<note>)(Er is hier sprake)""", r"\1<super>1</super> \2"),),
    "12:p0293-0309": ((r"""(<note>)(In de marge)""", r"\1<super>1</super> \2"),),
    "12:p0293-0373": ((r"""</note>\s*<note>(9 mei)""", r"\1"),),
    "12:p0403-0480": (
        (r"""<para>6<lb/>\s*</para>\s*<note>""", r"<note><super>6</super> "),
    ),
    "12:p0500-0500": (
        (r"""<note>i<lb/>\s*</note>\s*<note>""", r"<note><super>1</super> "),
    ),
    "12:p0501-0504": (
        (r"""</para>\s*<note>(<und>zijn,</und>)""", r"\1"),
        (r"""</note>\s*<note>(Den Soerats)""", r"</para>\n<para>\1"),
        (r"""</note>\s*$""", "</para>\n"),
    ),
    "12:p0510-0603": ((r"""(<note>)(De rijksdaalder)""", r"\1<super>8</super> \2"),),
    "13:p0008-0011": (
        (r"""<note>(Zullende.*?)</note>""", r"<para>\1</para>"),
        (r"""<note>(De.*?)</note>""", r"<para>\1</para>"),
    ),
    "13:p0014-0039": ((r"""<note>(Voorts.*)</note>""", r"</para><para>\1"),),
    "13:p0014-0059": ((r"""(<note>)(Platkoper)""", r"\1<super>8</super> \2"),),
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
    "13:p0231-0274": ((r"""(<note>)(Firtij)""", r"\1<super>8</super> \2"),),
    "13:p0362-0453": ((r"""(<note>)(Hoe dit)""", r"\1<super>8</super> \2"),),
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
    "13:p0501-0536": ((r"""(<note>)(Juister)""", r"\1<super>7</super> \2"),),
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
    "13:p0501-0549": ((r"""(<note>)(Dit lijkt)""", r"\1<super>8</super> \2"),),
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
<para>ƒ 4.814, 9,-9<lb/>
</para>
<note><super>9</super> Juister is ƒ 4.815,9,-<lb/>
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
    "13:p0501-0578": ((r"""(<note>)(Het totaal)""", r"\1<super>11</super> \2"),),
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
CORRECTIONS = {
    page: tuple((re.compile(spec[0], re.S), spec[1]) for spec in specs)
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
OVERRIDE_NOTE_TEXT = {}
OVERRIDE_NOTE_BODY = {
    "01:p0204-0224": {4: "3"},
    "01:p0482-0483": {6: "5"},
    "01:p0553-0553": {2: "1"},
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
    "04:p0038-0038": {5: "6"},
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
    "04:p0651-0668": {2: "1"},
    "04:p0680-0693": {5: "6"},
    "04:p0680-0703": {3: "4"},
    "04:p0707-0709": {5: "6"},
    "05:p0605-0618": {5: "6"},
    "06:p0051-0060": {5: "6"},
    "06:p0066-0072": {5: "6"},
    "06:p0236-0250": {5: "6"},
    "06:p0275-0278": {5: "6"},
    "06:p0383-0386": {5: "6"},
    "06:p0415-0442": {5: "6"},
    "06:p0477-0493": {5: "6"},
    "06:p0477-0497": {5: "6"},
    "06:p0514-0519": {5: "6"},
    "06:p0587-0588": {5: "6"},
    "06:p0641-0652": {5: "6"},
    "06:p0750-0787": {5: "6"},
    "06:p0750-0806": {5: "6"},
    "06:p0810-0820": {5: "6"},
    "06:p0810-0830": {5: "6"},
    "06:p0844-0860": {5: "6"},
    "07:p0610-0619": {1: "2"},
    "07:p0684-0690": {2: "3", 3: "4"},
    "07:p0710-0713": {2: "1"},
    "07:p0710-0733": {2: "1", 3: "2"},
    "09:p0344-0355": {2: "1"},
}
SKIP_NOTE_BODY = {
    "08:p0128-0133": {11},
}
REMARK_SPURIOUS_RE = re.compile(r"""<remark>(y[y ]*)</remark>""", re.S)
REMARK_END_CORR_RE = re.compile(r"""\)\s*\.\s*([*\]^])\s*(</remark>)""", re.S)

COMMENT_RE = re.compile(r"""<(fnote|remark)\b([^>]*)>(.*?)</\1>""", re.S)
REMARK_START_RE = re.compile(
    r"""
        ^
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


def processPage(text, previous, result, info, *args, **kwargs):
    global NOTE_START
    remarkInfo = info["remarkInfo"]
    fnotebInfo = info["fnotebInfo"]
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
            fnotebInfo[page].insert(0, ("≮", curSummary))
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

    fnotebInfo = info["fnotebInfo"]

    thisFnotebInfo = []
    (text, bodies) = formatNoteBodies(text, info, current, thisFnotebInfo)
    # (text, marks) = formatNoteMarks(text, info, bodies)
    if len(bodies) != 0:
        NOTE_START = max(bodies)

    if bodies:
        for (ref, (markBody, summary)) in bodies.items():
            thisFnotebInfo.append((ref, markBody, summary))
        fnotebInfo[page].extend(thisFnotebInfo)
    else:
        label = "0"
        thisFnotebInfo.append((label, ""))
        for x in reversed(thisFnotebInfo):
            fnotebInfo[page].insert(0, x)

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
    "!": (0, "missing mark in body or text bot not both"),
    "≠": (0, "mark in conflict with sequence number"),
    "↓": (0, "no mark in text"),
    "°": (0, "indefinite mark in body and text"),
    "+": (20, "mark is one more than sequence number"),
    "-": (20, "mark is one less than sequence number"),
    "→": (40, "no mark in body"),
    "∉": (40, "sequence number not contained in mark"),
    "∈": (80, "sequence number contained in mark"),
    "*": (50, "mark is * or x, will be filled in by sequence number"),
    "<": (50, "indefinite mark in body only"),
    ">": (80, "indefinite mark in text only"),
    ":": (100, "mark overridden to be good"),
    "∷": (100, "mark exactly equal to sequence number"),
    "≡": (100, "mark text and body exactly equal"),
    "=": (100, "mark text and body exactly equal after overriding"),
    "x": (100, "mark text and body clearly unequal"),
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

    fnotebInfo = info["fnotebInfo"]

    totalNotes = 0
    totalPages = len(fnotebInfo)
    totalScore = 0
    scores = collections.defaultdict(list)

    noteLog = collections.defaultdict(dict)

    for page in sorted(fnotebInfo):
        report = []
        overrideMarkBody = OVERRIDE_NOTE_BODY.get(page, {})
        entries = fnotebInfo[page]

        score = 0
        nNotes = 0

        for entry in entries:
            if len(entry) == 2:
                (label, summary) = entry
                report.append(f"\t{label} «{summary or ''}»\n")
                continue

            nNotes += 1
            (ref, markBodyOrig, summary) = entry
            markBody = normalize(markBodyOrig)

            bodyParts = tuple(n for n in markBody.split())
            bodyNums = {int(n) for n in bodyParts if n.isdigit()}
            polyBodyNums = len(bodyParts) > 1

            labelBody = (
                "→"
                if not markBody
                else "∷"
                if str(ref) == markBody
                else ":"
                if overrideMarkBody.get(ref, None) == markBody
                else "≃"
                if ref in bodyNums
                else "∉"
                if polyBodyNums and ref not in bodyNums
                else "*"
                if markBody == "*" or markBody == "x"
                else "-"
                if str(ref - 1) == markBody
                else "+"
                if str(ref + 1) == markBody
                else "≠"
            )
            thisScore = LEGEND_SCORE[labelBody]
            score += thisScore
            markBodyRep = f"⌈{markBody}⌉"
            report.append(f" {ref:>2} {markBodyRep:<4} «{summary}»\n")

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
        f"NOTES: {totalNotes} notes on {totalPages} pages"
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
        text = text.replace("<und>", "_")
        text = text.replace("</und>", "_")
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
        text = REMARK_START_RE.sub(r"«", text)
        text = REMARK_END_RE.sub(r"\1»", text)
    text = REF_RE.sub(refRepl, text)

    if full:
        if "<" in text:
            print(f"\nunclean {tag}")
            print(f"\t==={text}===")
    return text


def normalize(text):
    if text == "il":
        return "1"
    elif text == "[il":
        return "1"
    elif text == "<ref>il</ref>":
        return "1"
    if text == "ï":
        return "1"
    if text == "ö":
        return "5"
    if text == "]":
        return "1"
    if text == "K":
        return "8"
    if text == "b":
        return "6"
    if text == "y":
        return "9"
    if text == "n":
        return "11"
    elif text == "<emph>2</emph> Q":
        return "20"
    return (
        text.replace("i", "1")
        .replace("'", "1")
        .replace("l", "1")
        .replace("L", "1")
        .replace("y", "9")
        .replace("z", "3")
        .replace("n", "11")
    )


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
"""
MARKED_NOTE = (
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


def showPage(text, label):
    (tb, te) = (-1200, -600)
    show = False and 'n="145"' in text
    if show:
        print(
            f"=== [ {label} ] ========================================================"
        )
        print(text[tb:te])


def formatNoteBodies(text, info, current, thisFnotebInfo):
    showPage(text, "AAAA")
    text = SPURIOUS_PARA_RE.sub(r"""\1\2) """, text)
    showPage(text, "BBBB")
    text = MARKED_NOTE_DBL_RE.sub(r"""\1\n\2""", text)
    showPage(text, "CCCC")
    for (convertRe, convertRepl) in MARKED_UN_NOTE:
        text = convertRe.sub(convertRepl, text)
    showPage(text, "DDDD")
    text = DEL_LB_RE.sub(r"""\1\n""", text)
    showPage(text, "EEEE")
    for (trimRe, trimRepl) in MARKED_NOTE:
        text = trimRe.sub(trimRepl, text)
    showPage(text, "FFFF")
    text = NOTE_RENAME_RE.sub(r"""<fnote\1>\2</fnote>""", text)
    showPage(text, "GGGG")
    text = PARA_END_BEFORE_NOTES_RE.sub(r"\2\n\1", text)
    showPage(text, "HHHH")
    for (trimRe, trimRepl) in NOTES_FILTER1:
        text = trimRe.sub(trimRepl, text)
    showPage(text, "IIII")
    text = NOTE_COLLAPSE_RE.sub(collapseNotes, text)
    showPage(text, "JJJJ")
    for (trimRe, trimRepl) in NOTES_FILTER2:
        text = trimRe.sub(trimRepl, text)
    showPage(text, "KKKK")
    text = COMMENT_RE.sub(cleanTag, text)
    showPage(text, "LLLL")
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
            markBody = mmatch.group(1) if mmatch else ""
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
                thisFnotebInfo.append((label, summary))
            else:
                ref += 1
                if page in SKIP_NOTE_BODY:
                    while ref in SKIP_NOTE_BODY[page]:
                        ref += 1
                notes.append((ref, body, summary))
                bodies[ref] = (markBody, summary)

    current["notes"] = notes
    current["onlyNote"] = onlyNote
    current["firstNote"] = firstNote
    return (text, bodies)


def formatNoteMarks(text, info, bodies):
    noteBrackets = info["noteBrackets"]
    markDetectRe = MARK_PLAIN_BR_RE if noteBrackets else MARK_PLAIN_RE

    text = CL_BR_ESCAPE_RE.sub(r"←\1→", text)
    text = FL_RE.sub(r"ƒ \1", text)

    if not noteBrackets:
        for (escRe, escRepl) in CL_BR_NO:
            text = escRe.sub(escRepl, text)

    matches = tuple(markDetectRe.finditer(text))
    replacements = []
    marks = {}
    ref = NOTE_START
    for (i, match) in enumerate(matches):
        complete = match.group(0)
        if noteBrackets:
            (mark, trail) = match.group(1, 2)
        else:
            mark = match.group(1)
            trail = ""
        if noteBrackets:
            if "<super>" in complete:
                trail = trail.replace("</super>", "")
            else:
                mark = (
                    mark.replace("<super>", "")
                    .replace("</super>", "")
                    .replace("⌊", "")
                    .replace("⌋", "")
                )
        (b, e) = match.span()
        ref += 1
        marks[ref] = mark
        replacement = f"""<fref ref="{ref}"/> {trail}"""
        replacements.append((b, e, replacement))
    for (b, e, r) in reversed(replacements):
        text = text[0:b] + r + text[e:]
    text = CL_BR_RESTORE_RE.sub(r"(\1)", text)
    return (text, marks)


MARK_LETTERS_TEXT_BR = "xyziLlbn"
MARK_LETTERS_TEXT = "i"
MARK_SIGNS_TEXT = "*'"

MARK_PLAIN_BR_RE = re.compile(
    fr"""
        (?:
            ⌊
            |
            <super>
        )?
        (
            (?:
                (?:
                    \b
                    [{MARK_LETTERS_TEXT_BR}]
                )
                |
                [*'0-9]
            )
            [{MARK_LETTERS_TEXT_BR}{MARK_SIGNS_TEXT}0-9]?
            (?:
                \s+
                [{MARK_LETTERS_TEXT_BR}{MARK_SIGNS_TEXT}0-9]{{1,2}}
            )*
        )
        (?:</super>\ ?)?
        (?:
            \)
            |
            ⌋
        )
        (
            (?:
                [^<]*
                </super>
            )?
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
    r"""
        (
            (?:
               <super>
               [0-9]{1,2}
               </super>
            )
            |
            (?:
               ⌊
               [0-9]{1,2}
               ⌋
            )
            |
            (?:
                (?<=[a-z])
                [0-9]{1,2}
                \b
            )
        )
    """,
    re.S | re.X,
)

CL_BR_ESCAPE_RE = re.compile(
    r"""
        \(
        (
            [^)]*
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


def summarize(text, limit=20):
    lText = len(text)
    if lText <= limit:
        start = text
        inter = ""
        end = ""
    elif lText <= 2 * limit:
        start = text[0:limit]
        inter = ""
        end = text[limit:]
    else:
        start = text[0:limit]
        inter = " ... "
        end = text[-limit:]

    summary = f"{start:<{limit}}{inter:<5}{end:>{limit}}"
    trimmed = f"{start}{inter}{end}"

    return (summary, trimmed)
