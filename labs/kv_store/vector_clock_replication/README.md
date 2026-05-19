# Lab: KV Store Distribuito con Vector Clock

Questo laboratorio integra i vector clock in un KV store distribuito multi-master.
È pensato per una dimostrazione di circa un'ora in classe: gli studenti vedono
scritture causali, scritture concorrenti, conflitti, risoluzione esplicita e
convergenza tra repliche.

Il codice è volutamente compatto e non usa dipendenze esterne.

## Materiale collegato

- [Lezione 23](../../../lessons/23/README.md)
- [Handout tecnico](../../../lessons/23/handout.md)
- [Guida operativa](../../../lessons/23/lab-guide.md)
- [Scenari di discussione](../../../lessons/23/scenarios.md)
- [Slide](../../../slides/23-vector-clock-kv.pdf)

## Obiettivo didattico

La domanda guida è:

```text
Se due repliche accettano scritture indipendenti sulla stessa chiave,
come capiamo se una versione sostituisce l'altra o se le due versioni
sono concorrenti?
```

Il laboratorio mostra che una singola versione intera non basta. Serve un
metadato che rappresenti chi ha prodotto quali aggiornamenti. In questo caso
usiamo un **vector clock per chiave**, chiamato anche **version vector**.

## Modello

Ogni replica ha un identificatore stabile:

```text
A, B, C
```

Ogni valore salvato nel KV store è accompagnato da un clock:

```text
value = aula-a
clock = A:1,B:0,C:0
```

Il significato è:

```text
questa versione conosce 1 aggiornamento prodotto da A,
0 aggiornamenti prodotti da B,
0 aggiornamenti prodotti da C
```

Il clock è associato alla versione della chiave, non al tempo fisico.

## Regola di confronto

Dati due clock `x` e `y`:

```text
x <= y se ogni componente di x è <= della componente corrispondente di y
x < y  se x <= y e almeno una componente è strettamente minore
```

Quindi:

```text
A:1,B:0,C:0 < A:2,B:0,C:0
```

La seconda versione domina la prima: può sostituirla.

Invece:

```text
A:1,B:0,C:0
A:0,B:1,C:0
```

non sono confrontabili. Le due versioni sono concorrenti e il KV store deve
mantenerle entrambe come **siblings**.

## Contratto dell'interfaccia

Comandi client:

| Comando | Significato |
| --- | --- |
| `PING` | controlla che il nodo risponda |
| `MEMBERS` | mostra la membership del vector clock |
| `SET <key> <value>` | scrive una nuova versione se non esiste un conflitto locale |
| `GET <key>` | legge una chiave e mostra valore, clock o conflitto |
| `DELETE <key>` | crea una tombstone versionata |
| `RESOLVE <key> <value>` | risolve un conflitto scegliendo un nuovo valore |
| `SYNC [host] <port>` | sincronizza due repliche con anti-entropy bidirezionale |
| `DUMP` | mostra lo stato locale in JSON |
| `QUIT` | chiude la connessione client |

Il vincolo più importante è:

```text
SET non risolve automaticamente un conflitto.
```

Se una chiave ha più versioni concorrenti, `SET` restituisce errore. Lo
studente deve usare `RESOLVE`, perché la scelta del valore vincente non è una
decisione tecnica neutra: appartiene al contratto applicativo.

## Avvio manuale

Aprire tre terminali.

Terminale 1:

```bash
python3 labs/kv_store/vector_clock_replication/node.py \
  --node-id A \
  --port 6481 \
  --members A,B,C
```

Terminale 2:

```bash
python3 labs/kv_store/vector_clock_replication/node.py \
  --node-id B \
  --port 6482 \
  --members A,B,C
```

Terminale 3:

```bash
python3 labs/kv_store/vector_clock_replication/node.py \
  --node-id C \
  --port 6483 \
  --members A,B,C
```

In un quarto terminale si può usare il client:

```bash
python3 labs/kv_store/vector_clock_replication/client.py --port 6481
```

## Demo automatica

Per una dimostrazione rapida:

```bash
python3 labs/kv_store/vector_clock_replication/demo_vector_clock_kv.py
```

La demo avvia tre repliche, esegue i comandi principali e poi le termina.

Se si vogliono vedere anche i log dei nodi:

```bash
python3 labs/kv_store/vector_clock_replication/demo_vector_clock_kv.py --show-node-logs
```

## Percorso da un'ora

### 0-10 minuti: perché serve un metadato causale

Avviare A e B. Scrivere una chiave su A:

```text
A> SET course sistemi-distribuiti
A< OK key=course value=sistemi-distribuiti clock=A:1,B:0,C:0
```

Leggere da B prima della sincronizzazione:

```text
B> GET course
B< NOT_FOUND key=course
```

Discussione:

```text
Il valore esiste nel sistema?
Esiste su ogni replica?
GET deve promettere una vista globale o locale?
```

### 10-20 minuti: sincronizzazione e dominio causale

Sincronizzare A con B:

```text
A> SYNC 6482
A< OK synced peer=B@127.0.0.1:6482 local_changed=False peer_changed=True
```

Leggere da B:

```text
B> GET course
B< OK key=course value=sistemi-distribuiti clock=A:1,B:0,C:0 origin=A
```

Ora B aggiorna la stessa chiave:

```text
B> SET course sistemi-distribuiti-2026
B< OK key=course value=sistemi-distribuiti-2026 clock=A:1,B:1,C:0
```

Il clock `A:1,B:1,C:0` domina `A:1,B:0,C:0`, quindi la versione precedente può
essere eliminata localmente da B e, dopo `SYNC`, anche da A.

### 20-35 minuti: scritture concorrenti

Senza sincronizzare, scrivere la stessa chiave su A e B:

```text
A> SET room aula-a
A< OK key=room value=aula-a clock=A:1,B:0,C:0
```

```text
B> SET room aula-b
B< OK key=room value=aula-b clock=A:0,B:1,C:0
```

Sincronizzare:

```text
A> SYNC 6482
```

Leggere:

```text
A> GET room
A< CONFLICT key=room siblings=2 | [0] value=aula-b clock=A:0,B:1,C:0 origin=B | [1] value=aula-a clock=A:1,B:0,C:0 origin=A
```

Discussione:

```text
A:1,B:0,C:0 non domina A:0,B:1,C:0.
A:0,B:1,C:0 non domina A:1,B:0,C:0.
Il sistema non può scegliere automaticamente senza una policy applicativa.
```

### 35-45 minuti: contratto e risoluzione esplicita

Provare a usare `SET`:

```text
A> SET room aula-c
A< ERR conflict_exists key=room use RESOLVE <key> <value>
```

Poi risolvere:

```text
A> RESOLVE room aula-c
A< OK resolved key=room value=aula-c clock=A:2,B:1,C:0
```

Il nuovo clock domina entrambe le versioni concorrenti:

```text
A:2,B:1,C:0 > A:1,B:0,C:0
A:2,B:1,C:0 > A:0,B:1,C:0
```

Dopo `SYNC`, anche B converge su un solo valore.

### 45-60 minuti: safety, liveness e limiti

Safety:

```text
Una versione non viene scartata se il suo clock è concorrente con quello di un'altra versione.
```

Questo evita perdita silenziosa di aggiornamenti.

Liveness:

```text
Se le repliche continuano a sincronizzarsi e i conflitti vengono risolti,
le repliche convergono.
```

Limiti del laboratorio:

```text
Non c'è persistenza su disco.
Non c'è autenticazione.
Non c'è membership dinamica.
Non c'è consenso.
Non c'è una policy automatica di merge dei valori.
```

Questi limiti sono intenzionali: la demo isola il ruolo dei vector clock senza
nascondere il problema dietro un framework.

## File

| File | Ruolo |
| --- | --- |
| `vector_clock.py` | confronto, merge e incremento dei vector clock |
| `node.py` | replica KV multi-master con protocollo client e RPC interno |
| `client.py` | client interattivo |
| `demo_vector_clock_kv.py` | scenario automatico per la lezione |

## Domande per la classe

```text
Un clock fisico avrebbe risolto il conflitto room?
Perché SET viene rifiutato in presenza di siblings?
Chi deve decidere il valore vincente?
Quale proprietà di safety protegge il mantenimento dei siblings?
Quale ipotesi di liveness serve per arrivare alla convergenza?
Cosa cambia se la membership A,B,C non è stabile?
```
