# Lezione 10: KV Store Multithread

Questa lezione introduce la prima vera rottura rispetto al nodo singolo:
piu' client possono interagire contemporaneamente con lo stesso stato.

L'interfaccia del servizio resta quasi invariata. Il problema si sposta su:

- accesso concorrente allo stato condiviso;
- percorsi read-modify-write;
- safety violations;
- liveness e granularita' del lock.

## Materiale

- [Handout tecnico](./handout.md)
- [Contratto del protocollo](./api-contract.md)
- [Rappresentazione ad automi](./automata.md)
- [Lab multithread](../../labs/kv_store/threaded_locking/README.md)
- [Slide della lezione](../../slides/10-kv-store-threaded.pdf)

## Obiettivi

Alla fine della lezione dovresti saper:

- identificare i punti del codice che accedono a stato condiviso;
- distinguere accessi innocui e percorsi critici;
- motivare perche' `INCR` richiede una sezione critica;
- discutere una implementazione in termini di safety e liveness;
- leggere il comportamento del software come automa di stati e transizioni.
