#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
borehole_breakdown.py  (Settimana 1 — Z441-specifico vs sistemico?)
===================================================================
Disaggrega per SONDAGGIO i risultati del modello YOLO ESISTENTE, con le
STESSE metriche di sempre (valuta_detector, soglia_mode='full', GT invariato).

ONESTÀ METODOLOGICA (cruciale):
  Il modello e' stato addestrato su TUTTI i sondaggi TRANNE Z441.
  -> Z441 e' l'UNICO realmente HELD-OUT.
  -> Tutti gli altri sondaggi sono IN-SAMPLE (erano nel training) = leakage.
  Quindi questo NON e' borehole-CV vera (servirebbe ri-addestrare un modello
  per fold). E' una disaggregazione che misura il GAP train-vs-heldout.

Nessun nuovo modello, training invariato, metriche invariate.
"""
from __future__ import annotations
from pathlib import Path
import csv
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from spike_models import DetectorYOLO, DetectorCV, valuta_detector, metriche, YOLO_BEST
from rqd_baseline import costruisci_manovre

OUT = Path(__file__).resolve().parent / "out"
HELD_OUT = "Z441"          # l'unico sondaggio fuori dal training


def per_borehole(detector, manovre):
    boreholes = sorted({k[0] for k in manovre})
    rows = []
    for b in boreholes:
        sub = {k: v for k, v in manovre.items() if k[0] == b}
        righe, _, _ = valuta_detector(sub, detector, soglia_mode="full")
        if not righe:
            continue
        m = metriche(righe)
        rows.append(dict(borehole=b, n=len(righe), mae=m["mae"], corr=m["corr"],
                         split="HELD-OUT" if b == HELD_OUT else "in-sample"))
    return rows


def riassunto(rows, etichetta):
    insample = [r for r in rows if r["split"] == "in-sample"]
    held = [r for r in rows if r["split"] == "HELD-OUT"]
    # statistiche su sondaggi con n>=2 (MAE per-sondaggio piu' stabile)
    stabili = [r for r in insample if r["n"] >= 2]
    maes_is = np.array([r["mae"] for r in insample])
    maes_stab = np.array([r["mae"] for r in stabili])

    print(f"\n{'='*70}\n{etichetta}\n{'='*70}")
    print(f"{'sondaggio':10s} {'n':>3s} {'MAE':>7s} {'corr':>7s}  split")
    for r in sorted(rows, key=lambda x: (x["split"] != "HELD-OUT", x["mae"])):
        c = f"{r['corr']:+.2f}" if not np.isnan(r["corr"]) else "  n/d"
        print(f"{r['borehole']:10s} {r['n']:3d} {r['mae']:7.1f} {c:>7s}  {r['split']}")

    print(f"\n--- DISTRIBUZIONE ---")
    if held:
        print(f"HELD-OUT (Z441):           MAE {held[0]['mae']:.1f}  corr {held[0]['corr']:+.2f}  (n={held[0]['n']})")
    print(f"IN-SAMPLE (tutti):         media MAE {maes_is.mean():.1f}  std {maes_is.std():.1f}  (n_sond={len(insample)})")
    if len(maes_stab):
        print(f"IN-SAMPLE (n>=2 manovre):  media MAE {maes_stab.mean():.1f}  std {maes_stab.std():.1f}  (n_sond={len(stabili)})")
    if insample:
        best = min(insample, key=lambda r: r["mae"])
        worst = max(insample, key=lambda r: r["mae"])
        print(f"Miglior caso in-sample:    {best['borehole']}  MAE {best['mae']:.1f} (n={best['n']})")
        print(f"Peggior caso in-sample:    {worst['borehole']}  MAE {worst['mae']:.1f} (n={worst['n']})")
    # gap generalizzazione
    if held and len(maes_stab):
        gap = held[0]["mae"] - maes_stab.mean()
        print(f"\nGAP generalizzazione = MAE(held-out) - MAE(in-sample n>=2) = "
              f"{held[0]['mae']:.1f} - {maes_stab.mean():.1f} = {gap:+.1f} pp")
    return rows


def main():
    manovre, _ = costruisci_manovre()
    print(f"Manovre totali: {len(manovre)}  | sondaggi: {len({k[0] for k in manovre})}")
    print(f"HELD-OUT reale: {HELD_OUT} (unico fuori dal training)")

    all_rows = []
    if YOLO_BEST.exists():
        rows = per_borehole(DetectorYOLO(), manovre)
        riassunto(rows, "YOLO11-seg (addestrato) — per sondaggio")
        for r in rows:
            all_rows.append(("YOLO", *r.values()))
    rows_cv = per_borehole(DetectorCV(), manovre)
    riassunto(rows_cv, "OpenCV (baseline) — per sondaggio")
    for r in rows_cv:
        all_rows.append(("OpenCV", *r.values()))

    with open(OUT / "borehole_breakdown.csv", "w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["detector", "borehole", "n", "mae", "corr", "split"])
        for r in all_rows:
            w.writerow([r[0], r[1], r[2], f"{r[3]:.2f}", f"{r[4]:.3f}", r[5]])
    print(f"\nCSV: {OUT/'borehole_breakdown.csv'}")


if __name__ == "__main__":
    main()
