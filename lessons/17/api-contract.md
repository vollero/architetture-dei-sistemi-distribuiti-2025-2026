# Contratto del Protocollo: KV Store v8 con Versioni e CAS

Questa versione espone esplicitamente la nozione di versione di una chiave.

## Trasporto

- Protocollo testuale su TCP.
- Una richiesta per riga.
- Una risposta per riga.

## Comandi

- `PING`
- `GET <key>`
- `GETV <key>`
- `SET <key> <value...>`
- `CAS <key> <expected_version> <value...>`
- `DELETE <key>`
- `QUIT`

## Semantica

### `GETV`

- restituisce valore e versione corrente della chiave;
- espone al client lo stato osservato su cui puo' basare una decisione.

### `SET`

- aggiorna il valore senza vincolare l'operazione a una versione attesa;
- produce una nuova versione.

### `CAS`

- aggiorna il valore solo se la versione corrente coincide con
  `expected_version`;
- se la versione non coincide, fallisce con `ERR version_mismatch current=<v>`.

## Punto chiave della tappa

La versione non e' piu' solo un dettaglio di implementazione. Diventa parte
del contratto osservabile tra client e server, perche' influenza la legittimita'
di una scrittura.
