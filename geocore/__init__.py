#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
geocore — pipeline di produzione GeoCore Demo v1
================================================
Livello PULITO e DISACCOPPIATO sopra il lavoro esistente:
  - phase1_rows   : carica (EXIF-corretto) + rettifica + taglia le file   [riusa estrai_file_carote]
  - phase2_segment: segmenta i pezzi di carota con YOLO11-seg              [modello addestrato]
  - phase4_rqd    : foto NUOVA (senza ground-truth) -> RQD + classe Deere  [NUOVO, mancava]
  - pipeline      : orchestratore foto -> risultato + overlay

NON tocca experiments/ (la spina scientifica della tesi resta riproducibile).
"""
from __future__ import annotations
import sys
from pathlib import Path

# rende importabili gli script di Fase 1 alla radice del repo (single source of truth)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

__all__ = ["phase1_rows", "phase2_segment", "phase4_rqd", "pipeline"]
__version__ = "0.1.0"
