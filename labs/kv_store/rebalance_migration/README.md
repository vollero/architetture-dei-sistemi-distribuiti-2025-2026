# Lab: KV Store con Rebalancing e Migrazione

Questa tappa evolve il router di sharding con una nuova capacita':

- la topologia cambia;
- il routing cambia;
- il dato deve essere migrato.

## File

- `shard_node.py`: shard con primitive di export/import locale
- `router.py`: router con `ADD_SHARD`, `PLAN` e `REBALANCE`
- `client.py`: client interattivo

## Topologia tipica

Shard iniziali:

```bash
python3 labs/kv_store/rebalance_migration/shard_node.py --shard-id S0 --port 6441
python3 labs/kv_store/rebalance_migration/shard_node.py --shard-id S1 --port 6442
```

Nuovo shard:

```bash
python3 labs/kv_store/rebalance_migration/shard_node.py --shard-id S2 --port 6443
```

Router:

```bash
python3 labs/kv_store/rebalance_migration/router.py --port 6440
```

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

## Esperimento 1: routing che cambia

1. avviare due shard e il router;
2. scrivere alcune chiavi;
3. osservare `WHERE alpha` e `WHERE gamma`;
4. aggiungere uno shard con `ADD_SHARD`;
5. ripetere `WHERE` sulle stesse chiavi.

Senza migrazione, il routing nuovo puo' non coincidere con la posizione reale
dei dati scritti prima.

## Esperimento 2: migrazione

1. dopo `ADD_SHARD`, eseguire `REBALANCE`;
2. rileggere le chiavi;
3. osservare che `WHERE` e posizione reale tornano coerenti.

## Domande tecniche da discutere

- il cambio di topologia quando diventa osservabile dal client?
- cosa succede tra il momento in cui cambia il routing e il momento in cui i
  dati sono stati migrati?
- il router puo' rispondere correttamente durante una migrazione parziale?
- come cambierebbe il problema con chiavi molto grandi o traffico concorrente?

## Discussione implementativa

La versione del lab e' volutamente minima:

- il router esegue `LIST_ITEMS` su ogni shard;
- ricalcola il target di ogni chiave;
- per ogni chiave da spostare fa `IMPORT_KEY` e poi `DELETE_LOCAL`.

Questo protocollo e' utile perche' e' leggibile, ma non e' una soluzione
generale.

### Pregi

- semplice da spiegare e debuggare;
- copia prima di cancellare;
- espone chiaramente la finestra di incoerenza.

### Limiti

- migrazione sequenziale;
- nessun batching;
- nessun metadata di stato della migrazione;
- nessuna gestione delle scritture concorrenti;
- nessun resume in caso di crash del router.

## Tempi e costi

In prima approssimazione, il costo del rebalance e' dato da:

- una scansione completa di tutti gli shard;
- due RPC per ogni chiave migrata.

Quindi il tempo cresce soprattutto con:

- numero di chiavi da migrare;
- dimensione media dei valori;
- latenza delle RPC;
- carico concorrente presente durante la migrazione.

## Soluzioni da confrontare

Per la discussione in aula conviene mettere a confronto almeno queste opzioni:

- `stop-the-world`: blocco temporaneo delle scritture durante la migrazione;
- `forwarding`: il vecchio shard o il router reindirizzano temporaneamente le letture;
- `dual mapping`: vecchia e nuova mappa valide insieme per una finestra;
- `copy + catch-up + cutover`: copia iniziale, recupero scritture concorrenti, commutazione finale.
