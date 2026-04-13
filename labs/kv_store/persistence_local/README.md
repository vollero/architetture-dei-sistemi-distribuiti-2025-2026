# Lab: KV Store con Persistenza Locale

Questa tappa aggiunge durabilita' locale al key-value store.

L'interfaccia verso il client resta quasi invariata, ma cambia il significato
operativo di una risposta positiva:

- nella variante `unsafe`, `OK` significa solo "stato aggiornato in RAM";
- nella variante `safe`, `OK` significa "intento scritto su log e forzato su
  disco".

## File

- `server_persistent_unsafe.py`: aggiorna prima la RAM e persiste tramite
  snapshot periodici in background
- `server_persistent.py`: usa write-ahead log append-only con `fsync` prima
  dell'ack
- `client.py`: client interattivo per entrambe le varianti

## Comandi

Comandi applicativi:

- `PING`
- `SET <key> <value...>`
- `GET <key>`
- `DELETE <key>`
- `EXISTS <key>`
- `KEYS`
- `INCR <key>`
- `QUIT`

Comandi di laboratorio:

- `SYNC`: forza la persistenza immediata
- `CRASH`: termina il processo senza shutdown pulito

## Avvio rapido

Variante unsafe:

```bash
python3 labs/kv_store/persistence_local/server_persistent_unsafe.py
```

Variante safe:

```bash
python3 labs/kv_store/persistence_local/server_persistent.py
```

Client:

```bash
python3 labs/kv_store/persistence_local/client.py --port 6384
python3 labs/kv_store/persistence_local/client.py --port 6385
```

## Esperimento 1: ack in RAM contro ack durable

Variante unsafe:

1. avviare `server_persistent_unsafe.py`;
2. eseguire `SET course distributed-systems`;
3. eseguire subito `CRASH`;
4. riavviare il server sulla stessa directory dati;
5. eseguire `GET course`.

Se il crash arriva prima dello snapshot, la scrittura puo' risultare persa
nonostante il client abbia ricevuto `OK`.

Variante safe:

1. avviare `server_persistent.py`;
2. eseguire `SET course distributed-systems`;
3. eseguire `CRASH`;
4. riavviare il server sulla stessa directory dati;
5. eseguire `GET course`.

Qui la scrittura deve risultare presente, perche' l'ack arriva solo dopo
append e `fsync` del record nel log.

## Esperimento 2: `SYNC`

Sulla variante unsafe:

- `SYNC` forza uno snapshot immediato;
- dopo `SYNC`, un crash successivo non deve perdere gli aggiornamenti gia'
  inclusi nello snapshot.

Sulla variante safe:

- `SYNC` non cambia la semantica delle scritture gia' ackate;
- serve solo a rendere esplicito che il log e' gia' durable.

## Domande da discutere

- In quale punto una `SET` puo' essere detta davvero completata?
- Quale struttura e' autorevole: RAM o disco?
- Cosa succede se il crash avviene tra persistenza su disco e update in RAM?
- Come cambia la liveness se tratteniamo il lock durante `fsync`?
- Che differenza c'e' tra snapshot periodico e write-ahead log?
