#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
valuta_calibrazione.py
======================
Mette alla frusta estrai_file_carote.py su tutto il set di calibrazione.
Per ogni foto confronta il numero di file RILEVATE con quelle VERE (verita.csv)
e stampa: accuratezza globale + elenco dei casi sbagliati (su cui debuggare).

Metrica Tier-1 (economica): "ha contato il giusto numero di file?".
E' il primo filtro: se sbaglia gia' il conteggio, e' inutile misurare i tagli.

USO:
  python valuta_calibrazione.py calibrazione/foto calibrazione/verita.csv
"""

from __future__ import annotations
from pathlib import Path
import csv
import sys

# riusa la pipeline della Fase 1 (stesso parametro -n NON passato: test "a freddo")
from estrai_file_carote import (carica_immagine, raddrizza_cassetta,
                                 profilo_texture, trova_divisori, taglia_in_file)


def conta_file(percorso_foto: str) -> int:
    img = carica_immagine(percorso_foto)
    warp, _ = raddrizza_cassetta(img)
    file_ = taglia_in_file(warp, trova_divisori(profilo_texture(warp), n_file=None))
    return len(file_)


def main(cartella_foto: str, csv_verita: str):
    foto_dir = Path(cartella_foto)
    righe = [r for r in csv.DictReader(open(csv_verita, encoding="utf-8"))
             if r.get("file") and r.get("n_file_vere")]
    if not righe:
        sys.exit("[!] verita.csv vuoto o senza colonne 'file'/'n_file_vere'.")

    ok, errori = 0, []
    for r in righe:
        f = foto_dir / r["file"]
        if not f.exists():
            errori.append((r["file"], "MANCANTE", r["n_file_vere"])); continue
        try:
            rilevate = conta_file(str(f))
        except Exception as e:
            errori.append((r["file"], f"ERRORE:{e}", r["n_file_vere"])); continue
        vere = int(r["n_file_vere"])
        if rilevate == vere:
            ok += 1
        else:
            errori.append((r["file"], rilevate, vere))

    tot = len(righe)
    print(f"\n=== RISULTATO CALIBRAZIONE ===")
    print(f"Accuratezza conteggio file: {ok}/{tot} = {100*ok/tot:.1f}%\n")
    if errori:
        print("Casi da debuggare (file | rilevate | vere):")
        for f, ril, ver in errori:
            print(f"  - {f:35s} | {ril} | {ver}")
    else:
        print("Nessun errore: la Fase 1 e' pronta per i casi avversi successivi.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Uso: python valuta_calibrazione.py <cartella_foto> <verita.csv>")
    main(sys.argv[1], sys.argv[2])
