# Lab: KV Store con Replica Primary-Secondary

Questa tappa aggiunge un secondo nodo.

Il problema centrale non e' piu' solo la durabilita' locale di un singolo
processo, ma il significato di una scrittura quando lo stato deve essere
propagato su piu' macchine.

## File

- `replica_secondary.py`: nodo secondario che riceve aggiornamenti dal primary
  e puo' servire letture
- `primary_async.py`: primary che acka il client prima dell'ack del secondario
- `primary_sync.py`: primary che acka il client solo dopo ack del secondario
- `client.py`: client interattivo per connettersi a primary o secondario

## Topologia del laboratorio

Default:

- primary async su `127.0.0.1:6390`
- secondario letture su `127.0.0.1:6391`
- canale interno di replica del secondario su `127.0.0.1:6491`
- primary sync su `127.0.0.1:6392`

## Comandi lato client

Sui primary:

- `PING`
- `SET <key> <value...>`
- `GET <key>`
- `DELETE <key>`
- `EXISTS <key>`
- `KEYS`
- `INCR <key>`
- `QUIT`

Sul secondario:

- `PING`
- `GET <key>`
- `EXISTS <key>`
- `KEYS`
- `QUIT`

Il secondario e' deliberatamente read-only per i client.

## Avvio rapido

Secondario:

```bash
python3 labs/kv_store/replication_primary_secondary/replica_secondary.py --apply-delay 1.0
```

Primary async:

```bash
python3 labs/kv_store/replication_primary_secondary/primary_async.py
```

Primary sync:

```bash
python3 labs/kv_store/replication_primary_secondary/primary_sync.py
```

Client su primary async:

```bash
python3 labs/kv_store/replication_primary_secondary/client.py --port 6390
```

Client su secondario:

```bash
python3 labs/kv_store/replication_primary_secondary/client.py --port 6391
```

Client su primary sync:

```bash
python3 labs/kv_store/replication_primary_secondary/client.py --port 6392
```

## Esperimento 1: lettura stantia su replica

1. avviare il secondario con `--apply-delay 1.0`;
2. avviare `primary_async.py`;
3. eseguire `SET course ads`;
4. leggere subito `GET course` dal secondario;
5. attendere un secondo e rileggere.

Aspettativa:

- il primary risponde `OK` subito;
- il secondario puo' inizialmente rispondere `NOT_FOUND`;
- dopo il delay la replica converge.

## Esperimento 2: semantica del commit

1. fermare il secondario;
2. usare `primary_async.py` e inviare `SET course ads`;
3. osservare che il primary puo' ancora rispondere `OK`;
4. usare `primary_sync.py` e ripetere la stessa operazione.

Aspettativa:

- il primary async accetta l'update locale anche senza replica;
- il primary sync rifiuta la scrittura con errore sulla replica.

## Domande tecniche da discutere

- Quando una scrittura puo' dirsi davvero committed?
- Che differenza c'e' tra "visibile sul primary" e "replicata"?
- E' legittimo leggere dal secondario subito dopo un `OK` del primary?
- Cosa compriamo con replica sincrona e cosa perdiamo in liveness?
- Quale rischio nasce se due nodi credono entrambi di essere primary?
