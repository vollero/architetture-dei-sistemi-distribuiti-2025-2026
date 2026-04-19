# Lezione 13: KV Store con Failover e Leader Instabile

Questa lezione continua il percorso dopo la replica primary-secondary.

La domanda non e' piu' solo "come replico?", ma:

- come faccio a capire se il leader e' ancora vivo?
- quando un follower puo' promuoversi?
- cosa succede se due nodi si credono entrambi leader?

## Materiale

- [Handout tecnico](./handout.md)
- [Contratto del protocollo](./api-contract.md)
- [Lab failover a due nodi](../../labs/kv_store/failover_pair/README.md)
- [Slide della lezione](../../slides/13-kv-store-failover.pdf)

## Obiettivi

Alla fine della lezione dovresti saper:

- distinguere heartbeat, timeout e sospetto di guasto;
- motivare una promozione a leader dopo timeout;
- spiegare perche' due nodi non bastano a evitare split brain;
- discutere safety e liveness di un failover basato solo su timeout;
- collegare il problema alla necessita' di quorum.
