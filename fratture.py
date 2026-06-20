#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fratture.py  (FASE 2 — rilevamento rotture)
===========================================
Input: una singola FILA rettificata e rifilata prodotta dalla Fase 1 (fila_NN.png).

Due rilevatori, scopi diversi:
  A) segmenta_pezzi_sam()        -> PRIMARIO per l'RQD. Segmenta i singoli pezzi
                                    con SAM 2.1; le ROTTURE sono i gap tra maschere
                                    adiacenti. Da' direttamente le lunghezze dei pezzi.
  B) traccia_fratture_classico() -> COMPLEMENTARE. Traccia linee sulle fratture
                                    trasversali (verticali/oblique), robusto a
                                    ombre e sporco. Serve per le rotture "chiuse"
                                    (pezzi che si toccano, che SAM fonde in uno solo).

Sinergia: prendi i pezzi da SAM e, dentro ogni maschera lunga, lancia il
tracciatore classico per trovare le rotture interne senza gap visibile.

LIMITE ONESTO: distinguere frattura NATURALE vs ARTIFICIALE (da perforazione) vs
VENA non e' risolvibile in modo affidabile da una sola foto 2D dall'alto. Questi
strumenti producono ROTTURE CANDIDATE; la classificazione finale resta euristica
(gap ~zero + sezioni che combaciano = artificiale) + conferma umana sui dubbi.

DIPENDENZE:
  classico:  pip install opencv-python numpy
  SAM:       pip install ultralytics            (scarica il checkpoint al primo uso)
"""

from __future__ import annotations
import numpy as np
import cv2


# =========================================================================== #
# B) TRACCIATORE CLASSICO — con riduzione dei falsi positivi incorporata
# =========================================================================== #
def traccia_fratture_classico(img: np.ndarray,
                              angolo_max_da_verticale: float = 45.0,
                              frazione_span_min: float = 0.55,
                              tol_merge_px: int = 12):
    """Traccia le fratture TRASVERSALI (verticali/oblique) su una fila di carota.
    Restituisce (lista_linee, img_annotata).
    Ogni linea: dict {x_medio, angolo_deg, punti:(x1,y1,x2,y2)}.

    Ogni passo elimina una classe di falsi positivi (vedi commenti)."""
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # --- FP #1: OMBRE e luce non uniforme -------------------------------------
    # Le ombre sono gradienti LENTI e morbidi. Le rimuovo con flat-field:
    # divido l'immagine per una sua versione molto sfocata (stima dell'illuminazione).
    sfondo = cv2.GaussianBlur(gray, (0, 0), sigmaX=max(1, w * 0.04))
    norm = cv2.divide(gray, sfondo, scale=255).astype(np.uint8)
    # contrasto locale uniforme (non globale) -> robusto a zone chiare/scure
    norm = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(norm)

    # --- FP #2: SPORCO/FANGO (macchie) ----------------------------------------
    # Il black-hat con kernel LINEARE VERTICALE esalta i SOLCHI scuri, sottili e
    # allungati (= fratture) e sopprime le macchie larghe (sporco) e le ombre morbide.
    alt_k = max(15, h // 3)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, alt_k))
    blackhat = cv2.morphologyEx(norm, cv2.MORPH_BLACKHAT, kernel)
    _, binc = cv2.threshold(blackhat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # --- fit di segmenti rettilinei -------------------------------------------
    min_len = int(h * frazione_span_min)          # FP #3a: deve attraversare la carota
    linee = cv2.HoughLinesP(binc, 1, np.pi / 180, threshold=50,
                            minLineLength=min_len, maxLineGap=int(h * 0.15))
    candidate = []
    if linee is not None:
        for x1, y1, x2, y2 in linee[:, 0]:
            dx, dy = abs(x2 - x1), abs(y2 - y1)
            ang = np.degrees(np.arctan2(dx, dy + 1e-6))   # 0 = verticale
            # --- FP #3b: ORIENTAMENTO ---------------------------------------
            # Tieni solo verticale/obliquo. Scarta gli edge orizzontali:
            # graffi lungo l'asse, linea bagnato/asciutto, bordi del canale.
            if ang <= angolo_max_da_verticale:
                candidate.append((int((x1 + x2) / 2), float(ang), (int(x1), int(y1), int(x2), int(y2))))

    # --- FP #4: VENE / bandeggio di colore ------------------------------------
    # Validazione "valle scura": una vera frattura e' un solco scuro in sezione
    # (minimo locale di intensita'). Una vena/bandeggio e' in piano, niente solco.
    validate = [c for c in candidate if _e_valle_scura(norm, c[0])]

    # --- FP #5: rilevamenti MULTIPLI della stessa frattura --------------------
    # Raggruppa per posizione x e tieni un rappresentante per cluster.
    fratture = _merge_per_x(validate, tol_merge_px)

    # disegno
    vis = img.copy()
    for f in fratture:
        x1, y1, x2, y2 = f["punti"]
        cv2.line(vis, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(vis, f"{f['angolo_deg']:.0f}", (f["x_medio"], 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    return fratture, vis


def _e_valle_scura(gray: np.ndarray, x: int, semi: int = 6, drop: float = 8.0) -> bool:
    """True se alla colonna x c'e' un minimo di intensita' piu' scuro dei lati
    (solco). Filtra le linee chiare e i bordi di colore senza solco fisico."""
    h, w = gray.shape
    x = int(np.clip(x, semi + 1, w - semi - 2))
    centro = gray[:, x - 1:x + 2].mean()
    lati = np.concatenate([gray[:, x - semi:x - semi + 2].ravel(),
                           gray[:, x + semi - 1:x + semi + 1].ravel()]).mean()
    return (lati - centro) > drop


def _merge_per_x(linee, tol):
    """Fonde le linee vicine in x (stessa frattura vista piu' volte)."""
    if not linee:
        return []
    linee = sorted(linee, key=lambda c: c[0])
    gruppi, corrente = [], [linee[0]]
    for c in linee[1:]:
        if c[0] - corrente[-1][0] <= tol:
            corrente.append(c)
        else:
            gruppi.append(corrente); corrente = [c]
    gruppi.append(corrente)
    out = []
    for g in gruppi:
        x = int(np.mean([c[0] for c in g]))
        rappr = min(g, key=lambda c: c[1])          # il piu' verticale del gruppo
        out.append({"x_medio": x, "angolo_deg": rappr[1], "punti": rappr[2]})
    return out


# =========================================================================== #
# A) SEGMENTAZIONE PEZZI CON SAM 2.1 -> rotture per l'RQD
# =========================================================================== #
def segmenta_pezzi_sam(immagine, modello: str = "sam2.1_b.pt",
                       frazione_altezza_min: float = 0.4,
                       frazione_area_min: float = 0.01):
    """Segmenta i singoli pezzi di carota con SAM (modalita' automatica, zero training).
    Restituisce i pezzi ordinati sx->dx: lista di dict {x0,x1,y0,y1,larghezza_px}.

    NOTA: la modalita' automatica e' il punto di partenza SENZA addestramento, ma
    puo' sovra/sotto-segmentare. Il percorso affidabile (letteratura: YOLO11+SAM)
    e' allenare un detector leggero che dia i box, poi promptare SAM coi box.
    Vedi segmenta_pezzi_sam_da_box() sotto."""
    try:
        from ultralytics import SAM
    except ImportError:
        raise ImportError("Installa ultralytics:  pip install ultralytics")

    img = cv2.imread(immagine) if isinstance(immagine, str) else immagine
    H, W = img.shape[:2]
    res = SAM(modello)(img, verbose=False)          # 'segment everything'
    if res[0].masks is None:
        return []
    masks = res[0].masks.data.cpu().numpy() > 0.5   # (N,H,W) booleane

    pezzi = []
    for m in masks:
        ys, xs = np.where(m)
        if len(xs) == 0:
            continue
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        # filtra: deve coprire buona parte dell'altezza del canale e avere area minima
        if (y1 - y0) < frazione_altezza_min * H:
            continue
        if m.sum() < frazione_area_min * H * W:
            continue
        pezzi.append({"x0": int(x0), "x1": int(x1), "y0": int(y0), "y1": int(y1),
                      "larghezza_px": int(x1 - x0)})
    return sorted(pezzi, key=lambda p: p["x0"])     # sx->dx = profondita' crescente


def segmenta_pezzi_sam_da_box(immagine, boxes, modello: str = "sam2.1_b.pt"):
    """Variante affidabile: SAM promptato con i box di un detector (YOLO11).
    boxes: lista [x1,y1,x2,y2] in pixel. API ultralytics: model(img, bboxes=...)."""
    from ultralytics import SAM
    img = cv2.imread(immagine) if isinstance(immagine, str) else immagine
    res = SAM(modello)(img, bboxes=boxes, verbose=False)
    masks = res[0].masks.data.cpu().numpy() > 0.5
    pezzi = []
    for m in masks:
        ys, xs = np.where(m)
        if len(xs):
            pezzi.append({"x0": int(xs.min()), "x1": int(xs.max()),
                          "larghezza_px": int(xs.max() - xs.min())})
    return sorted(pezzi, key=lambda p: p["x0"])


def rotture_da_pezzi(pezzi, scala_cm_px: float | None = None,
                     gap_aperto_px: int = 8):
    """Dai pezzi ordinati ricava ROTTURE e lunghezze (input per l'RQD).
    Classifica ogni rottura in modo euristico:
      - gap ampio  -> 'vuoto'      (perdita reale / tritume -> NON ricuce, RQD basso)
      - gap ~zero  -> 'da_validare' (possibile rottura artificiale -> ricuce se le
                      sezioni combaciano: decisione finale all'utente)
    Restituisce dict con lunghezze pezzi (cm se c'e' la scala) e lista rotture."""
    def cm(px):
        return round(px * scala_cm_px, 1) if scala_cm_px else None

    rotture = []
    for prec, succ in zip(pezzi[:-1], pezzi[1:]):
        gap = succ["x0"] - prec["x1"]
        rotture.append({
            "x_px": int((prec["x1"] + succ["x0"]) / 2),
            "gap_px": int(gap),
            "gap_cm": cm(max(0, gap)),
            "tipo": "vuoto" if gap > gap_aperto_px else "da_validare",
        })
    pezzi_out = [{"larghezza_px": p["larghezza_px"], "lunghezza_cm": cm(p["larghezza_px"])}
                 for p in pezzi]
    return {"pezzi": pezzi_out, "rotture": rotture}


# --------------------------------------------------------------------------- #
# Esempio d'uso
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import argparse, json
    p = argparse.ArgumentParser(description="Rileva fratture/rotture su una fila.")
    p.add_argument("fila", help="immagine di una singola fila (fila_NN.png)")
    p.add_argument("--metodo", choices=["classico", "sam"], default="classico")
    p.add_argument("--scala-cm-px", type=float, default=None)
    p.add_argument("-o", "--output", default="fratture_out.png")
    a = p.parse_args()

    img = cv2.imread(a.fila)
    if img is None:
        raise SystemExit(f"Immagine non trovata: {a.fila}")

    if a.metodo == "classico":
        fratture, vis = traccia_fratture_classico(img)
        cv2.imwrite(a.output, vis)
        print(f"[i] Fratture candidate: {len(fratture)} -> {a.output}")
    else:
        pezzi = segmenta_pezzi_sam(a.fila)
        print(json.dumps(rotture_da_pezzi(pezzi, a.scala_cm_px), indent=2, ensure_ascii=False))
