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

