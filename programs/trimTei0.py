processPage = None


ADD_PAGE = {
    "09:p0233-0236": """
<pb n="235" tpl="2" vol="09" facs="205_235"/>
eenige maanden voor zijn vaders dood verlaten, en dus ook tegelijk verijdelt was de<lb/>
hoope van dat geraffineerde en staatkundige hoff om op dese en diergelijke wij se eens<lb/>
een voet in het Bimase rijk te verkrijgen.<lb/>
</p>
<hi rend="font-size:10; font-family:Liberation Serif">Fol. 45v-46r.</hi><lb/>

<note place="inline" type="editorial-summary" resp="editor" rend="font-style: italic; line-height: 14.4pt; text-indent: 27.0pt; text-align: justify; font-size: 11">(De regenten van Saleyer hebben hun tribuut betaald. Expeditie met 3 pantjalangs en<lb/>
2 inlandse vaartuigen tegen Mandar en Sureang.<lb/>
</note>

<p rend="font-size: 10.5; font-variant: small-caps; text-align: justify; line-height: 14.4pt">Bandjarmasin<lb/>
</p>

<note place="inline" type="editorial-summary" resp="editor" rend="font-style: italic; line-height: 14.4pt; text-indent: 27.0pt; text-align: justify; font-size: 11">De Haften, Bergwerker en Onbeschaamdheid met 30.000 Spaanse realen afgezonden
voor de inkoop van peper op 1 april 1731. De Haften is naar Semarang verzeild. Op 22
juli is de Westfriesland eveneens naar Bandjarmasin gezonden met20.000 Mexicaanse realen
en goederen t. w. van ƒ 68.793.</note>

<p rend="font-size: 10.5; font-variant: small-caps; text-align: justify; line-height: 14.4pt">Timor<lb/>
</p>
<note place="inline" type="editorial-summary" resp="editor" rend="font-style: italic; line-height: 14.4pt; text-indent: 27.0pt; text-align: justify; font-size: 11">De koning van Kupang is overleden; de blanke en zwarte Portugezen hebben een<lb/>
wapenstilstand gesloten.<lb/>
</note>

<p rend="font-size: 10.5; font-variant: small-caps; text-align: justify; line-height: 14.4pt">Palembang<lb/>
</p>
<note place="inline" type="editorial-summary" resp="editor" rend="font-style: italic; line-height: 14.4pt; text-indent: 27.0pt; text-align: justify; font-size: 11">Nog geen nieuws over de expeditie van Oostwalt, hoewel opzettelijk enkele lichte<lb/>
bootjes waren meegegeven, terwijl Oostwalt slechts voor 3 maanden proviand heeft. De<lb/>
Windhond is op 19 juni met 60.000 Spaanse realen uitgezonden om peper af te halen en<lb/>
om nieuws van Oostwalt. De Windhond heeft een lading t.w.v. ƒ 239.937 voor Palembang<lb/>
en ƒ 19.171 voor Djambi; de Suikermaler ƒ 1050. Oostwalt had zich voor de post ook)<lb/>
</note>
<p resp="int_paragraph_joining">
kunnen bedienen van een meenigte Portugeese scheepen en joncken aldaar<lb/>
gepasseerd zijnde.<lb/>
</p>
<hi rend="font-size:10; font-family:Liberation Serif">Fol. 58r.</hi><lb/> .
<note place="inline" type="editorial-summary" resp="editor" rend="font-style: italic; line-height: 14.4pt; text-indent: 27.0pt; text-align: justify; font-size: 11">(Door het gebrek aan tin heeft men veel Chinese handelaren moeten teleurstellen, ook<lb/>
al omdat de Berbices uit Siam op zich liet wachten. Op 26 juni twee brieven van Oostwalt<lb/>
d.d. 12 mei en 18 mei. Deze zijn vermoedelijk geantedateerd. Op 18 juli is de Anna Maria<lb/>
naar Palembang gezonden met goederen ter waarde van ƒ 43.079. Oostwalt op 14 april te<lb/>
Palembang aangekomen. De eerste zending om Aru Apalla op te eisen heeft niets opgeleverd.<lb/>
Oostwalt is te Palembang gebleven i.p.v. zijn expeditie naar Bangka te vervolgen en heeft<lb/>
in zijn plaats de eerste resident Roos erop uit gezonden. Een tweede expeditie naar Tandjung<lb/>
Ular en Bangka om Aru Apalla gevangen te nemen is eveneens mislukt. De peperaanvoer<lb/>
naar Batavia stagneert. Er is vanwege de troebelen slechts 4172 pikol peper uit Palembang<lb/>
aangebracht, alleen met Chinese schepen; voorts nog 366.854 en 94.062 lb peper met resp.<lb/>
de Hogenes en een sloep.<lb/>
</note>

<p rend="font-size: 10.5; font-variant: small-caps; text-align: justify; line-height: 14.4pt">Djambi<lb/>
</p>
<note place="inline" type="editorial-summary" resp="editor" rend="font-style: italic; line-height: 14.4pt; text-indent: 27.0pt; text-align: justify; font-size: 11">Op 19 juni zijn 2000 Spaanse realen, 300 lb buskruit en andere goederen naar Djambi<lb/>
gestuurd ter waarde van ƒ 20.222.<lb/>
</note>

<p rend="font-size: 10.5; font-variant: small-caps; text-align: justify; line-height: 14.4pt">Siam<lb/>
</p>
<note place="inline" type="editorial-summary" resp="editor" rend="font-style: italic; line-height: 14.4pt; text-indent: 27.0pt; text-align: justify; font-size: 11">Op 13 juli de Berbices met tin, sapanhout, olifantstanden etc. t.w.v. ƒ 106.146 te<lb/>
Batavia aangekomen. Het zilver is door de koninklijke factoors geschat op 355 kati of<lb/>
ƒ 51.193, een nadeel voor de Compagnie van ƒ 28.291. De schuld van de koning is opgelopen<lb/>
tot ƒ 213.854. Op de schenkage is ƒ 4184 verloren. De phra-klang belooft een grotere<lb/>
leverantie van sapanhout in de toekomst. De Compagnie wijst de beschuldiging van de<lb/>
phra-klang over de gebrekkige zorg voor de koninklijke paarden af, de schuld voor het<lb/>
</note>
    """,
}


def trimPage(text, info, *args, **kwargs):
    text = text.replace(''' rend=""''', "")
    text = text.replace(''' rend=" "''', "")
    page = info["page"]

    return ADD_PAGE[page] if page in ADD_PAGE else text
