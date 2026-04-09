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
- `server_dispatch.py`: stessa interfaccia, implementata con dispatch table
- `client.py`: client interattivo semplice

## Avvio

Terminale 1:

```bash
python3 labs/kv_store/single_node/server.py
```

oppure:

```bash
python3 labs/kv_store/single_node/server_dispatch.py
```

Terminale 2:

```bash
python3 labs/kv_store/single_node/client.py
```

Nota: `client.py` usa di default la porta `6380`, quindi per provare
`server_dispatch.py` va cambiata la porta nel client oppure va usato un
client TCP generico come `nc 127.0.0.1 6381`.

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

## Nota didattica

`server.py` e `server_dispatch.py` espongono lo stesso contratto, ma usano
due strategie implementative diverse:

- catena di `if`;
- dizionario di dispatch comando -> handler.

Questo permette di discutere come l'interfaccia resti stabile mentre cambia
l'organizzazione interna del codice.
