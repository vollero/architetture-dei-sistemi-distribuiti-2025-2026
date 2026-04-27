# Lezione 16: KV Store con Rebalancing e Migrazione

Questa lezione riparte dal limite piu' evidente dello store shardato:

- aggiungere uno shard cambia il routing;
- ma le chiavi gia' scritte non si spostano da sole.

## Materiale

- [Handout tecnico](./handout.md)
- [Contratto del protocollo](./api-contract.md)
- [Lab rebalancing e migrazione](../../labs/kv_store/rebalance_migration/README.md)
- [Slide della lezione](../../slides/16-kv-store-rebalancing.pdf)

## Obiettivi

Alla fine della lezione dovresti saper:

- distinguere routing teorico e posizione reale dei dati;
- spiegare perche' aggiungere uno shard rompe l'assunzione di localita';
- discutere una migrazione come protocollo, non come copia banale;
- confrontare strategie implementative diverse per la migrazione delle chiavi;
- stimare costi, tempi e finestre di rischio del rebalance;
- individuare le finestre di incoerenza durante il rebalance;
- collegare il tema alla membership dinamica.
