#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rqd_baseline.py  (ESPERIMENTO §6 — feasibility probe, READ-ONLY)
================================================================
Obiettivo: stabilire una BASELINE QUANTITATIVA della tesi di prodotto
("foto di carota -> RQD affidabile") usando SOLO il dataset Kaggle gia'
presente in archive/, SENZA annotare nulla, SENZA addestrare nulla,
SENZA modificare gli script esistenti.

Confronta due stime di RQD per ogni MANOVRA (= gruppo di righe con stesso
sondaggio + range di profondita', ricostruito dal nome file):

  RQD_GT  (ground-truth)  = Sigma(lunghezza pezzi TenCm annotati a mano) / Sigma(larghezza riga)
  RQD_CV  (baseline)      = Sigma(lunghezza pezzi >=10cm rilevati da CV classica) / Sigma(larghezza riga)

Entrambe sono RQD "recovery-based", calcolate in rapporto di PIXEL sulla
stessa immagine -> la scala cm/px si CANCELLA nel numeratore/denominatore.
La soglia fisica dei 10 cm per il rilevatore CV viene derivata per-manovra
dal range di profondita' nel nome file (assume recupero ~100% + carota
continua: e' un'ipotesi dichiarata, non un fatto).

NOTA DI ONESTA': RQD_GT qui e' "recovery RQD" (denominatore = lunghezza della
riga recuperata), non l'RQD ASTM puro (denominatore = lunghezza perforata).
E' la scelta robusta perche' non richiede scala. Misura la FISICA del problema
(separare pezzi >=10cm dal resto), che e' esattamente cio' che vogliamo testare.

USO:
  python experiments/rqd_baseline.py
Output in experiments/out/: rqd_results.csv, rqd_scatter.png, esempi_*.png
DIPENDENZE: opencv-python, numpy  (gia' nel progetto; nessun SAM/torch)
"""
from __future__ import annotations
from pathlib import Path
from collections import defaultdict
import json
import re
import csv
import numpy as np
import cv2

ROOT = Path(__file__).resolve().parent.parent
SEG_DIR = ROOT / "archive" / "Annotation of core segments longer than 10cm"
BAND_DIR = ROOT / "archive" / "Annotation of core bands"
OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(parents=True, exist_ok=True)

# nome file -> (sondaggio, prof_inizio_m, prof_fine_m)
# borehole catturato a inizio stringa; range profondita' = ultima coppia "a-b m".
RE_SOND = re.compile(r"^(?:IMG[_-]?)?([A-Za-z]+\d+)", re.IGNORECASE)
# nel dataset il n. di manovra e' spesso incollato alla quota di inizio:
# "Z441-72489.00-496.00m" = manovra 72, quota 489.00-496.00m. Estraggo il 'b'
# pulito (prima della m) e cerco una 'a' plausibile fra i suffissi del numero.
RE_RANGE = re.compile(r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*m")
TENCM_LABELS = {"tencm", "tencn"}   # 'TenCn' = refuso presente nel dataset


# --------------------------------------------------------------------------- #
# Utility
# --------------------------------------------------------------------------- #
def union_len(intervalli: list[tuple[float, float]]) -> float:
    """Lunghezza dell'unione di intervalli 1D (gestisce pezzi sovrapposti)."""
    if not intervalli:
        return 0.0
    iv = sorted(intervalli)
    tot, c0, c1 = 0.0, iv[0][0], iv[0][1]
    for a, b in iv[1:]:
        if a <= c1:
            c1 = max(c1, b)
        else:
            tot += c1 - c0
            c0, c1 = a, b
    return tot + (c1 - c0)


def x_extent(shape) -> tuple[float, float]:
    xs = [p[0] for p in shape["points"]]
    return min(xs), max(xs)


def parse_manovra(nome: str):
    ms = RE_SOND.search(nome)
    if not ms:
        return None
    sond = ms.group(1).upper()
    for pre, b_s in RE_RANGE.findall(nome):
        b = float(b_s)
        # prova i suffissi del numero di sinistra (toglie il n. manovra incollato)
        for i in range(len(pre)):
            sub = pre[i:]
            if not sub or sub.startswith("."):
                continue
            try:
                a = float(sub)
            except ValueError:
                continue
            if a < b and 0.5 <= (b - a) <= 30:
                return sond, a, b
    return None


# --------------------------------------------------------------------------- #
# BASELINE CV CLASSICA — rileva i pezzi (>=10cm) senza training, senza SAM
# --------------------------------------------------------------------------- #
def rileva_pezzi_cv(img: np.ndarray, soglia_px: float,
                    frac_presenza: float = 0.18,
                    gap_min_px: int = 6) -> list[tuple[int, int]]:
    """Stima i pezzi di carota su una riga rettificata, in modo classico:
       1. texture per-colonna (Sobel): carota = alta, vuoto/gap = bassa
       2. colonne 'core presente' = profilo > frazione del massimo
       3. run contigui di colonne presenti = pezzi candidati
       4. tiene solo i pezzi piu' lunghi della soglia fisica (10 cm in px)
    Restituisce lista di (x0, x1). LIMITE NOTO: le fratture CHIUSE (pezzi che
    si toccano senza gap visibile) non vengono separate -> sovrastima RQD.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    col = cv2.magnitude(gx, gy).mean(axis=0)             # texture per colonna
    k = max(3, gray.shape[1] // 200) | 1
    col = cv2.GaussianBlur(col.reshape(1, -1), (k, 1), 0).ravel()
    if col.max() <= 0:
        return []
    presente = col > (frac_presenza * col.max())

    # run-length encoding dei tratti 'presente', con chiusura dei micro-gap
    pezzi = []
    x = 0
    W = len(presente)
    while x < W:
        if not presente[x]:
            x += 1
            continue
        x0 = x
        while x < W and presente[x]:
            x += 1
        x1 = x
        # assorbe micro-gap (rumore) col pezzo successivo
        while x1 < W:
            gstart = x1
            while x < W and not presente[x]:
                x += 1
            gap = x - gstart
            if gap <= gap_min_px and x < W and presente[x]:
                while x < W and presente[x]:
                    x += 1
                x1 = x
            else:
                x = gstart
                break
        if (x1 - x0) >= soglia_px:
            pezzi.append((x0, x1))
    return pezzi


# --------------------------------------------------------------------------- #
# 1) Conteggi dataset
# --------------------------------------------------------------------------- #
def conteggi():
    n_core = 0
    band_imgs = 0
    for f in BAND_DIR.glob("*.json"):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        band_imgs += 1
        n_core += sum(1 for s in d.get("shapes", []) if s["label"].lower() == "core")

    n_tencm = 0
    seg_imgs = 0
    for f in SEG_DIR.glob("*.json"):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        seg_imgs += 1
        n_tencm += sum(1 for s in d.get("shapes", [])
                       if s["label"].lower() in TENCM_LABELS)
    return dict(band_imgs=band_imgs, n_core=n_core,
                seg_imgs=seg_imgs, n_tencm=n_tencm)


# --------------------------------------------------------------------------- #
# 2) Costruzione manovre + GT + baseline CV
# --------------------------------------------------------------------------- #
def costruisci_manovre():
    # raccoglie i crop per manovra
    manovre = defaultdict(list)   # key -> list of (json_path, jpg_path)
    senza_chiave = 0
    for jf in SEG_DIR.glob("*.json"):
        key = parse_manovra(jf.stem)
        jpg = jf.with_suffix(".jpg")
        if not jpg.exists():
            # prova imagePath dentro il json
            try:
                d = json.load(open(jf, encoding="utf-8"))
                cand = SEG_DIR / Path(d.get("imagePath", "")).name
                jpg = cand if cand.exists() else jpg
            except Exception:
                pass
        if key is None:
            senza_chiave += 1
            continue
        manovre[key].append((jf, jpg))
    return manovre, senza_chiave


def valuta(manovre):
    righe = []
    for key, crops in manovre.items():
        sond, a, b = key
        L_cm = (b - a) * 100.0
        # prima passata: somma larghezze (px) per la scala della manovra
        infos = []
        sumW = 0
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
        # scala: L_cm di carota distribuita su sumW px (ipotesi recupero ~100%)
        scala_cm_px = L_cm / sumW
        soglia_px = 10.0 / scala_cm_px          # 10 cm in pixel

        num_gt = 0.0
        num_cv = 0.0
        den = 0.0
        n_crop_cv = 0
        for W, tencm, img in infos:
            den += W
            num_gt += union_len(tencm)
            if img is not None:
                pezzi = rileva_pezzi_cv(img, soglia_px)
                num_cv += union_len([(p[0], p[1]) for p in pezzi])
                n_crop_cv += 1
        rqd_gt = 100.0 * num_gt / den
        rqd_cv = 100.0 * num_cv / den if n_crop_cv == len(infos) else None
        righe.append(dict(
            sondaggio=sond, prof_in=a, prof_fin=b, manovra_m=round(b - a, 2),
            n_crop=len(infos), n_crop_immagine=n_crop_cv,
            scala_cm_px=round(scala_cm_px, 4), soglia_px=round(soglia_px, 1),
            rqd_gt=round(rqd_gt, 1),
            rqd_cv=round(rqd_cv, 1) if rqd_cv is not None else None,
            err=round(abs(rqd_gt - rqd_cv), 1) if rqd_cv is not None else None,
        ))
    return righe


# --------------------------------------------------------------------------- #
# 3) Classe di Deere (per accuratezza di classe)
# --------------------------------------------------------------------------- #
def classe_deere(rqd):
    for soglia, nome in [(25, "very_poor"), (50, "poor"), (75, "fair"),
                         (90, "good"), (101, "excellent")]:
        if rqd < soglia:
            return nome
    return "excellent"


# --------------------------------------------------------------------------- #
# 4) Scatter plot (senza matplotlib: disegnato con OpenCV)
# --------------------------------------------------------------------------- #
def scatter_png(righe, path):
    S = 600
    M = 60
    cv = np.full((S, S, 3), 255, np.uint8)

    def px(v):  # rqd 0..100 -> coord
        return int(M + v / 100.0 * (S - 2 * M))

    # griglia + diagonale
    for t in range(0, 101, 25):
        x = px(t); y = S - px(t)
        cv2.line(cv, (M, y), (S - M, y), (230, 230, 230), 1)
        cv2.line(cv, (x, M), (x, S - M), (230, 230, 230), 1)
        cv2.putText(cv, str(t), (x - 8, S - M + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (120, 120, 120), 1)
        cv2.putText(cv, str(t), (M - 30, y + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (120, 120, 120), 1)
    cv2.line(cv, (px(0), S - px(0)), (px(100), S - px(100)), (180, 180, 180), 1)  # y=x
    for r in righe:
        if r["rqd_cv"] is None:
            continue
        x = px(r["rqd_gt"]); y = S - px(r["rqd_cv"])
        cv2.circle(cv, (x, y), 4, (200, 120, 0), -1)
    cv2.putText(cv, "RQD ground-truth (%)", (S // 2 - 90, S - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.putText(cv, "RQD baseline CV (%)", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.imwrite(str(path), cv)


# --------------------------------------------------------------------------- #
# Overlay di un esempio: GT (verde) vs CV (rosso) sul 1° crop della manovra
# --------------------------------------------------------------------------- #
def salva_overlay(r, manovre, path):
    key = (r["sondaggio"], r["prof_in"], r["prof_fin"])
    crops = manovre.get(key)
    if not crops:
        return
    # ricalcola scala della manovra come nel valuta()
    sumW = 0
    primo = None
    for jf, jpg in crops:
        try:
            d = json.load(open(jf, encoding="utf-8"))
        except Exception:
            continue
        W = d.get("imageWidth")
        if not W:
            continue
        sumW += W
        if primo is None and jpg.exists():
            primo = (jf, jpg, d, W)
    if primo is None or sumW == 0:
        return
    jf, jpg, d, W = primo
    img = cv2.imread(str(jpg))
    if img is None:
        return
    scala = (r["prof_fin"] - r["prof_in"]) * 100.0 / sumW
    soglia_px = 10.0 / scala

    vis = img.copy()
    H = vis.shape[0]
    # GT TenCm in verde
    for s in d.get("shapes", []):
        if s["label"].lower() in TENCM_LABELS:
            pts = np.array(s["points"], np.int32)
            cv2.polylines(vis, [pts], True, (0, 180, 0), 3)
    # pezzi CV in rosso
    for x0, x1 in rileva_pezzi_cv(img, soglia_px):
        cv2.rectangle(vis, (x0, 4), (x1, H - 4), (0, 0, 255), 3)
    banner = np.full((40, vis.shape[1], 3), 255, np.uint8)
    cv2.putText(banner, f"{r['sondaggio']} {r['prof_in']}-{r['prof_fin']}m  "
                f"GT(verde)={r['rqd_gt']:.0f}%  CV(rosso)={r['rqd_cv']:.0f}%  err={r['err']:.0f}pp",
                (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.imwrite(str(path), np.vstack([banner, vis]))


# --------------------------------------------------------------------------- #
# MAIN
# --------------------------------------------------------------------------- #
def main():
    print("=" * 70)
    print("ESPERIMENTO §6 — BASELINE RQD su dataset Kaggle (read-only)")
    print("=" * 70)

    c = conteggi()
    manovre, senza_chiave = costruisci_manovre()
    righe = valuta(manovre)
    valide = [r for r in righe if r["rqd_cv"] is not None]

    gt = np.array([r["rqd_gt"] for r in valide])
    cvp = np.array([r["rqd_cv"] for r in valide])
    err = np.abs(gt - cvp)
    mae = err.mean() if len(err) else float("nan")
    # baseline ingenua: predici sempre la media -> MAE "floor"
    mae_naive = np.abs(gt - gt.mean()).mean() if len(gt) else float("nan")
    entro5 = 100.0 * np.mean(err <= 5) if len(err) else 0.0
    entro10 = 100.0 * np.mean(err <= 10) if len(err) else 0.0
    # accuratezza di classe Deere
    cls_ok = np.mean([classe_deere(g) == classe_deere(p) for g, p in zip(gt, cvp)]) * 100 if len(gt) else 0.0
    # correlazione
    corr = float(np.corrcoef(gt, cvp)[0, 1]) if len(gt) > 1 else float("nan")

    print(f"\n--- DATASET ---")
    print(f"Immagini 'core bands'      : {c['band_imgs']:4d}   (annotazioni Core : {c['n_core']})")
    print(f"Immagini 'core segments'   : {c['seg_imgs']:4d}   (annotazioni TenCm: {c['n_tencm']})")
    print(f"Manovre ricostruite        : {len(manovre):4d}   (crop senza range nel nome: {senza_chiave})")
    print(f"Manovre VALUTABILI (GT+CV) : {len(valide):4d}")

    print(f"\n--- RQD GROUND-TRUTH (recovery-based, pixel ratio) ---")
    if len(gt):
        print(f"distribuzione RQD_gt  min/med/max : {gt.min():.0f} / {np.median(gt):.0f} / {gt.max():.0f}")

    print(f"\n--- RISULTATO BASELINE CV CLASSICA ---")
    print(f"MAE RQD (punti %)            : {mae:5.1f}")
    print(f"MAE 'naive' (predici media) : {mae_naive:5.1f}   <- la CV deve battere questo")
    print(f"manovre entro ±5 pp         : {entro5:4.0f}%")
    print(f"manovre entro ±10 pp        : {entro10:4.0f}%")
    print(f"accuratezza classe di Deere : {cls_ok:4.0f}%")
    print(f"correlazione gt vs cv       : {corr:+.2f}")

    # CSV
    csv_path = OUT / "rqd_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fp:
        w = csv.DictWriter(fp, fieldnames=list(righe[0].keys()))
        w.writeheader()
        w.writerows(righe)

    # scatter
    scatter_path = OUT / "rqd_scatter.png"
    scatter_png(valide, scatter_path)

    # esempi: 3 migliori, 3 peggiori + overlay immagine del 1° crop
    ordinati = sorted(valide, key=lambda r: r["err"])
    print(f"\n--- 3 SUCCESSI (errore minore) ---")
    for r in ordinati[:3]:
        print(f"  {r['sondaggio']:6s} {r['prof_in']}-{r['prof_fin']}m | "
              f"gt={r['rqd_gt']:5.1f}  cv={r['rqd_cv']:5.1f}  err={r['err']:4.1f}")
    print(f"\n--- 3 FALLIMENTI (errore maggiore) ---")
    for r in ordinati[-3:]:
        print(f"  {r['sondaggio']:6s} {r['prof_in']}-{r['prof_fin']}m | "
              f"gt={r['rqd_gt']:5.1f}  cv={r['rqd_cv']:5.1f}  err={r['err']:4.1f}")

    for tag, gruppo in [("successo", ordinati[:2]), ("fallimento", ordinati[-2:])]:
        for i, r in enumerate(gruppo, 1):
            salva_overlay(r, manovre, OUT / f"esempio_{tag}_{i}.png")

    print(f"\nOutput salvato in: {OUT}")
    print(f"  - {csv_path.name}  (tutte le manovre)")
    print(f"  - {scatter_path.name}  (gt vs cv)")
    return dict(mae=mae, mae_naive=mae_naive, entro5=entro5, cls_ok=cls_ok,
                corr=corr, n=len(valide))


if __name__ == "__main__":
    main()
