#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
estrai_file_carote.py  (FASE 1)
===============================
Prende la foto di una cassetta catalogatrice, RADDRIZZA la prospettiva,
individua le FILE orizzontali col profilo di texture (Sobel) e salva:
  - un crop pulito per ogni fila (gia' rifilato dai listelli)  -> input per SAM
  - un manifest.json con ordine, coordinate, scala e quote nominali
  - un'immagine di controllo con i riquadri

CONFINE DI RESPONSABILITA':
  Questo script NON misura le carote e NON calcola l'RQD. Si ferma alla
  produzione di file pulite e ordinate, pronte per la Fase 2 (YOLO11 + SAM 2.1).
  La segmentazione carota/vuoto/cartellino e' compito della Fase 2.

SCALE (importante, vedi note di progetto):
  - La SCALA FISICA (cm/px) serve a misurare la lunghezza dei pezzi (numeratore RQD).
    La ricavi dalla lunghezza interna nota di uno scomparto (--lunghezza-fila-cm)
    oppure, meglio, da un marker ArUco in foto (vedi snippet in fondo).
  - La QUOTA (m) e' una etichetta NOMINALE: la mappatura pixel->metro assume
    recupero 100% e carota uniforme. Va usata solo per orientarsi, non per misurare.

DIPENDENZE:  pip install opencv-python numpy scipy
USO:
  python estrai_file_carote.py foto.jpg -n 5 --lunghezza-fila-cm 100 \
         --quota-inizio 10.0 --quota-fine 15.0 -o risultati/
"""

from __future__ import annotations
from pathlib import Path
import json
import cv2
import numpy as np
from scipy.signal import find_peaks


# --------------------------------------------------------------------------- #
# STEP 1 — Caricamento + ridimensionamento (parametri indipendenti dalla risoluzione)
# --------------------------------------------------------------------------- #
def carica_immagine(percorso: str, lato_max: int = 2000) -> np.ndarray:
    img = cv2.imread(percorso)
    if img is None:
        raise FileNotFoundError(f"Immagine non trovata: {percorso}")
    h, w = img.shape[:2]
    s = lato_max / max(h, w)
    if s < 1.0:
        img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    return img


# --------------------------------------------------------------------------- #
# STEP 2 — Rettifica prospettica (la "correzione del trapezio")
# --------------------------------------------------------------------------- #
def _ordina_vertici(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0], rect[2] = pts[np.argmin(s)], pts[np.argmax(s)]   # tl, br
    d = np.diff(pts, axis=1)
    rect[1], rect[3] = pts[np.argmin(d)], pts[np.argmax(d)]   # tr, bl
    return rect


def raddrizza_cassetta(img: np.ndarray):
    """Trova il quadrilatero piu' grande (la cassetta) e lo riporta a rettangolo."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 50, 150)
    edges = cv2.dilate(edges, np.ones((5, 5), np.uint8), iterations=2)
    contorni, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contorni:
        return img, None
    area_img = img.shape[0] * img.shape[1]
    for c in sorted(contorni, key=cv2.contourArea, reverse=True):
        approx = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
        if len(approx) == 4 and cv2.contourArea(approx) > 0.25 * area_img:
            quad = _ordina_vertici(approx.reshape(4, 2).astype("float32"))
            tl, tr, br, bl = quad
            larg = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
            alt = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
            dst = np.array([[0, 0], [larg - 1, 0], [larg - 1, alt - 1], [0, alt - 1]],
                           dtype="float32")
            M = cv2.getPerspectiveTransform(quad, dst)
            return cv2.warpPerspective(img, M, (larg, alt)), quad.tolist()
    return img, None


# --------------------------------------------------------------------------- #
# STEP 3 — Profilo di texture (Sobel): carote ruvide = picchi, listelli lisci = valli
# --------------------------------------------------------------------------- #
def profilo_texture(warp: np.ndarray) -> np.ndarray:
    g = cv2.cvtColor(warp, cv2.COLOR_BGR2GRAY)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    prof = cv2.magnitude(gx, gy).mean(axis=1)          # media per riga -> segnale 1D
    k = max(3, warp.shape[0] // 100) | 1               # leviga (finestra dispari)
    return cv2.GaussianBlur(prof.reshape(-1, 1), (1, k), 0).ravel()


# --------------------------------------------------------------------------- #
# STEP 4 — Divisori (minimi del profilo) e taglio in bande
# --------------------------------------------------------------------------- #
def trova_divisori(prof: np.ndarray, n_file: int | None) -> np.ndarray:
    inv = prof.max() - prof
    dist = int(len(prof) / (n_file + 1) * 0.6) if n_file else None
    picchi, _ = find_peaks(inv, distance=dist, prominence=inv.std() * 0.5)
    return picchi


def _trim_verticale(banda: np.ndarray):
    """Rifila la banda in alto/basso tenendo solo la zona ad alta texture
    (= la carota), eliminando i resti di listello inclusi nel taglio."""
    g = cv2.cvtColor(banda, cv2.COLOR_BGR2GRAY)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy).mean(axis=1)
    if mag.max() <= 0:
        return 0, banda.shape[0]
    righe = np.where(mag > mag.max() * 0.30)[0]
    return (int(righe[0]), int(righe[-1]) + 1) if len(righe) else (0, banda.shape[0])


def taglia_in_file(warp: np.ndarray, divisori: np.ndarray):
    h = warp.shape[0]
    bordi = [0] + sorted(int(d) for d in divisori) + [h]
    file_ = []
    for y0, y1 in zip(bordi[:-1], bordi[1:]):
        if y1 - y0 <= h * 0.03:                        # scarta bande sottili = rumore
            continue
        ty0, ty1 = _trim_verticale(warp[y0:y1])        # rifila i bordi
        file_.append((y0 + ty0, y0 + ty1, warp[y0 + ty0:y0 + ty1]))
    return file_


# --------------------------------------------------------------------------- #
# STEP 5 — Output: crop + manifest.json + immagine di controllo
# --------------------------------------------------------------------------- #
def main(percorso: str, out_dir: str = "fase1_out", n_file: int | None = None,
         lunghezza_fila_cm: float | None = None,
         quota_inizio: float | None = None, quota_fine: float | None = None):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)

    img = carica_immagine(percorso)
    warp, quad = raddrizza_cassetta(img)
    if quad is None:
        print("[!] Cassetta non rilevata: uso l'immagine intera (rettifica saltata).")

    prof = profilo_texture(warp)
    file_ = taglia_in_file(warp, trova_divisori(prof, n_file))
    n = len(file_)
    print(f"[i] File rilevate: {n}")

    # scala fisica cm/px: dalla larghezza della fila e la lunghezza nota dello scomparto
    larg_px = warp.shape[1]
    scala_cm_px = (lunghezza_fila_cm / larg_px) if lunghezza_fila_cm else None

    # quote NOMINALI per fila (assume recupero 100% + carota uniforme: solo indicativo!)
    quote = []
    if quota_inizio is not None and quota_fine is not None and n > 0:
        passo = (quota_fine - quota_inizio) / n
        quote = [(round(quota_inizio + i * passo, 2),
                  round(quota_inizio + (i + 1) * passo, 2)) for i in range(n)]

    manifest = {
        "sorgente": percorso,
        "rettifica_applicata": quad is not None,
        "vertici_cassetta_px": quad,
        "dim_rettificata_px": [warp.shape[1], warp.shape[0]],
        "scala_cm_per_px": scala_cm_px,
        "quote_nominali_avviso": "mappatura pixel->metro valida solo a recupero 100%",
        "convenzione": "ordine file: alto->basso ; entro la fila: sx->dx = profondita' crescente",
        "n_file": n,
        "file": []
    }

    vis = warp.copy()
    for i, (y0, y1, banda) in enumerate(file_):
        nome = f"fila_{i+1:02d}.png"
        cv2.imwrite(str(out / nome), banda)
        cv2.rectangle(vis, (0, y0), (larg_px - 1, y1), (0, 255, 0), 3)
        cv2.putText(vis, f"fila {i+1}", (10, y0 + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        manifest["file"].append({
            "indice": i + 1,
            "file": nome,
            "bbox_px": [0, int(y0), larg_px, int(y1)],
            "dim_px": [int(banda.shape[1]), int(banda.shape[0])],
            "quota_nominale_m": quote[i] if quote else None,
        })
    cv2.imwrite(str(out / "_controllo.png"), vis)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"[i] Output + manifest.json in: {out.resolve()}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Fase 1: rettifica + estrazione file di carote.")
    p.add_argument("immagine")
    p.add_argument("-n", "--n-file", type=int, default=None, help="n. scomparti attesi")
    p.add_argument("--lunghezza-fila-cm", type=float, default=None,
                   help="lunghezza interna nota di uno scomparto (per la scala fisica)")
    p.add_argument("--quota-inizio", type=float, default=None, help="quota inizio manovra (m)")
    p.add_argument("--quota-fine", type=float, default=None, help="quota fine manovra (m)")
    p.add_argument("-o", "--output", default="fase1_out")
    a = p.parse_args()
    main(a.immagine, a.output, a.n_file, a.lunghezza_fila_cm, a.quota_inizio, a.quota_fine)


# =========================================================================== #
# SNIPPET OPZIONALE — scala automatica con marker ArUco (richiede opencv-contrib-python)
# =========================================================================== #
# Metti un marker ArUco stampato di lato noto (es. 5 cm) nel piano della cassetta.
# def scala_da_aruco(warp, lato_marker_cm=5.0):
#     import cv2.aruco as aruco
#     d = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
#     corners, ids, _ = aruco.ArucoDetector(d, aruco.DetectorParameters()).detectMarkers(warp)
#     if ids is None: return None
#     lato_px = cv2.norm(corners[0][0][0] - corners[0][0][1])   # un lato del marker
#     return lato_marker_cm / lato_px                            # cm/px, robusto e per-foto
