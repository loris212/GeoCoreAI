#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phase2_segment.py — Fase 2: segmentazione dei pezzi di carota con YOLO11-seg.
Versione di PRODUZIONE, disaccoppiata da experiments/spike_models.py: carica il
modello UNA volta (fix del bug "ricarico a ogni chiamata") e ritorna i pezzi con
bbox completo (non solo x-extent), utile per overlay e misura.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import cv2

_PKG = Path(__file__).resolve().parent
# modello versionato nel pacchetto; fallback all'output di training se assente
_DEFAULT_WEIGHTS = _PKG / "models" / "best.pt"
_FALLBACK_WEIGHTS = _PKG.parent / "experiments/yolo_runs/piece_seg/weights/best.pt"
_MAXW = 1280          # i crop sono strisce molto larghe; cap per inferenza
_COVER_V = 0.40       # un pezzo copre >=40% dell'altezza della fila


def pick_device() -> str:
    """Sceglie il device disponibile: mps (Mac) -> cuda -> cpu (cloud/server)."""
    try:
        import torch
        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


class PieceSegmenter:
    """Segmentatore di pezzi. Carica il modello una sola volta."""

    def __init__(self, weights: str | Path | None = None, device: str | None = None):
        weights = Path(weights) if weights else (
            _DEFAULT_WEIGHTS if _DEFAULT_WEIGHTS.exists() else _FALLBACK_WEIGHTS)
        if not weights.exists():
            raise FileNotFoundError(
                f"Pesi YOLO non trovati: {weights}\n"
                "Riproduci il modello con experiments/prep_e_train_yolo.py")
        from ultralytics import YOLO
        self.model = YOLO(str(weights))
        self.device = device or pick_device()

    def segment(self, row_img: np.ndarray, min_width_px: float = 0.0) -> list[dict]:
        """Segmenta una fila -> lista di pezzi {x0,x1,y0,y1,larghezza_px}, sx->dx.
        min_width_px: soglia opzionale (10 cm in pixel) per tenere solo i pezzi 'integri'.
        """
        H0, W0 = row_img.shape[:2]
        sc = _MAXW / W0 if W0 > _MAXW else 1.0
        small = (cv2.resize(row_img, (int(W0 * sc), max(8, int(H0 * sc))))
                 if sc < 1.0 else row_img)
        res = self.model(small, verbose=False, device=self.device, retina_masks=True)
        if not res or res[0].masks is None:
            return []
        Hs = small.shape[0]
        masks = res[0].masks.data.cpu().numpy() > 0.5
        pezzi = []
        for m in masks:
            if m.shape != small.shape[:2]:
                m = cv2.resize(m.astype(np.uint8), (small.shape[1], Hs)) > 0
            ys, xs = np.where(m)
            if len(xs) == 0 or (ys.max() - ys.min()) < _COVER_V * Hs:
                continue
            x0, x1 = int(xs.min() / sc), int(xs.max() / sc)
            y0, y1 = int(ys.min() / sc), int(ys.max() / sc)
            w = x1 - x0
            if w >= min_width_px:
                pezzi.append({"x0": x0, "x1": x1, "y0": y0, "y1": y1, "larghezza_px": w})
        return sorted(pezzi, key=lambda p: p["x0"])
