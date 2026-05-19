# Contratto: Consenso e Basic Paxos

## Contratto di consenso

L'interfaccia logica di consenso espone:

```text
propose(value) -> accepted_for_consensus
learn() -> chosen_value
```

Il contratto non promette che ogni chiamata completi immediatamente.
Promette che, se un valore viene appreso, non sarà incompatibile con un valore
appreso da un altro learner corretto.

## Proprietà

### Validity

```text
learned(v) => proposed(v)
```

### Agreement

```text
learned(l1, v1) and learned(l2, v2) => v1 = v2
```

### Liveness condizionata

Il progresso richiede condizioni operative:

- quorum raggiungibile;
- rete sufficientemente stabile;
- proposer non continuamente in conflitto;
- retry con proposal number crescenti;
- stato persistente degli acceptor non perso.

## Stato degli acceptor

Ogni acceptor conserva:

```text
promised_n
accepted_n
accepted_value
```

`promised_n` vincola il futuro.
`accepted_n` e `accepted_value` rappresentano memoria del passato.

## Messaggi

```text
PREPARE(n)
PROMISE(n, accepted_n, accepted_value)
ACCEPT(n, value)
ACCEPTED(n, value)
```

## Valore scelto

Un valore è scelto quando un quorum di acceptor invia `ACCEPTED` per lo stesso
proposal number e valore:

```text
chosen(v) iff exists n, exists quorum q:
  for every a in q:
    accepted[a] = (n, v)
```

## Collegamento con il KV store

Nel KV store il contratto può essere usato per:

- decidere `leader = node`;
- decidere `log[i] = command`;
- decidere una configurazione di cluster;
- coordinare recovery o commit critici.
