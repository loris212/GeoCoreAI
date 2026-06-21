#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli.py — entrypoint GeoCore Demo v1.
  python -m geocore foto.jpg --scomparto-cm 100 --manovra-cm 500 -o out/
Salva overlay PNG + risultato JSON e stampa un riepilogo.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import json
import cv2

from geocore.pipeline import analizza


def main(argv=None):
    p = argparse.ArgumentParser(description="GeoCore Demo v1 — foto cassetta -> RQD")
    p.add_argument("immagine")
    p.add_argument("--scala-cm-px", type=float, default=None,
                   help="scala fisica cm/px (se nota da marker/righello)")
    p.add_argument("--scomparto-cm", type=float, default=None,
                   help="lunghezza interna nota di uno scomparto (per derivare la scala)")
    p.add_argument("--manovra-cm", type=float, default=None,
                   help="lunghezza perforata della manovra (denominatore RQD ASTM)")
    p.add_argument("-n", "--n-file", type=int, default=None, help="n. scomparti attesi")
    p.add_argument("-o", "--output", default="geocore_out")
    a = p.parse_args(argv)

    out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
    res = analizza(a.immagine, scala_cm_px=a.scala_cm_px, scomparto_cm=a.scomparto_cm,
                   manovra_cm=a.manovra_cm, n_file=a.n_file)
    overlay = res.pop("_overlay")
    stem = Path(a.immagine).stem
    cv2.imwrite(str(out / f"{stem}_overlay.png"), overlay)
    (out / f"{stem}_rqd.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))

    print(f"[i] File rilevate: {res['n_file']}  | rettifica: {res['rettifica_applicata']}")
    print(f"[i] Scala: {res['scala_cm_px']} cm/px  | soglia 10cm: {res['soglia_10cm_px']} px")
    if res["rqd_cassetta"] is not None:
        print(f"[i] RQD cassetta: {res['rqd_cassetta']}% ({res['classe_cassetta']}) "
              f"[denominatore: {res['denominatore']}]")
    else:
        print("[!] RQD non calcolabile: manca la scala (usa --scomparto-cm o --scala-cm-px)")
    print(f"[i] Output in {out.resolve()}")
    print(f"[disclaimer] {res['disclaimer']}")


if __name__ == "__main__":
    main()
