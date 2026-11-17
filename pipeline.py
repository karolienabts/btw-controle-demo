"""De stappen van de BTW-controle, als pure functies (geen Streamlit, geen internet).

Volgorde:  lees_demo -> kuis_en_zoek -> btw_voor_vies -> (vies.py) -> deel_in

normaliseer_btw, zoek_btw_in_company, voeg_btw_toe, vies_formaat en btw_voor_vies zijn
ongewijzigd overgenomen uit FactuurTool/pipeline.py, zodat deze demo exact doet wat de echte
tool doet. deel_in is de BTW-indeling uit FactuurTool, zonder tarieven en boeken.
"""
import re

import pandas as pd

import instellingen as I
import vies

KIES, B2B, B2C, TE_BESLISSEN = "? kies", "B2B", "B2C", "Te beslissen"

# Antwoorden voor "demo zonder internet": deze drie (publieke BTW-nummers van grote bedrijven)
# zijn geldig in VIES, nagekeken op 17/11/2026. Alle andere EU-nummers in de demo zijn verzonnen.
OFFLINE_GELDIG = {("BE", "0202239951"), ("BE", "0417497106"), ("BE", "0400378485")}


# ---------------------------------------------------------------- 1. inlezen

def lees_demo(pad) -> pd.DataFrame:
    """Lees de verzonnen demolijnen. Tekstkolommen blijven tekst (geen 0 die wegvalt)."""
    return pd.read_csv(pad, dtype={"invoice_number": str, "company": str, "vat_id": str,
                                   "country_code": str})


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


# ---------------------------------------------------------------- 2. kuisen en vinden

def kuis_en_zoek(ruw: pd.DataFrame) -> pd.DataFrame:
    """Kuis vat_id (ruwe waarde blijft bewaard in vat_id_ruw) en zoek nummers in company."""
    df = ruw.copy()
    df["vat_id_ruw"] = df["vat_id"]
    df["vat_id"] = df["vat_id"].map(normaliseer_btw).astype(object)
    return voeg_btw_toe(df)


# ---------------------------------------------------------------- 3. VIES zonder internet

def vies_offline(formaten: dict) -> dict:
    """Vaste VIES-antwoorden voor de demo, in hetzelfde formaat als vies.controleer_alle."""
    uit = {}
    for b, (land, nr, _) in formaten.items():
        if land not in I.EU_LANDEN:
            uit[b] = vies.controleer_een(land, nr)          # niet-EU: belt VIES niet
        elif (land, nr) in OFFLINE_GELDIG:
            uit[b] = (vies.GELDIG, "geldig volgens VIES (vast antwoord, demo zonder internet)")
        else:
            uit[b] = (vies.ONGELDIG, "bestaat niet volgens VIES (vast antwoord, demo zonder internet)")
    return uit


# ---------------------------------------------------------------- 4. indelen

def ongeldige_nummers(status: dict) -> list:
    """De BTW-nummers waarover de gebruiker moet beslissen."""
    return sorted(b for b, (s, _) in status.items() if s == vies.ONGELDIG)


def deel_in(df: pd.DataFrame, status: dict, keuzes: dict) -> pd.DataFrame:
    """Elke lijn krijgt een groep en een reden. Dezelfde regels als in FactuurTool.

    status = {btw_nummer: (status, uitleg)} uit VIES; keuzes = {btw_nummer: B2B/B2C}.
    """
    groepen, redenen = [], []
    for b in df["btw_nummer"]:
        if not isinstance(b, str):
            g, r = B2C, "geen BTW-nummer"
        elif b not in status:
            g, r = TE_BESLISSEN, "nog niet gecontroleerd in VIES"
        elif status[b][0] == vies.GELDIG:
            g, r = B2B, "geldig in VIES"
        elif status[b][0] == vies.ONBEKEND:
            g, r = B2B, "niet te controleren → B2B, met melding"
        elif keuzes.get(b, KIES) in (B2B, B2C):
            g, r = keuzes[b], f"ongeldig in VIES → jij koos {keuzes[b]}"
        else:
            g, r = TE_BESLISSEN, "ongeldig in VIES → jij moet beslissen"
        groepen.append(g)
        redenen.append(r)
    return df.assign(groep=groepen, reden=redenen)
