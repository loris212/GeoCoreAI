#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline.py — orchestratore GeoCore Demo v1: foto -> RQD + overlay.

Flusso: carica(EXIF) -> rettifica -> file -> [per fila] segmenta pezzi (YOLO)
-> scala cm/px -> RQD per fila e aggregato -> dict risultato + immagine overlay.

DISCLAIMER incorporato: strumento di assistenza. La validazione su sondaggio
held-out (Z441) ha dato MAE ~34 pp con crollo della generalizzazione cross-sito:
i numeri vanno verificati da un geologo. Vedi REPORT_spike_3way.md.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import cv2

from geocore.phase1_rows import estrai_file
from geocore.phase2_segment import PieceSegmenter
from geocore.phase4_rqd import rqd_da_pezzi, soglia_px, classe_deere

DISCLAIMER = ("Strumento di assistenza, NON sostituisce il geologo. "
              "Validazione held-out (Z441): MAE ~34 pp, generalizzazione cross-sito debole. "
              "Verificare ogni valore.")


def analizza(percorso: str,
             segmenter: PieceSegmenter | None = None,
             scala_cm_px: float | None = None,
             scomparto_cm: float | None = None,
             manovra_cm: float | None = None,
             n_file: int | None = None) -> dict:
    """Analizza una foto di cassetta e ritorna risultato + overlay (np.ndarray BGR)."""
    seg = segmenter or PieceSegmenter()
    warp, rettificata, file_ = estrai_file(percorso, n_file=n_file)
    larg_warp = warp.shape[1]

    # scala cm/px: esplicita, oppure da lunghezza nota dello scomparto, altrimenti None
    if scala_cm_px is None and scomparto_cm and larg_warp > 0:
        scala_cm_px = scomparto_cm / larg_warp
    thr_px = soglia_px(scala_cm_px) if scala_cm_px else 0.0

    vis = warp.copy()
    file_out = []
    tot_integri_cm = 0.0
    tot_file_px = 0
    for f in file_:
        banda = f["banda"]
        pezzi = seg.segment(banda, min_width_px=0.0)   # tutti, soglia applicata in Fase 4
        larghezze = [p["larghezza_px"] for p in pezzi]
        r = rqd_da_pezzi(larghezze, scala_cm_px,
                         manovra_cm=None,                 # per fila usa il recupero
                         lunghezza_file_px=banda.shape[1])
        # disegno pezzi: integri (verde) vs <10cm (giallo)
        for p in pezzi:
            integro = scala_cm_px and (p["larghezza_px"] * scala_cm_px >= 10.0)
            col = (0, 180, 0) if integro else (0, 200, 220)
            cv2.rectangle(vis, (p["x0"], f["y0"] + p["y0"]),
                          (p["x1"], f["y0"] + p["y1"]), col, 3)
        etich = f"fila {f['indice']}: RQD={r['rqd']}% ({r['classe']})" if r["rqd"] is not None \
                else f"fila {f['indice']}: scala assente"
        cv2.putText(vis, etich, (8, f["y0"] + 26), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 0, 255), 2)
        if scala_cm_px:
            tot_integri_cm += sum(L for L in r["pezzi_cm"] if L >= 10.0)
            tot_file_px += banda.shape[1]
        file_out.append({"indice": f["indice"], **r})

    # RQD aggregato della cassetta
    if scala_cm_px:
        if manovra_cm and manovra_cm > 0:
            denom_cm, denom_mode = manovra_cm, "manovra"
        else:
            denom_cm, denom_mode = tot_file_px * scala_cm_px, "recupero"
        rqd_tot = round(max(0.0, min(100.0, 100.0 * tot_integri_cm / denom_cm)), 1) if denom_cm else 0.0
        classe_tot = classe_deere(rqd_tot)
    else:
        rqd_tot, classe_tot, denom_mode = None, None, None

    return {
        "sorgente": str(percorso),
        "rettifica_applicata": rettificata,
        "n_file": len(file_),
        "scala_cm_px": round(scala_cm_px, 4) if scala_cm_px else None,
        "soglia_10cm_px": round(thr_px, 1) if thr_px else None,
        "rqd_cassetta": rqd_tot,
        "classe_cassetta": classe_tot,
        "denominatore": denom_mode,
        "file": file_out,
        "disclaimer": DISCLAIMER,
        "_overlay": vis,
    }
