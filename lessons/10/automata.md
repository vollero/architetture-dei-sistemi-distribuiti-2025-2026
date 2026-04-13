# Rappresentazione ad Automi di Due Thread su `INCR`

Questa nota descrive una vista a stati globali dell'esecuzione concorrente di
due thread `T1` e `T2` che eseguono contemporaneamente `INCR counter`.

## Idea di base

Ogni nodo del grafo rappresenta uno **stato globale** del sistema:

```text
(stato locale di T1, stato locale di T2, valore condiviso, lock)
```

dove:

- lo stato locale puo' essere `Idle`, `Read(10)`, `Write(11)`, `Done`, oppure
  varianti con acquisizione/rilascio del lock;
- il valore condiviso e' il contenuto di `counter`;
- `lock` vale `free`, `held by T1`, `held by T2`.

## Caso unsafe

Figura:

- [Automa unsafe](./assets/incr-unsafe-automaton.svg)

Osservazione chiave:

- e' raggiungibile uno stato in cui **entrambi** i thread hanno letto `10`;
- da li' entrambi possono scrivere `11`;
- il valore finale `11` e' una safety violation: un incremento si perde.

## Caso safe

Figura:

- [Automa safe](./assets/incr-safe-automaton.svg)

Osservazione chiave:

- il lock impedisce che due thread attraversino insieme la parte
  `ReadCurrent -> ComputeNext -> WriteBack`;
- lo stato globale con due letture simultanee dello stesso valore non e'
  piu' raggiungibile;
- il risultato finale corretto e' `12`.

## Cosa leggere nel grafo

Domande utili:

1. Quali stati globali sono raggiungibili solo nella versione unsafe?
2. Quali transizioni vengono eliminate dal lock?
3. Quale safety violation e' resa impossibile?
4. Quale costo di liveness introduciamo imponendo serializzazione?

## Collegamento con il codice

Il blocco logico dell'operazione `INCR` e':

```text
read current -> compute next -> write back
```

Nel caso unsafe questo blocco e' interleavabile.

Nel caso safe il lock rende atomica l'intera sottosequenza critica.
