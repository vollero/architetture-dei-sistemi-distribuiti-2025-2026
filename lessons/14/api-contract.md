# Contratto del Protocollo: KV Store v5 con Quorum

Questa versione introduce un coordinator e un insieme di repliche numerate.

Il client continua a parlare con un solo endpoint, ma il significato di `SET`
e `GET` dipende da:

- `N`: numero totale di repliche;
- `W`: numero minimo di ack per una scrittura;
- `R`: numero minimo di risposte per una lettura.

## Trasporto

- Protocollo testuale su TCP tra client e coordinator.
- Protocollo JSON line-oriented tra coordinator e repliche.

## Comandi client

- `PING`
- `STATUS`
- `SET <key> <value...>`
- `GET <key>`
- `QUIT`

## Semantica

### `SET`

- il coordinator sceglie una nuova `version`;
- tenta di scrivere la coppia `(value, version)` sulle repliche;
- risponde `OK` solo se ottiene almeno `W` acknowledgement.

### `GET`

- il coordinator interroga almeno `R` repliche;
- tra le risposte osservate sceglie il valore con `version` massima.

## Garanzie dipendenti dalla configurazione

- con quorum deboli, una lettura puo' fermarsi troppo presto e non vedere la
  versione piu' recente;
- con quorum tali che `R + W > N`, una lettura e una scrittura di successo
  devono sovrapporsi su almeno una replica.

## Cosa non e' garantito

- nessuna gestione completa di write concorrenti da coordinator multipli;
- nessun vector clock;
- nessuna risoluzione automatica di conflitti complessi;
- nessuna replica geografica.

## Punto chiave della tappa

Il commit non e' piu' una proprietà di un singolo leader. Diventa il risultato
di una regola numerica di intersezione tra insiemi di repliche.
