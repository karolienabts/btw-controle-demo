# Spec-prompt — FactuurTool (Project 1)

> **Toelichting bij deze demo**
> - Dit is de spec waarmee de volledige FactuurTool gebouwd werd, ongewijzigd overgenomen.
>   Het BTW-deel dat deze demo toont: **sectie 4, punt 5** (B2B en VIES) en **sectie 7, vragen 2, 4 en 7**.
> - De spec eindigt niet met de letterlijke slotzin uit de opdracht. Dezelfde rol speelt
>   **sectie 7 "Open vragen: eerst beantwoorden, dan bouwen"**. De antwoorden staan in
>   `beslissingslogboek.md`.
> - Afwijking van de spec: de echte tool werd een Windows-programma, geen Streamlit-app
>   (zie het logboek). Deze Streamlit-demo bestaat voor de publieke URL, op verzonnen data.

---

# Projectplan — Automatisatie inkomstfacturen Plug&Pay

> Startdocument voor een nieuwe Claude Code-sessie. Lees dit eerst helemaal, en daarna de
> bronbestanden die hieronder genoemd worden. Bouw pas als de open vragen (sectie 7)
> beantwoord zijn.

## 1. Context

- **Wie**: cursist Data Scientist (Syntra), niveau beginner. Ze werkt op Windows met Anaconda,
  VS Code en Claude Code. Uitleg in het Nederlands (Vlaams), met veel uitleg per stap.
- **Doel**: de maandelijkse manuele verwerking van de verkoopfacturen uit Plug&Pay
  automatiseren: van de export naar een Excel met tabbladen, PDF-totaalfacturen, een B2B-map
  en een controlerapport. De resultaten gaan daarna naar Billit.
- **Tweede doel**: dit project wordt ingediend als **Project 1** van de opleiding (eigen-data-spoor).
  Het moet dus voldoen aan de opdrachteisen in sectie 6.

## 2. Bronbestanden in deze map

| Bestand | Wat het is |
|---|---|
| `Verwerking inkomstfacturen plug&pay.txt` | De huidige manuele werkwijze, stap voor stap (de echte spec) |
| `business_case_automatisatie_p&p.md` | De business case: doel, B2B/B2C-regels, gewenste output, controles |
| `Project 1 - demo-case verkeersveiligheid.pdf` | De opdracht van de opleiding: eisen en evaluatiecriteria |
| `ee0a649fc78125bf88e7dc8ae9137c9e.xlsx` | Ruwe Plug&Pay-export van oktober 2026 (**echte klantdata**) |
| `facturen_PP_oktober_26.xlsx` | Het manueel gemaakte resultaat (doelformaat, alle tabbladen) |
| `oktober_26_plug&pay_totaalfactuur_21.pdf` / `_6.pdf` | Voorbeeld van de PDF-output |
| `PP_invoice_cleanup.osts` | Het bestaande Office Script dat de kolommen opkuist |
| `files_verplaatsen.ipynb` | Een eerste experiment met `shutil.move` om bestanden te verplaatsen |

Het voorbeeld-Excel `facturen_PP_oktober_26.xlsx` kon in de eerste sessie niet gelezen worden
(`PermissionError`: het bestand stond waarschijnlijk open in Excel). Lees de tabbladen en de opmaak
eerst uit en vergelijk ze met deze spec.

## 3. Wat er in de export staat (oktober 2026, nagekeken met pandas)

- 1 tabblad `Worksheet`: 658 lijnen, 55 kolommen, 646 unieke `invoice_number`. Het formaat is
  altijd `PP` + 9 cijfers.
- `invoice_date`: van 2026-10-01 tot en met 2026-10-31.
- `vat_rate` is tekst: `BE 21%` (584), `BE 6%` (26), `BE 0%` (1), **leeg (47)**.
  - Van die 47: 45 uit NL **met** `vat_id` (wellicht verlegde BTW, dus B2B) en 2 uit ES
    **zonder** `vat_id`. Bij alle 47 is `vat` = 0.
- `vat_id` is ingevuld bij 155 lijnen. Bij 44 lijnen is `company` ingevuld zonder `vat_id`: daar
  kan een BTW-nummer in `company` staan.
- 27 lijnen hebben een negatief `amount` (creditnota's of terugbetalingen).
- 24 lijnen delen hun `invoice_number` met een andere lijn (facturen met meerdere lijnen).
- 163 lijnen hebben "Boek" of "Masterclass" in `product`.
- Kolommen die de kuisstap behoudt (zie de txt): order_id, product, quantity, sku, country_code,
  company, firstname, lastname, invoice_number, invoice_date, amount, amount_with_tax, vat,
  vat_id, vat_rate.

**Formaat van de input**: neem de **Excel-export**, niet CSV. pandas leest beide even makkelijk,
maar in Excel blijven datums en bedragen getallen. Met CSV krijg je problemen met
scheidingstekens, decimale komma's en tekencodering.

## 4. Gewenste verwerking (spec)

1. **Inlezen** van de export (.xlsx).
2. **Kuisen**: enkel de kolommen uit sectie 3 behouden, punten (en spaties) uit `vat_id`
   verwijderen en sorteren op `vat_id` (A→Z).
3. **Totaal excl. BTW** over alles. Dat totaal wordt manueel vergeleken met het Plug&Pay-dashboard.
4. **Tabblad `boek`**: alle lijnen met product "Boek Stap uit de ratrace" én de lijnen
   "Masterclass investeren : The Final Chapter" met `amount_with_tax` = €25 of −€25. Dat is enkel
   voor een manuele controle of alle boeken verzonden (of geannuleerd) werden.
5. **Tabblad `B2B`**: alle lijnen met een BTW-nummer in `vat_id` **of** in `company`.
   - Controleer elk BTW-nummer in **VIES**. De EU heeft daarvoor een officiële REST-API: kijk het
     endpoint na in de officiële documentatie vóór je het gebruikt. Rapporteer ongeldige nummers.
     De mens beslist of zo'n factuur B2B blijft of naar B2C gaat.
   - Lijnen met een BTW-nummer in `company`: zet het `invoice_number` in het rapport, zodat
     de klantgegevens voor de toekomst aangepast kunnen worden.
   - Maak een lijst van de unieke `invoice_number` en verplaats (of kopieer) daarmee de B2B-PDF's
     naar een aparte map, klaar voor upload in Billit.
6. **Tabblad `totaalfactuur_plug&pay_21%`**: B2C (geen BTW-nummer) met 21% **en** 0%.
   - Rapporteer de 0%-lijnen met hun `invoice_number`. Die worden de volgende maand rechtgezet.
   - Maak een totaal van `amount`, geel gemarkeerd, en een PDF zoals in het voorbeeld.
7. **Tabblad `totaalfactuur_plug&pay_6%`**: B2C met 6%, met een geel totaal en een PDF.
8. **Controlerapport**: aantallen per groep, ongeldige BTW-nummers, BTW-nummers in `company`,
   0%-lijnen, lijnen zonder tarief, dubbele factuurnummers en ontbrekende PDF's.
9. **Opmaak in Excel**: kolommen op breedte, bedragen als euro (`€ #,##0.00`), een autofilter op
   rij 1 (dat doet het Office Script nu ook).

## 5. Gekozen aanpak (voorstel)

- **Één Streamlit-app** die de cursist **lokaal** draait voor de echte maandverwerking, plus een
  **publiek gedeployde versie op verzonnen (synthetische) demodata** voor de opdracht.
  Een Windows-.exe is een eventuele latere stap en valt buiten de scope van Project 1.
- **Projectstructuur**, volgens de opdracht:
  ```
  automatisatie_facturen/
  ├─ pipeline.py              pure functies, één per stap, geen Streamlit-imports
  ├─ app.py                   Streamlit: elke stap in een st.expander + rijen-trechter bovenaan
  ├─ export.py                Excel-opmaak (openpyxl) en PDF-generatie
  ├─ vies.py                  BTW-controle (met cache, en een time-out die netjes afgehandeld wordt)
  ├─ tests/test_pipeline.py   pytest op de beslisregels
  ├─ data/demo_export.xlsx    synthetische export (zelfde kolommen en randgevallen)
  ├─ CLAUDE.md                projectafspraken (B2B-regel, 0%-regel, privacy)
  ├─ beslissingslogboek.md
  ├─ requirements.txt         enkel wat de app nodig heeft
  └─ .gitignore               echte exports, PDF's en output NIET in git
  ```
- **Elke stap inspecteerbaar**: hoeveel rijen erin en eruit gaan, waarom rijen naar een andere
  groep gaan, en een voorbeeld na elke stap. Een rijen-trechter toont: export → B2B / boek /
  B2C 21% / B2C 6% / na te kijken. De som van de groepen moet kloppen met het totaal (dat is een test).
- **Korte lus**: twijfelgevallen (ongeldig BTW-nummer, geen tarief, 0%) worden **niet** stil
  ingedeeld, maar getoond in een lijst "na te kijken" waarin de gebruiker zelf beslist.
- **PDF's verplaatsen**: lokaal kies je een bronmap en een doelmap. Kopieer liever dan te
  verplaatsen, en verplaats pas na een bevestiging. In de online demo upload je een ZIP en
  download je de B2B-ZIP.

## 6. Eisen van de opdracht (Project 1) en hoe het project eraan voldoet

| Eis | Invulling |
|---|---|
| Ontwerp eerst (papier of digitaal) | Schets van de pijplijn en de schermen; bewaar een foto in de repo |
| Spec-prompt die eindigt met "Stel ons eerst een vraag op elke plek waar je zelf een aanname zou maken…" | Dit document dient als basis |
| `pipeline.py` + `app.py` met expanders en een rijen-trechter | Zie sectie 5 |
| `CLAUDE.md` met eigen afspraken | B2B-regel, 0%-regel, randgevallen, "geen echte data in git" |
| Git: commits, push naar GitHub, minstens één branch die terug gemerged wordt | bv. een branch `vies-controle` |
| pytest + zelf een test toevoegen voor "wat test dit niet?" | bv. een creditnota, een BTW-nummer met punten, het randgeval ES zonder tarief |
| Publieke Streamlit-URL (geen localhost) | Deploy met **enkel de demodata** |
| Beslissingslogboek, concreet | Elke regel uit sectie 4/7: wat besloten en waarom |
| No-AI gesprek: elk getal in de app kunnen aanwijzen | Elk totaal toont van welke stap en welke rijen het komt |

## 7. Open vragen: eerst beantwoorden, dan bouwen

1. **Factuur-PDF's**: waar staan ze (lokale map? ZIP uit Plug&Pay?) en hoe heten ze? Is de
   bestandsnaam gelijk aan `invoice_number`?
2. **Lijnen zonder `vat_rate`**: gaan de NL-lijnen met BTW-nummer (verlegde BTW) gewoon naar B2B?
   En waar horen de 2 ES-lijnen zonder BTW-nummer thuis?
3. **Creditnota's** (negatieve bedragen): blijven die gewoon in hun groep en tellen ze negatief mee?
4. **BTW-nummer in `company`**: hoe herken je dat? (Bv. een landcode + cijfers, zoals `BE0123456789`.)
   Behandel je zo'n lijn als B2B?
5. **Boek-tabblad**: een exacte productnaam of een "bevat"-zoekterm? Blijven die lijnen ook in
   hun B2B/B2C-groep staan? (Wellicht wel: het is enkel een controlelijst.)
6. **Totalen**: welk bedrag op de totaalfactuur, `amount` (excl. BTW) of `amount_with_tax`?
   Vergelijk met de voorbeeld-PDF's.
7. **VIES**: wat als de dienst niet bereikbaar is? Voorstel: markeren als "niet gecontroleerd" en niet blokkeren.
8. **Python-environment**: de actieve environment heet `syntra-DS`, de cursus-environment heet
   `syntra-ds`. Kies er één en installeer niets zonder te vragen.

## 8. Privacy: harde regels

- De echte exports en PDF's bevatten namen, e-mails, adressen en telefoonnummers. Ze komen
  **nooit** in git en **nooit** in de publieke app. Zet `*.xlsx`, `*.pdf` en `output/` in
  `.gitignore`, met een uitzondering voor `data/demo_export.xlsx`.
- De demodata wordt verzonnen (met de kolomstructuur en de randgevallen van sectie 3), niet
  "geanonimiseerd" uit de echte data.
- Geen API-sleutels in de code. Als die er ooit komen (bv. voor Billit): in een `.env` die in `.gitignore` staat.

## 9. Volgorde van werken

1. Open vragen (sectie 7) beantwoorden en noteren in `beslissingslogboek.md`.
2. Ontwerp schetsen. Daarna `git init` (of een nieuwe repo) en een eerste commit.
3. De synthetische `demo_export.xlsx` maken.
4. `pipeline.py` stap voor stap, met een test per beslisregel.
5. `app.py` met expanders en een rijen-trechter.
6. De Excel-export met opmaak, daarna de PDF-export (vergelijken met de voorbeeld-PDF's).
7. VIES-controle op een aparte branch, en die terug mergen.
8. Lokaal testen met de echte oktober-export. De totalen moeten kloppen met het manuele
   `facturen_PP_oktober_26.xlsx`.
9. Deploy op Streamlit Community Cloud met de demodata.
10. Later (optioneel): een snelkoppeling of `.bat` om de app lokaal te starten, eventueel een .exe.

## Verificatie

- De som van alle groepen is gelijk aan het aantal lijnen in de export. Elke uitsluiting is
  zichtbaar in de trechter.
- De totalen van 21% en 6% op de echte oktober-export zijn gelijk aan die in
  `facturen_PP_oktober_26.xlsx` en de voorbeeld-PDF's.
- `pytest` slaagt. De publieke URL werkt en toont enkel demodata.
