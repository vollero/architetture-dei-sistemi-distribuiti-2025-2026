# Lab: KV Store con Versioni e Compare-And-Set

Questa tappa introduce un avanzamento importante dell'interfaccia:

- il client non scrive piu' solo "alla cieca";
- puo' osservare una versione;
- puo' scrivere solo se la versione osservata e' ancora valida.

## File

- `server.py`: store versionato con `GETV` e `CAS`
- `client.py`: client interattivo

## Comandi

- `PING`
- `GET <key>`
- `GETV <key>`
- `SET <key> <value...>`
- `CAS <key> <expected_version> <value...>`
- `DELETE <key>`
- `QUIT`

## Semantica

- `SET` crea o aggiorna una chiave e incrementa la versione;
- `GETV` restituisce valore e versione osservata;
- `CAS` riesce solo se la versione corrente coincide con quella attesa.

## Esperimento 1: aggiornamento condizionale riuscito

1. eseguire `SET course ads`;
2. eseguire `GETV course`;
3. usare la versione restituita in `CAS course <versione> advanced-distributed-systems`.

## Esperimento 2: conflitto

1. aprire due client;
2. leggere `GETV` su entrambi;
3. completare `CAS` dal primo;
4. ripetere `CAS` dal secondo con la vecchia versione.

Aspettativa:

- il primo update riesce;
- il secondo riceve `ERR version_mismatch`.

## Domande tecniche da discutere

- qual e' la differenza semantica tra `SET` e `CAS`?
- una versione e' parte dell'interfaccia o solo un dettaglio interno?
- che cosa promette davvero un `ERR version_mismatch`?
- come si trasporterebbe questa semantica in uno store replicato o shardato?
