# Lezione 21: Sincronizzazione e Clock Logici

Questa lezione è dedicata alla temporalità nei sistemi distribuiti.

Il punto centrale non è "leggere l'ora", ma chiarire quale contratto temporale
un sistema può promettere:

- tempo fisico locale;
- tempo fisico sincronizzato entro un errore;
- clock monotoni per misurare durate;
- happened-before;
- clock di Lamport;
- ordine totale artificiale;
- vector clock;
- causal delivery.

Il consenso distribuito e Basic Paxos sono stati separati nella
[lezione 22](../22/README.md).

## Materiale

- [Handout tecnico](./handout.md)
- [Contratto e modelli temporali](./api-contract.md)
- [Scenari di discussione](./scenarios.md)
- [Esempi eseguibili](./lab-examples.md)
- [Lab sui clock logici](../../labs/logical_clocks/README.md)
- [Slide della lezione](../../slides/21-logical-clocks.pdf)

## Obiettivi

Alla fine della lezione dovresti saper:

- distinguere clock fisico locale, clock monotono e clock sincronizzato;
- spiegare skew, drift, precisione, accuratezza e incertezza temporale;
- motivare quando usare NTP, PTP, timeout, lease e timestamp fisici;
- spiegare perché un timestamp fisico locale non prova causalità globale;
- applicare la relazione `happened-before` di Lamport;
- implementare e leggere clock di Lamport;
- distinguere ordine causale e ordine totale artificiale;
- usare un tie-breaker deterministico `(lamport_time, process_id)`;
- spiegare vector clock a partire dalla membership ordinata;
- distinguere causalità e concorrenza con vector clock;
- descrivere causal delivery come layer tra trasporto e applicazione.
