# Handout: Rebalancing, Routing e Posizione Reale dei Dati

## Obiettivo della tappa

Lo sharding della lezione precedente introduceva un'assunzione implicita:

> la funzione di routing e la posizione reale del dato coincidono.

Questa lezione mostra che l'assunzione si rompe non appena cambia la topologia.

## Due nozioni da separare

Da ora in poi vanno tenute distinte:

- destinazione teorica di una chiave secondo il routing corrente;
- posizione reale della chiave negli shard.

Finche' la topologia e' statica, le due nozioni coincidono.
Dopo `ADD_SHARD`, non piu'.

## `ADD_SHARD` non sposta dati

Aggiungere uno shard cambia il risultato della funzione:

```text
target = hash(key) mod numero_di_shard
```

Ma non cambia automaticamente dove il dato e' gia' stato scritto.

Nasce quindi una finestra in cui:

- il router crede che una chiave debba stare su un certo shard;
- il valore reale e' ancora altrove.

## Rebalance come protocollo

Il rebalance non e' solo "copiare chiavi".

Deve almeno:

1. individuare le chiavi che hanno cambiato destinazione;
2. importarle nello shard corretto;
3. rimuoverle da quello vecchio;
4. riportare il sistema a uno stato coerente.

## Domanda centrale

Durante il rebalance, che cosa dovrebbe osservare il client?

Opzioni possibili:

- routing nuovo, ma dato vecchio non ancora spostato;
- blocco temporaneo di alcune operazioni;
- doppia presenza transitoria;
- protocollo piu' complesso con fasi esplicite.

Il laboratorio usa una versione semplice, ma serve proprio a far emergere il
problema.

## La soluzione minima del laboratorio

La versione attuale del lab adotta un protocollo molto semplice:

1. il router legge tutte le chiavi da tutti gli shard;
2. per ogni chiave ricalcola la destinazione con la topologia nuova;
3. se la destinazione e' cambiata, esegue `IMPORT_KEY` sullo shard target;
4. solo dopo esegue `DELETE_LOCAL` sullo shard sorgente.

Questa soluzione ha alcuni meriti didattici:

- e' facile da leggere;
- evita la perdita immediata del dato, perche' copia prima di cancellare;
- rende visibile la differenza tra topologia e posizione reale.

Ma ha anche limiti netti:

- il router esegue la migrazione in modo sequenziale;
- non esiste una nozione di "epoca di configurazione";
- non esiste uno stato esplicito di chiave "in migrazione";
- non c'e' coordinamento con scritture concorrenti.

## Complessita' e tempi della soluzione minima

Anche senza distribuire davvero il carico, si possono gia' discutere i costi.

Per una singola chiave migrata il protocollo fa almeno:

- una decisione di routing;
- una RPC `IMPORT_KEY`;
- una RPC `DELETE_LOCAL`.

In piu', prima di migrare, il router deve ottenere l'elenco completo delle
chiavi tramite `LIST_ITEMS` su ogni shard.

Quindi il costo totale e' approssimativamente:

- una scansione completa di tutti gli shard;
- due RPC per ogni chiave che cambia shard.

Se indichiamo con:

- `S` il numero di shard;
- `K` il numero totale di chiavi;
- `M` il numero di chiavi da migrare;
- `Lrpc` la latenza media di una RPC tra router e shard,

allora, in prima approssimazione, il tempo del rebalance e':

```text
T ~= S * Lrpc + M * (IMPORT_KEY + DELETE_LOCAL)
```

Se `IMPORT_KEY` e `DELETE_LOCAL` hanno costo simile:

```text
T ~= S * Lrpc + 2 * M * Lrpc
```

Questo modello e' rozzo, ma e' sufficiente per far ragionare gli studenti su
due punti:

- il tempo cresce con il numero di chiavi da spostare, non solo con il numero di shard;
- la migrazione sequenziale diventa rapidamente dominante.

## Tre famiglie di soluzioni

### 1. Stop-the-world reconfiguration

Strategia:

- si blocca temporaneamente `SET`, `DELETE` e talvolta anche `GET`;
- si migra tutto il necessario;
- si riapre il traffico a migrazione conclusa.

Vantaggi:

- contratto molto pulito;
- implementazione relativamente semplice;
- quasi nessuna ambiguita' semantica durante la migrazione.

Problemi:

- disponibilita' ridotta;
- tempo di stop che cresce con il volume dei dati;
- esperienza pessima se le chiavi sono molte o grandi.

Questa e' spesso la prima soluzione che si implementa in un progetto didattico
o in sistemi piccoli.

### 2. Migrazione online con doppia consultazione o forwarding

Strategia:

- il routing nuovo diventa visibile;
- durante una fase transitoria, il sistema mantiene memoria della posizione vecchia;
- se il target nuovo non ha la chiave, il router o il vecchio shard possono fare forwarding.

Vantaggi:

- minore interruzione del servizio;
- il client vede meno `NOT_FOUND` spurii;
- il passaggio puo' essere quasi trasparente.

Problemi:

- servono metadata di migrazione;
- aumenta la complessita' del protocollo;
- bisogna decidere per quanto tempo tenere valida la vecchia posizione.

Questa strategia introduce spesso una nozione di stato come:

- `stable-old`
- `copying`
- `dual-present`
- `stable-new`

### 3. Copy, catch-up, cutover

Strategia piu' seria:

1. si copia una fotografia iniziale dei dati;
2. si registrano o si inoltrano le scritture arrivate durante la copia;
3. si esegue un cutover finale;
4. solo allora si dismette la posizione vecchia.

Vantaggi:

- riduce la finestra di inconsistenza al momento del cutover;
- si presta meglio a dataset grandi;
- e' una base realistica per sistemi con traffico concorrente.

Problemi:

- richiede log, versioni o forwarding delle scritture;
- il cutover va coordinato con attenzione;
- la gestione dei retry e dell'idempotenza diventa cruciale.

## Il vero nodo: che cosa succede alle scritture concorrenti

La domanda piu' importante non e' "come copio una chiave", ma:

> che cosa succede se un client fa `SET key value2` mentre `key` sta migrando?

Possibili approcci:

- bloccare le scritture sulla chiave o sullo shard durante la migrazione;
- accettarle solo sul vecchio shard e replayarle sul nuovo;
- accettarle solo sul nuovo shard dopo una certa fase;
- accettarle in entrambi, ma con versioni e risoluzione dei conflitti.

Qui si vede bene come un problema apparentemente "di sharding" tocchi in realta':

- coordinamento;
- serializzazione degli eventi;
- definizione del punto in cui il nuovo assetto diventa autorevole.

## Safety e liveness della migrazione

### Safety

Durante la migrazione, tipicamente vogliamo preservare proprieta' come:

- nessuna chiave ackata viene persa;
- una chiave non sparisce solo per effetto del cambio di topologia;
- se una scrittura e' stata accettata, esiste almeno una copia autorevole;
- il sistema non dichiara conclusa una migrazione che non e' davvero chiusa.

### Liveness

Allo stesso tempo, vogliamo evitare:

- migrazioni che restano aperte indefinitamente;
- shard bloccati per tempi troppo lunghi;
- backlog di scritture che cresce piu' rapidamente della migrazione.

Questo compromesso e' il cuore tecnico della lezione.

## Problemi implementativi che emergono subito

Anche in un prototipo piccolo come questo, si vedono gia' problemi reali:

- migrazione troppo grossolana: una sola chiamata `REBALANCE` lavora su tutto;
- assenza di batching: le chiavi vengono spostate una alla volta;
- assenza di retry strutturati;
- nessuna distinzione tra errore temporaneo ed errore definitivo;
- assenza di resume: se il router cade, la migrazione riparte da zero;
- nessun controllo di rate limiting verso gli shard.

In un sistema piu' ampio, si introdurrebbero spesso:

- migrazione per range o per bucket;
- batch di dimensione controllata;
- checkpoint di avanzamento;
- metriche di throughput e backlog;
- timeout separati per copy, delete e commit logico.

## Tempi: cosa ha senso dire agli studenti

In aula conviene essere concreti e non fittiziamente precisi.

Una discussione ragionevole e':

- con poche chiavi e rete locale, anche un protocollo ingenuo puo' sembrare istantaneo;
- con molte chiavi, il costo dominante diventa la scansione piu' la serializzazione delle RPC;
- con valori grandi, il costo dominante diventa il trasferimento dei byte;
- con traffico concorrente, il costo vero include il coordinamento, non solo la copia.

Quindi il "tempo di migrazione" non e' un numero unico.
Dipende almeno da:

- numero di chiavi;
- dimensione media dei valori;
- percentuale di chiavi che cambiano shard;
- latenza di rete;
- numero di operazioni concorrenti che continuano ad arrivare.

## Una possibile traiettoria progettuale

Se si volesse far evolvere questo laboratorio in passi successivi, una
sequenza sensata sarebbe:

1. versione attuale: copy-then-delete sequenziale, senza scritture concorrenti;
2. versione con blocco temporaneo delle scritture durante `REBALANCE`;
3. versione con metadata di migrazione e forwarding in lettura;
4. versione con scritture catturate durante la copia e cutover finale;
5. versione con migrazione per range e metriche di avanzamento.

Didatticamente e' una sequenza utile perche' ogni passo migliora il contratto,
ma impone un costo implementativo chiaramente visibile.

## Messaggio da portare a casa

Con il rebalancing la topologia del cluster diventa dinamica. A quel punto il
contratto dell'interfaccia non riguarda piu' solo "dove dovrebbe andare una
chiave", ma anche:

- quando il sistema puo' dire che la migrazione e' conclusa;
- quale copia e' autorevole durante il transitorio;
- se il servizio privilegia semplicita', disponibilita' o continuita' semantica.
