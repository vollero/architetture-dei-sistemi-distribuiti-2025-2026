# Handout: Versioni, GETV e Compare-And-Set

## Obiettivo della tappa

Finora il client poteva:

- leggere un valore;
- scrivere un valore;
- affidarsi alle garanzie interne del server.

Ora vogliamo introdurre un contratto piu' ricco:

- il client osserva una versione;
- il client puo' dire "scrivi solo se nulla e' cambiato nel frattempo".

## Blind write contro conditional write

Una `SET` e' una blind write:

- aggiorna senza chiedere se il valore sia cambiato rispetto a una lettura
  precedente del client.

Una `CAS` e' una conditional write:

- aggiorna solo se la versione osservata e' ancora corrente.

## `GETV`

`GETV` espone:

- il valore;
- la versione.

Questa scelta ha conseguenze importanti:

- il client vede una parte della logica di concorrenza;
- la versione entra nel contratto dell'API;
- il server non puo' piu' cambiare arbitrariamente il significato di quella
  versione senza rompere i client.

## `version_mismatch`

Il risultato:

```text
ERR version_mismatch current=7
```

non e' un errore "tecnico" qualsiasi.

E' un esito applicativo del contratto: il server sta dicendo che la precondizione
della scrittura non era piu' vera.

## Perche' questa tappa e' importante

`CAS` e' un ponte concettuale tra:

- store locale concorrente;
- store replicato;
- store shardato con migrazioni.

In tutti questi casi la domanda e':

> il client puo' ancora fidarsi dello stato che aveva osservato prima di
> scrivere?

## Messaggio da portare a casa

Con `GETV` e `CAS` il contratto non descrive piu' solo "quale valore leggi" o
"quale valore scrivi", ma anche:

- quale stato hai osservato;
- sotto quale precondizione il server accetta la tua scrittura.
