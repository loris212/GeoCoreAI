#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spike_models.py  (SPIKE — confronto OpenCV vs SAM vs YOLO-seg)
==============================================================
Stesso identico harness di rqd_baseline.py (§6): stesso ground-truth (poligoni
TenCm annotati a mano), stesso calcolo RQD recovery-based in rapporto di pixel,
stesse manovre. CAMBIA SOLO il detector dei pezzi.

Test set: SOLO il sondaggio Z441 (held-out, mai visto da YOLO in training) ->
confronto onesto e apples-to-apples per tutti e tre i detector.

I detector espongono la stessa firma del baseline:  detector(img, soglia_px) -> [(x0,x1)]
"""
from __future__ import annotations
from pathlib import Path
import time, json, csv
import numpy as np
import cv2

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
# RIUSO ESATTO del harness §6 (nessuna modifica al metodo ne' al GT)
from rqd_baseline import (costruisci_manovre, union_len, x_extent,
                          rileva_pezzi_cv, classe_deere, TENCM_LABELS)

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
TEST_SOND = "Z441"
SAM_CKPT = "sam2.1_t.pt"            # tiny = piu' veloce per lo spike
YOLO_BEST = HERE / "yolo_runs/piece_seg/weights/best.pt"
COVER_V = 0.40                       # un pezzo copre >=40% dell'altezza del canale


# --------------------------------------------------------------------------- #
# Detector 2: SAM 2.1 (zero-shot, 'segment everything') — caricato UNA volta
# --------------------------------------------------------------------------- #
class DetectorSAM:
    name = "SAM2.1 (zero-shot)"
    def __init__(self):
        from ultralytics import SAM
        self.model = SAM(SAM_CKPT)
    def __call__(self, img, soglia_px):
        H = img.shape[0]
        res = self.model(img, verbose=False, device="mps")
        if not res or res[0].masks is None:
            return []
        masks = res[0].masks.data.cpu().numpy() > 0.5
        out = []
        for m in masks:
            ys, xs = np.where(m)
            if len(xs) == 0:
                continue
            if (ys.max() - ys.min()) < COVER_V * H:     # scarta non-pezzi (cartellini, slivers)
                continue
            x0, x1 = int(xs.min()), int(xs.max())
            if (x1 - x0) >= soglia_px:
                out.append((x0, x1))
        return out


# --------------------------------------------------------------------------- #
# Detector 3: YOLO11-seg addestrato sui TenCm (split per sondaggio)
# --------------------------------------------------------------------------- #
class DetectorYOLO:
    name = "YOLO11-seg (addestrato)"
    def __init__(self):
        from ultralytics import YOLO
        self.model = YOLO(str(YOLO_BEST))
    def __call__(self, img, soglia_px):
        H = img.shape[0]
        res = self.model(img, verbose=False, device="mps", retina_masks=True)
        if not res or res[0].masks is None:
            return []
        masks = res[0].masks.data.cpu().numpy() > 0.5
        out = []
        for m in masks:
            if m.shape != img.shape[:2]:
                m = cv2.resize(m.astype(np.uint8), (img.shape[1], img.shape[0])) > 0
            ys, xs = np.where(m)
            if len(xs) == 0:
                continue
            if (ys.max() - ys.min()) < COVER_V * H:
                continue
            x0, x1 = int(xs.min()), int(xs.max())
            if (x1 - x0) >= soglia_px:
                out.append((x0, x1))
        return out


# --------------------------------------------------------------------------- #
# VALUTAZIONE — copia FEDELE di rqd_baseline.valuta(), detector iniettato.
# GT (num_gt) identico per tutti i detector: il ground-truth NON cambia.
# --------------------------------------------------------------------------- #
def valuta_detector(manovre_test, detector):
    righe = []
    t_det = 0.0
    n_crop = 0
    for key, crops in manovre_test.items():
        sond, a, b = key
        L_cm = (b - a) * 100.0
        infos, sumW = [], 0
        for jf, jpg in crops:
            try:
                d = json.load(open(jf, encoding="utf-8"))
            except Exception:
                continue
            W = d.get("imageWidth")
            img = cv2.imread(str(jpg)) if jpg.exists() else None
            if W is None and img is not None:
                W = img.shape[1]
            if not W:
                continue
            tencm = [x_extent(s) for s in d.get("shapes", [])
                     if s["label"].lower() in TENCM_LABELS]
            infos.append((W, tencm, img))
            sumW += W
        if not infos or sumW == 0:
            continue
        scala_cm_px = L_cm / sumW
        soglia_px = 10.0 / scala_cm_px
        num_gt = num_pred = den = 0.0
        crop_ok = 0
        for W, tencm, img in infos:
            den += W
            num_gt += union_len(tencm)                       # GT INVARIATO
            if img is not None:
                t0 = time.perf_counter()
                pezzi = detector(img, soglia_px)
                t_det += time.perf_counter() - t0
                n_crop += 1
                num_pred += union_len([(p[0], p[1]) for p in pezzi])
                crop_ok += 1
        if crop_ok != len(infos):
            continue
        rqd_gt = 100.0 * num_gt / den
        rqd_pred = 100.0 * num_pred / den
        righe.append(dict(sondaggio=sond, prof_in=a, prof_fin=b,
                          rqd_gt=round(rqd_gt, 1), rqd_pred=round(rqd_pred, 1),
                          err=round(abs(rqd_gt - rqd_pred), 1)))
    return righe, t_det, n_crop


def metriche(righe):
    gt = np.array([r["rqd_gt"] for r in righe])
    pr = np.array([r["rqd_pred"] for r in righe])
    err = np.abs(gt - pr)
    return dict(
        n=len(righe), mae=float(err.mean()),
        entro5=float(100 * np.mean(err <= 5)),
        entro10=float(100 * np.mean(err <= 10)),
        classe=float(100 * np.mean([classe_deere(g) == classe_deere(p)
                                    for g, p in zip(gt, pr)])),
        corr=float(np.corrcoef(gt, pr)[0, 1]) if len(gt) > 1 and pr.std() > 0 else float("nan"),
        mae_poor=float(err[gt < 50].mean()) if (gt < 50).any() else float("nan"),
    )


def overlay(case_righe, manovre_test, detector, tag):
    """Salva l'overlay del 1° crop: GT(verde) vs detector(rosso)."""
    for r in case_righe:
        key = (r["sondaggio"], r["prof_in"], r["prof_fin"])
        crops = manovre_test.get(key)
        if not crops:
            continue
        sumW = 0; primo = None
        for jf, jpg in crops:
            d = json.load(open(jf, encoding="utf-8"))
            W = d.get("imageWidth")
            if not W:
                continue
            sumW += W
            if primo is None and jpg.exists():
                primo = (jpg, d, W)
        if primo is None:
            continue
        jpg, d, W = primo
        img = cv2.imread(str(jpg))
        if img is None:
            continue
        scala = (r["prof_fin"] - r["prof_in"]) * 100.0 / sumW
        soglia_px = 10.0 / scala
        vis = img.copy(); H = vis.shape[0]
        for s in d.get("shapes", []):
            if s["label"].lower() in TENCM_LABELS:
                cv2.polylines(vis, [np.array(s["points"], np.int32)], True, (0, 180, 0), 3)
        for x0, x1 in detector(img, soglia_px):
            cv2.rectangle(vis, (x0, 6), (x1, H - 6), (0, 0, 255), 3)
        banner = np.full((42, vis.shape[1], 3), 255, np.uint8)
        cv2.putText(banner, f"[{detector.name}] {r['sondaggio']} {r['prof_in']}-{r['prof_fin']}m "
                    f"GT={r['rqd_gt']:.0f}% PRED={r['rqd_pred']:.0f}% err={r['err']:.0f}pp",
                    (10, 29), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        fn = OUT / f"cmp_{tag}_{detector.name.split()[0].replace('.','').replace('2','2')}.png"
        cv2.imwrite(str(fn), np.vstack([banner, vis]))


class DetectorCV:
    name = "OpenCV (baseline)"
    def __call__(self, img, soglia_px):
        return rileva_pezzi_cv(img, soglia_px)


def main():
    manovre, _ = costruisci_manovre()
    test = {k: v for k, v in manovre.items() if k[0] == TEST_SOND}
    print(f"Test set (held-out {TEST_SOND}): {len(test)} manovre\n")

    detectors = [DetectorCV()]
    try:
        detectors.append(DetectorSAM())
    except Exception as e:
        print(f"[!] SAM non disponibile: {e}")
    if YOLO_BEST.exists():
        try:
            detectors.append(DetectorYOLO())
        except Exception as e:
            print(f"[!] YOLO non disponibile: {e}")
    else:
        print(f"[!] Pesi YOLO non trovati ({YOLO_BEST}) — addestra prima con prep_e_train_yolo.py")

    risultati = {}
    righe_per_det = {}
    for det in detectors:
        print(f"--- {det.name} ---")
        righe, t_det, n_crop = valuta_detector(test, det)
        m = metriche(righe)
        m["t_tot"] = t_det
        m["t_crop"] = t_det / max(1, n_crop)
        risultati[det.name] = m
        righe_per_det[det.name] = righe
        print(f"    MAE={m['mae']:.1f}  corr={m['corr']:+.2f}  classe={m['classe']:.0f}%  "
              f"entro5={m['entro5']:.0f}%  MAE_poor={m['mae_poor']:.1f}  "
              f"t={m['t_tot']:.1f}s ({m['t_crop']*1000:.0f}ms/crop)\n")

    # esempi: scegli la manovra a GT piu' basso e a GT piu' alto (comune a tutti)
    base = righe_per_det[detectors[0].name]
    case_low = min(base, key=lambda r: r["rqd_gt"])
    case_high = max(base, key=lambda r: r["rqd_gt"])
    for det in detectors:
        rr = righe_per_det[det.name]
        low = [r for r in rr if (r["prof_in"], r["prof_fin"]) == (case_low["prof_in"], case_low["prof_fin"])]
        high = [r for r in rr if (r["prof_in"], r["prof_fin"]) == (case_high["prof_in"], case_high["prof_fin"])]
        overlay(low, test, det, "poor")
        overlay(high, test, det, "good")

    # tabella finale
    print("=" * 84)
    print(f"{'Detector':24s} {'MAE':>6s} {'corr':>6s} {'classe%':>8s} "
          f"{'entro5%':>8s} {'MAE_poor':>9s} {'t/crop':>9s}")
    print("-" * 84)
    for name, m in risultati.items():
        print(f"{name:24s} {m['mae']:6.1f} {m['corr']:+6.2f} {m['classe']:8.0f} "
              f"{m['entro5']:8.0f} {m['mae_poor']:9.1f} {m['t_crop']*1000:7.0f}ms")
    print("=" * 84)

    with open(OUT / "spike_results.csv", "w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["detector", "n", "mae", "corr", "classe_pct", "entro5_pct",
                    "entro10_pct", "mae_poor", "t_tot_s", "t_crop_ms"])
        for name, m in risultati.items():
            w.writerow([name, m["n"], f"{m['mae']:.2f}", f"{m['corr']:.3f}",
                        f"{m['classe']:.0f}", f"{m['entro5']:.0f}", f"{m['entro10']:.0f}",
                        f"{m['mae_poor']:.2f}", f"{m['t_tot']:.1f}", f"{m['t_crop']*1000:.0f}"])
    print(f"\nCSV: {OUT/'spike_results.csv'}  | overlay: cmp_*.png")


if __name__ == "__main__":
    main()
