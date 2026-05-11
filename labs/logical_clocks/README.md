# Lab: Sincronizzazione e Clock Logici

Questo laboratorio contiene esempi Python eseguibili per discutere temporalita'
nei sistemi distribuiti.

Gli script non implementano un sistema di produzione. Sono simulazioni piccole,
pensate per rendere osservabili:

- clock fisici locali non allineati;
- clock logici di Lamport;
- ordine totale con tie-breaker;
- clock vettoriali;
- consegna causale dei messaggi.

## File

- `physical_clock_skew.py`: mostra come i log fisici possano risultare ingannevoli.
- `lamport_clock_simulation.py`: implementa le regole base dei clock di Lamport.
- `total_order_lamport.py`: ordina eventi con `(lamport_time, process_id)`.
- `vector_clock_simulation.py`: distingue causalita' e concorrenza.
- `causal_delivery.py`: simula consegna causale con vector clock.

## Esecuzione

```bash
python3 labs/logical_clocks/physical_clock_skew.py
python3 labs/logical_clocks/lamport_clock_simulation.py
python3 labs/logical_clocks/total_order_lamport.py
python3 labs/logical_clocks/vector_clock_simulation.py
python3 labs/logical_clocks/causal_delivery.py
```

## Domande per il lab

Per ogni script:

1. quale modello temporale viene usato?
2. quale proprieta' garantisce?
3. quale proprieta' non garantisce?
4. quale metadata viene aggiunto agli eventi o ai messaggi?
5. quale sarebbe il costo in un sistema reale?

## Collegamento con il KV store

I meccanismi del lab possono essere applicati al KV store per:

- ordinare update;
- ricostruire log distribuiti;
- riconoscere update concorrenti;
- implementare regole di conflitto;
- garantire causal delivery di messaggi tra repliche.

