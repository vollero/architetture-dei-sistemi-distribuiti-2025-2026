# Lezione 09: Key-Value Store v0

Questa lezione introduce un key-value store minimale accessibile via rete.

Lo scopo non e' costruire subito un sistema "ricco", ma fissare con precisione:

- l'interfaccia esposta al client;
- il contratto delle operazioni;
- i casi limite;
- i limiti della versione attuale.

La versione di oggi e' volutamente semplice:

- un solo nodo;
- stato in memoria;
- protocollo testuale su TCP;
- nessuna persistenza;
- nessuna replica;
- nessuna tolleranza ai guasti.

## Obiettivi

Alla fine della lezione dovresti saper:

- progettare un'interfaccia piccola ma coerente;
- distinguere sintassi del protocollo e semantica delle operazioni;
- motivare cosa significhi che una scrittura e' andata a buon fine;
- identificare cosa manca per trasformare un server locale in un sistema distribuito.

## Materiale

- [Traccia della lezione](./today.md)
- [Contratto del protocollo](./api-contract.md)
- [Laboratorio: single node](../../labs/kv_store/single_node/README.md)

## Domande guida

Durante il laboratorio tieni presenti queste domande:

1. Che cosa promette davvero `SET`?
2. Come distingui una chiave assente da un valore vuoto?
3. Quali errori sono errori di protocollo e quali sono esiti applicativi?
4. Quali scelte di oggi diventano problematiche quando il sistema sara' distribuito?
