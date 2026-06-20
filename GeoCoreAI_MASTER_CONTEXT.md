# GeoCore AI — MASTER CONTEXT

> **Scopo di questo file.** Documento di handoff auto-sufficiente. Permette a un agente
> (Claude Code) di continuare il progetto **senza accesso alla cronologia della chat**.
> Contiene: obiettivo, architettura, decisioni e *perché*, specifica geologica dell'RQD,
> inventario file con bug noti, schema dati, protocollo di validazione e roadmap.
> Mantieni questo file aggiornato a ogni cambiamento sostanziale.

---

## 0. TL;DR per l'agente — stato e prossimo task

- **Cos'è:** pipeline di Computer Vision che, da una **foto di una cassetta catalogatrice di
  sondaggi geognostici**, calcola automaticamente l'**RQD (Rock Quality Designation)** e
  digitalizza il log geomeccanico. Non è un catalogo visivo.
- **Stato:** PROTOTIPO. Fasi 1–3 abbozzate, **Fase 4 (calcolo RQD) NON esiste ancora**.
- **PROSSIMO TASK PRIORITARIO:** implementare la **Fase 4 (RQD)** + applicare i **fix critici**
  della sezione 6. La Fase 4 è ciò che rende il progetto un prodotto.
- **Regola d'oro:** non ribaltare le decisioni della sezione 3 senza una ragione esplicita;
  sono frutto di analisi e allineate alla letteratura (YOLO11 + SAM) e agli standard (ASTM D6032).

---

## 1. Cos'è GeoCore AI

**Obiettivo.** Automatizzare la stesura del log geomeccanico a partire da foto ad alta
risoluzione di cassette catalogatrici: rilevare le file di carote, segmentare i singoli pezzi,
individuare le rotture, **calcolare l'RQD per manovra** e produrre un output digitale
verificabile dal geologo.

**Utente/mercato.** Geologi abilitati e studi geologici (focus iniziale Italia / Lazio). B2B.

**Non-obiettivi (espliciti).**
- NON un semplice catalogo visivo / archiviazione immagini.
- NON consulenza o report su commessa: è un prodotto software.
- NON pretendere classificazione *automatica* affidabile frattura naturale vs artificiale da
  sola foto 2D (vedi sezione 3): serve human-in-the-loop.

**Vincolo legale (influenza il design):** la relazione geologica va firmata da un **geologo
abilitato**. Il prodotto fornisce **misura + candidati**, la **validazione/firma resta al
geologo**. L'human-in-the-loop non è solo tecnico ma legale.

---

## 2. Architettura della pipeline (4 fasi)

| Fase | Nome | Tecnologia | Stato |
|------|------|-----------|-------|
| 1 | Estrazione file di carota | OpenCV classico (rettifica + profilo texture Sobel) | Prototipo OK |
| 2 | Segmentazione singoli pezzi | YOLO11 (detector) + SAM 2.1 box-prompted *(o YOLO-seg)* | Parziale |
| 3 | Rilevamento rotture/fratture | Tracciatore classico + gap tra maschere SAM | Parziale |
| 4 | **Calcolo RQD + digitalizzazione** | Geometria su maschere + regole ASTM | **DA SCRIVERE** |

Flusso dati: `foto → Fase1 (file + manifest.json) → Fase2 (maschere pezzi) → Fase3 (rotture) → Fase4 (RQD)`.

---

## 3. Decisioni architetturali (e perché)

1. **Fase 1 = CV classica, non deep learning.** La geometria della cassetta è deterministica
   (N scomparti orizzontali paralleli). Niente training, niente dataset, interpretabile.
   La letteratura SOTA stessa parte da rettifica prospettica classica.
2. **Deep learning solo dove serve:** segmentazione dei pezzi per l'RQD (Fase 2/3).
3. **Per la Fase 2 lo standard è YOLO11 (detector) → SAM 2.1 promptato coi box.** La modalità
   *automatica* di SAM è inaffidabile (sovra/sotto-segmenta, maschere annidate). Valutare anche
   **YOLO11-seg da solo**: molto più leggero e veloce di SAM, potenzialmente sufficiente in locale.
4. **Frattura naturale vs artificiale NON è risolvibile in modo affidabile da una foto 2D
   dall'alto** (la faccia di frattura si vede di taglio). Euristica difendibile: gap ≈ 0 + sezioni
   che combaciano ⇒ probabile rottura artificiale (ricuci); gap aperto / tritume / fango ⇒ vuoto
   reale (RQD 0 sul tratto). Decisione finale: **utente**.
5. **Disaccoppia due scale diverse** (errore classico da evitare):
   - **Scala fisica (cm/px)** per misurare la lunghezza dei pezzi → numeratore RQD. Da lunghezza
     interna nota dello scomparto o, meglio, da **marker ArUco** in foto.
   - **Quota (m)** dal valore di manovra inserito dall'utente → denominatore RQD. La mappa
     pixel→metro è solo **nominale** (assume recupero 100% + carota uniforme): non usarla per misurare.
6. **Soglie geologiche in mm reali, mai in pixel.** Una soglia in px dipende da risoluzione/scala.
7. **macOS-local, lean, open-source.** Niente cloud obbligatorio per il core.

---

## 4. Specifica geologica: RQD (regola del gioco per la Fase 4)

**Convenzione di lettura/profondità.** Top-down, left-right. Fila 1 (alto): da sinistra (inizio
manovra, es. 10.00 m) a destra (es. 11.50 m). Fila 2 (sotto): riparte da sinistra (11.50 m) →
destra. Entro la fila, **sx→dx = profondità crescente**.

**Formula.**
```
RQD = ( Σ lunghezze dei pezzi INTEGRI ≥ 10 cm  /  lunghezza totale della manovra ) × 100
```

**Regole di misura (ASTM D6032 / ISRM / Eurocode 7 — quest'ultimo rilevante in Italia):**
- Misura **lungo la centerline** (asse della carota), **non** la larghezza del bounding box.
  Per pezzi obliqui il bbox sovrastima → usare la lunghezza lungo l'asse.
- Contano **solo le fratture naturali**. Le **rotture meccaniche da perforazione** (superfici
  fresche, ruvide, che combaciano) si **ricuciono**: i due pezzi contano come uno solo.
- Solo pezzi **integri e sani** ("hard and sound").
- **Denominatore = lunghezza della manovra** (avanzamento perforato), da input utente —
  **NON** dalla geometria della cassetta (il recupero può essere < 100%).
- Soglia pezzo: **≥ 100 mm**.

**Classi di Deere (per la metrica di classe della Fase 4):**

| RQD (%) | Classe |
|---------|--------|
| 0–25 | Molto scadente (very poor) |
| 25–50 | Scadente (poor) |
| 50–75 | Discreto (fair) |
| 75–90 | Buono (good) |
| 90–100 | Ottimo (excellent) |

**Nota:** l'RQD da solo non descrive la qualità dell'ammasso (non considera orientazione,
apertura, riempimento dei giunti). È input di RMR (Bieniawski) e del Q-system (Barton).

---

## 5. Inventario file

| File | Ruolo | Stato | Azione |
|------|-------|-------|--------|
| `estrai_file_carote.py` | **Fase 1 canonica**: rettifica + Sobel + crop + `manifest.json` | OK (con bug sez.6) | Mantenere, applicare fix |
| `rileva_file_carote.py` | Versione **vecchia** della Fase 1, senza trim/manifest | Duplicato | **ELIMINARE** |
| `valuta_calibrazione.py` | Harness QA: conta le file e confronta con `verita.csv` | Solo Tier-1 (conteggio) | Estendere a IoU/F1/RQD + exit code per CI |
| `verita.csv` | Template ground-truth set di calibrazione (1 riga per foto) | OK | Popolare con foto reali |
| `fratture.py` | Fase 2/3: tracciatore classico + SAM 2.1 + `rotture_da_pezzi` | Parziale (bug sez.6) | Refactor + fix |
| `GeoCoreAI_MASTER_CONTEXT.md` | Questo file | — | Tenere aggiornato |

**Funzioni chiave attuali**
- `estrai_file_carote.py`: `carica_immagine`, `raddrizza_cassetta`, `profilo_texture`,
  `trova_divisori`, `_trim_verticale`, `taglia_in_file`, `main`.
- `fratture.py`: `traccia_fratture_classico`, `_e_valle_scura`, `_merge_per_x`,
  `segmenta_pezzi_sam`, `segmenta_pezzi_sam_da_box`, `rotture_da_pezzi`.

---

## 6. Bug noti e fix prioritari (dall'audit)

**Critici (fare prima):**
1. **EXIF/orientamento ignorato.** `cv2.imread` non legge il flag di rotazione → foto da telefono
   caricate storte → pipeline rotta. *Fix:* auto-rotazione (`PIL.ImageOps.exif_transpose`) in ingresso.
2. **Orientamento cassetta non normalizzato.** `_ordina_vertici` sbaglia i vertici per box ruotato
   > 45°. *Fix:* forzare il lato lungo in orizzontale dopo la rettifica.
3. **`fratture.py` ricarica SAM a ogni chiamata** (`SAM(modello)(img)`). *Fix:* caricare il modello
   una sola volta e riusarlo (singleton / parametro iniettato).
4. **SAM automatico → maschere annidate/sovrapposte ⇒ pezzi contati doppi.** *Fix:* NMS/dedup per
   IoU, o passare a `segmenta_pezzi_sam_da_box` con detector YOLO11.
5. **Soglia gap in pixel (`gap_aperto_px=8`).** *Fix:* esprimerla in **mm**, convertita via `scala_cm_px`.
6. **FASE 4 (RQD) assente.** *Fix:* implementarla (centerline, soglia 10 cm, ricucitura, denominatore manovra).

**Importanti:**
7. **Lunghezza pezzo = larghezza bbox**, non centerline → sovrastima sui pezzi obliqui (viola ASTM).
8. **`_e_valle_scura` campiona una sola colonna x** su tutta l'altezza → sbaglia sulle fratture
   **oblique**. *Fix:* campionare lungo la retta della frattura.
9. **`-n` non garantisce N file** (imposta solo `distance`). *Fix:* selezionare i migliori N−1 divisori.
10. **Euristica texture fragile** su litologia liscia/umida (profilo piatto). *Fix:* combinare con
    segnale di colore/bordo o fallback a divisione uniforme quando `-n` è noto.
11. **Guardie runtime mancanti:** crop degeneri (ty1≤ty0), `ZeroDivisionError` se `larg_px=0`,
    `res[0].masks=None` non gestito in `segmenta_pezzi_sam_da_box`, gap negativo in `rotture_da_pezzi`.
12. **Duplicazione `rileva_*`/`estrai_*`** → eliminare il legacy.

**Igiene di progetto mancante:** test (unit/integration), CI con gate, logging strutturato
(non `print`), config centralizzata dei parametri, gestione device CPU/GPU per SAM.

---

## 7. Schema dati — `manifest.json` (output Fase 1, input Fase 2)

```json
{
  "sorgente": "foto.jpg",
  "rettifica_applicata": true,
  "vertici_cassetta_px": [[x,y], [x,y], [x,y], [x,y]],
  "dim_rettificata_px": [larghezza, altezza],
  "scala_cm_per_px": 0.123,
  "quote_nominali_avviso": "mappatura pixel->metro valida solo a recupero 100%",
  "convenzione": "ordine file alto->basso ; entro la fila sx->dx = profondita' crescente",
  "n_file": 5,
  "file": [
    {
      "indice": 1,
      "file": "fila_01.png",
      "bbox_px": [0, y0, larghezza, y1],
      "dim_px": [w, h],
      "quota_nominale_m": [10.0, 11.0]
    }
  ]
}
```

La Fase 2 consuma `scala_cm_per_px` (per le lunghezze) e le `quote` (nominali) di ogni fila.

---

## 8. Protocollo di validazione e soglie di accettazione

**Principi.**
- Set **separati per fase**, ground-truth diverso.
- **Split per SONDAGGIO/sito, non per immagine** (file della stessa cassetta in train e test = leakage).
- Una fase è "valida" se supera il **gate** sul hold-out.

**Dimensione dei set.**
- Fasi 1–2 (classico, solo validazione): ~150 cassette stratificate per stima robusta
  (MVP: parti da 50). Stratifica su: tipo cassetta, luce, prospettiva, litologia, % recupero,
  presenza cartellino.
- Fase 3: 150–300 file etichettate da geologo (posizione + tipo di ogni rottura).
- Fase 4: **50–100 manovre con RQD già loggato nelle relazioni geologiche esistenti** =
  ground-truth gold-standard a costo quasi nullo. **(Mossa chiave: riusa i log esistenti.)**

**Etichettatura.** CVAT o Label Studio + SAM-assisted. Doppia annotazione su un campione →
concordanza inter-annotatore (κ).

**Soglie per fase:**

| Fase | Metrica primaria | Metrica secondaria | Min | Buona | Eccellente | Gate |
|------|------------------|--------------------|-----|-------|-----------|------|
| 1 Conteggio file | % cassette con N esatto | MAE su \|N_ril−N_vero\| | 85% | 95% | ≥99% | ≥95% (con -n) |
| 2 Estrazione file | IoU medio banda riv./vera | % bande IoU≥0.9 ; clipping | 0.80 | 0.90 | ≥0.95 | IoU≥0.90 e clipping<2% |
| 3 Rilevamento rotture | F1 a tolleranza ±5 mm | **recall** (sicurezza) ; FP/m | 0.70 | 0.85 | ≥0.92 | F1≥0.85 e recall≥0.90 |
| 4 Calcolo RQD | MAE RQD (punti %) | % entro ±5 pp ; accuratezza classe | ≤10 pp | ≤5 pp | ≤3 pp | MAE≤5 pp e classe≥90% |

Nota Fase 3: **recall prioritario** — una rottura mancata gonfia l'RQD (errore ottimistico =
pericoloso). Riferimento letteratura RQD: errori riportati ~2.6–4.8%.

---

## 9. Stack tecnico, dipendenze, comandi

**Linguaggio/ambiente:** Python 3.10+, macOS-local.

**Dipendenze:**
```bash
# Fase 1 + QA
pip install opencv-python numpy scipy
# Scala automatica via ArUco (opzionale)
pip install opencv-contrib-python
# Fase 2/3 (SAM/YOLO)
pip install ultralytics            # SAM 2.1 = "sam2.1_b.pt" ; detector "yolo11n-seg.pt"
```
Versioni di riferimento note: torch ~2.10, ultralytics ~8.4.x (verificare la doc Ultralytics
prima di scrivere codice SAM/YOLO: l'API cambia).

**API SAM (ultralytics, verificata):**
```python
from ultralytics import SAM
model = SAM("sam2.1_b.pt")
res = model(img, bboxes=[x1, y1, x2, y2])        # prompt con box (consigliato)
res = model(img, points=[[x, y]], labels=[1])    # 1=foreground, 0=background
res = model(img)                                  # 'segment everything' (inaffidabile su carote)
```

**Comandi attuali:**
```bash
# Fase 1
python estrai_file_carote.py foto.jpg -n 5 --lunghezza-fila-cm 100 \
       --quota-inizio 10.0 --quota-fine 15.0 -o fase1_out/
# QA Fase 1
python valuta_calibrazione.py calibrazione/foto calibrazione/verita.csv
# Fase 2/3
python fratture.py fase1_out/fila_01.png --metodo sam --scala-cm-px 0.12
python fratture.py fase1_out/fila_01.png --metodo classico
```

**Standard da consultare:** ASTM D6032 / D6032M-17, ISRM Suggested Methods, Eurocode 7 (EN 1997).
NB: ASTM vieta l'uso di IA sul testo dei propri standard — implementare le regole, non copiarne il testo.

---

## 10. Contesto business & vincoli

- **Moat ≠ codice** (replicabile in ~2 settimane). Moat = **dataset proprietario di cassette
  italiane + ground-truth RQD validato da geologi + protocollo di cattura** integrato nel workflow.
- **Capture protocol = feature di prodotto.** Standardizzare lo scatto (luce piatta, dall'alto,
  marker ArUco per la scala, cartellini fuori dai canali) abbatte gran parte dei falsi positivi
  a monte. Definire e distribuire un protocollo di 1 pagina.
- **Cartellini di profondità:** in Fase 2 aggiungere una classe YOLO `cartellino` per (a) escluderli
  dal calcolo e (b) leggerne la quota via OCR (Tesseract / VLM).
- **Validazione di mercato:** servono 3–5 geologi design-partner con cassette reali e log RQD.

---

## 11. Roadmap / Definition of Done

**Ordine consigliato:**
1. **Eliminare `rileva_file_carote.py`** (un solo rilevatore canonico).
2. **Fix critici** (sez. 6, punti 1–5): EXIF, orientamento, SAM caricato una volta, dedup maschere,
   soglie in mm.
3. **Scrivere la FASE 4 (RQD):** modulo `rqd.py` che, dati i pezzi (da Fase 2) e le rotture (Fase 3)
   con la `scala_cm_px`, applica: centerline, soglia 10 cm, ricucitura delle rotture artificiali,
   denominatore = lunghezza manovra (input), e produce RQD% + classe Deere + lista rotture da validare.
4. **Set di validazione (split per sito) + gate automatici in CI** (estendere `valuta_*` a IoU/F1/MAE-RQD
   con exit code).
5. **Procurare 3–5 geologi design-partner** + costruire il dataset RQD dai log esistenti.

**DoD per dire "prodotto MVP vendibile":** Fase 4 validata su ≥ 50 manovre reali con **MAE ≤ 5 pp e
accuratezza di classe ≥ 90%** su hold-out per sito, pipeline robusta a foto da telefono reali, e
almeno 3 geologi che confermano di volerlo usare/pagare.

---
*Fine MASTER CONTEXT. Aggiornare a ogni cambiamento sostanziale di architettura, file o soglie.*
