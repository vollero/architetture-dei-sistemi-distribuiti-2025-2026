# Guida Operativa: Laboratorio Vector Clock e KV Store

## File disponibili

Il laboratorio si trova in:

```text
labs/kv_store/vector_clock_replication/
```

File principali:

| File | Ruolo |
| --- | --- |
| `README.md` | traccia rapida del laboratorio e percorso da un'ora |
| `vector_clock.py` | primitive di confronto, merge, incremento e serializzazione dei clock |
| `node.py` | replica KV multi-master con protocollo client e protocollo interno JSON |
| `client.py` | client interattivo per inviare comandi a una replica |
| `demo_vector_clock_kv.py` | demo automatizzata con tre repliche locali |

## Ruoli concettuali

### Replica

Una replica è un nodo del KV store. Nel laboratorio usiamo:

```text
A, B, C
```

Ogni replica:

- accetta comandi client;
- mantiene stato locale;
- produce aggiornamenti incrementando la propria componente del clock;
- sincronizza lo stato con altre repliche tramite `SYNC`.

### Client

Il client invia comandi a una replica specifica.

Il client non vede una memoria globale atomica: vede il contratto offerto dalla
replica a cui è collegato.

### Versione

Una versione è una possibile rappresentazione del valore di una chiave.

Nel codice:

```text
Version(value, clock, origin, deleted)
```

Campi:

- `value`: valore applicativo;
- `clock`: version vector della chiave;
- `origin`: replica che ha creato quella versione;
- `deleted`: indica se la versione è una tombstone.

### Sibling

Un sibling è una versione concorrente della stessa chiave.

Due siblings non sono ordinabili causalmente. Il sistema li conserva entrambi
fino a una risoluzione esplicita.

### Operatore o applicazione

Chi invia `RESOLVE` interpreta il conflitto e sceglie un nuovo valore.

Questo ruolo è intenzionale: un conflitto non è solo un dettaglio tecnico, ma
una domanda sul significato applicativo dei dati.

## Ruoli per lavoro in classe

Per una demo partecipata si possono assegnare questi ruoli agli studenti:

| Ruolo | Responsabilità |
| --- | --- |
| Driver A | gestisce il terminale della replica `A` |
| Driver B | gestisce il terminale della replica `B` |
| Driver C | gestisce il terminale della replica `C` |
| Osservatore dei clock | annota i clock prodotti da `SET`, `SYNC` e `RESOLVE` |
| Verificatore del contratto | controlla se il comportamento osservato rispetta le promesse dell'interfaccia |
| Analista safety/liveness | identifica cosa non deve mai accadere e cosa deve prima o poi accadere |

In gruppi piccoli, una persona può coprire più ruoli.

## Modalità di esecuzione rapida

Dalla radice del repository:

```bash
python3 labs/kv_store/vector_clock_replication/demo_vector_clock_kv.py
```

La demo:

1. avvia tre repliche locali;
2. scrive una chiave su `A`;
3. mostra che `B` non la vede prima della sincronizzazione;
4. sincronizza `A` e `B`;
5. produce due scritture concorrenti su `room`;
6. mostra il conflitto;
7. rifiuta `SET` in presenza di siblings;
8. risolve con `RESOLVE`;
9. propaga la versione risolta fino a `C`.

## Modalità manuale

Aprire tre terminali per le repliche.

Replica A:

```bash
python3 labs/kv_store/vector_clock_replication/node.py \
  --node-id A \
  --port 6481 \
  --members A,B,C
```

Replica B:

```bash
python3 labs/kv_store/vector_clock_replication/node.py \
  --node-id B \
  --port 6482 \
  --members A,B,C
```

Replica C:

```bash
python3 labs/kv_store/vector_clock_replication/node.py \
  --node-id C \
  --port 6483 \
  --members A,B,C
```

Poi collegarsi con il client:

```bash
python3 labs/kv_store/vector_clock_replication/client.py --port 6481
```

Per parlare con `B`:

```bash
python3 labs/kv_store/vector_clock_replication/client.py --port 6482
```

Per parlare con `C`:

```bash
python3 labs/kv_store/vector_clock_replication/client.py --port 6483
```

## Protocollo client

### `GET`

```text
GET room
```

Risposte possibili:

```text
NOT_FOUND key=room
OK key=room value=aula-a clock=A:1,B:0,C:0 origin=A
CONFLICT key=room siblings=2 | ...
```

### `SET`

```text
SET room aula-a
```

Se non ci sono conflitti locali, crea una nuova versione.

Se ci sono siblings:

```text
ERR conflict_exists key=room use RESOLVE <key> <value>
```

### `SYNC`

```text
SYNC 6482
```

Sincronizza la replica corrente con la replica in ascolto sulla porta indicata.

Il protocollo è bidirezionale: il chiamante importa lo snapshot remoto e poi
invia al peer il proprio snapshot aggiornato.

### `RESOLVE`

```text
RESOLVE room aula-c
```

Richiede che esista un conflitto locale sulla chiave. Crea una nuova versione
che domina i siblings osservati.

### `DELETE`

```text
DELETE room
```

Non cancella semplicemente il valore dalla storia distribuita. Crea una
tombstone versionata, perché anche una cancellazione deve competere causalmente
con eventuali scritture concorrenti.

### `DUMP`

```text
DUMP
```

Mostra lo stato locale completo in JSON. È utile per verificare manualmente la
struttura interna:

```text
key -> list[Version]
```

## Percorso operativo consigliato

### Fase 1: visibilità locale

```text
A> SET course sistemi-distribuiti
B> GET course
```

Domanda:

```text
Il sistema deve promettere read-your-writes su qualunque replica?
```

### Fase 2: anti-entropy

```text
A> SYNC 6482
B> GET course
```

Domanda:

```text
SYNC ha creato una decisione globale o ha solo scambiato stato?
```

### Fase 3: concorrenza

```text
A> SET room aula-a
B> SET room aula-b
A> SYNC 6482
A> GET room
```

Domanda:

```text
Perché il sistema conserva due versioni?
```

### Fase 4: contratto

```text
A> SET room aula-c
```

Domanda:

```text
Perché SET non può essere usato come risoluzione implicita?
```

### Fase 5: risoluzione e convergenza

```text
A> RESOLVE room aula-c
A> SYNC 6482
B> SYNC 6483
C> GET room
```

Domanda:

```text
Quali ipotesi servono per arrivare alla convergenza?
```

## Cosa osservare nel codice

In `vector_clock.py`:

- `compare`: decide before, after, same o concurrent;
- `merge`: calcola il massimo componente per componente;
- `increment`: incrementa solo la componente della replica corrente.

In `node.py`:

- `_next_clock_for_key`: costruisce il clock della prossima versione;
- `_compact_versions`: elimina solo versioni dominate;
- `_handle_set`: rifiuta scritture semplici in presenza di conflitto;
- `_handle_resolve`: crea una versione che domina i siblings;
- `_handle_sync`: implementa la sincronizzazione bidirezionale.

## Invarianti da controllare

Durante la demo, verificare questi invarianti:

- una replica incrementa solo la propria componente;
- due versioni concorrenti non vengono compattate;
- una versione dominata viene eliminata;
- `SET` non nasconde un conflitto;
- `RESOLVE` produce un clock che domina i siblings osservati;
- dopo sincronizzazioni sufficienti, una versione risolta si propaga.
