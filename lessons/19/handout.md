# Handout: Chiusura del Percorso KV Store

## Perche' abbiamo costruito un KV store

Il KV store e' stato usato come palestra per un motivo preciso:

- ha un'interfaccia piccola;
- permette esperimenti rapidi;
- fa emergere problemi reali dei sistemi distribuiti;
- obbliga a distinguere sintassi, contratto e implementazione.

Comandi semplici come:

```text
SET key value
GET key
CAS key version value
REBALANCE
```

sembrano banali solo finche' il sistema e' locale, sequenziale e volatile.
Appena introduciamo concorrenza, crash, replica, topologia dinamica o versioni,
ogni risposta del server diventa una promessa da difendere.

## Il filo del percorso

### Nodo singolo

La prima versione serviva a separare:

- interfaccia testuale;
- stato interno;
- semantica delle risposte.

Il messaggio centrale era:

> un comando non e' solo una stringa; e' una richiesta con precondizioni,
> effetti e risultati osservabili.

### Dispatch table

La seconda variante ha mostrato che anche la struttura del codice comunica un
contratto interno:

- ogni comando ha un handler;
- l'estensione del protocollo diventa piu' esplicita;
- la lista dei comandi supportati diventa una mappa leggibile.

### Multithread e sezioni critiche

Con piu' thread, il problema non era piu' solo "memorizzare valori".

Il punto era:

- quali percorsi leggono soltanto;
- quali modificano;
- quali fanno read-modify-write;
- quali interleaving violano la safety.

`INCR` ha reso visibile la differenza tra:

- esecuzione intuitiva;
- esecuzione realmente possibile;
- stato finale corretto.

### Persistenza locale

La persistenza ha cambiato il significato di `OK`.

Prima:

```text
OK = il dato e' stato aggiornato in RAM
```

Dopo:

```text
OK = il dato e' ricostruibile dopo crash locale
```

Da qui nasce il problema della coerenza interna tra:

- stato in memoria;
- log o snapshot su disco;
- procedura di recovery.

### Replica primary-secondary

La replica ha introdotto una domanda nuova:

> `OK` significa scritto sul primary o scritto anche sul secondary?

La differenza tra replica asincrona e sincrona non e' un dettaglio di
implementazione. Cambia il contratto:

- latenza;
- disponibilita';
- possibilita' di letture stantie;
- perdita di dati dopo crash del primary.

### Failover

Con heartbeat e timeout abbiamo visto che "rilevare un guasto" significa
interpretare assenza di messaggi.

Questo introduce una tensione inevitabile:

- timeout breve: failover piu' rapido, piu' falsi positivi;
- timeout lungo: meno falsi positivi, recupero piu' lento.

Il rischio centrale diventa lo split brain: due nodi che credono entrambi di
essere autorevoli.

### Quorum

I quorum hanno trasformato il contratto in un vincolo numerico.

Con `N` repliche:

- `W` indica quante repliche devono accettare una scrittura;
- `R` indica quante repliche devono partecipare a una lettura.

La condizione:

```text
R + W > N
```

non e' una formula decorativa. Dice che letture e scritture devono
intersecarsi almeno su una replica.

### Sharding

Lo sharding ha spostato il problema dalla singola copia al partizionamento.

Da quel momento:

- ogni chiave ha una destinazione;
- il router diventa parte del contratto;
- operazioni globali come `KEYS` diventano costose;
- hotspot e distribuzione delle chiavi diventano problemi osservabili.

### Rebalancing e migrazione

Quando cambia la topologia, routing teorico e posizione reale possono divergere.

Il punto critico e':

- `ADD_SHARD` cambia la funzione di destinazione;
- il dato non si muove da solo;
- `REBALANCE` diventa un protocollo, non una copia banale.

La migrazione obbliga a scegliere tra:

- bloccare il sistema;
- accettare finestre di incoerenza;
- introdurre forwarding;
- usare copy, catch-up e cutover.

### Versioni e CAS

`GETV` e `CAS` hanno spostato una parte del controllo di concorrenza
nell'interfaccia.

Il client non dice piu' solo:

```text
scrivi questo valore
```

Dice:

```text
scrivi questo valore solo se la versione che ho osservato e' ancora valida
```

`version_mismatch` non e' un errore tecnico qualsiasi. E' un risultato
semantico: la precondizione della scrittura non vale piu'.

### Capstone

La capstone ha combinato:

- sharding;
- rebalancing;
- versioni;
- `CAS`;
- test di accettazione.

Il risultato importante non e' solo il codice. E' il fatto che il sistema abbia
una specifica dichiarata:

- dove vive la versione;
- quando cambia il routing;
- cosa succede prima di `REBALANCE`;
- quale stato viene trasferito durante la migrazione;
- quali limiti restano aperti.

## La tabella mentale da portare via

| Tema | Domanda tecnica | Contratto che cambia |
| --- | --- | --- |
| Concorrenza | due operazioni possono interleavarsi? | atomicita' e sezioni critiche |
| Persistenza | cosa sopravvive al crash? | significato di `OK` |
| Replica | quante copie devono sapere? | ack locale o replicato |
| Failover | chi e' autorevole? | ruolo del nodo |
| Quorum | quante risposte bastano? | lettura/scrittura come vincolo numerico |
| Sharding | dove sta la chiave? | routing osservabile |
| Rebalancing | quando il routing torna vero? | migrazione come protocollo |
| CAS | posso fidarmi della versione letta? | scrittura condizionale |

## Safety e liveness come lente comune

Una lezione importante e' che quasi ogni tappa puo' essere riletta con due
domande.

### Safety

Che cosa non deve mai accadere?

Esempi:

- perdere una scrittura ackata;
- accettare due `CAS` incompatibili sulla stessa versione;
- promuovere due primary indipendenti;
- dichiarare finita una migrazione incompleta;
- rispondere con una versione che non corrisponde al valore.

### Liveness

Che cosa deve prima o poi riuscire ad accadere?

Esempi:

- un client deve poter completare una richiesta;
- il sistema deve recuperare dopo crash;
- una replica lenta non deve bloccare sempre tutto;
- una migrazione non deve restare aperta indefinitamente;
- i retry di `CAS` non devono produrre starvation sistematica.

## Interfaccia, contratto, implementazione

Il filo didattico piu' importante e' questo:

- l'interfaccia e' cio' che il client puo' invocare;
- il contratto e' cio' che il sistema promette osservabilmente;
- l'implementazione e' il meccanismo scelto per mantenere quella promessa.

Confondere questi tre livelli porta a errori progettuali.

Esempio:

```text
GET key -> NOT_FOUND
```

puo' significare:

- la chiave non esiste;
- il router sta interrogando lo shard sbagliato durante migrazione;
- una replica non ha ancora ricevuto l'update;
- il contratto consente letture stantie.

Stessa risposta testuale, contratti diversi.

## Cosa manca ancora a un sistema reale

Il percorso costruito resta intenzionalmente didattico.

Per avvicinarsi a un sistema reale servirebbero ancora:

- membership robusta;
- consenso o leader election piu' formale;
- log replicato;
- snapshot e compaction;
- riconfigurazione sicura del cluster;
- gestione dei conflitti multi-versione;
- metriche operative;
- backpressure;
- autenticazione e autorizzazione;
- test di fault injection piu' sistematici.

Questi non sono dettagli marginali. Sono cio' che trasforma una buona palestra
in un sistema di produzione.

## Come valutare una proposta progettuale

Di fronte a una nuova feature o a una nuova architettura, le domande utili sono:

1. Che cosa vede il client?
2. Quale promessa viene fatta?
3. Quale stato interno serve per mantenerla?
4. Quali crash o interleaving possono romperla?
5. Cosa succede se una parte del sistema e' lenta?
6. Cosa viene sacrificato: latenza, disponibilita', semplicita' o forza del contratto?
7. Quale test dimostra che la promessa e' rispettata?

Se non sappiamo rispondere a queste domande, non abbiamo ancora un progetto:
abbiamo solo un'idea di implementazione.

## Messaggio finale

Il KV store non e' stato il fine del percorso.

E' stato un dispositivo per vedere emergere, una alla volta, le domande
fondamentali dei sistemi distribuiti:

- chi sa cosa;
- quando lo sa;
- chi e' autorizzato a rispondere;
- quale storia degli eventi viene resa osservabile;
- quali promesse valgono anche quando il sistema cambia stato, fallisce o si divide.

Queste domande restano le stesse anche quando il sistema reale e' molto piu'
grande del laboratorio.

