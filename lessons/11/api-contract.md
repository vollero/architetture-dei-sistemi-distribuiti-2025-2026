# Contratto del Protocollo: KV Store v2 con Persistenza Locale

Questa versione mantiene il protocollo testuale delle tappe precedenti, ma
introduce uno stato persistente locale e la possibilita' di recovery dopo
crash.

## Trasporto

- Protocollo testuale su TCP.
- Encoding UTF-8.
- Una richiesta per riga.
- Una risposta per riga.
- Ogni connessione e' gestita da un thread dedicato.

## Modello dati

- Chiavi: stringhe senza spazi.
- Valori: stringhe UTF-8.
- Stato attivo mantenuto in RAM.
- Stato persistente mantenuto su file locali.

## Comandi supportati

- `PING`
- `SET <key> <value...>`
- `GET <key>`
- `DELETE <key>`
- `EXISTS <key>`
- `KEYS`
- `INCR <key>`
- `SYNC`
- `CRASH`
- `QUIT`

## Semantica dei comandi applicativi

Le operazioni applicative mantengono la semantica gia' vista:

- `SET` crea o sovrascrive il valore di una chiave;
- `GET` restituisce `NOT_FOUND` se la chiave non esiste;
- `DELETE` rimuove la chiave se presente;
- `EXISTS` restituisce `OK 1` oppure `OK 0`;
- `KEYS` restituisce l'elenco delle chiavi;
- `INCR` incrementa un intero, assumendo `0` se la chiave non esiste.

## Comando di laboratorio: `SYNC`

Richiesta:

```text
SYNC
```

Risposte possibili:

```text
OK SNAPSHOT_SAVED
OK SNAPSHOT_ALREADY_CLEAN
OK ALREADY_DURABLE
```

Uso:

- nella variante snapshot, forza una persistenza immediata;
- nella variante write-ahead log, esplicita che le scritture ackate sono gia'
  state sincronizzate su disco.

## Comando di laboratorio: `CRASH`

Richiesta:

```text
CRASH
```

Effetto:

- il processo termina senza shutdown pulito;
- il client osserva la chiusura improvvisa della connessione;
- serve a simulare un crash di processo in un punto controllabile
  dell'esperimento.

## Garanzie della variante safe

- ogni scrittura ackata e' presente nel log persistente locale;
- al riavvio, il replay del log ricostruisce almeno tutte le scritture ackate;
- `INCR` resta atomico rispetto agli altri thread;
- il contratto osservabile dal client include durabilita' locale dopo crash
  di processo.

## Cosa non e' garantito

- nessuna replica su altre macchine;
- nessuna tolleranza a perdita completa del disco locale;
- nessuna fairness tra thread;
- nessuna latenza massima su `fsync`;
- nessuna compattazione del log.

## Punto chiave della tappa

Il contratto non riguarda piu' solo "quale valore vedo subito", ma anche
"quale stato posso ricostruire dopo un crash". Questa e' una proprieta'
distinta e piu' forte rispetto alla sola coerenza in RAM.
