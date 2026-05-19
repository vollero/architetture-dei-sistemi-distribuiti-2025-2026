# Scenari di Discussione: Vector Clock nel KV Store

## Scenario 1: il valore esiste nel sistema?

Sequenza:

```text
A> SET course sistemi-distribuiti
B> GET course
```

Domande:

- `B` deve vedere il valore scritto su `A`?
- Il contratto del laboratorio promette una vista globale o locale?
- Cosa dovrebbe cambiare per offrire una lettura globale?

Punto atteso:

```text
il laboratorio offre letture locali; la convergenza richiede sincronizzazione
```

## Scenario 2: aggiornamento causale

Sequenza:

```text
A> SET course sistemi-distribuiti
A> SYNC 6482
B> SET course sistemi-distribuiti-2026
```

Clock:

```text
A scrive: A:1,B:0,C:0
B aggiorna: A:1,B:1,C:0
```

Domande:

- Perché il clock di `B` contiene anche la componente di `A`?
- La nuova versione può eliminare quella precedente?
- Quale relazione causale è stata osservata?

Punto atteso:

```text
B ha visto l'aggiornamento di A prima di produrre il proprio aggiornamento
```

## Scenario 3: aggiornamenti concorrenti

Sequenza:

```text
A> SET room aula-a
B> SET room aula-b
A> SYNC 6482
```

Clock:

```text
aula-a = A:1,B:0,C:0
aula-b = A:0,B:1,C:0
```

Domande:

- I due clock sono ordinabili?
- Cosa succederebbe se il sistema scegliesse automaticamente l'ultimo arrivato?
- Quale proprietà di safety verrebbe violata?

Punto atteso:

```text
i clock sono concorrenti; scartarne uno sarebbe perdita silenziosa di update
```

## Scenario 4: perché `SET` viene rifiutato

Sequenza:

```text
A> GET room
A< CONFLICT ...
A> SET room aula-c
A< ERR conflict_exists ...
```

Domande:

- Perché `SET` non viene interpretato come scelta del vincitore?
- Chi ha l'autorità per decidere il valore corretto?
- Come dovrebbe essere documentato questo vincolo nel contratto?

Punto atteso:

```text
SET è una scrittura semplice; RESOLVE è una decisione applicativa sul conflitto
```

## Scenario 5: risoluzione

Sequenza:

```text
A> RESOLVE room aula-c
```

Clock dei siblings:

```text
A:1,B:0,C:0
A:0,B:1,C:0
```

Clock della risoluzione:

```text
A:2,B:1,C:0
```

Domande:

- Perché `A:2,B:1,C:0` domina entrambi i siblings?
- Cosa rappresenta l'incremento della componente `A`?
- Cosa succederebbe se la risoluzione usasse solo `A:2,B:0,C:0`?

Punto atteso:

```text
la risoluzione deve incorporare la conoscenza di tutti i siblings osservati
```

## Scenario 6: cancellazione concorrente

Sequenza proposta:

```text
A> SET doc v1
A> SYNC 6482
A> DELETE doc
B> SET doc v2
A> SYNC 6482
```

Domande:

- La cancellazione deve vincere sempre?
- Una tombstone è un valore speciale o una versione causale?
- Quando è sicuro rimuovere definitivamente una tombstone?

Punto atteso:

```text
delete è un aggiornamento causale; può essere concorrente con una scrittura
```

## Scenario 7: safety e liveness

Safety da verificare:

```text
una versione concorrente non viene eliminata
```

Liveness da discutere:

```text
se le repliche continuano a sincronizzarsi e i conflitti vengono risolti,
le repliche convergono
```

Domande:

- Quali guasti bloccano la liveness?
- Quali bug potrebbero violare la safety?
- È meglio bloccare scritture durante un conflitto o accettarle comunque?

Punto atteso:

```text
safety e liveness sono proprietà distinte; il laboratorio privilegia safety
```

## Scenario 8: limiti del modello

Domande:

- Cosa cambia se aggiungiamo una replica `D` dopo che esistono già dati?
- Come gestiamo un nodo che riparte dopo avere perso il proprio stato?
- Quando servirebbe consenso invece di vector clock?
- Quando servirebbe un CRDT invece di una risoluzione manuale?

Punto atteso:

```text
i vector clock risolvono il problema dell'osservazione causale, non tutti i problemi di coordinamento
```
