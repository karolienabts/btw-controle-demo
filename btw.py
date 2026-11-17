"""BTW-nummers kuisen, vinden en klaarmaken voor VIES.

Deze functies zijn ongewijzigd overgenomen uit FactuurTool/pipeline.py (stap 3. BTW-nummers),
zodat deze demo exact doet wat de echte tool doet. Geen internet hier: dat zit in vies.py.
"""
import re

import pandas as pd

import instellingen as I


def normaliseer_btw(waarde):
    """'BE 0123.456.789' -> 'BE0123456789'. Lege waarden -> None."""
    if waarde is None or pd.isna(waarde):
        return None
    tekst = re.sub(r"[\s.\-/]", "", str(waarde)).upper()
    return tekst or None


_LANDEN = "|".join(I.EU_LANDEN)
_BTW_PATRONEN = [
    # landcode + cijfers (met punten/spaties), eventueel NL-staart 'B01'
    re.compile(rf"\b(?:{_LANDEN})\s?[0-9][0-9.\s]{{6,13}}[0-9](?:\s?B\s?[0-9]{{2}})?\b"),
    re.compile(r"\bATU\s?[0-9]{8}\b"),                      # Oostenrijk
    re.compile(r"\bES\s?[A-Z0-9][0-9]{7}[A-Z0-9]\b"),       # Spanje
]
# Belgisch ondernemingsnummer zonder landcode: 0123.456.789 of 1234 567 890
_BE_ZONDER_LAND = re.compile(r"\b[01][0-9]{3}[.\s]?[0-9]{3}[.\s]?[0-9]{3}\b")


def zoek_btw_in_company(company):
    """Zoek een BTW-nummer in de bedrijfsnaam. Geeft het genormaliseerde nummer of None."""
    if company is None or pd.isna(company):
        return None
    tekst = str(company).upper()
    for patroon in _BTW_PATRONEN:
        gevonden = patroon.search(tekst)
        if gevonden:
            return normaliseer_btw(gevonden.group(0))
    gevonden = _BE_ZONDER_LAND.search(tekst)
    if gevonden:
        return "BE" + normaliseer_btw(gevonden.group(0))
    return None


def voeg_btw_toe(df: pd.DataFrame) -> pd.DataFrame:
    """Voeg kolommen toe: btw_in_company, btw_nummer (vat_id gaat voor) en btw_bron."""
    uit = df.copy()
    uit["btw_in_company"] = uit["company"].map(zoek_btw_in_company).astype(object)
    uit["btw_nummer"] = uit["vat_id"].where(uit["vat_id"].notna(), uit["btw_in_company"])
    uit["btw_bron"] = None
    uit.loc[uit["btw_in_company"].notna(), "btw_bron"] = "company"
    uit.loc[uit["vat_id"].notna(), "btw_bron"] = "vat_id"
    return uit


def vies_formaat(btw_nummer: str, country_code=None):
    """Splits een BTW-nummer in (landcode, nummer, opmerking) zoals VIES het verwacht."""
    opmerking = ""
    if len(btw_nummer) >= 2 and btw_nummer[:2].isalpha():
        land, nummer = btw_nummer[:2], btw_nummer[2:]
    else:
        land = str(country_code or "").upper()
        nummer = btw_nummer
        opmerking = f"landcode ontbrak, {land} genomen uit country_code"
    if land == "GR":
        land = "EL"
    if land == "BE" and re.fullmatch(r"[0-9]{9}", nummer):
        nummer = "0" + nummer
        opmerking = "Belgisch nummer had 9 cijfers, aangevuld met een 0 vooraan"
    return land, nummer, opmerking


def btw_voor_vies(df: pd.DataFrame) -> dict:
    """Unieke BTW-nummers om te controleren: {btw_nummer: (land, nummer, opmerking)}."""
    te_doen = {}
    for btw, land in df.loc[df["btw_nummer"].notna(), ["btw_nummer", "country_code"]].itertuples(index=False):
        if btw not in te_doen:
            te_doen[btw] = vies_formaat(btw, land)
    return te_doen
