# Scenari: Consenso e Basic Paxos

## Scenario 1: ordine non è consenso

Due repliche propongono leader diversi:

```text
P1 propone leader=A
P2 propone leader=B
```

Domande:

- un timestamp più alto basta per decidere?
- cosa succede se due gruppi di nodi vedono proposte diverse?
- quale proprietà impedisce due leader scelti?

## Scenario 2: primo round senza conflitti

```text
P1 -> A1,A2: PREPARE((1,P1))
A1 -> P1: PROMISE((1,P1), none, none)
A2 -> P1: PROMISE((1,P1), none, none)
```

Domande:

- perché `P1` può proporre il proprio valore?
- quale quorum ha raggiunto?
- quando il learner può apprendere il valore?

## Scenario 3: proposer successivo

Stato:

```text
A1 accepted ((1,P1), SET x 1)
A2 accepted ((1,P1), SET x 1)
A3 accepted none
```

Poi:

```text
P2 -> A2,A3: PREPARE((2,P2))
```

Domande:

- cosa deve rispondere `A2`?
- perché `P2` non può scegliere liberamente `SET x 2`?
- quale ruolo ha l'intersezione tra `{A1,A2}` e `{A2,A3}`?

## Scenario 4: round fallito

```text
P1 usa n=10
P2 usa n=11
P1 riprova con n=12
P2 riprova con n=13
```

Domande:

- quale proprietà rimane protetta?
- quale proprietà è a rischio?
- quale ruolo pratico può avere un leader stabile?

## Scenario 5: guasto di un acceptor

Tre acceptor, quorum di due.

```text
A3 non risponde
```

Domande:

- il sistema può ancora scegliere un valore?
- quale quorum resta disponibile?
- cosa cambia se falliscono due acceptor?
