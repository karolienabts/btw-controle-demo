"""Tests op de stappen in pipeline.py, zonder internet.

De tests op kuisen, vinden, VIES-formaat en VIES-antwoorden komen uit FactuurTool/tests/test_regels.py.
"""
import sys
from pathlib import Path

import pandas as pd
import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pipeline as P  # noqa: E402
import vies  # noqa: E402


# ------------------------------------------------------------ kuisen en vinden

@pytest.mark.parametrize("ruw, verwacht", [
    ("BE 0123.456.789", "BE0123456789"),
    ("nl123456789b01", "NL123456789B01"),
    ("  ", None),
    (None, None),
])
def test_normaliseer_btw(ruw, verwacht):
    assert P.normaliseer_btw(ruw) == verwacht


@pytest.mark.parametrize("company, verwacht", [
    ("Bakkerij Jansen BE0123456789", "BE0123456789"),
    ("Jansen bv be 0123.456.789", "BE0123456789"),
    ("Jansen 0123.456.789", "BE0123456789"),          # Belgisch zonder landcode
    ("Studio NL123456789B01", "NL123456789B01"),
    ("Jansen & Zonen", None),
    ("Bakkerij 2000", None),                            # te weinig cijfers
    (None, None),
])
def test_btw_in_company(company, verwacht):
    assert P.zoek_btw_in_company(company) == verwacht


@pytest.mark.xfail(strict=True, reason="Gekende fout: het patroon voor een Belgisch nummer zonder "
                   "landcode past ook op een gsm-nummer. Zie beslissingslogboek.")
def test_telefoonnummer_in_company_is_geen_btw_nummer():
    """Wat de oorspronkelijke tests niet testten: een vals positief."""
    assert P.zoek_btw_in_company("Kapsalon Lies - tel 0475 123 456") is None


def test_vat_id_gaat_voor_op_company():
    df = pd.DataFrame({"company": ["X BE0417497106"], "vat_id": ["BE0202239951"]})
    uit = P.voeg_btw_toe(df)
    assert uit.loc[0, "btw_nummer"] == "BE0202239951"
    assert uit.loc[0, "btw_bron"] == "vat_id"


# ------------------------------------------------------------ klaarmaken voor VIES

def test_vies_formaat_vult_belgisch_nummer_van_9_cijfers_aan():
    land, nummer, opmerking = P.vies_formaat("BE123456789")
    assert (land, nummer) == ("BE", "0123456789")
    assert "aangevuld" in opmerking


def test_vies_formaat_griekenland_wordt_EL():
    assert P.vies_formaat("GR123456789")[0] == "EL"


# ------------------------------------------------------------ VIES (zonder internet)

class Antwoord:
    def __init__(self, data, code=200):
        self.data, self.status_code = data, code

    def json(self):
        return self.data


@pytest.mark.parametrize("data, verwacht", [
    ({"valid": True}, vies.GELDIG),
    ({"valid": False}, vies.ONGELDIG),
    ({"actionSucceed": False, "errorWrappers": [{"error": "MS_MAX_CONCURRENT_REQ"}]}, vies.ONBEKEND),
    ({"valid": False, "userError": "MS_UNAVAILABLE"}, vies.ONBEKEND),
])
def test_vies_antwoorden(monkeypatch, data, verwacht):
    monkeypatch.setattr(vies.requests, "post", lambda *a, **k: Antwoord(data))
    assert vies.controleer_een("BE", "0123456789")[0] == verwacht


def test_vies_niet_bereikbaar(monkeypatch):
    def faal(*a, **k):
        raise requests.ConnectionError("geen internet")
    monkeypatch.setattr(vies.requests, "post", faal)
    assert vies.controleer_een("BE", "0123456789")[0] == vies.ONBEKEND


def test_vies_niet_eu_land_wordt_niet_gevraagd(monkeypatch):
    monkeypatch.setattr(vies.requests, "post", lambda *a, **k: pytest.fail("mag niet bellen"))
    assert vies.controleer_een("CH", "123")[0] == vies.ONBEKEND


# ------------------------------------------------------------ indelen (deel_in)

def lijnen(*btw_nummers):
    return pd.DataFrame({"btw_nummer": list(btw_nummers), "amount": [100.0] * len(btw_nummers)})


def test_indeling_volgens_de_regels():
    df = lijnen(None, "BE1", "BE2", "CH3", "BE4")
    status = {"BE1": (vies.GELDIG, ""), "BE2": (vies.ONGELDIG, ""),
              "CH3": (vies.ONBEKEND, ""), "BE4": (vies.ONGELDIG, "")}
    uit = P.deel_in(df, status, {"BE4": P.B2C})
    assert list(uit["groep"]) == [P.B2C, P.B2B, P.TE_BESLISSEN, P.B2B, P.B2C]


def test_ongeldig_nummer_wordt_nooit_stil_ingedeeld():
    """Zonder keuze van de gebruiker blijft een ongeldig nummer 'te beslissen'."""
    df = lijnen("BE2")
    uit = P.deel_in(df, {"BE2": (vies.ONGELDIG, "")}, {"BE2": P.KIES})
    assert uit.loc[0, "groep"] == P.TE_BESLISSEN


def test_nog_niet_gecontroleerd_is_geen_b2b():
    uit = P.deel_in(lijnen("BE1"), {}, {})
    assert uit.loc[0, "groep"] == P.TE_BESLISSEN


def test_demodata_zonder_internet_telt_op():
    """De hele pijplijn op de demodata: elke lijn in precies één groep, totalen kloppen."""
    df = P.kuis_en_zoek(P.lees_demo(Path(__file__).resolve().parent.parent / "data" / "demo_lijnen.csv"))
    status = P.vies_offline(P.btw_voor_vies(df))
    uit = P.deel_in(df, status, {b: P.B2C for b in P.ongeldige_nummers(status)})
    assert len(uit) == len(df) == 10
    assert uit["groep"].value_counts().to_dict() == {P.B2B: 4, P.B2C: 6}
    assert round(uit.groupby("groep")["amount"].sum().sum(), 2) == round(df["amount"].sum(), 2)
