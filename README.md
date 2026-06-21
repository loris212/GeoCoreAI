# GeoCore AI

Stima automatica dell'**RQD (Rock Quality Designation)** da foto di cassette
catalogatrici di sondaggi geognostici. Pipeline di Computer Vision +
**strumento di assistenza** al geologo (non sostitutivo).

> Prototipo di ricerca/tesi. La relazione geologica resta firmata da un geologo
> abilitato; lo strumento fornisce **misura + candidati**, non decisioni automatiche.

## Setup

```bash
pip install -r requirements.txt
```

## Demo (interfaccia per geologi)

```bash
# 1) genera i casi curati validati (una volta)
python -m geocore.demo_cases
# 2) avvia l'app
streamlit run app.py
```

L'app mostra casi **validati** (RQD predetto vs ground-truth annotato), il
metodo, la valutazione e — in trasparenza — i **limiti** del modello.

## Pipeline da riga di comando

```bash
python -m geocore foto_cassetta.jpg --scomparto-cm 100 --manovra-cm 500 -o out/
```
Produce overlay PNG + JSON con RQD per fila e aggregato.

## Riproduzione dei risultati (tesi)

```bash
python reproduce.py                 # ablazioni + borehole-CV + casi demo (no SAM)
python experiments/spike_models.py  # confronto a tre vie completo (con SAM, lento)
```
Struttura della tesi e mappatura capitoli→artefatti in **`THESIS_OUTLINE.md`**.
Il modello addestrato è versionato in `geocore/models/best.pt`.

## Struttura

| Percorso | Ruolo |
|---|---|
| `geocore/` | pipeline di produzione (fasi 1→4, CLI, demo) |
| `app.py` | interfaccia Streamlit per dimostrazioni |
| `estrai_file_carote.py` | Fase 1 originale (rettifica + file) |
| `experiments/` | **spina scientifica**: harness §6, spike 3-vie, ablazioni, report |
| `GeoCore_AI_*.md` | documenti di analisi (audit, validazione, strategia) |
| `archive/` | dataset Kaggle (non versionato) |

## Stato e limiti noti

- **Generalizzazione cross-sito debole**: ottima in-distribution (MAE ~5–7 pp),
  crolla su sondaggi mai visti (MAE ~34 pp). Vedi `experiments/REPORT_spike_3way.md`.
- La scala fisica (10 cm) richiede marker o lunghezza scomparto nota.
- Frattura naturale vs artificiale: non risolvibile da foto 2D → human-in-the-loop.
