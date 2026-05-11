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
- `lamport_mutex.py`: simula mutua esclusione distribuita con richieste timestampate.
- `vector_clock_simulation.py`: distingue causalita' e concorrenza.
- `causal_delivery.py`: simula consegna causale con vector clock.
- `paxos_single_decree.py`: simula Paxos single-decree con proposer concorrenti.

## Esecuzione

```bash
python3 labs/logical_clocks/physical_clock_skew.py
python3 labs/logical_clocks/lamport_clock_simulation.py
python3 labs/logical_clocks/total_order_lamport.py
python3 labs/logical_clocks/lamport_mutex.py
python3 labs/logical_clocks/vector_clock_simulation.py
python3 labs/logical_clocks/causal_delivery.py
python3 labs/logical_clocks/paxos_single_decree.py
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
- decidere un valore comune con consenso quando un ordine locale non basta.

## Paxos nel lab

Lo script `paxos_single_decree.py` implementa una versione didattica di Paxos:

- un solo valore da scegliere;
- tre acceptor;
- due proposer concorrenti;
- quorum di maggioranza;
- fase `prepare/promise`;
- fase `accept/accepted`.

Il punto da osservare e':

- non basta che un proposer abbia un clock o un timestamp;
- serve un protocollo che impedisca a due valori diversi di essere scelti da due quorum;
- se un proposer vede un valore gia' accettato, deve riproporre quello.
