# GeoCore AI — Opportunity Map (dolore pagante geotech)

> Prospettiva: partner VC geotech/infrastrutture/B2B software. Assunzioni: RQD-SaaS per geologi IT NON è
> venture-scale; il dataset da solo non basta; la CV è uno strumento, non il prodotto. Obiettivo: trovare
> il problema più doloroso e pagante. **Data:** 2026-06-20.
> Legenda: 💸 perde soldi · ⏱️ perde tempo · ⚖️ responsabilità legale · 📄 oggi Excel/PDF/email/manuale.

## 1. Contractor di sondaggi geognostici
| Problema | Tag |
|---|---|
| Utilizzo/scheduling perforatrici (rig idle = day-rate bruciato) | 💸 |
| Trascrizione campo→ufficio dei log (riscrittura in Excel/gINT, errori) | 💸⏱️📄 |
| Produzione log/daily report manuale | ⏱️📄 |
| Stima/offerta gare (preventivi error-prone) | 💸📄 |
| Strike di sottoservizi (utenze interrate) | 💸⚖️ |
| Tracciabilità campioni / chain of custody (persi→ri-perforare) | 💸⚖️📄 |
| Conversione deliverable (AGS/DIGGS/gINT/Excel) | ⏱️📄 |
| Coordinamento laboratori subappaltati / turnaround | ⏱️📄 |
| SAL/fatturazione a metro perforato (dispute) | 💸📄 |
| Documentazione H&S e permessi | ⚖️📄 |

## 2. Società di ingegneria geotecnica
| Problema | Tag |
|---|---|
| Ingestione+QA dati sporchi da più contractor (validazione AGS) | ⏱️📄 |
| Costruzione ground model 3D (interpolazione manuale) | ⏱️ |
| Scrittura relazioni geotecniche (fattuali+interpretative) | ⏱️⚖️📄 |
| Derivazione parametri di progetto da dati grezzi | ⏱️⚖️ |
| Riuso sapere di progetti passati (sepolto in PDF) | ⏱️📄 |
| Sovra-progettazione (perdi gare) vs sotto-progettazione (claim) | 💸⚖️ |
| Interoperabilità BIM con strutturisti | ⏱️📄 |
| Conformità Eurocodice 7 / standard | ⚖️📄 |
| Gestione dati di laboratorio | ⏱️📄 |
| Stima fee / bid–no bid | 💸📄 |

## 3. Gallerie / dighe / ferrovie / grandi infrastrutture
| Problema | Tag |
|---|---|
| Claim per Differing Site Conditions (baseline vs reale — milioni) | 💸⚖️📄 |
| Gestione dati Instrumentation & Monitoring (migliaia di sensori, soglie manuali) | 💸⏱️📄 |
| Danni a edifici terzi per cedimenti durante lo scavo | 💸⚖️ |
| Fermo TBM / decisioni real-time parametri vs terreno | 💸 |
| Silos di dati tra progettista/contractor/owner | ⏱️📄 |
| Mappatura del fronte di scavo (geologo on-site, manuale) | ⏱️⚖️📄 |
| Geotechnical Baseline Report come base contrattuale | ⚖️📄 |
| Risk register / contingency (Excel) | 💸📄 |
| Reportistica a owner/ente regolatore | ⏱️📄 |
| Documentazione as-built geotecnica | ⏱️📄 |

## 4. Proprietari / gestori di infrastrutture
| Problema | Tag |
|---|---|
| Asset management geotecnico di scarpate/rilevati/muri (migliaia di km) | 💸⚖️📄 |
| Cedimenti/frane che chiudono linee (sicurezza pubblica) | 💸⚖️ |
| Monitoraggio reattivo non predittivo (ispezioni manuali) | 💸⏱️📄 |
| Adattamento climatico (piogge→frane, scour) | 💸⚖️ |
| Dati pessimi su asset legacy (carta, terreno ignoto) | ⏱️📄 |
| Prioritizzazione capex risk-based sul portfolio | 💸📄 |
| Compliance sicurezza dighe / rilevati ferroviari | ⚖️📄 |
| Integrazione InSAR/IoT/LIDAR/drone nelle decisioni | ⏱️📄 |
| Scour ai ponti / subsidenza / sinkhole | 💸⚖️ |
| Finanziamento/assicurazione della resilienza | 💸📄 |

---

## Filtri (software · niente firma continua · non consulenza · scalabile · ≥1M€ · validabile in 2 mesi)

Il filtro **"niente firma continua del geologo"** elimina relazioni, scelta parametri, RQD-deliverable,
mappatura fronte. Spinge verso **dati operativi, monitoraggio, asset management, claim**: valore nel
*dato e nel flusso*, non nel giudizio firmato.

## Top 10 opportunità (rank per founder: geologia + GIS + Python)

| # | Opportunità | Perché vince | Filtro a rischio |
|---|---|---|---|
| 1 | **Asset management geotecnico per owner lineari (rilevati/scarpate ferrovie-strade)** | GIS-native, budget sicurezza pubblica, tailwind clima, ricorrente, niente firma | sales lunghi con enti |
| 2 | **Piattaforma dati I&M per cantieri gallerie/dighe** | Budget veri, ricorrente, dolore acuto, validabile | competitor (MissionOS, Bentley) |
| 3 | **Analytics InSAR/satellitare di deformazione del suolo** | GIS-native, puro software, owner+assicurazioni, in crescita | dato satellitare commodity |
| 4 | **Early-warning frane/scarpate per ferrovie-strade** | Sicurezza pubblica = urgenza+budget, niente firma | hardware/sensori |
| 5 | **Digitalizzazione campo→ufficio per contractor** (logging + AGS + job tracking) | Validazione facilissima, risparmio reale, scalabile | ACV medio |
| 6 | **Automazione QA/interoperabilità dati AGS/DIGGS** | Dolore universale, puro software, validabile subito | commoditizzabile da Bentley |
| 7 | **Piattaforma claim/evidence per Differing Site Conditions** | Valore enorme per deal | accesso buyer + legale, validazione lenta |
| 8 | **Monitoraggio cedimenti edifici terzi + difesa claim** | Alta liability/valore, ricorrente | nicchia, subset di #2 |
| 9 | **Compliance & monitoraggio sicurezza dighe** | Regolato, ricorrente, alto valore | pochi buyer, ciclo lungo |
| 10 | **Vertical SaaS scheduling/utilizzo flotta perforatrici** | Soldi veri (rig idle), validabile | poco geotech-differenziato, moat debole |

I primi 3-4 **non richiedono Computer Vision** e usano il GIS del founder.

## Distruzione di GeoCore (perché queste battono l'RQD)

GeoCore (RQD via CV) fallisce **3 filtri su 6**: (1) firma continua del geologo → value capture basso;
(2) scala/mercato minuscolo (Kill Memo); (3) CV come prodotto, mentre il founder ha **GIS** (skill reale),
non CV (nascente). Le #1–#4 hanno budget da owner/cantieri (non micro-studi), niente firma, GIS-native,
ricorrenti, con sicurezza pubblica/claim come driver d'urgenza: mercato 10–100× più grande.

**Frase spietata:** il dolore pagante non è "calcolare l'RQD più in fretta" — è *"il rilevato non deve
franare sotto il treno"* e *"non voglio perdere il claim da 10M perché il terreno era diverso dalla
baseline"*. Valgono ordini di grandezza di più, non richiedono la firma, si attaccano con GIS + dati +
Python.

**Raccomandazione:** 2 mesi di interviste su **#1 (asset management geotecnico ferrovie/strade)** e
**#2 (I&M cantieri)**. Se uno regge, archivia GeoCore-RQD e pivota lì, portando l'unica cosa che vale:
dominio e relazioni geologiche.

---
*Catena: …→ Market Kill Memo → Pivot Analysis → Asset Strategy → Dataset Value → Opportunity Map.*
