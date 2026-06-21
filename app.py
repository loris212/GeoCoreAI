#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GeoCore AI — Demo v1 (interfaccia per geologi)
==============================================
- Scheda "Pipeline live": ESEGUE davvero geocore.pipeline.analizza
  (foto → rettifica → YOLO → RQD) su un'immagine d'esempio o caricata.
- Scheda "Casi validati": evidenza precomputata (RQD predetto vs ground-truth),
  calcolata dall'harness di valutazione (RQD per manovra = corretto).

Avvio:  streamlit run app.py
"""
from pathlib import Path
import json
import tempfile
import glob
import cv2
import streamlit as st

ROOT = Path(__file__).resolve().parent
# asset versionati (per il deploy cloud); fallback ai casi generati localmente
_ASSETS = ROOT / "geocore" / "demo_assets"
_LOCAL = ROOT / "geocore" / "demo_cases_out"
CASI_DIR = _ASSETS if (_ASSETS / "manifest.json").exists() else _LOCAL
MANIFEST = CASI_DIR / "manifest.json"
ESEMPI_DIR = ROOT / "archive" / "Annotation of core bands"

st.set_page_config(page_title="GeoCore AI — Demo v1", page_icon="🪨", layout="wide")
st.title("🪨 GeoCore AI — stima automatica dell'RQD da foto di carota")
st.caption("Demo v1 · strumento di **assistenza** al geologo, non sostitutivo · "
           "prototipo di ricerca/tesi")

DEERE_COLORI = {"molto scadente": "🔴", "scadente": "🟠", "discreto": "🟡",
                "buono": "🟢", "ottimo": "🟢"}


@st.cache_resource(show_spinner="Carico il modello YOLO…")
def get_segmenter():
    from geocore.phase2_segment import PieceSegmenter
    return PieceSegmenter()


tab_live, tab_casi, tab_metodo, tab_limiti = st.tabs(
    ["▶️ Pipeline live (esecuzione reale)", "🔬 Casi validati",
     "📐 Metodo & validazione", "⚠️ Limiti (leggere)"])

# ============================ TAB LIVE =======================================
with tab_live:
    st.markdown("Esegue **davvero** la pipeline di produzione "
                "`foto → rettifica → YOLO → RQD` (`geocore/pipeline.py`).")
    modo = st.radio("Sorgente immagine",
                    ["Immagine di esempio (cassetta)", "Carica una tua foto"],
                    horizontal=True)

    percorso = None
    if modo.startswith("Immagine"):
        esempi = sorted(glob.glob(str(ESEMPI_DIR / "*.jpg")))[:30]
        if esempi:
            scelta = st.selectbox("Cassetta di esempio", esempi,
                                  format_func=lambda p: Path(p).name)
            percorso = scelta
        else:
            st.info("Nessuna immagine di esempio trovata in archive/.")
    else:
        up = st.file_uploader("Foto di una cassetta (jpg/png)", type=["jpg", "jpeg", "png"])
        if up:
            tmp = Path(tempfile.gettempdir()) / f"geocore_{up.name}"
            tmp.write_bytes(up.getbuffer())
            percorso = str(tmp)
        st.warning("⚠️ Prototipo: su foto/litologie mai viste la generalizzazione è "
                   "debole (vedi tab Limiti). Risultato indicativo.")

    c1, c2, c3 = st.columns(3)
    scomparto = c1.number_input("Lunghezza scomparto (cm) — per la scala", 0.0, 1000.0, 100.0)
    manovra = c2.number_input("Lunghezza manovra (cm) — denominatore RQD (0=auto)", 0.0, 5000.0, 0.0)
    n_file = c3.number_input("N. scomparti attesi (0=auto)", 0, 20, 0)

    if percorso and st.button("▶️ Esegui pipeline", type="primary"):
        from geocore.pipeline import analizza
        with st.spinner("Eseguo la pipeline reale…"):
            res = analizza(percorso, segmenter=get_segmenter(),
                           scomparto_cm=scomparto or None,
                           manovra_cm=manovra or None,
                           n_file=int(n_file) or None)
        overlay = res.pop("_overlay")
        st.image(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB),
                 caption="Verde = pezzo ≥10 cm · Giallo = pezzo <10 cm",
                 use_container_width=True)
        a, b, d = st.columns(3)
        a.metric("RQD cassetta", f"{res['rqd_cassetta']}%" if res['rqd_cassetta'] is not None else "n/d")
        b.metric("Classe di Deere", f"{DEERE_COLORI.get(res['classe_cassetta'],'')} {res['classe_cassetta'] or '—'}")
        d.metric("File rilevate", res["n_file"])
        st.caption(f"Scala: {res['scala_cm_px']} cm/px · soglia 10 cm = "
                   f"{res['soglia_10cm_px']} px · denominatore: {res['denominatore']}")
        st.dataframe([{"fila": f["indice"], "RQD %": f["rqd"], "classe": f["classe"],
                       "n pezzi": f["n_pezzi"], "≥10cm": f["n_integri"]} for f in res["file"]],
                     use_container_width=True)
        st.info(res["disclaimer"])

# ============================ TAB CASI =======================================
with tab_casi:
    st.markdown("Evidenza **validata**: RQD predetto vs **ground-truth** annotato a mano. "
                "Numeri identici alla valutazione della tesi (RQD per manovra, harness §6).")
    if not MANIFEST.exists():
        st.error("Casi non generati. Esegui:  `python -m geocore.demo_cases`")
    else:
        casi = json.loads(MANIFEST.read_text())
        etichette = [f"{c['label']}  ·  {c['tipo']}" for c in casi]
        i = st.selectbox("Caso", range(len(casi)), format_func=lambda i: etichette[i])
        c = casi[i]
        st.image(str(CASI_DIR / Path(c["overlay"]).name),
                 caption="Verde = pezzi ≥10 cm annotati (verità) · Rosso = pezzi del modello",
                 use_container_width=True)
        k1, k2, k3 = st.columns(3)
        k1.metric("RQD predetto", f"{c['rqd_pred']:.0f}%")
        k2.metric("RQD vero (geologo)", f"{c['rqd_gt']:.0f}%")
        k3.metric("Errore", f"{c['err']:.0f} pp",
                  delta="OK" if c["err"] <= 10 else "alto",
                  delta_color="normal" if c["err"] <= 10 else "inverse")
        st.markdown(f"**Classe di Deere** — predetta: {DEERE_COLORI.get(c['classe_pred'],'')} "
                    f"*{c['classe_pred']}* · vera: {DEERE_COLORI.get(c['classe_gt'],'')} *{c['classe_gt']}*")
        if not c["in_distribution"] and c["err"] > 10:
            st.warning("Caso **held-out** con **fallimento**: il modello non rileva i pezzi su "
                       "un sondaggio mai visto. Limite di generalizzazione cross-sito.")
        elif c["in_distribution"]:
            st.success("Caso **in-distribution**: accuratezza alta.")
        else:
            st.info("Caso **held-out**: qui generalizza bene.")

# ========================== TAB METODO =======================================
with tab_metodo:
    st.subheader("Pipeline")
    st.markdown("1. **Rettifica** prospettica (OpenCV) → 2. **File** via texture → "
                "3. **Segmentazione pezzi** YOLO11-seg → 4. **RQD** (soglia 10 cm, Deere).")
    st.subheader("Validazione (held-out Z441, 58 manovre)")
    st.table({"Metodo": ["OpenCV (baseline)", "SAM 2.1 (zero-shot)", "YOLO11-seg"],
              "MAE (pp)": [21.7, 42.2, 34.2], "Correlazione": [-0.12, 0.33, 0.16],
              "Tempo/crop": ["2 ms", "24 s", "150 ms"]})
    st.markdown("**Onestà:** in-distribution YOLO ~5–7 pp; su sondaggio mai visto la "
                "generalizzazione crolla (MAE 34). Il valore del progetto è la "
                "**valutazione rigorosa**, non un numero ottimistico.")

# ========================== TAB LIMITI =======================================
with tab_limiti:
    st.subheader("Cosa NON garantisce")
    st.markdown(
        "- **Generalizzazione cross-sito debole** (es. Z441 392–399 m: vero 93%, predetto 0%).\n"
        "- **Scala fisica**: i 10 cm richiedono marker o lunghezza scomparto nota.\n"
        "- **Naturale vs artificiale**: non distinguibile da foto 2D → giudizio del geologo.\n"
        "- **Recupero < 100%**: denominatore corretto = lunghezza manovra (input manuale).")
    st.error("⚖️ La relazione resta firmata da un **geologo abilitato**. Lo strumento "
             "fornisce misura + candidati, non una decisione automatica.")

st.divider()
st.caption("GeoCore AI Demo v1 · la scheda 'Pipeline live' esegue il codice di produzione; "
           "la scheda 'Casi validati' mostra l'evidenza dell'harness di valutazione.")
