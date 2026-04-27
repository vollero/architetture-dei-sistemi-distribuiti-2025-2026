# Contratto del Protocollo: KV Store v7 con Rebalancing

Questa versione estende il router shardato con comandi che cambiano la
topologia osservabile del cluster.

## Trasporto

- Protocollo testuale su TCP tra client e router.
- Protocollo JSON line-oriented tra router e shard.

## Comandi client

- `PING`
- `STATUS`
- `SET <key> <value...>`
- `GET <key>`
- `DELETE <key>`
- `KEYS`
- `WHERE <key>`
- `ADD_SHARD <id> <host> <port>`
- `PLAN <key>`
- `REBALANCE`
- `QUIT`

## Semantica nuova

### `ADD_SHARD`

- estende l'insieme degli shard attivi nel router;
- cambia la funzione di destinazione per alcune chiavi.

### `PLAN <key>`

- restituisce lo shard target secondo la topologia corrente del router.

### `REBALANCE`

- osserva le chiavi attualmente presenti negli shard;
- sposta ogni chiave verso lo shard che dovrebbe ospitarla nella topologia
  corrente;
- ripristina coerenza tra routing e posizione reale del dato.

## Punto chiave della tappa

Subito dopo `ADD_SHARD`, il router puo' sapere che una chiave \textit{dovrebbe}
stare altrove anche se il dato non e' ancora stato spostato. Quindi il
contratto del sistema deve esplicitare se:

- il routing nuovo diventa immediatamente vincolante;
- oppure esiste una finestra di migrazione.

## Semantiche possibili durante migrazione

La lezione discute almeno quattro famiglie di contratto:

### 1. Cutover immediato

- il router usa subito la nuova topologia;
- fino a `REBALANCE` completato, alcune `GET` possono restituire `NOT_FOUND`
  anche per chiavi esistenti.

Pregio:

- implementazione semplice.

Costo:

- continuita' semantica debole.

### 2. Freeze temporaneo

- durante la migrazione alcune operazioni vengono rifiutate o sospese;
- il nuovo routing diventa visibile solo a riallineamento completato.

Pregio:

- comportamento piu' pulito.

Costo:

- disponibilita' ridotta.

### 3. Forwarding o doppia consultazione

- il router o lo shard sorgente sanno ancora dove cercare la chiave durante il transitorio;
- una lettura puo' essere servita dal vecchio shard anche se il target teorico e' gia' cambiato.

Pregio:

- meno `NOT_FOUND` spurii.

Costo:

- metadata e protocollo piu' complessi.

### 4. Copy, catch-up, cutover

- si copia il bulk dei dati;
- si catturano le scritture concorrenti;
- il nuovo routing diventa autorevole solo al termine del cutover.

Pregio:

- semantica piu' forte.

Costo:

- maggiore complessita' implementativa.
