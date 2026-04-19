# Lezione 14: KV Store con Quorum di Lettura e Scrittura

Questa lezione risponde al limite emerso nel failover a due nodi.

La domanda adesso e':

- quante repliche devono confermare una scrittura?
- quante repliche devo leggere per fidarmi del risultato?

## Materiale

- [Handout tecnico](./handout.md)
- [Contratto del protocollo](./api-contract.md)
- [Lab quorum cluster](../../labs/kv_store/quorum_cluster/README.md)
- [Slide della lezione](../../slides/14-kv-store-quorum.pdf)

## Obiettivi

Alla fine della lezione dovresti saper:

- spiegare il significato operativo di `N`, `R`, `W`;
- discutere perche' `R + W > N` e' una soglia importante;
- mostrare come nascono letture stantie con quorum deboli;
- valutare il costo di quorum forti in termini di disponibilita';
- collegare il problema ai conflitti di versione.
