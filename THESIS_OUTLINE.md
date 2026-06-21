# GeoCore AI — Ossatura della tesi

> Stima automatica dell'RQD da foto di cassette di sondaggio: **una pipeline e una
> valutazione rigorosa della generalizzazione cross-sito.**
>
> Tesi: il contributo non è un prodotto, è la **valutazione onesta** di un metodo noto
> (YOLO11+SAM) — dove funziona, dove fallisce e perché. Ogni capitolo è già supportato
> da codice/artefatti riproducibili in questo repo.

## Struttura proposta

| # | Capitolo | Contenuto | Artefatti nel repo |
|---|---|---|---|
| 1 | **Introduzione** | RQD, log geomeccanico, perché automatizzare; obiettivo e contributo | `GeoCoreAI_MASTER_CONTEXT.md` (§1, §4) |
| 2 | **Stato dell'arte** | CV su carote; CNN/SAM/YOLO per RQD; prodotti commerciali (Datarock, Imago, KORE) | sezione "ricerca di mercato" della chat + sources |
| 3 | **Specifica geologica dell'RQD** | Definizione ASTM D6032/Deere, soglia 10 cm, centerline, ricucitura, denominatore manovra | `GeoCoreAI_MASTER_CONTEXT.md` §4; `geocore/phase4_rqd.py` |
| 4 | **Dataset e ground-truth** | Kaggle core-bands/core-segments; derivazione RQD dai poligoni TenCm; split per sondaggio | `experiments/rqd_baseline.py`; `archive/` |
| 5 | **Metodo (pipeline)** | Fase 1 rettifica+file; Fase 2 YOLO11-seg; Fase 4 RQD; addestramento | `geocore/` (phase1/2/4, pipeline); `experiments/prep_e_train_yolo.py` |
| 6 | **Esperimenti** | Baseline OpenCV; spike a tre vie OpenCV/SAM/YOLO; ablazione recovery-aware; borehole-CV | `experiments/spike_models.py`, `recovery_aware_eval.py`, `borehole_breakdown.py` |
| 7 | **Risultati e analisi dei limiti** | mAP vs MAE; gap di generalizzazione (val 0.97 → held-out 0.16); osservabilità; falsificazioni | `experiments/REPORT_spike_3way.md`, `REPORT_RQD_baseline.md`, `GeoCore_AI_Observability_Note.md` |
| 8 | **Discussione** | Misura vs modello; perché la generalizzazione è il limite; ruolo human-in-the-loop | `GeoCore_AI_Observability_Note.md`; risultati cap. 6 |
| 9 | **Conclusioni e lavori futuri** | Dataset multi-sito, marker ArUco, recupero-aware reale; cosa servirebbe per un prodotto | documenti strategici (sintesi) |
| — | **Appendice: demo** | App Streamlit (pipeline live + casi validati) come dimostrazione | `app.py`; `README.md` |

## Risultati-chiave da citare (numeri reali, riproducibili)

- Baseline OpenCV su 91 manovre: **MAE 31.2 pp** (satura ~100%, corr 0.17).
- Spike a tre vie (held-out Z441, 58 manovre): OpenCV **21.7** / SAM **42.2** (24 s/crop) / YOLO **34.2**.
- val mask **mAP50 ≈ 0.97** (in-sample) vs **corr +0.16** held-out = **gap di generalizzazione**.
- Ablazione recovery-aware: GT invariato (0/58), MAE invariato → **ipotesi misura falsificata**.
- Borehole breakdown: Z441 (held-out) MAE 34 vs in-sample ~6 → **debolezza sistemica, non Z441**.

## Punti di forza della tesi (da evidenziare in discussione)

1. **Split per sondaggio** (no leakage) — rigore raro in una triennale.
2. **Esperimenti di falsificazione** che smontano le spiegazioni comode (misura, soglia, Z441).
3. **Onestà sui limiti**: la demo mostra volutamente un fallimento.
4. **Riproducibilità**: `python reproduce.py` rigenera i risultati; modello versionato.

## Come riprodurre i risultati

```bash
pip install -r requirements.txt
python reproduce.py                 # ablazioni + breakdown + casi demo (no SAM)
python experiments/spike_models.py  # confronto a tre vie completo (con SAM, lento)
streamlit run app.py                # demo
```
