# Contratto del Protocollo: KV Store v0

Questo documento descrive il contratto minimo del primo key-value store del percorso.

## Obiettivo

Definire un'interfaccia abbastanza stabile da poter essere mantenuta anche quando l'implementazione cambiera' radicalmente nelle lezioni successive.

L'idea e' importante: il client parla con un servizio, non con un dizionario Python.

## Trasporto

- Protocollo testuale su TCP.
- Encoding UTF-8.
- Ogni richiesta occupa una riga terminata da newline `\n`.
- Ogni risposta occupa una riga terminata da newline `\n`.

## Modello dati

- Chiavi: stringhe senza spazi.
- Valori: stringhe arbitrarie, eventualmente vuote.
- Il server v0 mantiene i dati solo in memoria.

## Comandi supportati

### `PING`

Richiesta:

```text
PING
```

Risposta:

```text
OK PONG
```

### `SET <key> <value...>`

Richiesta:

```text
SET corso asd
```

Risposta:

```text
OK
```

Semantica nel v0:

- al ritorno di `OK`, il valore e' stato memorizzato in RAM nel processo server;
- nessuna garanzia di persistenza;
- nessuna garanzia di replica;
- nessuna garanzia oltre il singolo processo.

### `GET <key>`

Richiesta:

```text
GET corso
```

Risposte possibili:

```text
OK asd
```

oppure

```text
NOT_FOUND
```

Scelta semantica:

- `NOT_FOUND` distingue chiaramente la chiave assente da un valore vuoto;
- l'assenza della chiave non e' un errore di protocollo, ma un esito applicativo.

### `DELETE <key>`

Richiesta:

```text
DELETE corso
```

Risposte possibili:

```text
OK
```

oppure

```text
NOT_FOUND
```

### `EXISTS <key>`

Richiesta:

```text
EXISTS corso
```

Risposte possibili:

```text
OK 1
```

oppure

```text
OK 0
```

### `KEYS`

Richiesta:

```text
KEYS
```

Risposta:

```text
OK corso docenti aula
```

Note:

- nel v0 le chiavi sono restituite in ordine lessicografico;
- in un sistema distribuito questa operazione divergera' facilmente in costo e semantica, quindi va presentata come operazione di supporto, non come primitiva innocua.

### `QUIT`

Richiesta:

```text
QUIT
```

Risposta:

```text
OK BYE
```

## Errori di protocollo

In caso di richiesta malformata, il server risponde con:

```text
ERR <messaggio>
```

Esempi:

```text
ERR unknown command
ERR usage: GET <key>
ERR usage: SET <key> <value>
```

## Garanzie del v0

Il sistema promette solo quanto segue:

- ogni connessione vede le proprie richieste elaborate in ordine;
- il singolo processo mantiene una mappa chiave-valore coerente;
- `GET` dopo `SET` sullo stesso nodo restituisce il valore scritto, se il processo non e' terminato nel frattempo.

## Non-garanzie del v0

Il sistema non promette:

- durabilita' dopo crash;
- gestione concorrente efficiente;
- repliche;
- tolleranza ai guasti;
- isolamento tra client;
- limiti di memoria;
- autenticazione;
- atomicita' multi-operazione.

## Domande per le prossime versioni

- Quando una scrittura puo' essere dichiarata committed?
- Come si distingue disponibilita' da correttezza?
- Cosa succede a `GET` durante un failover?
- `KEYS` deve esistere ancora in un cluster shardato?
- Il client deve conoscere topologia e repliche oppure no?
