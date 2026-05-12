# Contratto REST: KV Store Distribuito

Questa lezione espone il KV store distribuito attraverso un gateway HTTP.

Il gateway traduce richieste REST in comandi verso il router della capstone.

## Risorse

### Chiave

```text
/kv/{key}
```

Rappresenta il valore associato a una chiave.

### Collezione delle chiavi

```text
/kv
```

Rappresenta l'insieme osservabile delle chiavi.

### Posizione della chiave

```text
/kv/{key}/location
```

Rappresenta il target di routing corrente della chiave.

### Cluster

```text
/cluster/status
/cluster/shards
/cluster/rebalance
```

Rappresentano operazioni di osservazione e amministrazione della topologia.

## Endpoints

| Metodo | Path | Semantica |
| --- | --- | --- |
| `GET` | `/health` | verifica raggiungibilita' del router |
| `GET` | `/kv` | lista chiavi |
| `GET` | `/kv/{key}` | legge valore e versione |
| `PUT` | `/kv/{key}` | crea o sostituisce il valore |
| `PATCH` | `/kv/{key}` | `CAS` tramite versione attesa |
| `DELETE` | `/kv/{key}` | elimina la chiave |
| `GET` | `/kv/{key}/location` | mostra il target di routing |
| `GET` | `/cluster/status` | mostra gli shard noti al router |
| `POST` | `/cluster/shards` | aggiunge uno shard |
| `POST` | `/cluster/rebalance` | avvia il rebalance |

## Rappresentazioni JSON

### PUT

```json
{
  "value": "distributed-systems"
}
```

### PATCH con CAS

```json
{
  "expected_version": 3,
  "value": "new-value"
}
```

### Aggiunta shard

```json
{
  "id": "S2",
  "host": "127.0.0.1",
  "port": 6463
}
```

## Codici di stato

| Codice | Uso |
| --- | --- |
| `200 OK` | lettura o update riuscito |
| `201 Created` | risorsa creata o shard aggiunto |
| `202 Accepted` | rebalance avviato e completato dal router didattico |
| `204 No Content` | delete riuscita senza body |
| `400 Bad Request` | JSON non valido o parametri mancanti |
| `404 Not Found` | chiave assente o endpoint inesistente |
| `409 Conflict` | `CAS` fallita per `version_mismatch` |
| `502 Bad Gateway` | router o shard sottostante non raggiungibile |

## Safety, idempotenza, cacheability

### Safe

Un metodo safe non dovrebbe modificare lo stato del sistema.

Nel lab:

- `GET /kv/{key}` e' safe rispetto al valore;
- `GET /cluster/status` e' safe;
- `GET /kv/{key}/location` e' safe.

Attenzione: anche richieste safe possono produrre log o metriche.

### Idempotente

Un metodo idempotente puo' essere ripetuto piu' volte ottenendo lo stesso stato
finale della risorsa.

Nel lab:

- `PUT /kv/{key}` e' trattato come sostituzione del valore;
- `DELETE /kv/{key}` e' idempotente rispetto allo stato finale;
- `PATCH /kv/{key}` con CAS non e' idempotente in senso generale, perche' la
  versione attesa cambia dopo il successo.

Il gateway prova a evitare incrementi inutili di versione su `PUT` ripetuti con
lo stesso valore, ma questa non e' una transazione distribuita forte.

### Cacheability

`GET` potrebbe essere cacheabile solo se il contratto definisce:

- validita' temporale;
- invalidazione;
- relazione tra cache e versioni.

Nel lab non abilitiamo cache HTTP perche' il valore puo' cambiare rapidamente e
il router puo' cambiare topologia.

## ACID nel contesto del KV store

### Atomicity

Una singola operazione deve riuscire completamente o non avere effetto visibile.

Nel lab:

- `CAS` e' atomica sullo shard che possiede la chiave;
- `REBALANCE` e' un protocollo composto e non va confuso con una transazione ACID globale.

### Consistency

Ogni operazione deve preservare invarianti dichiarati.

Esempi:

- la versione cresce monotonicamente per chiave;
- una `CAS` con versione stantia fallisce;
- dopo `REBALANCE`, routing e posizione reale devono tornare coerenti.

### Isolation

Operazioni concorrenti non devono osservare stati intermedi non previsti dal
contratto.

Nel lab:

- `CAS` aiuta a gestire concorrenza sulla singola chiave;
- non c'e' isolamento transazionale multi-key;
- durante finestre di migrazione il contratto deve dichiarare cosa e' osservabile.

### Durability

Una scrittura confermata deve sopravvivere ai guasti previsti dal contratto.

Nel gateway REST della capstone:

- la durabilita' su disco non e' garantita;
- il valore resta in memoria degli shard;
- per avere durability servirebbe integrare WAL, snapshot o replica persistente.

## Punto chiave

REST non rende automaticamente il sistema piu' corretto.

REST rende pubblico un contratto.

ACID non e' un'etichetta da applicare all'intero sistema senza distinguere:

- singola chiave;
- singolo nodo;
- replica;
- migrazione;
- transazione multi-key;
- crash recovery.

