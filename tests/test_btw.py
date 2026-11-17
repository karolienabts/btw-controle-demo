"""Tests op de BTW-regels. Overgenomen uit FactuurTool/tests/test_regels.py, zonder internet."""
import sys
from pathlib import Path

import pandas as pd
import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import btw  # noqa: E402
import vies  # noqa: E402


# ------------------------------------------------------------ kuisen en vinden

@pytest.mark.parametrize("ruw, verwacht", [
    ("BE 0123.456.789", "BE0123456789"),
    ("nl123456789b01", "NL123456789B01"),
    ("  ", None),
    (None, None),
])
def test_normaliseer_btw(ruw, verwacht):
    assert btw.normaliseer_btw(ruw) == verwacht


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
    assert btw.zoek_btw_in_company(company) == verwacht


def test_vat_id_gaat_voor_op_company():
    df = pd.DataFrame({"company": ["X BE0417497106"], "vat_id": ["BE0202239951"]})
    uit = btw.voeg_btw_toe(df)
    assert uit.loc[0, "btw_nummer"] == "BE0202239951"
    assert uit.loc[0, "btw_bron"] == "vat_id"


# ------------------------------------------------------------ klaarmaken voor VIES

def test_vies_formaat_vult_belgisch_nummer_van_9_cijfers_aan():
    land, nummer, opmerking = btw.vies_formaat("BE123456789")
    assert (land, nummer) == ("BE", "0123456789")
    assert "aangevuld" in opmerking


def test_vies_formaat_griekenland_wordt_EL():
    assert btw.vies_formaat("GR123456789")[0] == "EL"


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
