# Lab: KV Store Single Node

Questo laboratorio implementa la prima tappa del percorso sul key-value store distribuito.

Per ora il sistema e':

- locale;
- volatile;
- single-node;
- single-threaded;
- basato su TCP e protocollo testuale.

L'idea non e' fermarsi qui, ma usare questa base come contratto iniziale da mettere sotto pressione nelle prossime lezioni.

## File

- `server.py`: server key-value minimale
- `client.py`: client interattivo semplice

## Avvio

Terminale 1:

```bash
python3 labs/kv_store/single_node/server.py
```

Terminale 2:

```bash
python3 labs/kv_store/single_node/client.py
```

## Comandi supportati

- `PING`
- `SET <key> <value...>`
- `GET <key>`
- `DELETE <key>`
- `EXISTS <key>`
- `KEYS`
- `QUIT`

## Esempio di sessione

```text
kv> PING
OK PONG
kv> SET corso asd
OK
kv> GET corso
OK asd
kv> EXISTS corso
OK 1
kv> KEYS
OK corso
kv> DELETE corso
OK
kv> GET corso
NOT_FOUND
```

## Spunti di estensione immediata

- gestire client concorrenti;
- aggiungere persistenza su file;
- introdurre `TTL`;
- aggiungere `CAS key expected new_value`;
- separare parser, storage engine e rete in moduli distinti.
