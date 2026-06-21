#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
demo_cases.py — genera i CASI CURATI VALIDATI per la demo ai geologi.

Per ogni manovra selezionata produce: overlay (GT verde vs predetto rosso),
RQD predetto, RQD ground-truth (dai poligoni TenCm annotati), errore, classe
di Deere. I numeri sono IDENTICI a quelli della valutazione della tesi
(stesso harness) -> la demo mostra evidenza, non una promessa.

Selezione curata e ONESTA: casi in-distribution (forti) + 1 successo held-out
+ 1 fallimento held-out (per mostrare i limiti, non nasconderli).

Output cache in geocore/demo_cases_out/ (rigenerabile).
"""
from __future__ import annotations
from pathlib import Path
import json
import sys
import numpy as np
import cv2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "experiments"))

from spike_models import (costruisci_manovre, DetectorYOLO, valuta_detector,  # noqa: E402
                          x_extent, TENCM_LABELS)
from geocore.phase4_rqd import classe_deere  # noqa: E402

CACHE = HERE / "demo_cases_out"


def _soglia_px(key, crops):
    """Replica il calcolo di soglia (full mode) per disegnare i pezzi >=10cm."""
    sond, a, b = key
    L_cm = (b - a) * 100.0
    sumW = 0
    for jf, jpg in crops:
        try:
            import json as _j
            d = _j.load(open(jf, encoding="utf-8"))
            sumW += d.get("imageWidth") or 0
        except Exception:
            pass
    return (10.0 / (L_cm / sumW)) if sumW else 0.0


def _render(key, crops, detector, riga) -> Path:
    """Disegna il 1° crop: GT TenCm (verde) vs pezzi predetti >=10cm (rosso)."""
    import json as _j
    soglia = _soglia_px(key, crops)
    jf, jpg = crops[0]
    d = _j.load(open(jf, encoding="utf-8"))
    img = cv2.imread(str(jpg))
    vis = img.copy(); H = vis.shape[0]
    for s in d.get("shapes", []):
        if s["label"].lower() in TENCM_LABELS:
            cv2.polylines(vis, [np.array(s["points"], np.int32)], True, (0, 170, 0), 4)
    for x0, x1 in detector(img, soglia):
        cv2.rectangle(vis, (x0, 6), (x1, H - 6), (0, 0, 255), 4)
    banner = np.full((46, vis.shape[1], 3), 255, np.uint8)
    cv2.putText(banner, f"GT(verde)={riga['rqd_gt']:.0f}%  PRED(rosso)={riga['rqd_pred']:.0f}%"
                f"  err={riga['err']:.0f}pp", (12, 32),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    out = CACHE / f"case_{key[0]}_{key[1]:.0f}-{key[2]:.0f}m.png"
    cv2.imwrite(str(out), np.vstack([banner, vis]))
    return out


def seleziona(manovre) -> list[tuple]:
    """Lista curata e onesta di chiavi manovra."""
    z441 = {k for k in manovre if k[0] == "Z441"}
    altri = sorted(k for k in manovre if k[0] != "Z441")
    # in-distribution: prime manovre non-Z441 con >=2 crop
    indist = [k for k in altri if len(manovre[k]) >= 2][:3]
    # held-out: un successo noto e un fallimento noto (se presenti), altrimenti fallback
    noti_ok = [k for k in z441 if abs(k[1] - 295.0) < 1 or abs(k[1] - 267.0) < 1]
    noti_ko = [k for k in z441 if abs(k[1] - 316.0) < 1 or abs(k[1] - 392.0) < 1]
    sel = indist + noti_ok[:1] + noti_ko[:1]
    return sel or list(manovre)[:4]


def build(force: bool = False) -> list[dict]:
    CACHE.mkdir(exist_ok=True)
    manifest_path = CACHE / "manifest.json"
    if manifest_path.exists() and not force:
        return json.loads(manifest_path.read_text())

    manovre, _ = costruisci_manovre()
    keys = seleziona(manovre)
    det = DetectorYOLO()
    casi = []
    for k in keys:
        sub = {k: manovre[k]}
        righe, _, _ = valuta_detector(sub, det, soglia_mode="full")
        if not righe:
            continue
        r = righe[0]
        png = _render(k, manovre[k], det, r)
        in_dist = k[0] != "Z441"
        casi.append({
            "label": f"{k[0]} {k[1]:.0f}-{k[2]:.0f} m",
            "in_distribution": in_dist,
            "tipo": "in-distribution" if in_dist else "held-out (sondaggio mai visto)",
            "overlay": str(png.relative_to(ROOT)),
            "rqd_pred": r["rqd_pred"], "rqd_gt": r["rqd_gt"], "err": r["err"],
            "classe_pred": classe_deere(r["rqd_pred"]),
            "classe_gt": classe_deere(r["rqd_gt"]),
        })
    manifest_path.write_text(json.dumps(casi, indent=2, ensure_ascii=False))
    return casi


if __name__ == "__main__":
    casi = build(force=True)
    print(f"[i] Casi curati generati: {len(casi)}")
    for c in casi:
        print(f"  {c['label']:18s} [{c['tipo']:35s}] "
              f"pred={c['rqd_pred']:5.1f}  gt={c['rqd_gt']:5.1f}  err={c['err']:4.1f}")
    print(f"[i] Cache: {CACHE}")
