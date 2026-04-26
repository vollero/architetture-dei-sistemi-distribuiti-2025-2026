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
