"""Demo: hoe FactuurTool BTW-nummers controleert (op verzonnen demodata).

Starten:  streamlit run app.py
Alle regels zitten in pipeline.py (en vies.py voor de vraag aan de EU). Dit bestand toont
enkel elke stap, met hoeveel lijnen erin en eruit gaan.
"""
import inspect
from pathlib import Path

import pandas as pd
import streamlit as st

import pipeline as P
import vies
from pipeline import B2B, B2C, KIES, TE_BESLISSEN

DATA = Path(__file__).parent / "data" / "demo_lijnen.csv"

st.set_page_config(page_title="BTW-controle", page_icon="🧾", layout="wide")


@st.cache_data
def lees_demo() -> pd.DataFrame:
    return P.lees_demo(DATA)


@st.cache_data(show_spinner=False)
def vies_live(te_controleren: tuple) -> dict:
    """Live VIES. Gecachet: dezelfde nummers vragen we niet twee keer aan de EU."""
    return vies.controleer_alle({b: (land, nr, opm) for b, land, nr, opm in te_controleren})


def toon_code(*functies):
    if st.session_state.get("toon_code"):
        for f in functies:
            st.code(inspect.getsource(f), language="python")


# ------------------------------------------------------------------ berekenen

with st.sidebar:
    st.header("Instellingen")
    offline = st.toggle("Demo zonder internet", value=False,
                        help="Vaste VIES-antwoorden, voor als de EU-server druk of offline is.")
    st.toggle("Toon de code achter elke stap", key="toon_code")
    st.caption("Alle klanten en bedragen zijn verzonnen. Enkel de drie 'geldige' nummers zijn "
               "publieke BTW-nummers van grote Belgische bedrijven.")

ruw = lees_demo()
df = P.kuis_en_zoek(ruw)
formaten = P.btw_voor_vies(df)

if offline:
    status = P.vies_offline(formaten)
else:
    status = st.session_state.get("vies_live")
ongeldig = P.ongeldige_nummers(status or {})
keuzes = {b: st.session_state.get(f"keuze_{b}", KIES) for b in ongeldig}
resultaat = P.deel_in(df, status or {}, keuzes)

# ------------------------------------------------------------------ trechter

st.title("Het BTW-nummer beslist of een factuur B2B of B2C is")
st.write("Een factuur **met geldig BTW-nummer** gaat apart naar de boekhouding (B2B). "
         "Zonder BTW-nummer komt ze op de maandelijkse totaalfactuur (B2C). "
         "In de export is dat nummer vaak rommelig, verstopt in de bedrijfsnaam, of vals.")

n = len(df)
uit_vat = int((df["btw_bron"] == "vat_id").sum())
uit_comp = int((df["btw_bron"] == "company").sum())
k = st.columns(4)
k[0].metric("Lijnen in de export", n)
k[1].metric("Met BTW-nummer", uit_vat + uit_comp, help=f"{uit_vat} in vat_id, {uit_comp} gevonden in company")
if status is None:
    k[2].metric("Gecontroleerd in VIES", "nog niet")
else:
    tel = pd.Series([s for s, _ in status.values()]).value_counts()
    k[2].metric("Gecontroleerd in VIES",
                f"{tel.get(vies.GELDIG, 0)} ✔ · {tel.get(vies.ONGELDIG, 0)} ✘ · {tel.get(vies.ONBEKEND, 0)} ?",
                help="geldig · ongeldig · onbekend (niet te controleren)")
g = resultaat["groep"].value_counts()
k[3].metric("Ingedeeld", f"{g.get(B2B, 0)} B2B · {g.get(B2C, 0)} B2C",
            delta=f"{g.get(TE_BESLISSEN, 0)} te beslissen" if g.get(TE_BESLISSEN, 0) else "alles ingedeeld",
            delta_color="inverse" if g.get(TE_BESLISSEN, 0) else "normal")

# ------------------------------------------------------------------ stap 1

with st.expander(f"1 · Kuisen en vinden: {n} lijnen → {uit_vat + uit_comp} met een BTW-nummer"):
    st.write("Punten, spaties en streepjes weg, alles in hoofdletters. Staat er niets in `vat_id`, "
             "dan zoeken we met een **regex** (een zoekpatroon voor tekst) een nummer in `company`.")
    st.dataframe(
        df[["invoice_number", "company", "vat_id_ruw", "vat_id", "btw_in_company", "btw_nummer", "btw_bron"]],
        hide_index=True, width="stretch",
        column_config={"vat_id_ruw": "vat_id (ruw)", "vat_id": "vat_id (gekuist)"})
    st.caption(f"{uit_vat} lijnen met `vat_id`, {uit_comp} met een nummer in `company`, "
               f"{n - uit_vat - uit_comp} zonder BTW-nummer → die gaan straks naar B2C.")
    toon_code(P.normaliseer_btw, P.zoek_btw_in_company)

# ------------------------------------------------------------------ stap 2

with st.expander(f"2 · Klaarmaken voor VIES: {len(formaten)} unieke nummers"):
    st.write("VIES wil een landcode en een nummer apart. Twee aanpassingen: Griekenland heet "
             "in VIES `EL`, en een Belgisch nummer met 9 cijfers (oud formaat) krijgt een `0` vooraan.")
    st.dataframe(
        pd.DataFrame([(b, l, nr, o) for b, (l, nr, o) in formaten.items()],
                     columns=["btw_nummer", "landcode voor VIES", "nummer voor VIES", "opmerking"]),
        hide_index=True, width="stretch")
    toon_code(P.vies_formaat)

# ------------------------------------------------------------------ stap 3

with st.expander("3 · Controleren in VIES, de officiële EU-dienst"):
    st.write("Per nummer drie mogelijke antwoorden: **geldig**, **ongeldig**, of **onbekend** "
             "(geen EU-land, of de server is druk/offline). Het Belgische register weigert snel te veel "
             "vragen tegelijk: wat onbekend blijft, vragen we tot 3 keer opnieuw.")
    if not offline and st.button("Controleer in VIES", type="primary"):
        balk = st.progress(0.0, text="VIES vragen...")
        sleutel = tuple((b, *f) for b, f in sorted(formaten.items()))
        st.session_state["vies_live"] = vies_live(sleutel)
        balk.progress(1.0, text="Klaar")
        st.rerun()
    if status is None:
        st.info("Nog niet gecontroleerd. Klik op de knop (duurt 5 à 30 seconden).")
    else:
        st.dataframe(
            pd.DataFrame([(b, *formaten[b][:2], s, u) for b, (s, u) in sorted(status.items())],
                         columns=["btw_nummer", "land", "nummer", "status", "uitleg"]),
            hide_index=True, width="stretch")
    toon_code(vies.controleer_een)

# ------------------------------------------------------------------ stap 4

with st.expander(f"4 · Jij beslist bij twijfel: {len(ongeldig)} ongeldige nummers"):
    st.write("De tool deelt een ongeldig nummer **niet stil** in. Misschien typte de klant het fout "
             "(dan blijft het B2B), misschien is het geen bedrijf (dan B2C). Jij kiest.")
    if status is None:
        st.info("Eerst stap 3 uitvoeren.")
    for b in ongeldig:
        lijnen = df.loc[df["btw_nummer"] == b]
        st.radio(f"`{b}` · factuur {', '.join(lijnen['invoice_number'])} · {lijnen['company'].iloc[0]}",
                 [KIES, B2B, B2C], key=f"keuze_{b}", horizontal=True)

    st.subheader("Resultaat per lijn")
    st.dataframe(resultaat[["invoice_number", "company", "btw_nummer", "groep", "reden", "amount"]],
                 hide_index=True, width="stretch",
                 column_config={"amount": st.column_config.NumberColumn("amount (excl. BTW)", format="€ %.2f")})

    per_groep = resultaat.groupby("groep")["amount"].agg(["count", "sum"])
    st.dataframe(per_groep.rename(columns={"count": "lijnen", "sum": "totaal excl. BTW"}),
                 column_config={"totaal excl. BTW": st.column_config.NumberColumn(format="€ %.2f")})
    som_ok = per_groep["count"].sum() == n and round(per_groep["sum"].sum(), 2) == round(df["amount"].sum(), 2)
    if som_ok:
        st.success(f"Controle: {per_groep['count'].sum()} lijnen en € {per_groep['sum'].sum():,.2f} "
                   f"in de groepen = {n} lijnen en € {df['amount'].sum():,.2f} in de export.")
    else:
        st.error("Controle mislukt: de groepen tellen niet op tot de export.")
    toon_code(P.deel_in)
