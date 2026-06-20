# GeoCore AI — Piano di Esecuzione 4 Settimane (v1)

> **Input:** Decision Memo v1 (approvato). **Scopo:** verificare, con gate numerici,
> se GeoCore AI merita ulteriori investimenti di tempo. **Vincoli:** usa solo dati e
> strumenti già esistenti (harness §6, dataset Kaggle in `archive/`, pesi YOLO già
> addestrati). Nessuna nuova idea, nessun nuovo dato richiesto fino al gate.
>
> **Come usare questo documento:** eseguilo dall'alto verso il basso. Ogni attività ha
> un criterio di successo/fallimento **numerico**: se fallisce, applica la regola di
> stop indicata — **non prendere nuove decisioni**, segui la checklist (§7).
> Ipotesi di carico: ~4–6 h/giorno produttive, 5 giorni/settimana, sabato = buffer.

---

## 0. Gate complessivo (la domanda che tutto serve a rispondere)

> **PROCEDI ai 6 mesi SOLO SE, a fine settimana 4:**
> **MAE ≤ 15 pp su borehole-CV** (con denominatore recovery-aware) **E ≥ 1 geologo design-partner** disposto a testare.
> Altrimenti **STOP** (o pivot sul solo asset commerciale).

---

## 1. Attività ordinate per RAPPORTO informazione / tempo (decrescente)

| Rank | Attività | Info/Tempo | Perché |
|---|---|---|---|
| **1** | **Outreach a geologi** (5 contatti) | **altissimo** | 5 email/chiamate possono **falsificare la tesi commerciale** in ore. È il rischio più grande e il più economico da sondare. |
| **2** | **Denominatore recovery-aware + re-run** | **altissimo** | Quasi gratis (riusa harness); può mostrare che gran parte dei 34 pp è artefatto, non modello. |
| **3** | **Borehole-CV** (rotazione held-out) | **alto** | Dice se Z441 è unicamente difficile o se è sistemico. Riusa harness. |
| **4** | **Diagnosi casi "predice 0%"** | **alto** | Isola la causa dei pochi errori catastrofici che dominano il MAE. |
| **5** | **Validazione Fase 1 (IoU vs `Core`)** | **medio** | Chiude un buco mai misurato; ground-truth già presente (849 poligoni). |
| **6** | **Ritraining aspetto nativo/tiling** | **medio-basso** | Solo SE la diagnosi (#4) indica la geometria; costo maggiore, dipendente. |

**Regola d'oro:** esegui in quest'ordine. Le attività 1–3 sono quasi gratis e possono **chiudere il progetto** (in positivo o negativo) prima di spendere su 4–6.

## 2. Mappa di riduzione del rischio

**Riducono di più il RISCHIO TECNICO** (in ordine):
1. Denominatore recovery-aware (toglie il confondente che gonfia il MAE).
2. Borehole-CV (misura la *vera* generalizzazione).
3. Diagnosi "predice 0%" + eventuale tiling.

**Riducono di più il RISCHIO COMMERCIALE** (in ordine):
1. Outreach a geologi → ≥1 design-partner (esistenza di domanda).
2. Verifica accesso a **log RQD italiani esistenti** (il moat + il ground-truth gold).
3. Conferma del vincolo human-in-the-loop come *feature*, non ostacolo, parlando coi geologi.

---

## 3. Settimana 1 — De-confondere la misura (rischio TECNICO + avvio COMMERCIALE)

**Obiettivo settimana:** sapere il MAE "vero" senza l'artefatto di scala e su più sondaggi; avviare in parallelo l'outreach.

| Giorno | Attività | Output | Tempo | ✅ Successo | ❌ Fallimento |
|---|---|---|---|---|---|
| **L1** | Definire e applicare il **denominatore recovery-aware** nell'harness (sostituire l'assunzione recupero 100%); ri-eseguire su Z441 | MAE Z441 ricalcolato | 4 h | numero prodotto, pipeline gira | harness non eseguibile pulito |
| **L1 (pom.)** | **Outreach #1–#2**: scrivere a 2 geologi (rete universitaria/relatore) | 2 email inviate | 1 h | inviate | — |
| **M2** | **Borehole-CV**: ruotare l'held-out su tutti i sondaggi disponibili, raccogliere MAE/corr per fold | tabella MAE per fold + media | 5 h | tabella completa | dati insufficienti per ≥3 fold |
| **M3** | Consolidare: MAE medio cross-sondaggio + correlazione media, con e senza recovery-aware | 1 grafico + 1 tabella | 4 h | confronto chiaro artefatto vs reale | — |
| **M3 (pom.)** | **Outreach #3**: contattare un albo/ordine regionale o studio geologico | 1 contatto | 1 h | inviato | — |
| **G4** | Scrivere il **mini-report Settimana 1** (1 pagina) con il verdetto del gate 1 | report W1 | 3 h | verdetto numerico scritto | — |
| **G4 (pom.)** | **Outreach #4–#5** + follow-up #1–#2 | 2 contatti + follow-up | 1.5 h | inviati | — |
| **V5** | Buffer / recupero ritardi | — | — | — | — |

**🚦 GATE 1 (fine W1):**
- ✅ **PROCEDI** se MAE medio cross-sondaggio (recovery-aware) **≤ 20 pp E corr ≥ 0.4**.
- ❌ **STOP tecnico** se MAE **≥ 25 pp E corr < 0.3** dopo de-confounding → il problema non è misura, è fisica/modello: passa diretto a §6 (verdetto) e valuta pivot.

---

## 4. Settimana 2 — Attaccare i fallimenti catastrofici (rischio TECNICO)

**Obiettivo:** capire e ridurre i casi "predice 0% su roccia sana" (err~95) che dominano il MAE.

| Giorno | Attività | Output | Tempo | ✅ Successo | ❌ Fallimento |
|---|---|---|---|---|---|
| **L6** | **Diagnosi**: ispezionare gli overlay dei 5 peggiori; classificare la causa come (a) geometria 17:1 o (b) soglia/scala | nota diagnostica con causa dominante | 4 h | causa identificata su ≥4/5 casi | causa non determinabile |
| **M7** | Se causa = geometria: **ritraining ad aspetto nativo/tiling** (lancio) | run di training avviata | 4 h | training parte e converge | training non eseguibile |
| **M8** | Valutare il modello ri-addestrato sullo stesso borehole-CV | tabella MAE aggiornata | 5 h | numeri prodotti | — |
| **G9** | Confronto prima/dopo sui 5 casi peggiori + MAE complessivo | tabella delta | 4 h | delta misurato | — |
| **G9 (pom.)** | **Gestione outreach**: rispondere/fissare call con chi ha risposto | call fissate | 1.5 h | ≥1 call in calendario | 0 risposte da 5 contatti → flag |
| **V10** | **Mini-report Settimana 2** + buffer | report W2 | 3 h | verdetto gate 2 scritto | — |

**🚦 GATE 2 (fine W2):**
- ✅ **PROCEDI** se i 5 peggiori scendono a **err < 30 pp** (o MAE complessivo cala di **≥ 8 pp**).
- ❌ **STOP/flag** se i casi catastrofici **restano err > 70 pp** → il modello non si fida della roccia sana mai vista: limite serio, annota per il gate finale.

---

## 5. Settimana 3 — Chiudere i buchi (TECNICO) + spingere il COMMERCIALE

**Obiettivo:** validare la Fase 1 (mai fatto) e portare a casa almeno una conversazione di mercato seria.

| Giorno | Attività | Output | Tempo | ✅ Successo | ❌ Fallimento |
|---|---|---|---|---|---|
| **L11** | **Validazione Fase 1**: IoU delle bande rilevate vs gli 849 poligoni `Core` | distribuzione IoU + mediana | 5 h | IoU prodotto su tutto il set | — |
| **M12** | Analisi: dove la Fase 1 fallisce (litologia/luce) | nota con casi limite | 4 h | pattern identificato | — |
| **M13** | **Call con geologo #1**: capire workflow attuale, dolore reale, disponibilità a testare e a condividere **log RQD esistenti** | note strutturate call | 2 h call + 1 h note | risposte a: paga? testa? dà i log? | nessuna call realizzata |
| **G14** | Sintesi tecnica: MAE finale (borehole-CV, recovery-aware) + IoU Fase 1 | scheda numerica unica | 4 h | tutti i numeri in un posto | — |
| **G14 (pom.)** | **Call/outreach #2** o follow-up per LOI | contatto avanzato | 1.5 h | interesse esplicito | — |
| **V15** | **Mini-report Settimana 3** + buffer | report W3 | 3 h | verdetto gate 3 scritto | — |

**🚦 GATE 3 (fine W3):**
- ✅ tecnico: **IoU Fase 1 ≥ 0.85**; commerciale: **≥1 geologo disposto a testare**.
- ❌ **STOP commerciale** se **0 interesse dopo ≥5 contatti**; **flag tecnico** se IoU **< 0.70**.

---

## 6. Settimana 4 — Verdetto

**Obiettivo:** mettere tutti i numeri sul tavolo e decidere con il gate complessivo (§0).

| Giorno | Attività | Output | Tempo | ✅ Successo | ❌ Fallimento |
|---|---|---|---|---|---|
| **L16** | Consolidare **tutti i numeri**: MAE borehole-CV (recovery-aware), delta tiling, IoU Fase 1, esito casi catastrofici | dashboard 1 pagina | 4 h | dashboard completa | dati mancanti |
| **M17** | Consolidare **esito commerciale**: n. contatti, risposte, interesse, accesso a log italiani | scheda commerciale | 3 h | quadro chiaro | — |
| **M18** | Scrivere **Decision Memo v2** (go/no-go sui 6 mesi) confrontando i numeri col gate §0 | Memo v2 | 5 h | verdetto motivato | — |
| **G19** | Revisione critica del Memo v2 (rileggere a freddo, cercare bias ottimistico) | memo rivisto | 3 h | nessun numero gonfiato | — |
| **V20** | Decisione finale + (se GO) bozza piano 6 mesi / (se NO-GO) nota di chiusura e cosa riusare | decisione scritta | 3 h | decisione presa | — |

**🚦 GATE FINALE (§0):** MAE ≤ 15 pp (borehole-CV, recovery-aware) **E** ≥1 design-partner → **GO 6 mesi**. Altrimenti **NO-GO** (o pivot sul solo asset dati/commerciale se quello regge e la tecnica no).

---

## 7. Checklist operativa (eseguibile senza nuove decisioni)

**Settimana 1**
- [ ] Applicare denominatore recovery-aware nell'harness e ri-eseguire su Z441
- [ ] Eseguire borehole-CV su tutti i sondaggi; raccogliere MAE/corr per fold
- [ ] Produrre tabella MAE con/senza recovery-aware
- [ ] Inviare outreach #1–#5 (geologi/ordine/studio) + 2 follow-up
- [ ] Scrivere mini-report W1 con verdetto numerico
- [ ] **GATE 1:** MAE ≤20 & corr ≥0.4 → continua · MAE ≥25 & corr <0.3 → vai a §6 (stop tecnico)

**Settimana 2**
- [ ] Ispezionare overlay dei 5 peggiori; classificare causa (geometria vs soglia)
- [ ] Se geometria: lanciare ritraining ad aspetto nativo/tiling
- [ ] Rivalutare su borehole-CV; misurare delta sui 5 peggiori e sul MAE
- [ ] Fissare ≥1 call con chi ha risposto
- [ ] Scrivere mini-report W2
- [ ] **GATE 2:** 5 peggiori <30 pp o MAE −8 pp → continua · catastrofici >70 pp → flag

**Settimana 3**
- [ ] Calcolare IoU Fase 1 vs poligoni `Core`; trovare i casi di fallimento
- [ ] Fare ≥1 call con geologo: paga? testa? condivide log RQD?
- [ ] Mettere tutti i numeri tecnici in un'unica scheda
- [ ] Avanzare ≥1 contatto verso LOI/test
- [ ] Scrivere mini-report W3
- [ ] **GATE 3:** IoU ≥0.85 & ≥1 disposto a testare → continua · 0 interesse da 5 contatti → stop commerciale

**Settimana 4**
- [ ] Dashboard tecnica 1 pagina (tutti i numeri)
- [ ] Scheda commerciale (contatti/interesse/accesso log)
- [ ] Scrivere Decision Memo v2 contro il gate §0
- [ ] Revisione anti-bias del memo
- [ ] **GATE FINALE:** MAE ≤15 pp & ≥1 partner → GO 6 mesi · altrimenti NO-GO/pivot

---

## 8. Regole di stop (per non innamorarsi del progetto)

1. Se **GATE 1** dà stop tecnico → **non** continuare con W2–W4 sperando: vai diretto al verdetto.
2. Se **0 interesse commerciale** dopo 5 contatti reali → il rischio più grande non è risolvibile da solo: stop o pivot.
3. Il gate finale è **AND** (tecnica **E** mercato): superarne uno solo **non** è un GO.
4. Ogni mini-report settimanale deve contenere un numero, non un'opinione. Se non hai il numero, l'attività non è chiusa.

---
*Fine piano. Documento operativo. A fine W4 produrre `GeoCore_AI_Decision_Memo_v2`.*
