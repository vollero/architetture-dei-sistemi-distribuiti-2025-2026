# Scenari di Discussione: REST e ACID nel KV Store

## Scenario 1: `PUT` ripetuta

Un client invia due volte:

```http
PUT /kv/course
{"value": "ads"}
```

Domande:

- `PUT` dovrebbe essere idempotente?
- se la versione aumenta due volte, la richiesta e' davvero idempotente?
- la versione fa parte dello stato osservabile della risorsa?
- il gateway dovrebbe evitare update inutili quando il valore e' identico?

Hint:

L'idempotenza va definita rispetto allo stato della risorsa osservabile. Se la
versione e' esposta al client, anche la versione conta.

## Scenario 2: `CAS` via `PATCH`

Due client leggono:

```text
GET /kv/x -> version=4
```

Poi entrambi inviano:

```http
PATCH /kv/x
{"expected_version": 4, "value": "..."}
```

Domande:

- quale risposta deve ricevere il primo?
- quale risposta deve ricevere il secondo?
- perche' `409 Conflict` e' piu' adatto di `500 Internal Server Error`?
- quale proprieta' ACID stiamo cercando di difendere?

Hint:

`version_mismatch` e' un conflitto applicativo previsto dal contratto, non un
errore interno del server.

## Scenario 3: `REBALANCE` come risorsa REST

Un client invia:

```http
POST /cluster/rebalance
```

Domande:

- `REBALANCE` e' una risorsa o un comando?
- perche' usiamo `POST` e non `PUT`?
- la risposta dovrebbe essere `200`, `202` o `204`?
- cosa succede se il rebalance richiede molto tempo?

Hint:

Nel lab il rebalance e' sincrono ma lo esponiamo come procedura amministrativa.
In un sistema reale potrebbe diventare un job con risorsa propria:

```text
/cluster/rebalance-jobs/{id}
```

## Scenario 4: ACID su una chiave o su piu' chiavi

Un client vuole trasferire valore da `a` a `b`:

```text
GET a
GET b
PUT a
PUT b
```

Domande:

- il gateway REST garantisce atomicita' dell'intera sequenza?
- cosa succede se il processo cade dopo `PUT a` e prima di `PUT b`?
- quale protocollo servirebbe per rendere l'operazione atomica su due chiavi?

Hint:

ACID su una singola operazione non implica ACID su una sequenza.
Per transazioni multi-key servono log, lock, 2PC, consenso o un transaction manager.

## Scenario 5: Durability dichiarata male

La documentazione dice:

```text
PUT /kv/key e' durable
```

ma gli shard salvano solo in memoria.

Domande:

- quale parte del contratto e' falsa?
- quali guasti non sono coperti?
- cosa servirebbe aggiungere per rendere vera la promessa?

Hint:

Durability richiede storage stabile o replica con recovery. Una risposta HTTP
`200 OK` non rende durable una scrittura.

