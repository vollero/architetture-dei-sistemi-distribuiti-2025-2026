# Lab: Sincronizzazione, Clock Logici e Consenso

Questo laboratorio contiene esempi Python eseguibili per discutere temporalità,
clock logici e consenso nei sistemi distribuiti.

Gli script non implementano un sistema di produzione. Sono simulazioni piccole,
pensate per rendere osservabili:

- clock fisici locali non allineati;
- clock logici di Lamport;
- ordine totale con tie-breaker;
- clock vettoriali;
- consegna causale dei messaggi;
- consenso single-decree con Paxos.

## File

### Lezione 21: sincronizzazione e clock logici

- `physical_clock_skew.py`: mostra come i log fisici possano risultare ingannevoli.
- `lamport_clock_simulation.py`: implementa le regole base dei clock di Lamport.
- `total_order_lamport.py`: ordina eventi con `(lamport_time, process_id)`.
- `lamport_mutex.py`: simula mutua esclusione distribuita con richieste timestampate.
- `vector_clock_simulation.py`: distingue causalità e concorrenza.
- `causal_delivery.py`: simula consegna causale con un message vector derivato dai clock vettoriali.

### Lezione 22: consenso distribuito

- `paxos_single_decree.py`: simula Paxos single-decree con proposer concorrenti.

## Esecuzione per la lezione 21

```bash
python3 labs/logical_clocks/physical_clock_skew.py
python3 labs/logical_clocks/lamport_clock_simulation.py
python3 labs/logical_clocks/total_order_lamport.py
python3 labs/logical_clocks/lamport_mutex.py
python3 labs/logical_clocks/vector_clock_simulation.py
python3 labs/logical_clocks/causal_delivery.py
```

## Esecuzione per la lezione 22

```bash
python3 labs/logical_clocks/paxos_single_decree.py
```

## Domande per il lab

Per ogni script:

1. quale modello temporale viene usato?
2. quale proprietà garantisce?
3. quale proprietà non garantisce?
4. quale metadata viene aggiunto agli eventi o ai messaggi?
5. quale sarebbe il costo in un sistema reale?

Per `causal_delivery.py`, distinguere esplicitamente:

- ricezione del messaggio dalla rete;
- layer di causal delivery che può bufferizzare il messaggio;
- `message_clock`, che conta messaggi causalmente noti, da un vector clock completo degli eventi locali;
- consegna del messaggio all'applicazione;
- permanenza in buffer finché le dipendenze causali non sono soddisfatte.

Nel modello architetturale, causal delivery sta tra trasporto e applicazione:

```text
transport -> causal delivery -> application
```

Per `paxos_single_decree.py`, ricordare che gli acceptor sono non bizantini:
possono fermarsi o non rispondere, ma non mentono sullo stato promesso o
accettato.

## Collegamento con il KV store

I meccanismi del lab possono essere applicati al KV store per:

- ordinare update;
- ricostruire log distribuiti;
- riconoscere update concorrenti;
- implementare regole di conflitto;
- garantire causal delivery di messaggi tra repliche;
- decidere un valore comune con consenso quando un ordine locale non basta.

## Paxos nel lab

Lo script `paxos_single_decree.py` implementa un caso di studio su Basic Paxos:

- un solo valore da scegliere;
- tre acceptor;
- due proposer concorrenti;
- quorum di maggioranza;
- prima configurazione `{A1,A2}` che accetta `SET x=1`;
- seconda configurazione `{A2,A3}` che deve convergere sul valore già protetto;
- stato degli acceptor: `promised_n` è il massimo proposal number promesso, `accepted_n` è il proposal number dell'ultimo valore accettato, `accepted_value` è quel valore;
- fase `prepare/promise`;
- scelta del valore sicuro;
- fase `accept/accepted`.

Il punto da osservare è:

- non basta che un proposer abbia un clock o un timestamp;
- serve un protocollo che impedisca a due valori diversi di essere scelti da due quorum;
- se un proposer vede un valore già accettato, deve riproporre quello;
- la convergenza passa dall'intersezione dei quorum e dalla memoria degli acceptor.
