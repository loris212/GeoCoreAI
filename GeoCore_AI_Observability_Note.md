# GeoCore AI — Nota sull'Osservabilità (RQD da immagini 2D)

> **Domanda.** Dopo aver falsificato misura, soglia e specificità di Z441, resta:
> *l'RQD da foto 2D è intrinsecamente poco osservabile? Parte dell'informazione necessaria
> non è nei pixel?*
> **Vincoli.** Solo dataset attuale, risultati già ottenuti, overlay best/worst, errori
> catastrofici. Nessun nuovo modello, nessun benchmark. **Data:** 2026-06-20.

---

## 0. Sintesi in tre righe

L'osservabilità **non** è il collo di bottiglia attuale: i casi peggiori sono visibilmente
leggibili (carota integra letta correttamente da OpenCV e dall'occhio umano, sbagliata da YOLO).
L'osservabilità diventa un **soffitto reale solo sull'ultimo miglio** (≤5 pp: naturale vs artificiale,
fratture chiuse). Oggi il problema è **dataset/generalizzazione**, non fisica del segnale.

---

## 1. Prove A FAVORE dell'osservabilità (il segnale È nei pixel)

- **Separazione macroscopica delle classi.** GT≈100 = cilindro continuo; GT≈10 = ghiaia di pezzetti
  (es. 44-51m, GT 11, frammentazione evidente in `esempio_fallimento_2.png`). Sono immagini diversissime.
- **Un metodo triviale legge il grossolano.** OpenCV (training-free) sul caso 316-323m (GT 98) → 100%
  (err 2): satura, ma sulla roccia integra **azzecca**. Il segnale "continuo ⇒ RQD alto" è prendibile
  senza apprendimento.
- **I successi di YOLO sono perfetti.** 5 migliori casi held-out: err 0.0–0.2 su GT 87–99%
  (`cmp_good_YOLO11-seg.png`): i box rossi combaciano coi poligoni GT verdi. Quando il modello "vede",
  la misura è esatta.
- **In-sample quasi perfetto.** YOLO sui sondaggi di training: MAE ~5–7, corr ~+1.0. L'informazione per
  segmentare i pezzi è sufficiente quando il dominio è noto.

## 2. Prove CONTRO l'osservabilità (informazione mancante nei pixel)

- **Naturale vs artificiale non risolvibile da foto top-down.** La faccia di frattura si vede "di taglio";
  freschezza/ruvidità/ossidazione (i segni che distinguono rottura naturale da rottura da perforazione)
  non sono leggibili da una singola vista dall'alto. Già dichiarato nel MASTER_CONTEXT.
- **Fratture chiuse.** Pezzi a contatto separati da una frattura naturale sottile possono essere
  sotto-pixel da sopra → due pezzi appaiono come uno. Influenza il conteggio vicino alla soglia 10 cm.
- **Mancano canali extra-immagine** (vedi §contesto): tattile, 3D, log di perforazione, % recupero.
- **Limite umano-da-foto.** Anche un geologo, con **solo** la foto 2D, sarebbe limitato proprio su
  queste distinzioni fini → il tetto teorico della singola immagine è < tetto del geologo in laboratorio.

## 3. Informazione che il geologo usa e NON è nei pixel

3D (rotazione del campione, faccia di frattura), tattile/meccanico (combaciare i pezzi, freschezza),
log di perforazione (recupero %, velocità, perdite d'acqua), storia di manipolazione (rotture da
trasporto), contesto litologico e di manovre adiacenti. **Quasi tutto serve al fine (naturale/artificiale,
fratture chiuse), non al grossolano.**

## 4. Ipotesi FALSIFICATE finora

| # | Ipotesi | Esito | Evidenza |
|---|---|---|---|
| 1 | Il MAE è artefatto di **misura/scala** (recupero 100%) | ❌ falsificata | recovery-aware: GT invariato (0/58), MAE 34.2→34.2, 0/9 catastrofici recuperati |
| 2 | Il MAE è artefatto di **soglia** in pixel | ❌ falsificata | soglia permissiva (43 px ≈1.2% larghezza) non cambia i Pred=0 |
| 3 | Il problema è **specifico di Z441** | ❌ falsificata | OpenCV training-free: Z441 tra i più FACILI (21.7 vs media altri 49); il sondaggio held-out è favorevole, non avverso |
| 4 | **CV classica** è un motore RQD | ❌ falsificata | satura, corr negativa, MAE_poor 75 |
| 5 | **SAM** è un motore RQD utile | ❌ falsificata | 24 s/crop, MAE peggiore, classe 6% |
| 6 | **Osservabilità** è la causa dei 34 pp attuali | ❌ falsificata | i peggiori sono carota integra, letta da OpenCV/umano; YOLO fallisce dove l'info c'è |

## 5. Ipotesi ANCORA APERTE

| # | Ipotesi aperta | Come si chiuderebbe |
|---|---|---|
| A | La **generalizzazione cross-sito** è ottenibile con più dati/diversità | borehole-CV vera (retraining per fold) + dataset multi-sito ampio |
| B | La **geometria 17:1** (letterbox delle strisce) causa i Pred=0 | training/inferenza ad aspetto nativo / tiling |
| C | Lo spec **≤5 pp** è raggiungibile da sola foto 2D | richiede input extra (multi-vista, ArUco, log) — probabilmente NO |
| D | Esiste **domanda di mercato** + accesso a log RQD italiani | outreach a geologi design-partner |
| E | La **Fase 1** (estrazione file) regge | IoU vs i 849 poligoni `Core` |

---

## 6. DECISIONE ATTUALE

**GeoCore AI è tecnicamente morto?**
**No.** Tre ipotesi-killer comode (misura, soglia, Z441) sono cadute, ma la spiegazione superstite —
debolezza di generalizzazione — è **risolvibile in linea di principio**: l'informazione grossolana è nei
pixel, i successi sono perfetti, il tetto umano è alto. Non è morto; è **acerbo e sotto-addestrato su dati
troppo poveri**.

**Merita altre 2-4 settimane?**
**Sì, ma spostando il focus.** Le settimane non vanno spese a "migliorare il modello" su questo dataset
(mono-sito, cinese), bensì a **chiudere le ipotesi aperte A, B, E** a basso costo e — soprattutto — ad
attaccare **D** (mercato + dati italiani). Il valore non è un MAE più basso su Z441; è capire se esiste
il percorso a un dataset multi-sito reale.

**Principale rischio TECNICO oggi.**
**Generalizzazione cross-sito.** Il modello memorizza i siti di training (in-sample MAE ~6) e collassa su
un sito nuovo (held-out 34, gap +27 pp). Senza dati molto più diversi, non trasferisce. (Rischio
secondario, ma non fisica: lo spec ≤5 pp è limitato dall'osservabilità dell'ultimo miglio.)

**Principale rischio BUSINESS oggi.**
**Inesistenza del moat e della domanda validata.** Zero geologi design-partner, zero log RQD italiani,
zero evidenza di willingness-to-pay. Il dato proprietario italiano — che è *sia* il moat *sia* la cura del
rischio tecnico (diversità di siti) — non esiste ancora. È il rischio più grande e il meno esplorato.

**Singolo esperimento a massimo valore informativo (prossimo passo).**
**Non un esperimento di modello, ma di accesso ai dati/mercato:** contattare 2–3 geologi e verificare due
cose insieme — (a) sono disposti a testare/pagare? (b) possono fornire **anche solo 5–10 cassette italiane
con RQD già loggato**? Questo singolo passo: convalida o falsifica il moat commerciale **e** procura il
primo dato multi-sito reale che attacca direttamente il rischio tecnico #1. Massimo valore perché tocca
contemporaneamente il rischio più grande (business) e la cura del secondo (generalizzazione) — cosa che
nessun esperimento puramente tecnico su questo dataset può fare.

---

## 7. Una frase per il fondatore

Il problema non è la fisica (i pixel bastano per il grossolano) e non è il codice (un terzo dei casi è già
perfetto): è che **non hai ancora i dati giusti né la prova che qualcuno li voglia**. Le prossime settimane
servono a procurare *entrambi* — non a limare un MAE su carote cinesi.

---
*Nota scientifica. Stato reale del progetto dopo: audit, esperimento §6, spike a tre vie, recovery-aware,
borehole-breakdown, ispezione overlay. Prossimo aggiornamento: dopo il contatto coi geologi.*
