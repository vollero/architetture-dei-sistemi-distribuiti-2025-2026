# Scenari: Sincronizzazione e Clock Logici

## Scenario 1: log fisico impossibile

```text
A 10:00:00.200 send m to B
B 10:00:00.100 receive m from A
```

Domande:

- il messaggio è stato ricevuto prima di essere inviato?
- quale assunzione sui clock fisici è falsa?
- il problema è di risoluzione, accuratezza o skew?

## Scenario 2: monotonic clock o wall-clock?

Un client invia una richiesta e il server deve misurare un timeout di 500 ms.

Domande:

- useresti wall-clock o monotonic clock?
- cosa succede se NTP sposta indietro il wall-clock?
- quale contratto temporale serve al timeout?

## Scenario 3: lease

Un nodo ottiene un lease valido fino a:

```text
12:00:10.000
```

Domande:

- quale errore massimo di sincronizzazione è tollerabile?
- cosa succede se il clock del nodo è indietro?
- perché un lease richiede margine di sicurezza?

## Scenario 4: Lamport e causalità

```text
A: send m to B      L=4
B: receive m        L=7
```

Domande:

- quale relazione causale è garantita?
- `L=4 < L=7` basta da solo a dimostrare causalità?
- quale parte della storia serve oltre al timestamp?

## Scenario 5: eventi concorrenti

```text
A: SET x 1      L=1
B: SET x 2      L=1
```

Non ci sono messaggi tra A e B prima delle scritture.

Domande:

- gli eventi sono ordinabili causalmente?
- un tie-breaker può scegliere un ordine deterministico?
- scegliere un ordine significa dimostrare causalità?

## Scenario 6: mutua esclusione

```text
B: request lock at L=1
A: request lock at L=1
C: request lock at L=1
```

Con ordine dei processi:

```text
A < B < C
```

Domande:

- quale richiesta entra prima?
- questa è una proprietà di safety o liveness?
- quale ipotesi sui messaggi serve per la liveness?

## Scenario 7: vector clock

Membership:

```text
P = [A, B, C]
```

Eventi:

```text
e1 = [2,0,0]
e2 = [2,1,0]
e3 = [0,1,0]
```

Domande:

- `e1` precede causalmente `e2`?
- `e1` ed `e3` sono confrontabili?
- chi incrementa la componente di `A`?

## Scenario 8: causal delivery

```text
m1: A pubblica x
m2: B reagisce a x
C riceve m2 prima di m1
```

Domande:

- C può consegnare `m2` all'applicazione subito?
- dove va tenuto `m2`?
- quale proprietà di safety protegge causal delivery?
