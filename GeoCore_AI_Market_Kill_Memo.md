# GeoCore AI — Market Kill Memo (Bear Case)

> Analisi VC spietata. Tech assunta funzionante (MAE < 15, prodotto funziona). Ignora la Computer Vision.
> Scopo: provare a **distruggere** la tesi di business. Fotografia fedele del bear case. **Data:** 2026-06-20.

## Il bersaglio iniziale (geologo italiano) è il punto più debole del progetto

### 1–3. Chi paga, quanto, perché
| Segmento | Paga? | ACV plausibile | Perché (o perché no) |
|---|---|---|---|
| Geologo singolo / micro-studio | Forse | €20–60/mese | Tedio ridotto. **Ma**: vedi obiezione #1 sotto. |
| Studio geotecnico medio | Sì, se QA/audit | €1–5k/anno | Standardizzazione, riduzione errori di trascrizione, deliverable digitali per gare. |
| Impresa di sondaggi / contractor | Sì, come value-add | €3–15k/anno | Vende "log digitale" al committente; volume alto. |
| Società di ingegneria infrastrutture (gallerie/dighe/AV) | Sì | €10–50k/progetto | Budget veri, obbligo documentale, migliaia di metri di carota. |
| Mining | Sì e con budget | alto | **Ma in Italia non esiste.** |

### 4. Come lavorano oggi senza GeoCore
Geologo in cantiere/deposito: misura i pezzi col metro, calcola l'RQD a mano o in Excel, scrive la relazione. Software esistenti: gINT/OpenGround (Bentley), Rocscience, Strater, fogli Excel. **Funziona già, è "abbastanza buono".**

### 5. Quanto è doloroso — **POCO, ed è il problema**
Il logging RQD è tedioso ma è una **frazione piccola** del lavoro (permessi, perforazione, relazione, cliente pesano di più). Non è il collo di bottiglia di nessuno. Dolore = 3/10.

### 6. Quanto spesso — regolare ma basso volume
Un'indagine = 5–50 cassette; un geologo fa pochi cantieri/mese. Volume per cliente **basso** → poca disponibilità a pagare ricorrente.

### 7. Budget — **misero**
Micro-studi: budget software di poche centinaia di €/anno. Profession conservatrice, anti-SaaS. I budget veri stanno **sopra** (contractor, infrastrutture), non nell'ICP scelto.

## Le tre obiezioni che da sole lo uccidono (mercato iniziale)

1. **Disallineamento ore-fatturabili.** Il geologo **fattura** il logging. Un tool che lo velocizza **riduce** le sue ore fatturabili, non le aumenta. Compra solo chi è capacity-constrained — e il mercato geologico italiano è **sovra-offerta**, non a corto di capacità. *Stai vendendo efficienza a chi guadagna sull'inefficienza.*
2. **Responsabilità legale → human-in-the-loop obbligatorio.** Il geologo firma e risponde. Non si fida del numero AI senza ricontrollare → rifà comunque il lavoro → risparmio marginale → **value capture basso**.
3. **TAM minuscolo.** ~15.000 geologi iscritti in Italia; forse **1.000–3.000** fanno geotecnica/carote con regolarità. Anche a penetrazione irrealistica (500 paganti × €50/mese) = €300k/anno. È un **lifestyle business**, non venture.

### 8. Quanti clienti realistici in Italia
- SAM plausibile: **1.000–3.000** tra geologi/studi/contractor.
- Clienti *paganti* realistici a 3 anni con esecuzione ottima: **50–300**.
- ARR ceiling Italia-only: **bassi milioni nel best case assoluto, più probabilmente centinaia di k**. Mercato **piccolo**.

### 9. I primi 20 da contattare — **non i micro-studi: i compratori con budget**
*(Da verificare uno per uno — archetipi e nomi reali noti del geotech infrastrutturale italiano, dove sta il budget.)*

**Tier 1 — ingegneria gallerie/dighe/AV (budget + obbligo documentale):**
1. Geodata Engineering (Torino) 2. Rocksoil (Milano) 3. SWS Engineering (Trento) 4. Studio Geotecnico Italiano–SGI (Milano) 5. Lombardi 6. Italferr (gruppo FS) 7. Pini Group 8. Politecnica.

**Tier 2 — contractor/sondaggi (volume, value-add al committente):**
9. Trevi Group (Cesena) 10. Rodio 11. ICOS 12. imprese di sondaggi geognostici regionali (decine).

**Tier 3 — committenti/owner con esigenza di dato standardizzato:**
13. ANAS 14. RFI 15. concessionarie autostradali 16. consorzi di bonifica/dighe.

**Tier 4 — canale/credibilità:**
17. Politecnico Torino (DISEG) 18. Politecnico Milano 19. Sapienza geotecnica 20. Consiglio Nazionale dei Geologi / ordini regionali.

Nota brutale: **18 di questi 20 NON sono il tuo ICP dichiarato** (il piccolo geologo). Il fatto che i compratori veri siano altrove è il segnale che **l'ICP iniziale è sbagliato**.

### 10. Possibili acquirenti (5–10 anni)
- **Bentley Systems** — *l'acquirente ovvio, e già armato*: possiede OpenGround **e ha già comprato Imago** (gestione foto di carote) nel 2021. Prova che lo spazio è acquisibile **e** che il compratore naturale ha già un cavallo in corsa → minaccia, non solo opportunità.
- **Seequent** (gruppo Bentley), **Rocscience**, **Hexagon**, **Trimble**.
- **AI-core mining**: Datarock, Plotlogic, MICROMINE — ma guardano al mining, non alla geologia civile italiana.
- **TIC**: SGS, Bureau Veritas (testing geotecnico).
- Esito più probabile: **acqui-hire piccolo o niente exit.**

---

## Verdetto VC: investirei?

**No, non con denaro venture.** Non è venture-scale: TAM piccolo, ACV basso, buyer lenti e conservatori, incentivo a NON comprare (ore fatturabili), incumbent (Bentley) già posizionato. Un fondo che cerca 10x **passa**.

| Domanda | Probabilità | Razionale |
|---|---:|---|
| Costruire un business reale (ramen-profittevole) | **35–45%** | Qualche studio/contractor pagherebbe; il founder ha vantaggio di dominio. |
| Arrivare a **100k€/anno** | **20–30%** | ~150–300 paganti o pochi account medi. Duro ma fattibile con hustle e rete. |
| Arrivare a **1M€/anno** | **5–10%** | Richiede uscire dall'Italia/salire a infrastrutture-mining: pivot + capitale + team. Improbabile solo. |
| Exit/acquisizione | **3–7%** | Tuck-in strategico Bentley/Seequent solo con dataset+clienti reali; più probabile nulla. |

## "Cerca di distruggerlo. Se sopravvive, spiega perché."

**Cosa muore:** la tesi "SaaS RQD per il geologo italiano". Muore per disallineamento ore-fatturabili, dolore basso, TAM minuscolo, e Bentley già nello spazio. Punto.

**Cosa sopravvive — e perché:**
1. **Il prodotto non è il valore; il dato lo è.** Un wedge che parte dall'RQD e digitalizza *l'intero log geomeccanico* può diventare il **system of record** del dato geotecnico di carota — appiccicoso, ri-vendibile, e con un dataset proprietario che è il vero moat.
2. **I compratori veri hanno budget**: gallerie/dighe/AV e contractor, spinti dall'obbligo di **deliverable digitali** nelle gare infrastrutturali (digitalizzazione/BIM). Lì €10–50k/progetto è reale.
3. **Il founder è l'asset, non l'azienda**: un 19enne geologo che impara CV+ML+go-to-market su un dominio verticale è esattamente il profilo da cui nascono fondatori bravi. Come **angelo che scommette sulla persona**, forse sì. Come **VC che scommette sul mercato**, no.

**La verità spietata in una riga:** GeoCore AI sopravvive **solo se pivota** dall'ICP "piccolo geologo italiano" verso "system of record per il dato geotecnico delle grandi infrastrutture" (e poi mining/estero). Il problema non è la Computer Vision — è che hai scelto **il segmento più povero del mercato come beachhead**. Cambia il compratore, non il modello.

**Cosa cambierebbe la mia risposta da "no" a "forse":** una sola prova — **un contractor o una società di gallerie che firma un pilota a pagamento**. Quella validazione vale più di qualsiasi miglioramento di MAE. È, guarda caso, lo stesso "prossimo esperimento a massimo valore" dell'observability note: contatta i compratori con budget, non lima il modello.
