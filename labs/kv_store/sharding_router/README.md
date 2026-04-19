# Lab: KV Store con Sharding e Router

Questa tappa separa il key space in piu' partizioni.

L'obiettivo e' rendere visibili:

- routing della chiave verso uno shard;
- differenza tra operazioni locali a una partizione e operazioni globali;
- hotspot su uno shard;
- costo di `KEYS` quando il cluster non e' piu' monolitico.

## File

- `shard_node.py`: nodo che gestisce una singola partizione
- `router.py`: endpoint client che applica hashing della chiave
- `client.py`: client interattivo per il router

## Topologia tipica

Shard:

```bash
python3 labs/kv_store/sharding_router/shard_node.py --shard-id S0 --port 6431
python3 labs/kv_store/sharding_router/shard_node.py --shard-id S1 --port 6432
```

Router:

```bash
python3 labs/kv_store/sharding_router/router.py --port 6430
```

## Comandi client

- `PING`
- `SET <key> <value...>`
- `GET <key>`
- `DELETE <key>`
- `EXISTS <key>`
- `INCR <key>`
- `KEYS`
- `WHERE <key>`
- `STATS`
- `QUIT`

## Semantica

- ogni chiave viene instradata a un solo shard tramite hashing stabile;
- `SET`, `GET`, `DELETE`, `EXISTS`, `INCR` toccano un solo shard;
- `KEYS` e `STATS` interrogano tutti gli shard.

## Esperimento 1: routing

1. eseguire `WHERE alpha`;
2. eseguire `WHERE beta`;
3. scrivere le due chiavi;
4. osservare da `STATS` che il carico si distribuisce sui due shard.

## Esperimento 2: hotspot

1. eseguire molti `INCR` sulla stessa chiave;
2. osservare `STATS`;
3. confrontare con scritture distribuite su chiavi diverse.

Anche con piu' shard, una chiave molto calda resta concentrata su una sola
partizione.

## Esperimento 3: costo di `KEYS`

1. popolare chiavi su piu' shard;
2. eseguire `KEYS`;
3. osservare che il router deve interrogare tutte le partizioni.

## Domande tecniche da discutere

- Quale parte del contratto dipende ora dal router?
- Perche' `GET` resta locale ma `KEYS` diventa globale?
- Cosa succede quando una partizione e' sovraccarica?
- Come cambierebbe il sistema se aggiungessimo un nuovo shard?
- Quale problema di migrazione dati resta aperto?
