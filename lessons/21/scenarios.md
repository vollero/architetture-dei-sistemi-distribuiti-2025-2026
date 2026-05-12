# Scenari di Discussione: Clock Logici e Sincronizzazione

Questi scenari sono pensati per essere discussi in aula prima di mostrare una
soluzione completa.

## Scenario 1: Log che sembrano impossibili

Due nodi producono questi log:

```text
A 10:00:00.200 send m to B
B 10:00:00.100 receive m from A
```

Domande:

- il messaggio e' stato ricevuto prima di essere inviato?
- quale assunzione sui clock fisici e' stata violata?
- un clock di Lamport risolverebbe il problema?
- quale informazione perdiamo usando solo Lamport?

Hint:

Il clock fisico locale serve per osservabilita' umana, ma non garantisce
causalita' se non conosciamo un limite all'errore tra clock.

## Scenario 2: Due scritture concorrenti sul KV store

Due client inviano update a repliche diverse:

```text
Client 1 -> Replica A: SET x 1
Client 2 -> Replica B: SET x 2
```

Non c'e' comunicazione tra i due eventi prima della replica successiva.

Domande:

- possiamo dire quale update e' avvenuto prima?
- un ordine totale con `(lamport_time, node_id)` puo' scegliere un vincitore?
- scegliere un vincitore significa aver dimostrato causalita'?
- quando sarebbe meglio conservare entrambi i valori come conflitto?

Hint:

Lamport puo' fornire un ordine deterministicamente condiviso. I vector clock
possono dire che i due update sono concorrenti.

## Scenario 3: Causal delivery

Un processo `A` invia un messaggio `m1` a `B`.
Poi, dopo aver ricevuto una risposta, invia `m2` a `C`.

Domande:

- quali eventi sono causalmente ordinati?
- cosa deve garantire un sistema di causal delivery?
- quale metadata serve allegare ai messaggi?

Hint:

Lamport clock puo' rispettare l'ordine causale, ma non basta sempre per decidere
quali messaggi devono essere consegnati prima se si vuole rilevare concorrenza.

## Scenario 4: Mutua esclusione distribuita

Tre processi vogliono entrare in una sezione critica distribuita.
Ogni richiesta viene timestampata con:

```text
(lamport_time, process_id)
```

Domande:

- perche' serve un ordine totale?
- cosa succede se due richieste hanno lo stesso Lamport time?
- cosa garantisce il tie-breaker sul process id?
- quali messaggi servono per sapere che la propria richiesta e' la prima?

Hint:

Questo e' il punto di partenza dell'algoritmo di Ricart-Agrawala: richiesta
timestampata, risposte dagli altri processi, ingresso solo quando la richiesta e'
la prima nell'ordine noto.

## Scenario 5: Lease e tempo fisico

Un primary ha un lease valido fino a:

```text
12:00:10.000
```

Un secondary vede scadere il lease e si promuove.

Domande:

- quali assunzioni servono sugli orologi?
- quanto deve essere lungo il lease rispetto all'errore massimo di sincronizzazione?
- cosa succede se il primary ha un clock indietro?
- un clock logico puo' sostituire completamente il tempo fisico in questo caso?

Hint:

I lease richiedono una nozione di tempo reale. I clock logici ordinano eventi,
ma non misurano durate reali.

## Scenario 6: Debug di una capstone fallita

Durante la capstone, un gruppo osserva:

```text
GETV alpha -> OK two version=1 shard=S2
CAS alpha 1 three -> ERR version_mismatch current=2
```

Ma nei log del client sembra che nessun altro abbia scritto `alpha`.

Domande:

- quali log bisogna raccogliere?
- un timestamp fisico basta?
- un Lamport timestamp sui messaggi router-shard aiuterebbe?
- un vector clock sarebbe eccessivo o utile?

Hint:

Per debug distribuito serve poter ricostruire relazioni di causalita' tra eventi
di processi diversi. Il timestamp fisico aiuta, ma puo' non bastare.

## Scenario 7: Due nodi vogliono diventare leader

Tre acceptor devono decidere quale nodo sara' leader.

Due proposer inviano quasi contemporaneamente:

```text
P1 propone leader=A
P2 propone leader=B
```

Domande:

- un Lamport timestamp basta per decidere in modo sicuro?
- cosa succede se P1 raggiunge gli acceptor `A1` e `A2`, mentre P2 raggiunge `A2` e `A3`?
- perche' e' importante che due quorum si intersechino?
- quale informazione deve restituire un acceptor nella fase `PROMISE`?

Hint:

Questa e' la motivazione di Paxos: non vogliamo solo ordinare proposte, vogliamo
impedire che due valori diversi vengano scelti da due quorum.

## Scenario 8: Proposer con numero piu' alto

Un proposer `P1` ha gia' ottenuto accept per:

```text
proposal=(1,P1), value=SET x=1
```

Poi arriva `P2` con:

```text
proposal=(2,P2), value=SET x=2
```

Domande:

- P2 puo' scegliere liberamente `SET x=2` solo perche' ha proposal number piu' alto?
- cosa deve fare se scopre che un acceptor aveva gia' accettato `SET x=1`?
- quale proprieta' di safety si romperebbe se P2 ignorasse quel valore?

Hint:

In Paxos, un numero di proposta piu' alto permette di proseguire, ma obbliga a
preservare il valore gia' accettato con proposal number piu' alto tra le promise
ricevute.

## Scenario 9: Verifica dell'invariante di Paxos

Consideriamo tre acceptor:

```text
A1, A2, A3
```

e quorum di maggioranza:

```text
{A1,A2}, {A1,A3}, {A2,A3}
```

Stato iniziale:

```text
accepted[A1] = none
accepted[A2] = none
accepted[A3] = none
```

Dopo alcune transizioni:

```text
accepted[A1] = ((1,P1), v1)
accepted[A2] = ((1,P1), v1)
accepted[A3] = none
```

Domande:

- `v1` e' scelto secondo la definizione formale?
- un proposer `P2` con proposta `(2,P2)` puo' scegliere `v2`?
- quale informazione deve ricevere da almeno un acceptor?
- quale invariante impedisce di scegliere `v2`?

Hint:

Usare la definizione:

```text
chosen(v) iff exists quorum q:
  for every a in q:
    accepted[a] = (n, v)
```

e la proprieta':

```text
ogni quorum successivo interseca il quorum che ha scelto v1
```
