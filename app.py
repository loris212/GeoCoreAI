#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GeoCore AI — Demo v1 (interfaccia per geologi)
==============================================
App curata: mostra casi VALIDATI (RQD predetto vs ground-truth), il metodo e i
LIMITI in modo trasparente. Pensata per dimostrazioni a geologi e per la tesi.

Avvio:  streamlit run app.py
"""
from pathlib import Path
import json
import streamlit as st

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "geocore" / "demo_cases_out" / "manifest.json"

st.set_page_config(page_title="GeoCore AI — Demo v1", page_icon="🪨", layout="wide")

# ---- intestazione -----------------------------------------------------------
st.title("🪨 GeoCore AI — stima automatica dell'RQD da foto di carota")
st.caption("Demo v1 · strumento di **assistenza** al geologo, non sostitutivo · "
           "prototipo di ricerca/tesi")

with st.expander("Cos'è l'RQD e cosa fa questo strumento", expanded=False):
    st.markdown(
        "**RQD (Rock Quality Designation)** = (Σ lunghezze dei pezzi integri ≥ 10 cm "
        "/ lunghezza della manovra) × 100. È un indice base della qualità dell'ammasso "
        "roccioso.\n\n"
        "La pipeline: foto cassetta → rettifica → individua le file → **segmenta i "
        "pezzi (YOLO11-seg)** → calcola RQD e classe di Deere. "
        "Qui sotto vedi casi **validati** contro l'annotazione manuale di un geologo.")

# ---- caricamento casi -------------------------------------------------------
if not MANIFEST.exists():
    st.error("Casi non generati. Esegui prima:  "
             "`python -m geocore.demo_cases`")
    st.stop()

casi = json.loads(MANIFEST.read_text())

DEERE_COLORI = {"molto scadente": "🔴", "scadente": "🟠", "discreto": "🟡",
                "buono": "🟢", "ottimo": "🟢"}

tab_demo, tab_metodo, tab_limiti = st.tabs(
    ["🔬 Casi validati", "📐 Metodo & validazione", "⚠️ Limiti (leggere)"])

# ============================ TAB DEMO =======================================
with tab_demo:
    etichette = [f"{c['label']}  ·  {c['tipo']}" for c in casi]
    idx = st.selectbox("Scegli un caso", range(len(casi)),
                       format_func=lambda i: etichette[i])
    c = casi[idx]

    st.image(str(ROOT / c["overlay"]),
             caption="Verde = pezzi ≥10 cm annotati dal geologo (verità) · "
                     "Rosso = pezzi rilevati dal modello", use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("RQD predetto", f"{c['rqd_pred']:.0f}%",
                help="Stima del modello")
    col2.metric("RQD vero (geologo)", f"{c['rqd_gt']:.0f}%",
                help="Da annotazione manuale")
    col3.metric("Errore", f"{c['err']:.0f} pp",
                delta=f"{'OK' if c['err'] <= 10 else 'alto'}",
                delta_color="normal" if c["err"] <= 10 else "inverse")

    st.markdown(
        f"**Classe di Deere** — predetta: {DEERE_COLORI.get(c['classe_pred'],'')} "
        f"*{c['classe_pred']}* · vera: {DEERE_COLORI.get(c['classe_gt'],'')} "
        f"*{c['classe_gt']}*")

    if c["in_distribution"]:
        st.success("Caso **in-distribution**: il modello ha visto sondaggi simili in "
                   "addestramento. Qui l'accuratezza è alta.")
    else:
        if c["err"] <= 10:
            st.info("Caso **held-out** (sondaggio mai visto): qui il modello generalizza bene.")
        else:
            st.warning("Caso **held-out** con **fallimento**: su questo sondaggio mai "
                       "visto il modello non rileva i pezzi e sottostima gravemente. "
                       "È il limite di generalizzazione cross-sito (vedi tab Limiti).")

# ========================== TAB METODO =======================================
with tab_metodo:
    st.subheader("Pipeline")
    st.markdown(
        "1. **Rettifica** prospettica della cassetta (OpenCV)\n"
        "2. **Individuazione file** via profilo di texture\n"
        "3. **Segmentazione pezzi** con YOLO11-seg addestrato su carote annotate\n"
        "4. **Calcolo RQD** (soglia 10 cm, classi di Deere)")
    st.subheader("Validazione (test su sondaggio held-out Z441, 58 manovre)")
    st.table({
        "Metodo": ["OpenCV (baseline)", "SAM 2.1 (zero-shot)", "YOLO11-seg"],
        "MAE (pp)": [21.7, 42.2, 34.2],
        "Correlazione": [-0.12, 0.33, 0.16],
        "Tempo/crop": ["2 ms", "24 s", "150 ms"],
    })
    st.markdown(
        "**Lettura onesta:** in-distribution YOLO è quasi perfetto (MAE ~5–7 pp); "
        "su un **sondaggio mai visto** la generalizzazione crolla (MAE 34, corr 0.16). "
        "Il valore scientifico del progetto è proprio questa **valutazione rigorosa**, "
        "non un numero ottimistico.")

# ========================== TAB LIMITI =======================================
with tab_limiti:
    st.subheader("Cosa NON garantisce questo strumento")
    st.markdown(
        "- **Generalizzazione cross-sito debole**: su litologie/cantieri mai visti "
        "può sottostimare gravemente (es. caso Z441 392–399 m: vero 93%, predetto 0%).\n"
        "- **Scala fisica**: i 10 cm richiedono una scala nota (marker/righello o "
        "lunghezza scomparto). Senza, l'RQD non è calcolabile.\n"
        "- **Frattura naturale vs artificiale**: non distinguibile in modo affidabile "
        "da una foto 2D dall'alto → richiede il giudizio del geologo.\n"
        "- **Recupero < 100%**: il denominatore corretto è la lunghezza della manovra, "
        "da inserire manualmente.")
    st.error("⚖️ La relazione geologica resta firmata e validata da un **geologo "
             "abilitato**. Questo strumento fornisce **misura + candidati**, non una "
             "decisione automatica.")

st.divider()
st.caption("GeoCore AI Demo v1 · numeri identici alla valutazione della tesi · "
           "i casi mostrati includono volutamente un fallimento per trasparenza.")
