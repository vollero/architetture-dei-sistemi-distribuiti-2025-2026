# Esercitazione: Rebalancing e CAS su un KV Store Evoluto

Questa esercitazione integra i due avanzamenti precedenti:

- sharding con topologia che cambia nel tempo;
- scritture condizionali basate su versione.

## Obiettivo

Progettare e implementare un KV store che:

- distribuisca le chiavi su piu' shard;
- supporti aggiunta di shard e migrazione;
- esponga `GETV` e `CAS`;
- conservi la coerenza delle versioni durante la migrazione.

La cartella contiene ora anche una soluzione di riferimento compatta. Non e'
pensata come sistema completo, ma come baseline tecnica da leggere, eseguire e
criticare.

## File

- `shard_node.py`: shard autonomo che conserva coppie `(value, version)`.
- `router.py`: router shardato con `GETV`, `CAS`, `ADD_SHARD` e `REBALANCE`.
- `client.py`: client interattivo verso il router.
- `acceptance_test.py`: test automatico end-to-end del contratto minimo.

## Punto didattico

L'interfaccia e' il centro dell'esercitazione.

Dovete decidere e difendere:

- che cosa significa la versione osservata da `GETV`;
- quando una `CAS` fallisce legittimamente;
- che cosa succede a una chiave durante `REBALANCE`;
- quale risposta osserva il client se il routing e la migrazione non sono ancora allineati.

## Deliverable richiesti

1. un documento breve di contratto dell'interfaccia;
2. un'implementazione funzionante;
3. almeno uno script di test o una procedura ripetibile di verifica;
4. una nota tecnica sui casi limite e sui trade-off.

## Interfaccia minima attesa

- `GET <key>`
- `GETV <key>`
- `SET <key> <value...>`
- `CAS <key> <expected_version> <value...>`
- `WHERE <key>`
- `ADD_SHARD <id> <host> <port>`
- `REBALANCE`

La soluzione di riferimento supporta anche:

- `PING`
- `STATUS`
- `KEYS`
- `PLAN <key>`
- `DELETE <key>`
- `QUIT`

## Contratto implementato dalla soluzione

La soluzione adotta scelte volutamente semplici e dichiarate:

- la versione e' locale alla chiave;
- una chiave assente ha versione implicita `-1`;
- `SET` su chiave assente produce `version=0`;
- `CAS key -1 value` crea la chiave solo se e' ancora assente;
- `DELETE` elimina valore e storia locale della chiave;
- `ADD_SHARD` rende subito visibile la nuova topologia;
- prima di `REBALANCE`, una chiave gia' esistente puo' risultare `NOT_FOUND`
  se il nuovo routing punta a uno shard dove non e' ancora stata migrata;
- `REBALANCE` blocca logicamente le operazioni del router, copia prima di
  cancellare e trasferisce sempre valore e versione insieme.

Quindi questa implementazione sceglie un contratto di migrazione semplice:

```text
cutover immediato della topologia + rebalance stop-the-world
```

Il vantaggio e' la leggibilita'. Il costo e' che la finestra tra `ADD_SHARD` e
`REBALANCE` resta osservabile dal client.

## Avvio manuale

Avviare due shard iniziali:

```bash
python3 labs/kv_store/capstone_exercise/shard_node.py --shard-id S0 --port 6461
python3 labs/kv_store/capstone_exercise/shard_node.py --shard-id S1 --port 6462
```

Avviare il router:

```bash
python3 labs/kv_store/capstone_exercise/router.py --port 6460
```

Avviare il client:

```bash
python3 labs/kv_store/capstone_exercise/client.py --port 6460
```

Quando serve il terzo shard:

```bash
python3 labs/kv_store/capstone_exercise/shard_node.py --shard-id S2 --port 6463
```

Dal client:

```text
ADD_SHARD S2 127.0.0.1 6463
REBALANCE
```

## Test automatico

Il test end-to-end avvia processi separati per shard e router, poi verifica:

- successo di `CAS`;
- fallimento di `CAS` con versione vecchia;
- cambio di routing dopo `ADD_SHARD`;
- `NOT_FOUND` nella finestra prima del rebalance;
- conservazione della versione dopo migrazione;
- `CAS` corretta dopo migrazione.

Esecuzione:

```bash
python3 labs/kv_store/capstone_exercise/acceptance_test.py
```

Esito atteso:

```text
acceptance test passed
```

## Vincoli minimi

- una migrazione non deve distruggere le versioni;
- dopo `REBALANCE`, `WHERE` e posizione reale dei dati devono tornare coerenti;
- una `CAS` con versione vecchia deve fallire;
- una `CAS` con versione corretta deve aggiornare valore e versione.

## Test di accettazione suggeriti

### Test 1: CAS base

1. `SET k v0`
2. `GETV k`
3. `CAS k current_version v1`
4. `GETV k`

### Test 2: conflitto

1. due client leggono la stessa versione;
2. il primo esegue `CAS`;
3. il secondo tenta `CAS` con versione vecchia.

### Test 3: migrazione

1. scrivere piu' chiavi su due shard;
2. aggiungere un terzo shard;
3. osservare `WHERE` prima e dopo `REBALANCE`;
4. verificare che `GETV` mantenga le versioni corrette dopo la migrazione.

### Test 4: CAS dopo migrazione

1. leggere `GETV` di una chiave;
2. aggiungere uno shard;
3. migrare la chiave;
4. eseguire `CAS` con la versione osservata;
5. verificare che il comportamento sia coerente con il contratto dichiarato.

## Domande da imporre al gruppo

- la versione e' globale o locale a una chiave?
- chi e' responsabile di mantenerla corretta durante `REBALANCE`?
- esiste una finestra in cui `WHERE` cambia ma il dato non e' ancora arrivato?
- come dovrebbe comportarsi il sistema in quella finestra?
- quali test difendono davvero il contratto?

## Strategie implementative da confrontare

### Router piu' ricco

- il router gestisce topologia, migrazione e inoltro delle operazioni versionate;
- gli shard custodiscono lo stato della chiave;
- il rebalance trasferisce valore e versione insieme.

Pregio:

- controllo centrale del flusso.

Costo:

- router piu' complesso e piu' delicato.

### Shard piu' autonomi

- `GETV` e `CAS` vengono gestiti direttamente dagli shard;
- il router si occupa soprattutto di scegliere dove inviare l'operazione;
- la migrazione deve preservare integralmente lo stato della chiave.

Pregio:

- migliore separazione delle responsabilita'.

Costo:

- protocollo di migrazione piu' importante.

## Pianificazione consigliata

Una timeline pragmatica per il lavoro potrebbe essere:

1. fissare il contratto di `GETV`, `CAS` e `REBALANCE`;
2. implementare il trasporto di `(value, version)` tra shard;
3. definire il comportamento di `CAS` durante la migrazione;
4. costruire test di successo, conflitto e post-migrazione;
5. scrivere una nota tecnica finale sui limiti residui.

## Problemi tipici

- perdere la versione durante lo spostamento;
- far passare una `CAS` usando una versione letta prima della migrazione senza averne deciso la semantica;
- far dire a `WHERE` piu' di quanto il sistema sappia davvero garantire;
- avere test che verificano solo il caso felice.
