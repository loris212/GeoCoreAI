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
OCC_FRAC = 0.18                      # regola FISSA: colonna = carota se texture > 18% del max


def occupied_span(img) -> int:
    """Larghezza (px) realmente occupata dalla carota in un crop, regola FISSA.
    Stessa primitiva texture del baseline: colonne con gradiente > OCC_FRAC*max.
    Serve a stimare P per la scala recovery-aware (toglie margini/cartellini/vuoti
    dalla mappatura lunghezza-perforata -> pixel). NON tocca il ground-truth."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    col = cv2.magnitude(gx, gy).mean(axis=0)
    k = max(3, gray.shape[1] // 200) | 1
    col = cv2.GaussianBlur(col.reshape(1, -1), (k, 1), 0).ravel()
    if col.max() <= 0:
        return 0
    return int((col > OCC_FRAC * col.max()).sum())


# --------------------------------------------------------------------------- #
# Detector 2: SAM 2.1 (zero-shot, 'segment everything') — caricato UNA volta
# --------------------------------------------------------------------------- #
class DetectorSAM:
    name = "SAM2.1 (zero-shot)"
    MAXW = 640                       # downscale: SAM auto full-res e' impraticabile
    def __init__(self):
        from ultralytics import SAM
        self.model = SAM(SAM_CKPT)
    def __call__(self, img, soglia_px):
        H0, W0 = img.shape[:2]
        sc = self.MAXW / W0 if W0 > self.MAXW else 1.0
        small = (cv2.resize(img, (int(W0 * sc), max(8, int(H0 * sc))))
                 if sc < 1.0 else img)
        Hs = small.shape[0]
        res = self.model(small, verbose=False, device="mps", imgsz=self.MAXW)
        if not res or res[0].masks is None:
            return []
        masks = res[0].masks.data.cpu().numpy() > 0.5
        out = []
        for m in masks:
            if m.shape != small.shape[:2]:
                m = cv2.resize(m.astype(np.uint8), (small.shape[1], Hs)) > 0
            ys, xs = np.where(m)
            if len(xs) == 0:
                continue
            if (ys.max() - ys.min()) < COVER_V * Hs:     # scarta non-pezzi (cartellini, slivers)
                continue
            # rimappa le x alla risoluzione originale (soglia_px e' in px originali)
            x0, x1 = int(xs.min() / sc), int(xs.max() / sc)
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
def valuta_detector(manovre_test, detector, soglia_mode="full"):
    """soglia_mode='full'      -> scala = L_cm/sumW   (assume recupero+riempimento 100%)
       soglia_mode='recovery'  -> scala = L_cm/P      (P = carota occupata, fill-aware)
    In ENTRAMBI i casi den=sumW e num_gt restano identici: il GT NON cambia."""
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
        # SOLO QUI entra l'assunzione di recupero: cambia la base in px della scala
        if soglia_mode == "recovery":
            P = sum(occupied_span(im) for (_, _, im) in infos if im is not None)
            base_px = P if P > 0 else sumW
        else:
            base_px = sumW
        scala_cm_px = L_cm / base_px
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
                          err=round(abs(rqd_gt - rqd_pred), 1),
                          sumW=int(sumW), base_px=int(base_px),
                          soglia_px=round(soglia_px, 1)))
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


SAM_MAX = 16   # SAM auto e' ~19s/crop anche a 640px: valutato su subset stratificato


def riga_metrica(name, m):
    return (f"{name:24s} {m['mae']:6.1f} {m['corr']:+6.2f} {m['classe']:8.0f} "
            f"{m['entro5']:8.0f} {m['mae_poor']:9.1f} {m['t_crop']*1000:8.0f}ms")


def valuta_su(test_dict, det):
    righe, t_det, n_crop = valuta_detector(test_dict, det)
    m = metriche(righe)
    m["t_tot"] = t_det
    m["t_crop"] = t_det / max(1, n_crop)
    return righe, m


def main():
    manovre, _ = costruisci_manovre()
    test = {k: v for k, v in manovre.items() if k[0] == TEST_SOND}
    print(f"Test set (held-out {TEST_SOND}): {len(test)} manovre\n")

    cv_det = DetectorCV()
    yolo_det = DetectorYOLO() if YOLO_BEST.exists() else None
    try:
        sam_det = DetectorSAM()
    except Exception as e:
        sam_det = None
        print(f"[!] SAM non disponibile: {e}")

    # --- candidati veri sul TEST PIENO ---
    print("--- OpenCV (test pieno) ---")
    cv_righe, cv_m = valuta_su(test, cv_det)
    print("    " + riga_metrica(cv_det.name, cv_m))
    yolo_righe, yolo_m = (None, None)
    if yolo_det:
        print("--- YOLO-seg (test pieno) ---")
        yolo_righe, yolo_m = valuta_su(test, yolo_det)
        print("    " + riga_metrica(yolo_det.name, yolo_m))

    # --- subset stratificato per SAM (per GT crescente) ---
    gt_ord = sorted(cv_righe, key=lambda r: r["rqd_gt"])
    step = max(1, len(gt_ord) // SAM_MAX)
    sel = gt_ord[::step][:SAM_MAX]
    keys = {(r["sondaggio"], r["prof_in"], r["prof_fin"]) for r in sel}
    sub = {k: v for k, v in test.items() if k in keys}
    print(f"\n--- SAM subset stratificato: {len(sub)} manovre ---")
    sam_m = sam_righe = None
    if sam_det:
        sam_righe, sam_m = valuta_su(sub, sam_det)
        print("    " + riga_metrica(sam_det.name, sam_m))
    # OpenCV e YOLO ricalcolati sullo STESSO subset (confronto equo a 3 vie)
    _, cv_sub_m = valuta_su(sub, cv_det)
    yolo_sub_m = valuta_su(sub, yolo_det)[1] if yolo_det else None

    # --- 5 migliori / 5 peggiori del candidato vincente (YOLO sul test pieno) ---
    win_name = yolo_det.name if yolo_det else cv_det.name
    win_righe = yolo_righe if yolo_det else cv_righe
    ordin = sorted(win_righe, key=lambda r: r["err"])
    print(f"\n=== 5 MIGLIORI ({win_name}, test pieno) ===")
    for r in ordin[:5]:
        print(f"  {r['prof_in']}-{r['prof_fin']}m | GT={r['rqd_gt']:5.1f}  PRED={r['rqd_pred']:5.1f}  err={r['err']:4.1f}")
    print(f"=== 5 PEGGIORI ({win_name}, test pieno) ===")
    for r in ordin[-5:]:
        print(f"  {r['prof_in']}-{r['prof_fin']}m | GT={r['rqd_gt']:5.1f}  PRED={r['rqd_pred']:5.1f}  err={r['err']:4.1f}")

    # overlay su caso peggiore (poor rock) e migliore (good rock) per ogni detector
    case_low, case_high = ordin[-1], ordin[0]
    for det, rr in [(cv_det, cv_righe), (yolo_det, yolo_righe)]:
        if det is None:
            continue
        for tag, c in [("poor", case_low), ("good", case_high)]:
            sel_r = [r for r in rr if (r["prof_in"], r["prof_fin"]) == (c["prof_in"], c["prof_fin"])]
            overlay(sel_r, test, det, tag)

    # --- TABELLE ---
    hdr = (f"{'Detector':24s} {'MAE':>6s} {'corr':>6s} {'classe%':>8s} "
           f"{'entro5%':>8s} {'MAE_poor':>9s} {'t/crop':>10s}")
    print("\n" + "=" * 86)
    print(f"TABELLA A — candidati sul TEST PIENO ({len(test)} manovre)")
    print(hdr); print("-" * 86)
    print(riga_metrica(cv_det.name, cv_m))
    if yolo_m:
        print(riga_metrica(yolo_det.name, yolo_m))
    print("=" * 86)
    print(f"TABELLA B — confronto a 3 vie sullo STESSO subset ({len(sub)} manovre)")
    print(hdr); print("-" * 86)
    print(riga_metrica(cv_det.name, cv_sub_m))
    if sam_m:
        print(riga_metrica(sam_det.name, sam_m))
    if yolo_sub_m:
        print(riga_metrica(yolo_det.name, yolo_sub_m))
    print("=" * 86)

    with open(OUT / "spike_results.csv", "w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["tabella", "detector", "n", "mae", "corr", "classe_pct",
                    "entro5_pct", "mae_poor", "t_crop_ms"])
        for tab, name, m in [("A_full", cv_det.name, cv_m)] + \
                ([("A_full", yolo_det.name, yolo_m)] if yolo_m else []) + \
                [("B_subset", cv_det.name, cv_sub_m)] + \
                ([("B_subset", sam_det.name, sam_m)] if sam_m else []) + \
                ([("B_subset", yolo_det.name, yolo_sub_m)] if yolo_sub_m else []):
            w.writerow([tab, name, m["n"], f"{m['mae']:.2f}", f"{m['corr']:.3f}",
                        f"{m['classe']:.0f}", f"{m['entro5']:.0f}", f"{m['mae_poor']:.2f}",
                        f"{m['t_crop']*1000:.0f}"])
    print(f"\nCSV: {OUT/'spike_results.csv'}  | overlay: cmp_*.png")


if __name__ == "__main__":
    main()
