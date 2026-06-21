#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reproduce.py — rigenera i risultati chiave del progetto con un comando.

Esegue (veloci, solo OpenCV/YOLO — SAM escluso perché 24 s/crop):
  1. recovery-aware ablation     -> experiments/out/recovery_aware_results.csv
  2. borehole breakdown          -> experiments/out/borehole_breakdown.csv
  3. casi curati della demo      -> geocore/demo_cases_out/

Per il confronto a tre vie con SAM (lento) usare:  python experiments/spike_models.py

Uso:  python reproduce.py
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "experiments"))


def main():
    print("=" * 60)
    print("GeoCore — riproduzione risultati (SAM escluso)")
    print("=" * 60)

    print("\n[1/3] Ablazione recovery-aware …")
    import recovery_aware_eval
    recovery_aware_eval.main()

    print("\n[2/3] Borehole breakdown (Z441-specifico vs sistemico) …")
    import borehole_breakdown
    borehole_breakdown.main()

    print("\n[3/3] Casi curati della demo …")
    from geocore import demo_cases
    casi = demo_cases.build(force=True)
    print(f"    casi generati: {len(casi)}")

    print("\n[OK] Risultati in experiments/out/ e geocore/demo_cases_out/")
    print("     Avvia la demo con:  streamlit run app.py")


if __name__ == "__main__":
    main()
