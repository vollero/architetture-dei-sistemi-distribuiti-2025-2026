# Contratto del Protocollo: KV Store v1 Multithread

Questa versione mantiene il protocollo testuale del `v0`, ma lo esegue in
presenza di piu' client concorrenti.

## Trasporto

- Protocollo testuale su TCP.
- Encoding UTF-8.
- Una richiesta per riga.
- Una risposta per riga.
- Ogni connessione e' gestita da un thread dedicato.

## Modello dati

- Chiavi: stringhe senza spazi.
- Valori: stringhe UTF-8.
- Stato mantenuto in memoria in una struttura condivisa da piu' thread.

## Comandi supportati

- `PING`
- `SET <key> <value...>`
- `GET <key>`
- `DELETE <key>`
- `EXISTS <key>`
- `KEYS`
- `INCR <key>`
- `QUIT`

## Nuovo comando: `INCR <key>`

Richiesta:

```text
INCR counter
```

Risposte possibili:

```text
OK 1
```

oppure

```text
ERR value is not an integer
```

Semantica:

- se la chiave non esiste, il valore iniziale e' considerato `0`;
- il server incrementa il valore intero associato alla chiave;
- nella versione corretta, l'intera sequenza read-modify-write e' atomica.

## Garanzie della versione safe

- ogni connessione vede le proprie richieste in ordine;
- lo stato condiviso resta coerente anche in presenza di piu' thread;
- due `INCR` concorrenti sulla stessa chiave non perdono aggiornamenti;
- `GET`, `SET`, `DELETE`, `EXISTS`, `KEYS` osservano uno stato consistente
  rispetto alla disciplina di lock adottata.

## Cosa non e' garantito

- fairness tra thread;
- assenza di starvation in generale;
- throughput massimo;
- durabilita' dopo crash;
- replicazione o tolleranza ai guasti.

## Nota tecnica

Il punto fondamentale di questa tappa non e' la semantica di rete, ma il
fatto che il contratto del servizio dipende ora anche dal controllo di
concorrenza interno.
