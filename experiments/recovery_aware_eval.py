#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
recovery_aware_eval.py  (Settimana 1 — de-confondere la misura)
===============================================================
Confronto BEFORE (soglia da L/sumW, assume recupero+riempimento 100%) vs
AFTER (soglia da L/P, P = carota occupata) sullo STESSO test Z441, stesso GT,
stesso criterio dei 10 cm. Cambia SOLO la base in px della scala della soglia.

Domande a cui risponde (oltre al MAE medio):
  1. I 5 casi peggiori: prima e dopo.
  2. Quanti casi "GT alto -> Pred ~0" vengono recuperati.
  3. Falsificazione: se i catastrofici NON migliorano -> il collo di bottiglia
     e' la GENERALIZZAZIONE DEL MODELLO, non la soglia.

NIENTE nuovi modelli, nessun nuovo dataset, criterio di valutazione invariato.
"""
from __future__ import annotations
from pathlib import Path
import csv
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from spike_models import (DetectorCV, DetectorYOLO, valuta_detector, metriche,
                          YOLO_BEST, TEST_SOND)
from rqd_baseline import costruisci_manovre, classe_deere

OUT = Path(__file__).resolve().parent / "out"
HIGH_GT = 75.0     # roccia buona/ottima
PRED0 = 5.0        # "predice ~0"


def key(r):
    return (r["prof_in"], r["prof_fin"])


def run(det, test):
    full, _, _ = valuta_detector(test, det, soglia_mode="full")
    reco, _, _ = valuta_detector(test, det, soglia_mode="recovery")
    return {key(r): r for r in full}, {key(r): r for r in reco}


def gt_invariante(full, reco):
    """Verifica byte-a-byte che il GT non sia cambiato (perno anti-manipolazione)."""
    diffs = [(k, full[k]["rqd_gt"], reco[k]["rqd_gt"])
             for k in full if abs(full[k]["rqd_gt"] - reco[k]["rqd_gt"]) > 1e-9]
    return diffs


def sezione(nome, full, reco):
    fk = sorted(full.keys())
    gt = np.array([full[k]["rqd_gt"] for k in fk])
    pf = np.array([full[k]["rqd_pred"] for k in fk])
    pr = np.array([reco[k]["rqd_pred"] for k in fk])
    mf, mr = metriche(list(full.values())), metriche(list(reco.values()))

    print(f"\n{'='*78}\n{nome}\n{'='*78}")
    # --- GT invariance ---
    diffs = gt_invariante(full, reco)
    print(f"[GT invariato] manovre con GT diverso prima/dopo: {len(diffs)} "
          f"{'(OK: GT identico)' if not diffs else '*** GT CAMBIATO! ***'}")

    # --- MAE / corr globali ---
    print(f"[Globale]  MAE  {mf['mae']:5.1f} -> {mr['mae']:5.1f}   "
          f"(Δ {mr['mae']-mf['mae']:+.1f})")
    print(f"           corr {mf['corr']:+5.2f} -> {mr['corr']:+5.2f}   "
          f"classe {mf['classe']:.0f}%->{mr['classe']:.0f}%   "
          f"entro5 {mf['entro5']:.0f}%->{mr['entro5']:.0f}%   "
          f"MAE_poor {mf['mae_poor']:.1f}->{mr['mae_poor']:.1f}")

    # --- 1) 5 casi peggiori (ordinati per err BEFORE) ---
    worst = sorted(fk, key=lambda k: full[k]["err"], reverse=True)[:5]
    print(f"\n[1) 5 CASI PEGGIORI (per err BEFORE) — prima -> dopo]")
    print(f"  {'manovra':14s} {'GT':>6s} | {'Pred_b':>7s} {'err_b':>6s} | "
          f"{'Pred_a':>7s} {'err_a':>6s} | {'sogliaΔ':>9s}")
    for k in worst:
        rb, ra = full[k], reco[k]
        print(f"  {rb['prof_in']:.0f}-{rb['prof_fin']:.0f}m".ljust(16) +
              f"{rb['rqd_gt']:6.1f} | {rb['rqd_pred']:7.1f} {rb['err']:6.1f} | "
              f"{ra['rqd_pred']:7.1f} {ra['err']:6.1f} | "
              f"{rb['soglia_px']:.0f}->{ra['soglia_px']:.0f}")

    # --- 2) casi "GT alto -> Pred ~0": quanti recuperati ---
    cata = [k for k in fk if full[k]["rqd_gt"] >= HIGH_GT and full[k]["rqd_pred"] <= PRED0]
    rec = [k for k in cata if reco[k]["rqd_pred"] > PRED0]
    print(f"\n[2) Casi catastrofici 'GT>={HIGH_GT:.0f} & Pred<={PRED0:.0f}']")
    print(f"  totali BEFORE: {len(cata)}   recuperati DOPO (Pred>{PRED0:.0f}): {len(rec)}")
    for k in cata:
        rb, ra = full[k], reco[k]
        tag = "RECUPERATO" if k in rec else "invariato"
        print(f"   {rb['prof_in']:.0f}-{rb['prof_fin']:.0f}m  GT={rb['rqd_gt']:.0f}  "
              f"Pred {rb['rqd_pred']:.0f}->{ra['rqd_pred']:.0f}  [{tag}]")

    # --- 3) verdetto falsificazione ---
    print(f"\n[3) VERDETTO]")
    if len(cata) == 0:
        print("  Nessun caso catastrofico nel BEFORE: test non applicabile.")
    elif len(rec) == 0:
        print("  ❌ IPOTESI SOGLIA FALSIFICATA: 0/{} catastrofici recuperati.".format(len(cata)))
        print("     Il collo di bottiglia NON e' la soglia -> e' GENERALIZZAZIONE DEL MODELLO.")
    elif len(rec) == len(cata):
        print(f"  ✅ Ipotesi soglia CONFERMATA: {len(rec)}/{len(cata)} recuperati.")
        print("     Una quota dei catastrofici era ARTEFATTO DI MISURA, non modello.")
    else:
        print(f"  ⚠️ MISTO: {len(rec)}/{len(cata)} recuperati.")
        print("     Parte era misura (soglia), parte resta modello/generalizzazione.")
    return mf, mr, len(cata), len(rec)


def main():
    manovre, _ = costruisci_manovre()
    test = {k: v for k, v in manovre.items() if k[0] == TEST_SOND}
    print(f"Test set (held-out {TEST_SOND}): {len(test)} manovre")
    print("Modifica: soglia_px da L/sumW (full) a L/P (recovery). GT e den invariati.")

    rows_csv = []
    cv = DetectorCV()
    cvf, cvr = run(cv, test)
    mf, mr, c, rc = sezione("OpenCV (baseline)", cvf, cvr)
    rows_csv.append(("OpenCV", mf["mae"], mr["mae"], mf["corr"], mr["corr"], c, rc))

    if YOLO_BEST.exists():
        yo = DetectorYOLO()
        yf, yr = run(yo, test)
        mf, mr, c, rc = sezione("YOLO11-seg (addestrato)", yf, yr)
        rows_csv.append(("YOLO-seg", mf["mae"], mr["mae"], mf["corr"], mr["corr"], c, rc))
    else:
        print("[!] Pesi YOLO non trovati — salto YOLO.")

    with open(OUT / "recovery_aware_results.csv", "w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["detector", "mae_full", "mae_recovery", "corr_full",
                    "corr_recovery", "catastrofici", "recuperati"])
        for r in rows_csv:
            w.writerow([r[0], f"{r[1]:.2f}", f"{r[2]:.2f}", f"{r[3]:.3f}",
                        f"{r[4]:.3f}", r[5], r[6]])
    print(f"\nCSV: {OUT/'recovery_aware_results.csv'}")


if __name__ == "__main__":
    main()
