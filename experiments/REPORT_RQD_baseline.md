# Esperimento §6 — Baseline RQD su dataset Kaggle

**Data:** 2026-06-20 · **Tipo:** feasibility probe, read-only · **Codice:** [`rqd_baseline.py`](rqd_baseline.py)
**Vincoli rispettati:** nessuno script esistente modificato, nessun file eliminato, nessun training, nessun download (no SAM/torch).

---

## 1. Cosa è stato misurato

Testare la tesi di prodotto — *«da una foto di carota si ricava un RQD affidabile»* — usando **solo** il dataset già presente in `archive/`, senza annotare nulla.

Per ogni **manovra** (gruppo di righe con stesso sondaggio + range di profondità, ricostruito dal nome file) si confrontano due RQD:

| Stima | Numeratore | Denominatore |
|-------|-----------|--------------|
| **RQD_GT** (verità) | Σ lunghezze pezzi `TenCm` **annotati a mano** | Σ larghezza righe |
| **RQD_CV** (baseline) | Σ lunghezze pezzi ≥10 cm **rilevati da CV classica** | Σ larghezza righe |

Entrambe sono RQD *recovery-based* in **rapporto di pixel** → la scala cm/px si cancella. La soglia fisica dei 10 cm per il rilevatore CV è derivata per-manovra dal range di profondità nel nome file.

> **Onestà metodologica.** RQD_GT qui è "recovery RQD" (denominatore = riga recuperata), non l'RQD ASTM puro (denominatore = lunghezza perforata). È la scelta robusta: non richiede scala e misura la *fisica* del problema — separare i pezzi ≥10 cm dal resto — che è ciò che vogliamo testare. Il dataset è cinese: valida la **fattibilità tecnica**, non il fit di mercato Italia né il moat.

## 2. Numeri

| Voce | Valore |
|------|--------|
| Immagini `core bands` | **150** (annotazioni `Core`: **849**) |
| Immagini `core segments >10cm` | **325** (annotazioni `TenCm`: **1023**) |
| Manovre ricostruite dai nomi file | **91** (su 158; 67 crop con nome non parsabile) |
| Manovre valutabili (GT + CV) | **91** |
| Distribuzione RQD_GT (min/med/max) | **11 / 78 / 99** |

## 3. Risultato baseline CV classica

| Metrica | Valore | Lettura |
|---------|-------:|---------|
| **MAE RQD** | **31.2 pp** | — |
| MAE "naive" (predici sempre la media) | **21.3 pp** | ❌ la CV è **peggio** del tirare a indovinare |
| Manovre entro ±5 pp | 9% | gate prodotto: ≥ ~80% |
| Accuratezza classe di Deere | 21% | gate prodotto: ≥ 90% |
| Correlazione GT vs CV | **+0.17** | praticamente nulla |
| **MAE su roccia scadente (GT<50)** | **65.3 pp** | ❌ catastrofico dove conta di più |
| MAE su roccia buona (GT≥75) | 11.4 pp | "giusto" solo per caso |
| Manovre in cui CV satura a ≥95% | **88 / 91** | la baseline è di fatto un *«RQD=100» costante* |

![scatter](out/rqd_scatter.png)

Lo scatter è una **riga piatta in alto**: il predittore restituisce ~100% qualunque sia la verità.

## 4. Esempi

**Successo** (`out/esempio_successo_*.png`): roccia integra, GT≈98%, CV≈100%. La baseline "azzecca" solo perché la carota *è* un pezzo unico — non perché abbia capito qualcosa.

**Fallimento** (`out/esempio_fallimento_*.png`): es. `Z441 44-51m`, GT=11%, CV=100%, **errore 89 pp**. La carota è visibilmente in decine di frammenti < 10 cm; il GT (verde) marca i pochi pezzi sani, ma la CV (rosso) vede texture continua e fonde tutto in un unico pezzo da 100%.

## 5. Perché fallisce (diagnosi tecnica)

Il rilevatore classico individua i **vuoti aperti** (carota persa) come gap di texture, ma **non vede le fratture chiuse** — i pezzi che si toccano senza vuoto visibile. In una carota frammentata ma compatta non c'è nessun gap di texture → la legge "un solo pezzo lungo" → RQD ≈ 100%. È esattamente il limite previsto in `fratture.py` ("fratture chiuse che SAM fonde in uno solo") e l'errore va **sempre nella direzione pericolosa**: ottimistico (sovrastima la qualità dell'ammasso).

## 6. Conclusione — GO / NO-GO

### ✅ Cosa è stato dimostrato POSITIVAMENTE
1. **Il ground-truth RQD è derivabile dai dati esistenti, oggi, a costo zero** (91 manovre, distribuzione geologicamente sensata 11–99%).
2. **Esiste un'infrastruttura di misura riusabile** ([`rqd_baseline.py`](rqd_baseline.py)): qualsiasi nuovo modello si valuta in minuti contro un MAE reale.

### ❌ Cosa è stato REFUTATO
3. **La CV classica da sola NON è un motore RQD.** Peggio del tirare a indovinare, anti-diagnostica proprio sulla roccia scadente. Il valore del prodotto **non** può poggiare sulla Fase 1/3 classica.

### 🎯 Verdetto: **GO CONDIZIONATO** (non un no-go di progetto)

L'esperimento **non refuta la tesi di prodotto** — la refuta *per la sola CV classica*. Ha però fatto la cosa più utile possibile con 100k€ in gioco: **ha ridotto l'intero rischio a una sola domanda misurabile** —

> *Un modello di segmentazione proper (SAM 2.1 box-promptato / YOLO11-seg) separa i pezzi che si toccano abbastanza bene da portare il MAE RQD da 31 a ≤ 5 pp?*

**Raccomandazione d'investimento:** finanziare **solo** uno *spike di Fase 2* da ~1 settimana, gate-ato:
- far girare SAM/YOLO sulle **stesse 91 manovre** attraverso **questo stesso harness**;
- **gate GO:** MAE ≤ 8 pp e accuratezza di classe ≥ 80% sul hold-out per sondaggio → sblocca il build completo (Fase 4 + design-partner);
- **gate NO-GO:** se nemmeno SAM scende sotto ~15 pp, la fisica 2D non basta → stop, risparmiati ~90k€.

Non finanziare il build completo prima di questo gate. Il dataset Kaggle permette di comprare la risposta in giorni, non mesi.

---
*Output completi in `experiments/out/`: `rqd_results.csv` (91 manovre), `rqd_scatter.png`, `esempio_{successo,fallimento}_*.png`.*
