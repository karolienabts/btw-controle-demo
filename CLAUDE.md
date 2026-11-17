# BTW-controle demo (FactuurTool)

Streamlit-demo van één onderdeel van FactuurTool: BTW-nummers kuisen, vinden, controleren in VIES
en indelen in B2B/B2C. Voor een presentatie van **maximaal 7 minuten** (Project 1, Syntra).

## Afspraken
- **Enkel verzonnen data** (`data/demo_lijnen.csv`). Nooit een echte Plug&Pay-export, PDF of
  klantnaam in deze repo. `.gitignore` blokkeert `*.xlsx`, `*.pdf`, `*.zip`.
- **Alle regels in `pipeline.py`** (pure functies, één per stap, geen Streamlit, geen internet).
  `app.py` toont enkel; `vies.py` is de enige plek die het internet op gaat.
- De BTW-functies in `pipeline.py` en heel `vies.py` zijn **kopieën** van FactuurTool. Pas de
  regels daar aan en kopieer ze opnieuw; anders toont de demo iets anders dan de echte tool.
- Elke regel in `deel_in` heeft een test in `tests/test_pipeline.py`.
- Indeling: geen BTW-nummer → B2C · geldig → B2B · onbekend (niet te controleren) → B2B met
  melding · ongeldig → de gebruiker beslist. Nooit stil indelen.
- Controle onderaan: som van de groepen = aantal lijnen en totaal van de export.
- Hou de app kort: 4 stappen, elk in ±1 minuut uit te leggen.

## Starten
```
conda activate syntra-ds
streamlit run app.py
pytest -v
```
