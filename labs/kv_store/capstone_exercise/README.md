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
