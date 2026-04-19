# Lezione 15: KV Store con Sharding e Routing

Questa lezione sposta il focus dalla replica al partizionamento.

La domanda centrale diventa:

- dove vive una chiave?
- chi decide il suo shard?
- quali operazioni restano locali e quali diventano globali?

## Materiale

- [Handout tecnico](./handout.md)
- [Contratto del protocollo](./api-contract.md)
- [Lab sharding con router](../../labs/kv_store/sharding_router/README.md)
- [Slide della lezione](../../slides/15-kv-store-sharding.pdf)

## Obiettivi

Alla fine della lezione dovresti saper:

- spiegare il ruolo del router nel partizionamento;
- mostrare come una chiave venga assegnata a uno shard;
- distinguere operazioni locali e scatter-gather;
- discutere hotspot e squilibrio di carico;
- motivare perche' aggiungere uno shard richiede migrazione dati.
