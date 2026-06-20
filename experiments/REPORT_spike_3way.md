# Spike a tre vie — OpenCV vs SAM vs YOLO-seg (RQD)

**Data:** 2026-06-20 · **Harness:** identico al §6 (GT = poligoni TenCm annotati, RQD recovery-based in rapporto di pixel) · **Codice:** [`spike_models.py`](spike_models.py)
**Test set:** sondaggio **Z441 held-out** (mai visto da YOLO in training), 58 manovre. Split per sito = test di generalizzazione reale.

> ⚠️ Il dataset è 64% Z441 → tenerlo come unico held-out è il caso peggiore di hold-out mono-sito. È un test severo, volutamente.

## Tabelle

**A — Candidati sul test pieno (58 manovre)**

| Detector | MAE (pp) | corr | classe% | entro5% | **MAE_poor** | t/crop |
|---|---:|---:|---:|---:|---:|---:|
| OpenCV (baseline) | **21.7** | −0.12 | 31 | 14 | 75.2 | **2 ms** |
| YOLO11-seg (addestrato) | 34.2 | +0.16 | 33 | **31** | **16.4** | 150 ms |

**B — Tre vie sullo stesso subset stratificato (16 manovre)**

| Detector | MAE (pp) | corr | classe% | entro5% | MAE_poor | t/crop |
|---|---:|---:|---:|---:|---:|---:|
| OpenCV | 27.3 | −0.10 | 19 | 0 | 73.6 | 4 ms |
| SAM2.1 (zero-shot, 640px) | 42.2 | +0.33 | 6 | 6 | 22.3 | **24 223 ms** |
| YOLO11-seg | 37.7 | +0.07 | 12 | 12 | 18.4 | 83 ms |

## Esempi (YOLO, test pieno)

**5 migliori** (err ~0): manovre a 295, 267, 413, 142, 135 m → GT 87–99%, PRED entro 0.2 pp. **YOLO sa farlo perfettamente.**

**5 peggiori** (err ~95): manovre a 253, 392, 420, 406, 316 m → GT 93–98% (roccia integra), **PRED ≈ 0%**. YOLO non rileva nulla su carota sana. L'overlay `cmp_poor_YOLO11-seg.png` lo mostra: carota visibilmente intatta, zero box rilevati.

## Interpretazione

- **SAM è eliminato.** Peggior MAE, classe 6%, e **24 s/crop** (≈12 000× più lento di OpenCV, 160× di YOLO): non deployabile. La correlazione +0.33 è l'unico spunto, irrilevante dato il costo. Box-prompted sarebbe ridondante con YOLO-seg.
- **OpenCV "vince" sul MAE (21.7) ma è un'illusione:** correlazione **negativa** (anti-diagnostico), satura a ~100%, **MAE_poor 75** (catastrofico e in direzione ottimistica = pericolosa). Bassa MAE solo perché Z441 è in prevalenza roccia buona e la saturazione "azzecca" per caso.
- **YOLO è l'unico con segnale reale:** azzecca **31% delle manovre entro 5 pp** (incl. roccia intatta), ed è **4.6× meglio sulla roccia scadente** (MAE_poor 16 vs 75) — l'errore che conta per la sicurezza. Ma è **bimodale**: o err≈0 o predice 0% su roccia sana.
- **Il dato più importante:** val mask mAP50 = **0.97** (immagini di sondaggi nel training) vs correlazione **+0.16** sul sondaggio held-out. Il 0.97 era un **miraggio da leakage**. La generalizzazione cross-sondaggio crolla.
- **Confondente noto:** l'RQD usa una scala derivata assumendo recupero 100% → penalizza i predittori (il GT no). Parte dei 34 pp è artefatto di scala, non modello.

## Risposte da investitore

1. **Quale metodo vince?** **YOLO-seg.** SAM perde su tutto (costo + accuratezza). OpenCV ha MAE più basso ma è anti-diagnostico (corr negativa, fallisce dove conta). YOLO è l'unico che a volte è *esatto* ed è il più sicuro sulla roccia scadente.
2. **Migliora vs baseline OpenCV (31.2 globale)?** Sul MAE grezzo del sondaggio held-out, **no** (YOLO 34.2 > OpenCV 21.7). Sulla metrica che conta — errore su roccia scadente — **sì, drasticamente** (16 vs 75) e la correlazione passa da negativa a positiva.
3. **Supera la soglia di interesse (<15 pp)?** **NO.** Miglior MAE 21.7 (illusorio) / YOLO 34.2. Nessuno < 15 pp sul held-out.
4. **Supera la soglia di investimento (<8 pp)?** **NO**, lontanissimo.
5. **Finanzierei i prossimi 6 mesi?** **No — non 6 mesi, non ora.** Ma neanche stop secco. Vedi sotto.

## Raccomandazione: **NO-GO sui 6 mesi · GO su uno sprint di de-risking 3–4 settimane**

Lo spike **non ha superato il gate** (<15 pp). Da investitore onesto, finanziare 6 mesi/100k oggi sarebbe ignorare che su un sondaggio mai visto **nessun metodo traccia l'RQD** (corr ~0) e che YOLO predice 0% su roccia intatta. Il 0.97 di mAP era leakage.

Ma il fallimento è **diagnosticabile e a basso costo da de-rischiare**, e lo spike ha già **eliminato SAM** (risparmio) e isolato il candidato (YOLO). Quindi:

**Finanziare uno sprint da ~3–4 settimane (~€8–12k), non 6 mesi.** Obiettivi misurabili:
1. **Togliere il confondente di scala** (marker ArUco / denominatore recovery-aware) e ri-misurare: quanto dei 34 pp è artefatto vs modello?
2. **Cross-validation per sondaggio** (non solo Z441): Z441 è unicamente difficile o è sistemico?
3. **Risolvere l'aspetto 17:1 delle strisce** (tiling) + modello più grande + più dati → attaccare i casi "predice 0 su roccia sana".
4. **Diagnosi dei casi a err≈95**: domain shift o artefatto di soglia?

**Gate dello sprint:** MAE ≤ 15 pp sotto borehole-CV con denominatore recovery-aware. Solo allora valutare i 6 mesi/100k — e con il vero moat (carote **italiane** + ground-truth dei geologi), non con un dataset cinese mono-sondaggio.

**Sintesi:** lo spike ha fatto il suo lavoro da €2k: ci ha impedito di scommettere 100k su una tesi che non ha superato neanche la soglia di interesse, indicando però gli esperimenti economici che la chiarirebbero. Questo *è* il ritorno dell'esperimento.

---
*Output: `experiments/out/spike_results.csv`, `cmp_{good,poor}_{OpenCV,YOLO11-seg}.png`.*
