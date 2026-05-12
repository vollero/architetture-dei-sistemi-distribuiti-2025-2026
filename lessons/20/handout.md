# Handout: REST, ACID e KV Store Distribuito

## Perche' introdurre REST

Finora il KV store e' stato esposto tramite protocolli testuali su TCP.

Questo e' utile per capire i meccanismi, ma un servizio reale viene spesso
esposto tramite HTTP.

REST ci obbliga a fare un passaggio concettuale:

- da comandi a risorse;
- da stringhe di risposta a rappresentazioni;
- da errori generici a codici di stato;
- da chiamate ad-hoc a un contratto pubblico leggibile.

## REST in una frase

REST non e' "usare JSON su HTTP".

REST e' uno stile architetturale in cui:

- il sistema espone risorse;
- ogni risorsa ha una rappresentazione;
- il client manipola risorse tramite un'interfaccia uniforme;
- le richieste sono stateless;
- i metodi hanno semantiche note.

## Risorse del nostro KV store

Nel lab useremo queste risorse:

```text
/kv
/kv/{key}
/kv/{key}/location
/cluster/status
/cluster/shards
/cluster/rebalance
```

La scelta e' importante.

Non stiamo solo rinominando comandi:

```text
GET key
SET key value
CAS key version value
```

Stiamo decidendo cosa il client vede come risorsa stabile.

## Mapping tra comandi e REST

| Protocollo testuale | REST |
| --- | --- |
| `GETV key` | `GET /kv/{key}` |
| `SET key value` | `PUT /kv/{key}` |
| `CAS key version value` | `PATCH /kv/{key}` |
| `DELETE key` | `DELETE /kv/{key}` |
| `WHERE key` | `GET /kv/{key}/location` |
| `ADD_SHARD ...` | `POST /cluster/shards` |
| `REBALANCE` | `POST /cluster/rebalance` |

Questo mapping non e' automatico.
Ogni riga va difesa semanticamente.

## Metodi HTTP e semantica

### GET

`GET` legge una rappresentazione.

Dovrebbe essere safe:

```text
GET /kv/course
```

non dovrebbe cambiare il valore di `course`.

### PUT

`PUT` sostituisce la rappresentazione della risorsa.

```text
PUT /kv/course
{"value": "ads"}
```

In REST, `PUT` e' idempotente rispetto allo stato finale.
Ripetere la stessa richiesta dovrebbe lasciare la risorsa nello stesso stato.

### PATCH

`PATCH` applica una modifica parziale o condizionale.

Nel nostro caso:

```text
PATCH /kv/course
{"expected_version": 3, "value": "distributed-systems"}
```

e' una forma REST di `CAS`.

### DELETE

`DELETE` elimina la risorsa.

Ripetere `DELETE` puo' restituire `404`, ma lo stato finale resta lo stesso:
la chiave non esiste.

### POST

`POST` viene usato per operazioni che creano sotto-risorse o attivano procedure.

Nel lab:

```text
POST /cluster/shards
POST /cluster/rebalance
```

## Codici di stato come parte del contratto

Una API REST non dovrebbe rispondere sempre `200 OK`.

Esempi:

- `404 Not Found`: chiave assente;
- `409 Conflict`: `CAS` fallita per versione stantia;
- `400 Bad Request`: JSON non valido;
- `502 Bad Gateway`: router sottostante non raggiungibile;
- `202 Accepted`: procedura di rebalance accettata.

Il codice di stato non e' decorazione.
E' parte del contratto.

## REST sopra un sistema distribuito

Il gateway REST del lab non contiene direttamente i dati.

Fa da adattatore:

```text
HTTP client -> REST gateway -> capstone router -> shard
```

Questo crea una distinzione importante:

- il gateway espone risorse HTTP;
- il router decide dove si trova la chiave;
- lo shard conserva valore e versione;
- il contratto REST deve riflettere i limiti del sistema sottostante.

## Dove entrano le logiche ACID

ACID nasce per discutere transazioni.

Nel nostro KV store va usato con precisione:

- ACID per una singola operazione su una chiave;
- ACID per una sequenza di operazioni;
- ACID durante migrazione;
- ACID con replica e crash.

Sono quattro problemi diversi.

## Atomicity

Atomicity significa:

```text
tutto o niente
```

Nel KV store:

- `CAS` sulla singola chiave deve essere atomica;
- `SET` deve aggiornare valore e versione insieme;
- `REBALANCE` e' composto da piu' azioni e non e' automaticamente atomico.

Domanda per la classe:

```text
se IMPORT_KEY riesce e DELETE_LOCAL fallisce, cosa ha osservato il sistema?
```

## Consistency

Consistency significa preservare invarianti.

Esempi di invarianti:

- una versione non diminuisce;
- una `CAS` con versione vecchia fallisce;
- dopo `REBALANCE`, `WHERE` e posizione reale tornano coerenti;
- una risposta `200` con `version` deve riferirsi al valore restituito.

Nel nostro percorso, "consistenza" non e' una parola unica.
Va sempre collegata a un invariante preciso.

## Isolation

Isolation riguarda cosa vedono operazioni concorrenti.

Nel gateway REST:

- due `PATCH` concorrenti con stessa versione non devono riuscire entrambe;
- `PUT` e `PATCH` concorrenti possono produrre storie diverse;
- operazioni multi-key non hanno isolamento transazionale;
- durante `REBALANCE` bisogna dichiarare quali stati intermedi sono visibili.

Il `CAS` e' una forma leggera di controllo di concorrenza.
Non e' una transazione generale.

## Durability

Durability significa:

```text
se ho confermato una scrittura, questa sopravvive ai guasti previsti
```

La capstone e il gateway REST lavorano in memoria.

Quindi il contratto corretto e':

- valore mantenuto finche' shard e router restano attivi;
- nessuna promessa di recovery dopo crash di processo;
- nessuna garanzia di WAL o snapshot.

Per avere durability servirebbe integrare la lezione sulla persistenza locale.

## ACID e distribuzione

In ambiente distribuito, ACID ha costi importanti:

- atomicita' multi-nodo richiede coordinamento;
- consistenza richiede invarianti globali;
- isolamento forte riduce parallelismo;
- durabilita' richiede storage stabile e spesso replica;
- transazioni distribuite richiedono protocolli come 2PC o consenso.

Questo e' il punto didattico:

> esporre una API REST e dichiarare ACID non basta. Bisogna spiegare il livello
> a cui quelle proprieta' valgono.

## Esempio progressivo

### Lettura

```bash
curl http://127.0.0.1:6470/kv/course
```

Possibili risposte:

```json
{"key": "course", "value": "ads", "version": 0, "shard": "S1"}
```

oppure:

```json
{"error": "not_found"}
```

con `404`.

### Scrittura condizionale

```bash
curl -X PATCH http://127.0.0.1:6470/kv/course \
  -H 'Content-Type: application/json' \
  -d '{"expected_version": 0, "value": "distributed-systems"}'
```

Se la versione e' corretta:

```text
200 OK
```

Se e' vecchia:

```text
409 Conflict
```

## Messaggio finale

REST definisce come il client vede il sistema.

ACID definisce quali proprieta' promettiamo sulle operazioni.

Il lavoro progettuale sta nel far combaciare:

- risorse esposte;
- metodi HTTP;
- codici di stato;
- meccanismi distribuiti sottostanti;
- proprieta' realmente garantite.

