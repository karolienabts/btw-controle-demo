"""BTW-nummers controleren in VIES, de officiële EU-dienst.

Ongewijzigd overgenomen uit FactuurTool/vies.py.

We gebruiken de REST-API van VIES (POST check-vat-number). Die geeft voor elk nummer
"valid": true of false. Is VIES niet bereikbaar of druk bezet, dan wordt het nummer
'onbekend': het programma blokkeert dan niet, maar meldt het.
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

import instellingen as I

GELDIG, ONGELDIG, ONBEKEND = "geldig", "ongeldig", "onbekend"


def controleer_een(land: str, nummer: str):
    """Controleer één BTW-nummer. Geeft (status, uitleg)."""
    if land not in I.EU_LANDEN:
        return ONBEKEND, f"{land or '?'} is geen EU-land: VIES kan dit nummer niet controleren"
    try:
        antwoord = requests.post(
            I.VIES_URL,
            json={"countryCode": land, "vatNumber": nummer},
            timeout=I.VIES_TIMEOUT_SECONDEN,
        )
    except requests.RequestException:
        return ONBEKEND, "VIES was niet bereikbaar (internet of EU-server)"
    if antwoord.status_code != 200:
        return ONBEKEND, f"VIES gaf een fout (code {antwoord.status_code})"
    try:
        data = antwoord.json()
    except ValueError:
        return ONBEKEND, "VIES gaf een onleesbaar antwoord"

    # Bij een storing (bv. het nationale register is offline) is er geen geldig antwoord.
    fout = data.get("userError")
    if data.get("actionSucceed") is False or data.get("errorWrappers") or (
        fout and fout not in ("VALID", "INVALID")
    ):
        reden = fout or str(data.get("errorWrappers"))
        return ONBEKEND, f"VIES kon dit nummer nu niet controleren ({reden})"
    if "valid" not in data:
        return ONBEKEND, "VIES gaf geen resultaat"
    if data["valid"]:
        return GELDIG, "geldig volgens VIES"
    return ONGELDIG, "VIES: dit nummer bestaat niet of is niet actief"


def controleer_alle(te_controleren: dict, voortgang=None, rondes: int = 4,
                    tegelijk: int = 3) -> dict:
    """Controleer alle nummers. te_controleren = {btw: (land, nummer, opmerking)}.

    Een echt nummer opzoeken duurt 2 à 3 seconden, dus we vragen er een paar tegelijk.
    Het Belgische register weigert wel snel te veel vragen tegelijk (MS_MAX_CONCURRENT_REQ):
    wat 'onbekend' blijft, proberen we in een volgende ronde opnieuw (na 5, 10, 15 s).

    Geeft {btw_nummer: (status, uitleg)}. voortgang(gedaan, totaal) na elk afgewerkt nummer.
    """
    resultaat = {}
    open_ = list(te_controleren)
    totaal, gedaan = len(open_), 0
    for ronde in range(rondes):
        laatste_ronde = ronde == rondes - 1
        opnieuw = []
        with ThreadPoolExecutor(max_workers=tegelijk) as pool:
            taken = {pool.submit(controleer_een, *te_controleren[btw][:2]): btw for btw in open_}
            for taak in as_completed(taken):
                btw = taken[taak]
                resultaat[btw] = taak.result()
                land = te_controleren[btw][0]
                if resultaat[btw][0] == ONBEKEND and land in I.EU_LANDEN and not laatste_ronde:
                    opnieuw.append(btw)
                else:
                    gedaan += 1
                    if voortgang:
                        voortgang(gedaan, totaal)
        if not opnieuw:
            break
        open_ = opnieuw
        time.sleep(5 * (ronde + 1))
    return resultaat
