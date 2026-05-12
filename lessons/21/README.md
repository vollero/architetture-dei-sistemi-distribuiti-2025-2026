# Lezione 21: Sincronizzazione e Clock Logici

Questa lezione introduce il problema della temporalita' nei sistemi distribuiti.

L'obiettivo non e' "leggere l'ora", ma capire quando un sistema distribuito puo'
dire che un evento e' avvenuto prima di un altro, quando non puo' dirlo, e quali
meccanismi puo' usare per costruire un ordine utile.

## Materiale

- [Handout tecnico](./handout.md)
- [Contratto e modelli temporali](./api-contract.md)
- [Scenari di discussione](./scenarios.md)
- [Approfondimento su Paxos](./paxos.md)
- [Lab sui clock logici](../../labs/logical_clocks/README.md)
- [Slide della lezione](../../slides/21-logical-clocks.pdf)

## Obiettivi

Alla fine della lezione dovresti saper:

- distinguere tempo fisico, tempo logico e ordine causale;
- spiegare perche' gli orologi locali non bastano per ordinare eventi distribuiti;
- applicare la relazione `happened-before` di Lamport;
- implementare clock logici di Lamport;
- riconoscere quando un ordine totale e' utile ma artificiale;
- discutere quando servono clock vettoriali o timestamp fisici sincronizzati;
- collegare clock logici a logging, replica, debug, mutual exclusion e causal delivery;
- spiegare perche' il consenso richiede piu' di un timestamp;
- descrivere Paxos single-decree, quorum, proposal number, prepare/promise e accept/accepted.
