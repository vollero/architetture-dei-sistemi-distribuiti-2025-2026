# Lab: KV Store Multithread con Sezioni Critiche

Questa tappa evolve il key-value store verso un server multi-client concorrente.

L'obiettivo non e' introdurre nuove funzionalita' "di prodotto", ma rendere
visibili i problemi di correttezza che emergono quando piu' thread accedono
allo stesso stato condiviso.

## File

- `server_threaded_unsafe.py`: versione thread-per-connection senza protezione
  dello stato condiviso
- `server_threaded.py`: versione corretta con lock e sezioni critiche esplicite
- `client.py`: client interattivo con host e porta configurabili
- `stress_incr.py`: client di carico per mostrare race su `INCR`

## Concetto chiave

L'interfaccia del servizio resta quasi invariata. Cambia l'implementazione:

- prima: un solo flusso di esecuzione;
- ora: piu' thread concorrenti;
- conseguenza: alcune sequenze di istruzioni non sono piu' safe senza lock.

## Nuovo comando

Rispetto al nodo singolo, viene aggiunto:

- `INCR <key>`

Questo comando serve a rendere evidente un classico percorso read-modify-write.
Su stato condiviso, `INCR` e' il punto piu' utile per osservare lost update.

## Avvio rapido

Versione unsafe:

```bash
python3 labs/kv_store/threaded_locking/server_threaded_unsafe.py
```

Versione safe:

```bash
python3 labs/kv_store/threaded_locking/server_threaded.py
```

Client interattivo:

```bash
python3 labs/kv_store/threaded_locking/client.py --port 6382
```

Stress test:

```bash
python3 labs/kv_store/threaded_locking/stress_incr.py --port 6383
python3 labs/kv_store/threaded_locking/stress_incr.py --port 6382
```

## Aspettativa sperimentale

- sulla versione unsafe, il valore finale dopo molti `INCR` concorrenti puo'
  risultare minore dell'atteso;
- sulla versione safe, il valore finale deve coincidere con il numero totale
  di incrementi riusciti.

## Domande tecniche da discutere

- Quali percorsi accedono a stato condiviso?
- Tutti gli accessi richiedono lock?
- Qual e' la sezione critica minima accettabile?
- Dove rischiamo safety violation?
- Dove rischiamo problemi di liveness se allarghiamo troppo il lock?
