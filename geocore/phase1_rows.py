#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phase1_rows.py — Fase 1: caricamento (EXIF-corretto) + rettifica + taglio file.
Riusa gli ALGORITMI di estrai_file_carote.py (single source), ma corregge il bug
noto del caricamento: cv2.imread ignora il flag EXIF di rotazione -> foto da
telefono caricate storte. Qui si applica PIL.ImageOps.exif_transpose in ingresso.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import cv2

# algoritmi esistenti, riusati senza duplicarli
from estrai_file_carote import (raddrizza_cassetta, profilo_texture,
                                 trova_divisori, taglia_in_file)


def carica_immagine_exif(percorso: str, lato_max: int = 2000) -> np.ndarray:
    """Carica rispettando l'orientamento EXIF, poi ridimensiona (BGR per OpenCV)."""
    try:
        from PIL import Image, ImageOps
        with Image.open(percorso) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            img = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
    except Exception:
        # fallback: nessun EXIF disponibile -> imread classico
        img = cv2.imread(percorso)
    if img is None:
        raise FileNotFoundError(f"Immagine non leggibile: {percorso}")
    h, w = img.shape[:2]
    s = lato_max / max(h, w)
    if s < 1.0:
        img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    return img


def estrai_file(percorso: str, n_file: int | None = None, lato_max: int = 2000):
    """Da percorso immagine -> (warp, rettifica_applicata, file).
    file = lista di dict {indice, y0, y1, banda (np.ndarray)}.
    """
    img = carica_immagine_exif(percorso, lato_max)
    warp, quad = raddrizza_cassetta(img)
    prof = profilo_texture(warp)
    bande = taglia_in_file(warp, trova_divisori(prof, n_file))
    file_ = [{"indice": i + 1, "y0": int(y0), "y1": int(y1), "banda": banda}
             for i, (y0, y1, banda) in enumerate(bande)]
    return warp, (quad is not None), file_
