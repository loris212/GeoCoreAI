#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rileva_file_carote.py
=====================
Rilevamento automatico delle FILE ORIZZONTALI di carote in una foto ad alta
risoluzione di una cassetta catalogatrice di sondaggi geognostici.

APPROCCIO: Computer Vision CLASSICA (OpenCV). Nessun addestramento richiesto.
Motivo: la geometria della cassetta e' deterministica (N scomparti orizzontali
paralleli, di altezza quasi uguale). Una rete neurale qui sarebbe over-engineering.
Il deep learning (PyTorch) serve DOPO, per separare carota-da-vuoto (RQD),
classificare litologia, ecc.  -> vedi note in fondo al file.

PIPELINE:
    1. Caricamento + ridimensionamento
    2. Individuazione della cassetta e raddrizzamento prospettico (rectify)
    3. Profilo di texture per riga (le carote sono ruvide, i divisori lisci)
    4. Individuazione dei divisori = minimi del profilo -> tagli tra le file
    5. Estrazione + visualizzazione delle singole file

DIPENDENZE:
    pip install opencv-python numpy scipy

USO:
    python rileva_file_carote.py foto_cassetta.jpg -n 5 -o risultati/
    (-n e' opzionale: se conosci il numero di scomparti, rende tutto piu' stabile)
"""

from __future__ import annotations   # consente int | None anche su Python 3.9
from pathlib import Path
import cv2
import numpy as np
from scipy.signal import find_peaks


# --------------------------------------------------------------------------- #
# STEP 1 — Caricamento e ridimensionamento
# --------------------------------------------------------------------------- #
def carica_immagine(percorso: str, lato_max: int = 2000) -> np.ndarray:
    """Carica la foto e la riduce se troppo grande.
    Motivo: lavorare a 2000 px e' piu' veloce e i parametri (soglie, kernel)
    diventano indipendenti dalla risoluzione del telefono/reflex usato."""
    img = cv2.imread(percorso)
    if img is None:
        raise FileNotFoundError(f"Immagine non trovata: {percorso}")
    h, w = img.shape[:2]
    scala = lato_max / max(h, w)
    if scala < 1.0:                       # riduci solo se serve, mai ingrandire
        img = cv2.resize(img, None, fx=scala, fy=scala,
                         interpolation=cv2.INTER_AREA)
    return img


# --------------------------------------------------------------------------- #
# STEP 2 — Trova la cassetta e raddrizza la prospettiva
# --------------------------------------------------------------------------- #
def _ordina_vertici(pts: np.ndarray) -> np.ndarray:
    """Ordina 4 punti come: alto-sx, alto-dx, basso-dx, basso-sx.
    Trucco classico: il vertice alto-sx ha somma (x+y) minima, il basso-dx
    massima; l'alto-dx ha differenza (x-y) minima, il basso-sx massima."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]           # alto-sinistra
    rect[2] = pts[np.argmax(s)]           # basso-destra
    d = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(d)]           # alto-destra
    rect[3] = pts[np.argmax(d)]           # basso-sinistra
    return rect


def raddrizza_cassetta(img: np.ndarray):
    """Individua il contorno quadrilatero piu' grande (= la cassetta) e lo
    riporta a un rettangolo perfetto con una trasformazione prospettica.
    Se non trova un quadrilatero affidabile, restituisce l'immagine intera.
    Questo passo elimina l'inclinazione del telefono e l'effetto trapezio."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)                  # mappa dei bordi
    edges = cv2.dilate(edges, np.ones((5, 5), np.uint8), iterations=2)  # chiude i buchi

    contorni, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    if not contorni:
        return img, None

    area_img = img.shape[0] * img.shape[1]
    # esamina i contorni dal piu' grande al piu' piccolo
    for c in sorted(contorni, key=cv2.contourArea, reverse=True):
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)  # semplifica a poligono
        # accetta solo un quadrilatero che copra almeno il 25% dell'immagine
        if len(approx) == 4 and cv2.contourArea(approx) > 0.25 * area_img:
            quad = _ordina_vertici(approx.reshape(4, 2).astype("float32"))
            (tl, tr, br, bl) = quad
            larg = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
            alt  = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
            dst = np.array([[0, 0], [larg - 1, 0],
                            [larg - 1, alt - 1], [0, alt - 1]], dtype="float32")
            M = cv2.getPerspectiveTransform(quad, dst)
            return cv2.warpPerspective(img, M, (larg, alt)), quad
    return img, None


# --------------------------------------------------------------------------- #
# STEP 3 — Profilo di texture per riga
# --------------------------------------------------------------------------- #
def profilo_texture(warp: np.ndarray) -> np.ndarray:
    """Calcola un 'indice di dettaglio' per OGNI riga di pixel.
    IPOTESI CHIAVE: le carote sono ruvide/dettagliate (gradiente alto),
    mentre i divisori (legno/plastica) sono lisci e uniformi (gradiente basso).
    Risultato: file di carote -> PICCHI ; divisori -> VALLI."""
    gray = cv2.cvtColor(warp, cv2.COLOR_BGR2GRAY)
    # magnitudo del gradiente (Sobel) = quantita' di dettaglio locale
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy)
    profilo = mag.mean(axis=1)                 # media su ogni riga -> segnale 1D
    # leviga il profilo per togliere rumore (finestra ~1% dell'altezza, dispari)
    k = max(3, warp.shape[0] // 100) | 1
    profilo = cv2.GaussianBlur(profilo.reshape(-1, 1), (1, k), 0).ravel()
    return profilo


# --------------------------------------------------------------------------- #
# STEP 4 — Trova i divisori e taglia in file
# --------------------------------------------------------------------------- #
def trova_divisori(profilo: np.ndarray, n_file_attese: int | None = None) -> np.ndarray:
    """Trova le posizioni Y dei divisori = MINIMI del profilo di texture.
    Tecnica: inverto il segnale (cosi' i minimi diventano massimi) e uso
    find_peaks. Se conosci n_file_attese, impongo una distanza minima tra
    i divisori, riducendo i falsi positivi."""
    inv = profilo.max() - profilo
    dist = None
    if n_file_attese:
        dist = int(len(profilo) / (n_file_attese + 1) * 0.6)
    picchi, _ = find_peaks(inv, distance=dist, prominence=inv.std() * 0.5)
    return picchi


def taglia_in_file(warp: np.ndarray, divisori: np.ndarray):
    """Usa le Y dei divisori come linee di taglio e ritaglia le bande (file).
    Scarta le bande troppo sottili (< 3% dell'altezza) = rumore, non carote."""
    h = warp.shape[0]
    bordi = [0] + sorted(int(d) for d in divisori) + [h]
    file_ = []
    for y0, y1 in zip(bordi[:-1], bordi[1:]):
        if y1 - y0 > h * 0.03:
            file_.append((y0, y1, warp[y0:y1]))
    return file_


# --------------------------------------------------------------------------- #
# STEP 5 — Esecuzione e output
# --------------------------------------------------------------------------- #
def main(percorso_input: str, cartella_output: str = "output_file",
         n_file_attese: int | None = None) -> None:
    out = Path(cartella_output); out.mkdir(parents=True, exist_ok=True)

    img = carica_immagine(percorso_input)
    warp, quad = raddrizza_cassetta(img)
    if quad is None:
        print("[!] Cassetta non rilevata con sicurezza: uso l'immagine intera.")

    profilo = profilo_texture(warp)
    divisori = trova_divisori(profilo, n_file_attese)
    file_ = taglia_in_file(warp, divisori)
    print(f"[i] File di carote rilevate: {len(file_)}")

    # immagine di controllo (rettangoli verdi) + ritagli delle singole file
    vis = warp.copy()
    for i, (y0, y1, banda) in enumerate(file_):
        cv2.rectangle(vis, (0, y0), (warp.shape[1] - 1, y1), (0, 255, 0), 3)
        cv2.putText(vis, f"fila {i+1}", (10, y0 + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        cv2.imwrite(str(out / f"fila_{i+1:02d}.png"), banda)
    cv2.imwrite(str(out / "_controllo.png"), vis)
    print(f"[i] Output salvato in: {out.resolve()}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(
        description="Rileva le file orizzontali di carote in una cassetta.")
    p.add_argument("immagine", help="percorso della foto della cassetta")
    p.add_argument("-n", "--n-file", type=int, default=None,
                   help="numero di scomparti attesi (opzionale, piu' stabile)")
    p.add_argument("-o", "--output", default="output_file",
                   help="cartella di output")
    a = p.parse_args()
    main(a.immagine, a.output, a.n_file)


# =========================================================================== #
# NOTE — DOVE entra PyTorch (NON in questo step)
# =========================================================================== #
# Questo script risolve solo "trova le file". I problemi che giustificano una
# rete neurale (e quindi un dataset etichettato) sono a valle:
#   - segmentare carota-vs-vuoto-vs-divisore dentro ogni fila (per l'RQD)
#   - classificare litologia / contare fratture
# Per quelli oggi lo standard NON e' allenare da zero, ma:
#   detector leggero (YOLO11) per i box -> SAM 2.1 zero-shot per le maschere.
# Cosi' SAM non va mai riaddestrato e annoti pochissimo a mano.
