# Lezione 22: Consenso Distribuito e Basic Paxos

Questa lezione separa il problema del consenso dai problemi di sincronizzazione
e clock logici trattati nella lezione 21.

Il riferimento strutturale per Paxos è la presentazione classica della voce
[Paxos (computer science)](https://en.wikipedia.org/wiki/Paxos_(computer_science)).

## Materiale

- [Handout tecnico](./handout.md)
- [Contratto e proprietà](./api-contract.md)
- [Scenari di discussione](./scenarios.md)
- [Approfondimento su Basic Paxos](./paxos.md)
- [Esempi eseguibili](./lab-examples.md)
- [Slide della lezione](../../slides/22-consensus-paxos.pdf)

## Obiettivi

Alla fine della lezione dovresti saper:

- spiegare perché ordinare eventi non equivale a decidere un valore condiviso;
- formalizzare Validity, Agreement e Termination;
- distinguere safety e liveness in un protocollo di consenso;
- descrivere le assunzioni di Basic Paxos su processi, rete e guasti;
- spiegare proposer, acceptor, learner e client;
- motivare l'uso dei quorum e della loro intersezione;
- seguire il flusso `Prepare`, `Promise`, `Accept`, `Accepted`;
- spiegare perché `accepted_n` e `accepted_value` vincolano i proposer successivi;
- collegare Basic Paxos a leader election e log replicato nel KV store.
