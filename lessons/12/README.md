# Lezione 12: KV Store con Replica Primary-Secondary

Questa lezione introduce il primo salto dal nodo singolo al sistema
replicato.

L'interfaccia applicativa resta quasi la stessa, ma il significato di una
risposta positiva cambia di nuovo:

- il primary puo' aver applicato localmente un update;
- il secondario puo' non averlo ancora visto;
- una lettura da replica puo' quindi osservare uno stato piu' vecchio.

## Materiale

- [Handout tecnico](./handout.md)
- [Contratto del protocollo](./api-contract.md)
- [Lab replica primary-secondary](../../labs/kv_store/replication_primary_secondary/README.md)
- [Slide della lezione](../../slides/12-kv-store-replication.pdf)

## Obiettivi

Alla fine della lezione dovresti saper:

- distinguere replica sincrona e asincrona;
- discutere il significato operativo di "committed";
- motivare perche' una lettura da replica puo' essere stantia;
- valutare il trade-off tra consistenza osservabile e liveness;
- identificare il rischio concettuale di split brain.
