# GeoCore AI — Decision Memo v1

> **Scopo.** Trasformare i risultati sperimentali ottenuti finora in una decisione operativa.
> Basato **esclusivamente** su ciò che è stato misurato (esperimento §6 + spike a tre vie su
> sondaggio held-out Z441). Nessuna nuova assunzione, nessun nuovo benchmark.
> **Data:** 2026-06-20 · **Autore:** CTO/Investor review · **Verdetto:** NO-GO sui 6 mesi · GO sulle 2–4 settimane.

---

## 1. Stato attuale del progetto

Prototipo di Computer Vision per calcolo automatico dell'**RQD** da foto di cassette catalogatrici.
- Fase 1 (estrazione file): prototipo OpenCV, mai misurato contro ground-truth.
- Fase 2/3 (segmentazione pezzi, rotture): YOLO11-seg addestrato + SAM valutato e **scartato**.
- Fase 4 (calcolo RQD): **non esiste come modulo**; l'RQD è stato calcolato solo dentro l'harness di valutazione.
- È stato costruito un **harness di misura riusabile** che deriva l'RQD ground-truth dalle annotazioni Kaggle (TenCm) senza annotare nulla.

**Risultati di riferimento (test held-out Z441, 58 manovre):**

| Metodo | MAE (pp) | corr | entro5% | MAE roccia scadente | t/crop |
|---|---:|---:|---:|---:|---:|
| OpenCV baseline | 21.7 | −0.12 | 14 | 75.2 | 2 ms |
| **YOLO11-seg** | 34.2 | +0.16 | 31 | **16.4** | 150 ms |
| SAM2.1 (zero-shot) | 42.2 | +0.33 | 6 | 22.3 | 24 223 ms |

Soglie di prodotto (da MASTER_CONTEXT, Fase 4): MAE ≤ 5 pp, accuratezza di classe ≥ 90%. **Oggi siamo lontani.**

---

## 2. Cosa è stato VALIDATO

- **L'RQD ground-truth è derivabile dai dati esistenti a costo zero** (91 manovre, distribuzione 11–99%, mediana sensata). L'harness funziona ed è brutalmente onesto.
- **YOLO-seg è capace, in linea di principio:** su un terzo delle manovre held-out l'errore è ~0 (5 migliori: err 0.0–0.2 pp), incluse rocce integre. La fisica del problema è risolvibile *su alcuni casi*.
- **YOLO è il candidato giusto e il più sicuro sulla roccia scadente** (MAE_poor 16 vs 75 di OpenCV): gli errori, quando ci sono, tendono a non essere ottimistici-pericolosi.

## 3. Cosa è stato FALSIFICATO

- **SAM (automatico) come motore RQD: morto.** 24 s/crop (≈12 000× OpenCV), MAE peggiore, classe 6%. Non deployabile, non più accurato. Box-prompted sarebbe ridondante con YOLO-seg.
- **La CV classica come motore RQD: falsificata.** Satura a ~100%, correlazione **negativa**, catastrofica sulla roccia scadente (MAE_poor 75). Il MAE basso (21.7) è un'illusione statistica (Z441 è in prevalenza roccia buona).
- **Il "0.97 di mAP50" come prova di funzionamento: falsificato.** Era misurato su immagini degli **stessi** sondaggi del training (leakage). Sul sondaggio mai visto la correlazione crolla a +0.16. **Il modello non generalizza cross-sito.**

## 4. Cosa sappiamo con ALTA confidenza

- SAM è fuori gioco per questo task/hardware.
- La metrica image-level (mAP) sovrastima enormemente la performance reale; conta solo la **CV per sondaggio**.
- Il fallimento di YOLO è **bimodale** (o err≈0 o predice 0% su roccia sana), quindi guidato da pochi casi catastrofici, non da rumore diffuso → è **diagnosticabile**, non un muro.
- Esiste un **confondente di misura**: l'RQD assume recupero 100% per la scala → penalizza i predittori ma non il GT. Parte dei 34 pp non è colpa del modello.
- Il dataset è **mono-sondaggio** (Z441 = 64%): l'hold-out attuale è il caso peggiore di generalizzazione.

## 5. Cosa NON sappiamo ancora

- **Il MAE "vero"** dopo aver tolto il confondente di scala e fatto CV multi-sondaggio (potrebbe essere sensibilmente < 34 pp, o no).
- Se i casi "predice 0% su roccia sana" siano **geometria input** (strisce 17:1 schiacciate dal letterboxing) o domain shift di lithology/illuminazione.
- Se il metodo **generalizzi a carote italiane** (mai testato — dataset cinese).
- Se esista **domanda di mercato reale**: nessun geologo design-partner, nessuna LOI, nessun log RQD italiano.
- Se la **Fase 1** regga (mai misurata contro i 849 poligoni `Core` disponibili).

## 6. Rischi tecnici

1. **Generalizzazione cross-sito** (il più grave): oggi non c'è.
2. **Geometria del dato**: strisce 17:1 mal gestite dai modelli standard → possibili miss sistematici.
3. **Misura confondibile**: scala a recupero 100%, denominatore non robusto.
4. **Dipendenza dalla scala fisica** (cm/px) per la soglia 10 cm: senza marker ArUco affidabile, errore a monte.

## 7. Rischi commerciali

1. **Moat inesistente oggi**: il valore difendibile è dato italiano + GT geologi, **non** il codice (replicabile in ~2 settimane).
2. **Distribuzione/validazione di mercato**: zero design-partner; serve fiducia di un albo professionale conservativo.
3. **Vincolo legale**: la relazione la firma un geologo abilitato → human-in-the-loop obbligatorio → il prodotto vende "misura + candidati", non automazione piena. Riduce il valore percepito.
4. **Rischio "tecnologia ≠ azienda"**: anche se la CV funzionasse, manca tutto il resto (dato, canale, fiducia).

## 8. Probabilità attuale di successo

Stima soggettiva, dichiarata come tale (non misurata):

| Livello | Prob. stimata | Razionale |
|---|---:|---|
| Fattibilità tecnica (MAE ≤ ~10 pp, generalizzante) | **35–45%** | fallimenti diagnosticabili, 1/3 già perfetto, ma generalizzazione oggi assente |
| Moat dati + adozione di mercato | **35–50%** | plausibile ma interamente da costruire, zero evidenza |
| **Prodotto vendibile (congiunto)** | **~15–25%** | il prodotto richiede *entrambi* |

Non è un progetto "morto", ma **non** è un progetto su cui scommettere 6 mesi/100k oggi.

## 9. Perché NO-GO sui 6 mesi

- Lo spike **non ha superato neanche la soglia di interesse** (<15 pp): miglior MAE reale 21.7 (illusorio) / YOLO 34.2.
- La prima vera prova di generalizzazione è **fallita** (corr +0.16; predice 0% su roccia integra).
- Il "0.97" che dava sicurezza era **leakage**.
- Finanziare 6 mesi adesso significherebbe ignorare tutto questo e bruciare capitale su una tesi non validata, con il moat commerciale a zero.

## 10. Perché GO sulle 2–4 settimane

- I fallimenti sono **diagnosticabili e a basso costo** (misura confondibile + mono-sito + training sotto-risorsato spiegano plausibilmente gran parte dei 34 pp).
- Lo spike ha già **ridotto il rischio** (SAM eliminato, candidato isolato, harness pronto).
- 3–4 settimane **comprano la risposta** che decide i 6 mesi, con **criteri di kill numerici pre-impegnati**.
- Il costo per risolvere l'incertezza è minuscolo rispetto all'informazione che produce.

---

## 11. Piano operativo a 4 settimane

Tutto con **dati e strumenti già esistenti**. Nessun nuovo dato richiesto.

| # | Attività | Tempo | Risultato atteso | ✅ Successo (numerico) | ❌ Kill (numerico) |
|---|---|---|---|---|---|
| 1 | **De-confondere la misura**: denominatore recovery-aware; CV per sondaggio (k-fold sui boreholes, non solo Z441) | Sett. 1 | MAE "pulito" + correlazione reale, separati dall'artefatto | MAE medio cross-sondaggio **scende a ≤ 20 pp** e corr **≥ 0.4** | MAE resta **≥ 25 pp** e corr **< 0.3** dopo de-confounding |
| 2 | **Diagnosi casi "predice 0%"** (geometria 17:1 vs soglia) + ritraining con aspetto nativo/tiling | Sett. 2 | I casi catastrofici (err~95) rientrano | I 5 peggiori scendono a **err < 30 pp** | I casi catastrofici **restano err > 70 pp** |
| 3 | **Validare Fase 1** contro gli 849 poligoni `Core` (mai fatto) | Sett. 3 (parz.) | IoU bande riv. vs vere | **IoU ≥ 0.85** | IoU **< 0.70** |
| 4 | **Gate finale + realtà di mercato**: 1–2 geologi contattati per test su poche cassette italiane / LOI | Sett. 3–4 | Segnale di domanda + sanity su dato italiano | **≥ 1 geologo** disposto a testare/pagare | **0 interesse** dopo ≥ 5 contatti |

**Gate complessivo per considerare i 6 mesi:** MAE ≤ 15 pp su **borehole-CV** con denominatore recovery-aware **E** almeno 1 design-partner. Altrimenti stop.

---

## 12. Decisione personale del fondatore

> *Founder: 19 anni, studente di geologia, budget limitato, molto tempo disponibile. Investire il prossimo mese su GeoCore AI o passare ad altro?*

**Da investitore:** **investi il mese — ma come gate di de-risking, non come scommessa.**
Il tuo capitale non è denaro, è **tempo**, e ne hai. Il payoff è asimmetrico: il downside è **capped** (un mese che comunque ti insegna CV, ML, geomeccanica, product thinking — competenze rare e cumulabili), l'upside è opzionalità reale su un problema verticale. Per un profilo time-rich/money-poor con **affinità di dominio** (sei già nel settore), questo è quasi il miglior uso aggiustato per il rischio del prossimo mese. A una condizione non negoziabile: **criteri di kill scritti prima** (sezione 11) e rispettati. Il pericolo vero alla tua età non è fallire, è **innamorarti del progetto** e ignorare i numeri.

**Da CTO:** il lavoro delle prossime 4 settimane è esattamente quello che costruisce competenze difendibili (geo + visione) e ti dà un **risultato pubblicabile/dimostrabile** comunque vada — un harness onesto e una valutazione rigorosa valgono già come portfolio. Tecnicamente il progetto è "interessante ma non provato": il posto giusto per imparare facendo.

**La risposta secca:** **sì, dedica il prossimo mese — al piano della sezione 11, con i kill criteria in mano.** Ma sii disciplinato su due punti:
1. Se i gate numerici falliscono, **molla senza rimpianti**: avrai comunque guadagnato le competenze e una storia da raccontare.
2. Il collo di bottiglia più duro **non è la CV, è il moat commerciale** (dato italiano + geologi). Inizia a tastare quello *adesso*, in parallelo: è ciò che, da studente di geologia con accesso al settore, puoi costruire meglio di qualunque ingegnere — ed è ciò che renderebbe GeoCore AI un'azienda e non un esercizio.

In una frase: **non scommettere la fattoria, scommetti un mese strutturato. Il progetto non merita la tua fede, ma merita le tue prossime 4 settimane.**

---
*Fine memo. Documento decisionale, non tecnico. Aggiornare a valle del gate di 4 settimane.*
