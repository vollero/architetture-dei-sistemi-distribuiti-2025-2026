# Lab: REST Gateway per KV Store Distribuito

Questo laboratorio espone la capstone del KV store tramite una API REST.

Topologia:

```text
HTTP client -> REST gateway -> capstone router -> shard nodes
```

Il gateway non conserva dati. Traduce richieste HTTP in comandi testuali verso
il router della capstone.

## File

- `rest_gateway.py`: server HTTP REST.
- `acceptance_test.py`: test end-to-end con shard, router e gateway.

## Avvio manuale

Avviare due shard:

```bash
python3 labs/kv_store/capstone_exercise/shard_node.py --shard-id S0 --port 6461
python3 labs/kv_store/capstone_exercise/shard_node.py --shard-id S1 --port 6462
```

Avviare il router della capstone:

```bash
python3 labs/kv_store/capstone_exercise/router.py --port 6460
```

Avviare il gateway REST:

```bash
python3 labs/kv_store/rest_gateway/rest_gateway.py --port 6470 --router-port 6460
```

## Esempi HTTP

Creare o sostituire una chiave:

```bash
curl -X PUT http://127.0.0.1:6470/kv/course \
  -H 'Content-Type: application/json' \
  -d '{"value": "ads"}'
```

Leggere valore e versione:

```bash
curl http://127.0.0.1:6470/kv/course
```

Scrittura condizionale:

```bash
curl -X PATCH http://127.0.0.1:6470/kv/course \
  -H 'Content-Type: application/json' \
  -d '{"expected_version": 0, "value": "distributed-systems"}'
```

Aggiungere uno shard:

```bash
python3 labs/kv_store/capstone_exercise/shard_node.py --shard-id S2 --port 6463

curl -X POST http://127.0.0.1:6470/cluster/shards \
  -H 'Content-Type: application/json' \
  -d '{"id": "S2", "host": "127.0.0.1", "port": 6463}'
```

Eseguire rebalance:

```bash
curl -X POST http://127.0.0.1:6470/cluster/rebalance
```

## Test automatico

```bash
python3 labs/kv_store/rest_gateway/acceptance_test.py
```

Il test verifica:

- `PUT` e `GET`;
- idempotenza osservabile di `PUT` sullo stesso valore;
- `PATCH` con `CAS` riuscita;
- `PATCH` con versione stantia e `409 Conflict`;
- `DELETE`;
- aggiunta shard e `REBALANCE` via REST.

## Discussione

Il gateway rende pubblica una API REST, ma non aggiunge automaticamente ACID.

In particolare:

- `CAS` resta atomica sulla singola chiave nello shard;
- non ci sono transazioni multi-key;
- non c'e' durabilita' su disco;
- il rebalance resta un protocollo composto.

