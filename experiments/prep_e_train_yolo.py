#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prep_e_train_yolo.py  (SPIKE — preparazione dati + training YOLO11-seg)
======================================================================
Converte le annotazioni LabelMe 'TenCm' in formato YOLO-seg e addestra
YOLO11n-seg con SPLIT PER SONDAGGIO (no leakage):
  - TEST  = sondaggio Z441 (mai visto in training)  -> NON entra qui
  - TRAIN = tutti gli altri sondaggi (TenCm)
Il test viene fatto da spike_models.py sullo stesso harness §6.

Non modifica gli script esistenti, non tocca il ground-truth.
"""
from __future__ import annotations
from pathlib import Path
import json, re, random, shutil, sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rqd_baseline import SEG_DIR, TENCM_LABELS, RE_SOND   # riuso esatto

HERE = Path(__file__).resolve().parent
DS = HERE / "yolo_ds"
TEST_SOND = "Z441"          # sondaggio held-out (il piu' numeroso) -> test
random.seed(7)


def borehole(stem: str):
    m = RE_SOND.search(stem)
    return m.group(1).upper() if m else None


def to_yolo_seg(json_path: Path):
    """Ritorna (W, H, [righe_yolo]) per le polilinee TenCm normalizzate."""
    d = json.load(open(json_path, encoding="utf-8"))
    W, H = d.get("imageWidth"), d.get("imageHeight")
    if not W or not H:
        return None
    righe = []
    for s in d.get("shapes", []):
        if s["label"].lower() not in TENCM_LABELS:
            continue
        pts = s["points"]
        if len(pts) < 3:
            continue
        coord = []
        for x, y in pts:
            coord.append(f"{min(max(x / W, 0), 1):.6f}")
            coord.append(f"{min(max(y / H, 0), 1):.6f}")
        righe.append("0 " + " ".join(coord))
    return (W, H, righe) if righe else None


def main():
    if DS.exists():
        shutil.rmtree(DS)
    for sub in ["images/train", "images/val", "labels/train", "labels/val"]:
        (DS / sub).mkdir(parents=True, exist_ok=True)

    train_items, n_test_skip = [], 0
    for jf in SEG_DIR.glob("*.json"):
        b = borehole(jf.stem)
        if b is None:
            continue
        if b == TEST_SOND:               # held-out: escluso dal training
            n_test_skip += 1
            continue
        jpg = jf.with_suffix(".jpg")
        if not jpg.exists():
            continue
        conv = to_yolo_seg(jf)
        if conv is None:
            continue
        train_items.append((jf, jpg, conv))

    random.shuffle(train_items)
    n_val = max(1, int(len(train_items) * 0.15))
    val_set = set(range(n_val))

    for i, (jf, jpg, (W, H, righe)) in enumerate(train_items):
        split = "val" if i in val_set else "train"
        # symlink dell'immagine (niente copie pesanti)
        dst_img = DS / f"images/{split}/{jpg.stem}.jpg"
        if not dst_img.exists():
            dst_img.symlink_to(jpg.resolve())
        (DS / f"labels/{split}/{jpg.stem}.txt").write_text("\n".join(righe))

    yaml = DS / "dataset.yaml"
    yaml.write_text(
        f"path: {DS}\ntrain: images/train\nval: images/val\nnames:\n  0: piece\n")

    print(f"[i] TRAIN immagini: {len(train_items)-n_val}  VAL: {n_val}  "
          f"(escluse {n_test_skip} di {TEST_SOND} = test)")

    # --- training ---
    import os
    os.environ.setdefault("PYTORCH_MPS_HIGH_WATERMARK_RATIO", "0.0")
    from ultralytics import YOLO
    model = YOLO("yolo11n-seg.pt")
    model.train(data=str(yaml), epochs=60, imgsz=640, rect=True, batch=4,
                device="mps", project=str(HERE / "yolo_runs"), name="piece_seg",
                patience=20, verbose=True, plots=False, exist_ok=True)
    print("[i] best:", HERE / "yolo_runs/piece_seg/weights/best.pt")


if __name__ == "__main__":
    main()
