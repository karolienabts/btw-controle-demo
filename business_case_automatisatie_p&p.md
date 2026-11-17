# Business Case: Automatisering verkoopfacturen voor Billit

## Doelstelling

Het huidige proces voor het verwerken van verkoopfacturen richting Billit bevat verschillende manuele stappen:

- Exporteren van verkoopfacturen naar Excel.
- Filteren van B2B-facturen.
- Controleren van BTW nummer in KBO of VIES
- Verzamelen van de juiste PDF-facturen voor upload in Billit.
- Opstellen van totaalfacturen voor particuliere klanten (B2C).
- Omzetten van deze overzichten naar PDF.
- Toevoegen van de PDF's als bijlage in Billit.

Het doel van dit project is om deze stappen grotendeels te automatiseren via een Windows-applicatie ontwikkeld in Python.

---

# Huidige werkwijze

Er wordt een excel bestand getrokken kan x

## B2B-facturen

Een verkoopfactuur wordt beschouwd als B2B wanneer een BTW-nummer aanwezig is.

Huidige stappen:

1. Export van verkoopfacturen naar Excel.
2. Filteren op facturen met BTW-nummer
3. BTW nummer controleren
3. Zoeken van de bijhorende PDF-facturen.
4. Verplaatsen of verzamelen van deze PDF's.
5. Upload naar Billit.

## B2C-facturen

Een verkoopfactuur wordt beschouwd als B2C wanneer geen BTW-nummer aanwezig is.

Huidige stappen:

1. Filteren van facturen zonder BTW-nummer.
2. Overnemen naar een apart tabblad.
3. Verwijderen van niet-relevante kolommen.
4. Berekenen van totalen.
5. Opmaak van overzichtsdocumenten.
6. Exporteren naar PDF.
7. Toevoegen als bijlage aan een totaalfactuur in Billit.

Er worden momenteel twee totaalfacturen gemaakt:

### Totaalfactuur 6%

Alle particuliere facturen met 6% BTW.

### Totaalfactuur 21%

Alle particuliere facturen met 21% BTW.

Facturen met 0% BTW komen uitzonderlijk voor, ze moeten mee opgenomen worden bij de totaalfactuur 21% en moeten worden geraporteerd zodat dit kan worden rechtgezet (die facturen worden dan verwerkt in de volgende maand).

---

# Voorgestelde oplossing

## Eén centrale applicatie

Een eenvoudige Windows-applicatie die na selectie van een Excel-export automatisch:

1. B2B-facturen detecteert.
2. BTW nummers controleert
3. De juiste PDF-facturen verzamelt.
4. Een uploadmap voor Billit opbouwt.
5. B2C-facturen groepeert.
6. Overzichten genereert voor:
   - 6% BTW
   - 21% BTW
7. PDF-bijlagen genereert.
8. Een controle- en logbestand aanmaakt.

---

# Automatische verwerking B2B

## Selectieregel

Factuur wordt als B2B beschouwd wanneer een BTW-nummer aanwezig is.

Voorbeelden:

| BTW-nummer | Resultaat |
|------------|------------|
| BE0123456789 | B2B |
| NL123456789B01 | B2B |
| FR12345678901 | B2B |
| Leeg veld | B2C |

## Output

Automatisch aangemaakte map:

```
BillitUpload/
├── PP20260001.pdf
├── PP20260002.pdf
├── PP20260003.pdf
└── ...
```

Deze map kan onmiddellijk gebruikt worden voor upload naar Billit.

---

# Automatische verwerking B2C

## Selectieregel

Factuur wordt als B2C beschouwd wanneer geen BTW-nummer aanwezig is.

## Verwerking

Facturen worden automatisch opgesplitst volgens BTW-tarief.

### Overzicht 6%

Bijvoorbeeld:

| Omschrijving | Waarde |
|--------------|---------|
| Aantal facturen | 154 |
| Omzet excl. BTW | € x.xxx |
| BTW 6% | € xxx |
| Totaal incl. BTW | € x.xxx |

### Overzicht 21%

Bijvoorbeeld:

| Omschrijving | Waarde |
|--------------|---------|
| Aantal facturen | 287 |
| Omzet excl. BTW | € x.xxx |
| BTW 21% | € xxx |
| Totaal incl. BTW | € x.xxx |

---

# PDF-generatie

Het systeem genereert automatisch:

```
B2C_6pct_2026-10.pdf
B2C_21pct_2026-10.pdf
```

Deze bestanden kunnen rechtstreeks als bijlage toegevoegd worden aan de verzamelfacturen in Billit.

---

# Controlemechanismen

De applicatie kan bijkomend volgende controles uitvoeren:

## Ontbrekende PDF-facturen

Rapporteert wanneer een factuur voorkomt in Excel maar de PDF ontbreekt.

## Dubbele factuurnummers

Detecteert mogelijke dubbels.

## 0%-facturen

Detecteert particuliere facturen met 0% BTW zodat deze nagekeken kunnen worden.

## Verwerkingsrapport

Automatisch rapport met bijvoorbeeld:

- Totaal aantal facturen.
- Aantal B2B-facturen.
- Aantal B2C-facturen 6%.
- Aantal B2C-facturen 21%.
- Aantal afwijkingen.
- Ontbrekende PDF's.

---

# Technische oplossing

## Ontwikkelomgeving

- Python
- Pandas (Excel-verwerking)
- OpenPyXL (Excel-output)
- PDF-generator
- Windows desktopinterface

## Distributie

De applicatie wordt verpakt als zelfstandige Windows-applicatie (.exe).

Voordelen:

- Geen Python-installatie nodig.
- Geen technische kennis vereist.
- Werkt op standaard Windows-pc's.

---

# Verwachte voordelen

## Tijdswinst

Een groot deel van de huidige manuele filtering en rapportering wordt geautomatiseerd.

## Minder fouten

- Geen handmatige selectie van facturen.
- Automatische controles op inconsistenties.
- Betere traceerbaarheid via logbestanden.

## Standaardisatie

Elke verwerking verloopt volgens dezelfde regels.

## Schaalbaarheid

De oplossing kan later uitgebreid worden met:

- Automatische Billit-importbestanden.
- Extra BTW-tarieven.
- Automatische archivering.
- Integratie met ERP- of facturatiepakketten.
- Geavanceerde rapportering.

---

# Benodigde input voor ontwikkeling

Om de toepassing te bouwen zijn volgende zaken nodig:

## 1. Voorbeeld van de Excel-export

Geanonimiseerd bestand is voldoende.

## 2. Beschrijving van de huidige workflow

- Oorsprong van de export.
- Eventuele handmatige aanpassingen.
- Welke kolommen belangrijk zijn.

## 3. Naamgeving van PDF-facturen

Voorbeeld:

```
PP20260001.pdf
PP20260002.pdf
```

## 4. Voorbeeld van huidige totaalfacturen

Excel, PDF of screenshot volstaat.

---

# Verwacht resultaat

Een eenvoudige Windows-toepassing waarmee de gebruiker:

1. Een Excel-export selecteert.
2. Op "Verwerken" klikt.
3. Beslissingen neemt over probleem lijnen (foute BTW nummer)
4. Automatisch:
   - een Billit-uploadmap krijgt voor B2B-facturen;
   - een PDF-overzicht krijgt voor 6%-facturen;
   - een PDF-overzicht krijgt voor 21%-facturen;
   - een controle-rapport ontvangt.

Hierdoor wordt het huidige proces grotendeels geautomatiseerd en wordt de kans op manuele fouten aanzienlijk verkleind.