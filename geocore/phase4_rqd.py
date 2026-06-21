#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phase4_rqd.py — Fase 4 (PRODUZIONE): da pezzi rilevati -> RQD + classe di Deere.

QUESTO MODULO NON ESISTEVA. Finora l'RQD viveva DENTRO l'harness di valutazione
(usava il ground-truth TenCm e la profondità dal nome file). Su una foto nuova
non hai né GT né profondità: serve una funzione standalone che, dati i pezzi e
una SCALA, calcoli l'RQD secondo la definizione geologica.

Definizione (ASTM D6032 / Deere):
  RQD = ( Σ lunghezze pezzi INTEGRI ≥ 10 cm  /  lunghezza della MANOVRA ) × 100

Scala (cm/px): obbligatoria per applicare la soglia fisica dei 10 cm.
  - da marker/righello noto, oppure
  - da lunghezza interna nota di uno scomparto: scala = L_scomparto_cm / larghezza_fila_px
Denominatore:
  - 'manovra'  : lunghezza perforata fornita dall'utente (RQD ASTM corretto)
  - 'recupero' : Σ lunghezze delle file (fallback se la manovra non è nota; assume
                 la fila piena di carota -> valore SOLO indicativo, lo dichiariamo)
"""
from __future__ import annotations

SOGLIA_CM = 10.0


def classe_deere(rqd: float) -> str:
    for soglia, nome in [(25, "molto scadente"), (50, "scadente"),
                         (75, "discreto"), (90, "buono"), (1e9, "ottimo")]:
        if rqd < soglia:
            return nome
    return "ottimo"


def soglia_px(scala_cm_px: float, soglia_cm: float = SOGLIA_CM) -> float:
    """10 cm espressi in pixel data la scala."""
    return soglia_cm / scala_cm_px


def rqd_da_pezzi(larghezze_px: list[float],
                 scala_cm_px: float | None,
                 manovra_cm: float | None = None,
                 lunghezza_file_px: float | None = None,
                 soglia_cm: float = SOGLIA_CM) -> dict:
    """Calcola l'RQD da una lista di larghezze di pezzi (px), sx->dx.

    Ritorna dict con: rqd, classe, denom_mode, n_pezzi, n_integri, pezzi_cm,
    avviso. Se scala_cm_px è None -> RQD non calcolabile (manca la scala).
    """
    if scala_cm_px is None:
        return {"rqd": None, "classe": None, "denom_mode": None,
                "n_pezzi": len(larghezze_px), "n_integri": None, "pezzi_cm": None,
                "avviso": "Scala assente: impossibile applicare la soglia dei 10 cm. "
                          "Fornire scala cm/px o lunghezza nota di uno scomparto."}

    pezzi_cm = [round(w * scala_cm_px, 1) for w in larghezze_px]
    integri = [L for L in pezzi_cm if L >= soglia_cm]
    numeratore_cm = sum(integri)

    avviso = None
    if manovra_cm and manovra_cm > 0:
        denom_cm = manovra_cm
        denom_mode = "manovra"
    elif lunghezza_file_px is not None:
        denom_cm = lunghezza_file_px * scala_cm_px
        denom_mode = "recupero"
        avviso = ("Denominatore = lunghezza delle file (assume recupero ~100%): "
                  "valore indicativo. Per RQD ASTM fornire la lunghezza della manovra.")
    else:
        return {"rqd": None, "classe": None, "denom_mode": None,
                "n_pezzi": len(pezzi_cm), "n_integri": len(integri), "pezzi_cm": pezzi_cm,
                "avviso": "Denominatore assente: fornire manovra_cm o lunghezza_file_px."}

    rqd = max(0.0, min(100.0, 100.0 * numeratore_cm / denom_cm)) if denom_cm > 0 else 0.0
    return {"rqd": round(rqd, 1), "classe": classe_deere(rqd), "denom_mode": denom_mode,
            "n_pezzi": len(pezzi_cm), "n_integri": len(integri),
            "pezzi_cm": pezzi_cm, "numeratore_cm": round(numeratore_cm, 1),
            "denom_cm": round(denom_cm, 1), "avviso": avviso}
