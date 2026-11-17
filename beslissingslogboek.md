# Beslissingslogboek: BTW-controle (FactuurTool)

De regels hieronder komen uit het logboek van FactuurTool (enkel het BTW-deel), aangevuld met
de keuzes voor deze demo.

## Regels van de BTW-controle

| Datum | Beslissing | Waarom | Wie |
|---|---|---|---|
| 2026-11-17 | Lijn met BTW-nummer (ook zonder tarief / verlegde BTW) → B2B, maar enkel als het nummer geldig is in VIES | Bevestigd door Karolien | Karolien |
| 2026-11-17 | Ongeldig BTW-nummer → melden, de gebruiker beslist B2B of B2C vóór de bestanden gemaakt worden | Mens beslist bij twijfel | Karolien |
| 2026-11-17 | Niet-controleerbaar BTW-nummer (VIES druk/offline, niet-EU) → B2B met melding, niet blokkeren | Het Belgische register weigert vaak drukte (`MS_MAX_CONCURRENT_REQ`); blokkeren zou het programma onbruikbaar maken. Knop "opnieuw controleren" voorzien. | voorstel Claude, aanvaard |
| 2026-11-17 | Belgisch BTW-nummer met 9 cijfers → 0 vooraan voor de VIES-controle, met melding | Oud formaat; VIES verwacht 10 cijfers. 2 gevallen in oktober. | aanname Claude, **na te kijken** |
| 2026-11-17 | `vat_id` gaat voor op een nummer in `company` | `vat_id` is het veld dat de klant zelf invulde als BTW-nummer | FactuurTool |

## Keuzes voor deze demo

| Datum | Beslissing | Waarom | Wie |
|---|---|---|---|
| 2026-11-17 | Aparte Streamlit-demo op verzonnen data; de echte tool blijft een Windows-programma | De opdracht vraagt een publieke URL. Echte klantdata mag nooit online. | Karolien |
| 2026-11-17 | Code uit FactuurTool **gekopieerd, niet aangepast** | Wat de demo toont, is exact wat de echte tool doet | voorstel Claude, aanvaard |
| 2026-11-17 | Drie publieke BTW-nummers van grote Belgische bedrijven als "geldige" voorbeelden | Verzonnen nummers zijn altijd ongeldig in VIES; zo zie je alle drie de uitkomsten | voorstel Claude |
| 2026-11-17 | Schakelaar "demo zonder internet" met vaste antwoorden | De presentatie mag niet afhangen van een drukke EU-server | voorstel Claude |
| 2026-11-17 | Indeelregel `deel_in` verhuisd van `app.py` naar `pipeline.py`, met 4 eigen tests | De opdracht vraagt alle regels als pure functies in `pipeline.py`; in `app.py` waren ze niet te testen | Karolien, na controle tegen de opdracht |

## Wat de tests niet testten

| Datum | Vondst | Wat ik ermee deed | Wie |
|---|---|---|---|
| 2026-11-17 | Een telefoonnummer in `company` (`tel 0475 123 456`) wordt herkend als BTW-nummer `BE0475123456`. Het patroon voor een Belgisch nummer zonder landcode (4-3-3 cijfers, begint met 0 of 1) past ook op een gsm-nummer. | Test toegevoegd (gemarkeerd als *gekende fout*). Nog niet opgelost: VIES zegt "ongeldig" en dan beslis ik zelf, dus de fout komt nooit stil in B2B. **Te beslissen**: patroon aanpassen (bv. niet na "tel") of zo laten. | gevonden met de demodata |
