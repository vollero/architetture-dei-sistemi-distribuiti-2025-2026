# Handout: Versioni, GETV e Compare-And-Set

## Obiettivo della tappa

Finora il client poteva:

- leggere un valore;
- scrivere un valore;
- affidarsi alle garanzie interne del server.

Ora vogliamo introdurre un contratto piu' ricco:

- il client osserva una versione;
- il client puo' dire "scrivi solo se nulla e' cambiato nel frattempo".

## Blind write contro conditional write

Una `SET` e' una blind write:

- aggiorna senza chiedere se il valore sia cambiato rispetto a una lettura
  precedente del client.

Una `CAS` e' una conditional write:

- aggiorna solo se la versione osservata e' ancora corrente.

## `GETV`

`GETV` espone:

- il valore;
- la versione.

Questa scelta ha conseguenze importanti:

- il client vede una parte della logica di concorrenza;
- la versione entra nel contratto dell'API;
- il server non puo' piu' cambiare arbitrariamente il significato di quella
  versione senza rompere i client.

## `version_mismatch`

Il risultato:

```text
ERR version_mismatch current=7
```

non e' un errore "tecnico" qualsiasi.

E' un esito applicativo del contratto: il server sta dicendo che la precondizione
della scrittura non era piu' vera.

## La soluzione implementata nel lab

Nel laboratorio il server mantiene, per ogni chiave:

```text
(value, version)
```

Le operazioni rilevanti lavorano cosi':

- `SET` legge la versione corrente, la incrementa e scrive il nuovo valore;
- `CAS` confronta la versione attesa con quella corrente;
- se il confronto riesce, aggiorna valore e versione nella stessa sezione critica.

Questa e' la soluzione minima sensata su nodo singolo.
Funziona bene didatticamente perche' mostra con chiarezza che il cuore del
problema non e' il parsing del comando, ma l'atomicita' del controllo
``check-then-update''.

## Perche' `CAS` richiede atomicita'

La forma logica di `CAS` e':

1. leggi la versione corrente;
2. confrontala con quella attesa;
3. se coincidono, applica l'update.

Se questi tre passi non sono atomici, puo' accadere che:

- due thread leggano la stessa versione;
- entrambi la giudichino valida;
- entrambi scrivano;
- uno dei due conflitti venga nascosto.

Quindi `CAS` non e' semplicemente un comando in piu'.
E' una richiesta di serializzare un certo tipo di decisione.

## Tre implementazioni possibili

### 1. Lock globale sullo store

E' la soluzione adottata nel lab.

Pregi:

- semplicissima da ragionare;
- facile da dimostrare corretta;
- ottima per fissare la semantica.

Limiti:

- contesa elevata;
- tutte le chiavi condividono la stessa sezione critica;
- il parallelismo e' piu' basso del necessario.

### 2. Lock per chiave

Possibile evoluzione:

- ogni chiave ha un proprio lock;
- `CAS` serializza solo le operazioni sulla stessa chiave.

Pregi:

- migliore parallelismo;
- semantica invariata verso il client.

Problemi:

- gestione del ciclo di vita dei lock;
- struttura dati piu' complessa;
- casi delicati se si introducono operazioni multi-key.

### 3. Storage atomico sottostante

In un sistema reale si puo' delegare la semantica di compare-and-set a:

- un database con primitive condizionali;
- un motore key-value con transazioni o operazioni atomiche;
- un layer replicato che serializza gia' gli update.

In quel caso il server applicativo espone il contratto, ma non ne implementa
da solo tutta la meccanica interna.

## Tempi e costi del protocollo

Anche qui e' utile distinguere il costo logico da quello osservato dal client.

Per un client corretto, un aggiornamento con `CAS` richiede spesso:

1. `GETV`;
2. logica applicativa locale;
3. `CAS`;
4. eventualmente nuovo `GETV` e retry.

Quindi, rispetto a `SET`, il costo applicativo cresce:

- piu' round trip;
- possibilita' di fallimenti legittimi;
- necessita' di retry espliciti.

Con bassa contesa, questo costo e' spesso accettabile.
Con alta contesa, il numero di `version_mismatch` puo' diventare dominante.

## Il vero costo: i retry

Il punto importante da spiegare agli studenti e':

> `CAS` non elimina il conflitto. Lo sposta in un protocollo esplicito di retry.

Un client ben progettato deve almeno decidere:

- quante volte riprovare;
- se fare backoff;
- se rileggere sempre con `GETV`;
- quando dichiarare fallimento all'applicazione.

Senza questa disciplina, `CAS` puo' portare a:

- loop aggressivi;
- starvation di alcuni client;
- spreco di round trip inutili.

## Safety e liveness

### Safety

Con `CAS` vogliamo difendere almeno queste proprieta':

- una write basata su stato stantio non deve essere accettata silenziosamente;
- il server non deve generare due successi incompatibili sulla stessa versione;
- la storia delle versioni di una chiave deve essere monotona.

### Liveness

Allo stesso tempo, non vogliamo:

- client che ritentano indefinitamente senza progresso;
- contesa tale da rendere impossibile completare gli aggiornamenti;
- lock mantenuti piu' del necessario.

Questa tensione e' un caso molto concreto del solito compromesso tra
``piu' controllo'' e ``piu' costo operativo''.

## Problemi implementativi da discutere

Questa tappa apre subito domande reali:

- la versione e' per chiave o globale?
- `DELETE` resetta la storia o introduce una nuova epoca?
- vogliamo esporre `current=` come dato su cui i client possono basarsi?
- cosa succede se una stessa operazione applicativa deve toccare piu' chiavi?

Ognuna di queste scelte cambia il contratto.
Non sono dettagli cosmetici.

## Indicazioni di tempi per l'implementazione

Per studenti che hanno gia' visto threading e sezioni critiche, una scaletta
ragionevole puo' essere:

1. 20-30 minuti per fissare il contratto di `GETV`, `CAS`, chiave assente e `DELETE`;
2. 30-45 minuti per l'implementazione base con lock globale;
3. 20-30 minuti per test di successo, conflitto e chiave assente;
4. tempo extra per discutere retry e possibili evoluzioni.

Il punto non e' correre sul codice.
Il punto e' vedere che una piccola estensione dell'interfaccia forza scelte
tecniche molto nette.

## Perche' questa tappa e' importante

`CAS` e' un ponte concettuale tra:

- store locale concorrente;
- store replicato;
- store shardato con migrazioni.

In tutti questi casi la domanda e':

> il client puo' ancora fidarsi dello stato che aveva osservato prima di
> scrivere?

## Messaggio da portare a casa

Con `GETV` e `CAS` il contratto non descrive piu' solo "quale valore leggi" o
"quale valore scrivi", ma anche:

- quale stato hai osservato;
- sotto quale precondizione il server accetta la tua scrittura.
- quanto costa, in termini di retry e coordinamento, far rispettare quella precondizione.
