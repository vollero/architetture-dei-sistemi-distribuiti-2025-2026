# Lezione 23: KV Store Distribuito con Vector Clock

Questa lezione collega i clock vettoriali al percorso sul KV store distribuito.
L'obiettivo è mostrare come un metadato causale diventi parte del contratto
dell'interfaccia e influenzi le scelte implementative di replica, lettura,
sincronizzazione e risoluzione dei conflitti.

Il caso di studio è un KV store multi-master con tre repliche. Ogni chiave può
avere una o più versioni, ciascuna annotata con un vector clock per chiave.

## Materiale

- [Handout tecnico](./handout.md)
- [Diagrammi temporali della demo](./handout.md#diagrammi-temporali)
- [Guida operativa del laboratorio](./lab-guide.md)
- [Scenari di discussione](./scenarios.md)
- [Lab eseguibile](../../labs/kv_store/vector_clock_replication/README.md)
- [Slide della lezione](../../slides/23-vector-clock-kv.pdf)

## Obiettivi

Alla fine della lezione dovresti saper:

- spiegare perché una versione scalare non distingue causalità e concorrenza;
- leggere un vector clock come version vector associato a una chiave;
- stabilire se una versione domina, è dominata o è concorrente;
- descrivere il ruolo di siblings e tombstone in un KV store replicato;
- distinguere `SET`, `SYNC` e `RESOLVE` come operazioni con contratti diversi;
- spiegare perché il sistema non deve risolvere automaticamente tutti i conflitti;
- collegare safety, liveness e convergenza al comportamento del laboratorio;
- riconoscere i limiti del caso di studio rispetto a un sistema di produzione.

## Demo principale

Eseguire dalla radice del repository:

```bash
python3 labs/kv_store/vector_clock_replication/demo_vector_clock_kv.py
```

La demo avvia tre repliche locali, genera una scrittura causale, poi una coppia
di scritture concorrenti, mostra il conflitto, forza una risoluzione esplicita
e sincronizza le repliche fino alla convergenza.
