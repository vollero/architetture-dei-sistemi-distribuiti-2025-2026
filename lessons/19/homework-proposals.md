# Proposte di Homework: KV Store e Contratti Distribuiti

Questo documento raccoglie cinque possibili homework di approfondimento sul
percorso KV store.

Ogni homework parte dagli argomenti visti a lezione, ma chiede di fare un passo
in piu': definire un contratto, implementarlo, difenderlo con test e discuterne
le proprieta' di safety e liveness.

## Organizzazione dei gruppi

Il lavoro e' pensato per gruppi da 3-4 persone.

Ruoli suggeriti:

| Ruolo | Responsabilita' |
| --- | --- |
| Protocol owner | Definisce interfaccia, risposte, precondizioni e casi fuori contratto. |
| Implementation owner | Coordina codice, integrazione e coerenza con lo stile dei lab. |
| Fault/test owner | Costruisce test, scenari di guasto, interleaving e stress. |
| Reviewer/architect | Verifica coerenza tra contratto, implementazione, test e limiti dichiarati. |

Nei gruppi da 3, il ruolo di reviewer puo' essere condiviso.

## Deliverable comuni

Ogni gruppo deve consegnare:

| Deliverable | Contenuto atteso |
| --- | --- |
| Contratto pubblico | Comandi, risposte, precondizioni, postcondizioni e casi fuori contratto. |
| Implementazione | Codice funzionante basato sui laboratori del KV store. |
| Safety/liveness note | Almeno 2 proprieta' di safety e 1 proprieta' di liveness. |
| Test ripetibili | Script o procedura automatizzabile con casi nominali e casi critici. |
| Nota tecnica | Trade-off scelti, limiti rimasti e possibili evoluzioni. |

## Homework 1: Migrazione Online Senza `NOT_FOUND` Spurio

### Obiettivo

Estendere la capstone in modo che, dopo `ADD_SHARD` e prima di `REBALANCE`, una
chiave esistente non sparisca solo perche' il routing teorico e' cambiato.

Nella reference implementation della capstone, questa finestra e' intenzionale:

```text
ADD_SHARD S2 ...
WHERE alpha -> target=S2
GETV alpha  -> NOT_FOUND
```

L'homework chiede di rafforzare il contratto.

### Requisiti minimi

- mantenere una nozione di configurazione vecchia e nuova;
- evitare `NOT_FOUND` spurio per chiavi gia' esistenti;
- preservare valore e versione durante la migrazione;
- dichiarare chiaramente cosa succede a `SET`, `GETV` e `CAS` durante la finestra transitoria.

### Safety

Proprieta' da discutere:

- una chiave ackata non deve diventare invisibile solo per cambio di topologia;
- una `CAS` non deve essere accettata due volte su due copie diverse della stessa chiave;
- dopo migrazione conclusa, valore e versione devono essere unici e coerenti.

### Liveness

Proprieta' da discutere:

- la migrazione deve terminare;
- il sistema deve prima o poi uscire dallo stato con doppia configurazione;
- una chiave non deve restare indefinitamente in stato "in migrazione".

### Hint

Una soluzione possibile e' mantenere:

```text
old_config
new_config
migration_state
```

Durante la transizione:

- `GET` e `GETV` possono consultare prima il nuovo target e poi il vecchio;
- `CAS` e' piu' delicata: conviene bloccarla sulla chiave in migrazione oppure inoltrarla a un'unica copia autorevole;
- `REBALANCE` dovrebbe marcare esplicitamente quando una chiave passa da vecchia a nuova configurazione.

## Homework 2: Quorum Con Read Repair

### Obiettivo

Estendere il quorum store con una forma di read repair.

Quando una lettura osserva versioni diverse sulle repliche, il coordinator deve:

1. scegliere la versione piu' recente secondo il contratto;
2. restituirla al client;
3. aggiornare le repliche stantie osservate durante la lettura.

### Requisiti minimi

- ogni valore deve avere una versione confrontabile;
- `GET` deve leggere da almeno `R` repliche;
- il coordinator deve scegliere la versione piu' recente tra le risposte valide;
- le repliche stale devono essere aggiornate dopo la lettura;
- il contratto deve dire cosa succede se due valori hanno versioni non ordinabili.

### Safety

Proprieta' da discutere:

- una lettura non deve restituire una versione piu' vecchia se nel quorum letto ne esiste una piu' recente;
- il read repair non deve sovrascrivere una versione piu' nuova con una piu' vecchia;
- due versioni uguali con valori diversi devono essere vietate o trattate come conflitto.

### Liveness

Proprieta' da discutere:

- repliche stale devono convergere se ricevono letture sufficienti;
- una replica lenta non deve impedire ogni lettura se il quorum minimo e' raggiungibile.

### Hint

Se usate versioni intere locali, dovete spiegare chi le assegna.

Soluzioni possibili:

- coordinator assegna versioni monotone;
- timestamp logici;
- coppia `(counter, node_id)` per rendere confrontabili versioni prodotte da nodi diversi;
- errore esplicito `ERR conflict` quando il sistema non sa scegliere.

## Homework 3: Retry Idempotenti Con `request_id`

### Obiettivo

Rendere sicuri i retry delle operazioni mutative.

In un sistema distribuito, un client puo' inviare una scrittura, perdere la
risposta e non sapere se il server l'abbia applicata. Se ritenta alla cieca,
rischia di applicare due volte lo stesso effetto.

### Interfaccia proposta

Esempi:

```text
SET_REQ clientA:42 key value
CAS_REQ clientA:43 key 7 value
DELETE_REQ clientA:44 key
```

Il `request_id` identifica univocamente una richiesta mutativa del client.

### Requisiti minimi

- il server deve ricordare l'esito delle richieste gia' viste;
- ripetere lo stesso `request_id` deve restituire la stessa risposta senza riapplicare l'effetto;
- il contratto deve dire quando un `request_id` puo' essere dimenticato;
- i test devono simulare almeno un retry dopo timeout del client.

### Safety

Proprieta' da discutere:

- la stessa richiesta mutativa non deve produrre effetti doppi;
- due richieste diverse non devono essere confuse solo perche' toccano la stessa chiave;
- il replay della risposta deve essere coerente con l'effetto gia' applicato.

### Liveness

Proprieta' da discutere:

- il server non puo' conservare per sempre tutti i `request_id`;
- la garbage collection dei request id non deve bloccare il servizio;
- un client corretto deve poter completare una sequenza di retry.

### Hint

Una soluzione base e':

```text
request_table[client_id][sequence_number] = response
```

Il punto difficile e' la pulizia.

Possibili strategie:

- conservare solo gli ultimi `N` request id per client;
- usare numeri di sequenza monotoni e un ack cumulativo;
- usare una scadenza temporale, dichiarando che oltre quella finestra il retry non e' piu' garantito.

## Homework 4: Primary Con Lease Temporale

### Obiettivo

Estendere il modello primary-secondary introducendo un lease: un nodo puo'
rispondere come primary solo se possiede un'autorizzazione valida per un certo
intervallo di tempo.

Questa traccia porta oltre quanto visto a lezione, perche' introduce il tempo
nel contratto del sistema.

### Requisiti minimi

- definire come viene assegnato un lease;
- definire quando un primary deve smettere di accettare scritture;
- definire quando un secondary puo' promuoversi;
- dichiarare le assunzioni sugli orologi;
- costruire un test o una simulazione di lease scaduto.

### Safety

Proprieta' da discutere:

- non devono esistere due primary validi contemporaneamente secondo il modello dichiarato;
- un primary con lease scaduto non deve accettare nuove scritture;
- una promozione non deve avvenire prima che il vecchio lease sia considerato scaduto.

### Liveness

Proprieta' da discutere:

- se il primary sparisce, un nuovo primary deve poter emergere dopo la scadenza del lease;
- lease troppo lunghi rallentano il failover;
- lease troppo brevi aumentano rinnovi e falsi blocchi.

### Hint

Non serve costruire un sistema di tempo perfetto.

Potete dichiarare un modello semplice:

```text
gli orologi locali hanno errore massimo epsilon
lease_duration >> epsilon
```

Poi discutete cosa succede se questa assunzione non vale.

Una versione didattica puo' usare un "lease manager" centrale. Una versione piu'
ambiziosa puo' simulare rinnovo periodico e perdita di heartbeat.

## Homework 5: Session Consistency Per Client

### Obiettivo

Aggiungere una garanzia di consistenza di sessione.

Un client che ha scritto o letto una certa versione non deve poi osservare, nella
stessa sessione, una versione piu' vecchia della stessa chiave.

Questa garanzia e' piu' debole della linearizzabilita', ma molto utile nei
sistemi distribuiti reali.

### Interfaccia proposta

Esempi:

```text
GETV key SESSION clientA
SET key value SESSION clientA
CAS key version value SESSION clientA
```

Oppure:

```text
GETV key MIN_VERSION 12
```

Il gruppo deve scegliere quale forma rendere pubblica.

### Requisiti minimi

- il sistema deve ricordare o ricevere la versione minima osservata dal client;
- una lettura non deve restituire una versione piu' vecchia della sessione;
- il contratto deve dire se il server aspetta, legge da piu' repliche o risponde con errore;
- i test devono mostrare almeno una lettura che sarebbe stantia senza garanzia di sessione.

### Safety

Proprieta' da discutere:

- read-your-writes per singolo client;
- monotonic reads per singolo client;
- una risposta non deve violare la versione minima dichiarata dalla sessione.

### Liveness

Proprieta' da discutere:

- se nessuna replica aggiornata e' raggiungibile, il sistema non deve bloccarsi indefinitamente senza dichiararlo;
- il client deve poter progredire quando almeno una replica soddisfa la versione minima;
- la gestione della sessione non deve richiedere memoria illimitata sul server.

### Hint

Due strategie ragionevoli:

- sessione stateful: il coordinator ricorda `client_id -> last_seen_version`;
- sessione stateless: il client invia `MIN_VERSION` a ogni richiesta.

La seconda e' spesso piu' semplice da scalare, ma sposta una parte del contratto
sul client.

## Criteri di valutazione suggeriti

| Criterio | Peso indicativo |
| --- | --- |
| Chiarezza del contratto | 25% |
| Correttezza dell'implementazione | 25% |
| Qualita' dei test sui casi critici | 25% |
| Discussione safety/liveness e trade-off | 20% |
| Organizzazione del gruppo e nota tecnica | 5% |

## Indicazione finale

Il lavoro non deve limitarsi ad aggiungere codice.

La domanda principale da difendere e':

> quale promessa nuova introduce il vostro sistema e quale costo tecnico avete
> accettato per mantenerla?

