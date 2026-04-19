# Contratto del Protocollo: KV Store v6 con Sharding

Questa versione mantiene un singolo endpoint client, ma lo stato non e' piu'
replicato integralmente su tutti i nodi. Il key space e' partizionato.

## Trasporto

- Protocollo testuale su TCP tra client e router.
- Protocollo JSON line-oriented tra router e shard.

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

- il router applica una funzione di hashing stabile sulla chiave;
- ogni chiave viene inviata a un solo shard;
- `GET`, `SET`, `DELETE`, `EXISTS`, `INCR` toccano una sola partizione;
- `KEYS` e `STATS` interrogano tutte le partizioni.

## Garanzie

- una chiave ha un solo shard di appartenenza nella configurazione corrente;
- `WHERE <key>` rende osservabile la decisione di routing;
- `STATS` permette di osservare distribuzione delle chiavi e del carico.

## Cosa non e' garantito

- nessun rebalancing automatico;
- nessuna migrazione online di chiavi;
- nessuna protezione contro hotspot;
- nessuna operazione transazionale multi-shard.

## Punto chiave della tappa

L'interfaccia del client sembra ancora uniforme, ma il costo e il percorso di
una richiesta dipendono ora dal partizionamento. Alcune operazioni restano
locali, altre diventano inevitabilmente globali.
