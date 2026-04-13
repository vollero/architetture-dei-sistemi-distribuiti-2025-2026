# Handout: Persistenza Locale, Crash Recovery e Coerenza Interna

## Obiettivo della tappa

Dopo avere affrontato concorrenza e sezioni critiche, il KV store entra nella
prima forma di durabilita':

- lo stato non deve esistere solo in RAM;
- dopo un crash il server deve poter ricostruire uno stato coerente;
- una risposta `OK` deve essere interpretata alla luce di questa nuova
  proprieta'.

Il punto didattico e' netto: la stessa interfaccia applicativa cambia
significato operativo quando viene introdotta la persistenza.

## Nuova distinzione: stato attivo e stato ricostruibile

Da questa lezione in poi e' utile distinguere:

- stato attivo: quello residente in RAM e usato per servire le richieste;
- stato ricostruibile: quello che possiamo recuperare dopo un crash tramite
  file persistenti.

La domanda tecnica centrale e':

> il server puo' trovarsi in uno stato in cui la RAM ha gia' accettato una
> scrittura ma il disco non la riflette ancora?

Se la risposta e' si', allora esiste una finestra di crash in cui il client ha
gia' ricevuto `OK` ma il sistema non puo' difendere quella risposta dopo il
riavvio.

## Variante unsafe: write-behind su snapshot

La prima implementazione del laboratorio e' deliberatamente debole:

1. `SET` aggiorna il dizionario in RAM;
2. il server risponde `OK`;
3. uno snapshot periodico in background salva lo stato su disco.

Questa scelta ha un vantaggio apparente:

- la risposta al client e' rapida;
- il path critico non include `fsync`.

Ma introduce una finestra di vulnerabilita':

```text
update in RAM -> reply OK -> crash -> snapshot non ancora eseguito
```

In quella finestra una scrittura ackata puo' essere persa.

## Variante safe: write-ahead log

La seconda implementazione usa un append-only log:

1. serializzare l'intento di update;
2. appendere il record al log;
3. forzare il record su disco con `fsync`;
4. applicare l'update alla struttura in RAM;
5. rispondere `OK`.

Questa disciplina sposta il significato di `OK`:

- non significa solo "ho aggiornato la cache";
- significa "posso ricostruire questo update anche dopo crash".

## Invariante tecnico da difendere

Per la variante safe possiamo formulare un invariante concreto:

> ogni scrittura che ha gia' ricevuto `OK` deve comparire nello stato
> ricostruibile dopo replay del log.

Questo non implica che RAM e disco siano sempre identici in ogni istante.
Implica invece che il disco sia sufficiente a ricostruire tutte le operazioni
che il server ha promesso come completate.

## Finestre di crash da analizzare

### Snapshot unsafe

Sequenza astratta:

```text
AcquireLock -> ApplyInMemory -> Reply -> BackgroundSnapshot
```

Finestre interessanti:

- crash prima di `ApplyInMemory`: nessun effetto visibile;
- crash tra `ApplyInMemory` e `Reply`: il client puo' non sapere se l'update
  sia riuscito;
- crash tra `Reply` e `BackgroundSnapshot`: update visibile prima del crash ma
  non recoverable dopo il riavvio.

### Write-ahead log safe

Sequenza astratta:

```text
AcquireLock -> AppendLog -> Fsync -> ApplyInMemory -> Reply
```

Finestre interessanti:

- crash prima di `AppendLog`: nessuna promessa al client;
- crash tra `AppendLog` e `Fsync`: il record puo' essere presente o no, quindi
  non si deve ancora rispondere `OK`;
- crash tra `Fsync` e `ApplyInMemory`: lo stato in RAM del processo appena
  morto puo' essere incompleto, ma il replay del log corregge il problema;
- crash dopo `Reply`: la scrittura deve risultare ricostruibile.

## Safety e liveness in questa tappa

### Safety

Nel contesto della persistenza, esempi di safety sono:

- nessuna scrittura ackata viene dimenticata dalla recovery;
- il replay non produce uno stato impossibile;
- `DELETE` e `INCR` restano coerenti rispetto al log.

### Liveness

Lato liveness emergono nuovi costi:

- `fsync` aumenta la latenza delle scritture;
- trattenere il lock durante persistenza serializza piu' lavoro;
- un disco lento puo' rallentare l'intero servizio.

Questa tappa e' utile proprio per mostrare che la durabilita' locale non e'
gratis: viene comprata con tempo e complessita' implementativa.

## Interfaccia e contratto

Dal punto di vista sintattico il client continua a vedere quasi gli stessi
comandi. Ma il contratto cambia:

- in `v1`, `OK` significava soprattutto "update coerente rispetto ai thread";
- in `v2`, `OK` deve essere letto come "update coerente e difendibile dopo
  crash locale", almeno nella variante safe.

Questo e' uno dei punti piu' importanti dell'intero percorso: la stessa API
puo' restare stabile mentre cambia profondamente il suo contenuto semantico.

## Esperimento suggerito

### Variante unsafe

1. avviare `server_persistent_unsafe.py`;
2. eseguire `SET course distributed-systems`;
3. eseguire subito `CRASH`;
4. riavviare il server sulla stessa directory dati;
5. osservare `GET course`.

Domanda: il `OK` osservato prima del crash era difendibile?

### Variante safe

1. avviare `server_persistent.py`;
2. eseguire `SET course distributed-systems`;
3. eseguire `CRASH`;
4. riavviare il server sulla stessa directory dati;
5. osservare `GET course`.

Domanda: cosa cambia e perche'?

## Vista come automa

Anche qui la lettura come automa e' utile.

Variante unsafe:

```text
Idle -> AcquireLock -> ApplyInMemory -> Reply -> SnapshotLater
```

Variante safe:

```text
Idle -> AcquireLock -> AppendLog -> Fsync -> ApplyInMemory -> Reply
```

La differenza vera non e' estetica, ma semantica: nella seconda sequenza il
server attraversa un punto in cui l'update e' gia' recoverable prima della
risposta al client.

## Messaggio da portare a casa

Un sistema che "funziona" prima del crash puo' essere comunque scorretto se
non sa difendere dopo il riavvio le promesse fatte al client.

La persistenza locale obbliga a distinguere:

- stato visibile adesso;
- stato ricostruibile domani;
- punto preciso in cui una risposta positiva diventa legittima.
