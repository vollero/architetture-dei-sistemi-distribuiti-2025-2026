# Contratto del Protocollo: KV Store v3 con Replica Primary-Secondary

Questa versione mantiene il protocollo testuale delle tappe precedenti, ma
introduce due ruoli distinti:

- un nodo `primary`, che accetta le scritture dei client;
- un nodo `secondary`, che riceve aggiornamenti dal primary e puo' servire
  letture.

## Trasporto

- Protocollo testuale su TCP per i client.
- Protocollo JSON line-oriented sul canale interno di replica.
- Ogni connessione e' gestita da un thread dedicato.

## Ruoli

### Primary

Accetta:

- `PING`
- `SET <key> <value...>`
- `GET <key>`
- `DELETE <key>`
- `EXISTS <key>`
- `KEYS`
- `INCR <key>`
- `QUIT`

### Secondary

Espone ai client solo:

- `PING`
- `GET <key>`
- `EXISTS <key>`
- `KEYS`
- `QUIT`

Le scritture dirette sul secondario sono rifiutate.

## Semantica dei due primary

### Variante async

- il primary aggiorna prima il proprio stato locale;
- risponde `OK` al client;
- tenta poi la replica verso il secondario.

Conseguenze:

- il primary puo' rispondere `OK` anche se il secondario e' in ritardo;
- una lettura immediata dal secondario puo' essere stantia;
- se il secondario e' irraggiungibile, il primary puo' ancora accettare la
  scrittura locale.

### Variante sync

- il primary invia il record al secondario;
- attende `ACK`;
- solo dopo aggiorna localmente e risponde `OK`.

Conseguenze:

- `OK` implica che l'update e' presente su almeno due nodi;
- se il secondario non risponde, la scrittura fallisce;
- la latenza della scrittura include il tempo di replica.

## Letture

- `GET` sul primary osserva lo stato locale del primary;
- `GET` sul secondario osserva lo stato gia' replicato sul secondario.

Non esiste garanzia che una lettura immediata dal secondario rifletta l'ultimo
`OK` visto sul primary async.

## Cosa non e' garantito

- nessuna leader election;
- nessun quorum;
- nessuna gestione di split brain;
- nessuna replica multi-secondary;
- nessuna riconciliazione automatica dopo partizione.

## Punto chiave della tappa

La stessa API `SET` puo' avere semantiche diverse a seconda del protocollo di
commit scelto tra primary e secondary. Il contratto verso il client non e'
quindi definito solo dal codice locale del primary, ma anche dal rapporto tra
i nodi.
