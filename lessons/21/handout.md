# Handout: Sincronizzazione e Clock Logici

## Il problema del tempo distribuito

In un programma sequenziale l'ordine degli eventi è naturale.

In un sistema distribuito:

- ogni nodo esegue localmente;
- i messaggi hanno latenza variabile;
- non esiste un osservatore globale immediato;
- i clock fisici non sono perfettamente allineati;
- due eventi possono essere indipendenti.

La domanda progettuale corretta non è solo:

```text
che ora era?
```

ma:

```text
quale relazione temporale posso promettere?
```

## Eventi e processi

Consideriamo un sistema:

```text
P = {p1, p2, ..., pn}
```

Ogni processo produce eventi locali:

```text
E_i = eventi del processo p_i
```

Gli eventi possono essere:

- computazioni locali;
- invii di messaggi;
- ricezioni di messaggi;
- letture o scritture di stato;
- operazioni applicative, per esempio `SET x 1`.

## Clock fisico locale

Ogni nodo ha un orologio fisico locale.

È utile per:

- log leggibili da operatori;
- timeout;
- misure operative;
- audit;
- scadenze applicative.

Limite:

```text
clock_A(t) != clock_B(t)
```

Due nodi possono attribuire timestamp diversi allo stesso tempo reale.

## Skew e drift

### Clock skew

Lo skew è la differenza tra due clock nello stesso istante reale.

```text
skew(A,B) = clock_A(real_time) - clock_B(real_time)
```

Esempio:

```text
clock_A = 10:00:00.200
clock_B = 10:00:00.100
skew = 100 ms
```

### Clock drift

Il drift è la divergenza progressiva tra clock.
Due oscillatori non avanzano esattamente alla stessa velocità.

```text
clock_A avanza leggermente più veloce di clock_B
```

Anche se due clock vengono sincronizzati ora, torneranno a divergere.

## Precisione, accuratezza, risoluzione

Tre termini da non confondere:

- **risoluzione:** il più piccolo incremento osservabile dal clock;
- **precisione:** quanto sono stabili e ripetibili le misure;
- **accuratezza:** quanto il clock è vicino al tempo reale di riferimento.

Un clock può avere alta risoluzione ma bassa accuratezza.

Esempio:

```text
timestamp con nanosecondi, ma clock avanti di 2 secondi
```

## Clock wall-clock e clock monotono

Un **wall-clock** rappresenta data e ora civile:

```text
2026-05-18 12:30:00
```

Può saltare avanti o indietro per sincronizzazione, correzioni manuali o cambi
di configurazione.

Un **clock monotono** non torna indietro.
È adatto a misurare durate:

```text
start = monotonic()
...
elapsed = monotonic() - start
```

Regola pratica:

- wall-clock per log e audit;
- monotonic clock per timeout e misure di durata.

## Log fisici apparentemente impossibili

Scenario:

```text
A 10:00:00.200 send m to B
B 10:00:00.100 receive m from A
```

Il messaggio non è stato ricevuto prima di essere inviato.

Il problema è che i timestamp appartengono a clock locali diversi.

Conclusione:

```text
timestamp fisico locale != prova di ordine globale
```

## Sincronizzazione fisica

Meccanismi come NTP e PTP riducono la distanza tra clock.

NTP è comune in sistemi generali.
PTP è usato quando serve maggiore accuratezza in reti e hardware compatibili.

Ma la sincronizzazione non produce un punto perfetto.
Produce un intervallo di incertezza:

```text
tempo reale in [t - epsilon, t + epsilon]
```

Quindi due eventi sono sicuramente ordinabili solo se gli intervalli non si
sovrappongono.

Esempio:

```text
e1 in [100, 110]
e2 in [130, 140]
=> e1 prima di e2
```

Caso ambiguo:

```text
e1 in [100, 130]
e2 in [120, 150]
=> intervalli sovrapposti, ordine reale non certo
```

## Timeout e lease

Un timeout misura una durata locale.
Va implementato con clock monotono.

Un lease è un diritto valido fino a una scadenza temporale.
È più delicato perché coinvolge clock di nodi diversi.

Per progettare un lease bisogna dichiarare:

- errore massimo di sincronizzazione;
- durata del lease;
- margine di sicurezza;
- comportamento in caso di clock non affidabile.

Regola:

```text
lease_duration >> clock_uncertainty + network_delay_bound_assumed
```

Se non è possibile sostenere queste assunzioni, il lease non è un contratto
sicuro.

## Happened-before

Lamport definisce una relazione causale:

```text
a -> b
```

Regole:

1. se `a` e `b` sono eventi dello stesso processo e `a` precede `b`, allora `a -> b`;
2. se `a` è l'invio di un messaggio e `b` è la ricezione dello stesso messaggio,
   allora `a -> b`;
3. la relazione è transitiva.

Se non vale `a -> b` e non vale `b -> a`, gli eventi sono concorrenti:

```text
a || b
```

## Esempio happened-before

```text
A: write x=1
A: send m to B
B: receive m
B: read x
```

Relazioni:

```text
write x=1 -> send m
send m -> receive m
receive m -> read x
```

Per transitività:

```text
write x=1 -> read x
```

## Clock di Lamport

Un clock di Lamport assegna un intero agli eventi:

```text
L: eventi -> interi
```

Ogni processo mantiene un contatore.

Regole:

```text
evento locale: L_i = L_i + 1
send:          L_i = L_i + 1, allega L_i
receive:       L_i = max(L_i, timestamp_messaggio) + 1
```

Garanzia:

```text
a -> b  =>  L(a) < L(b)
```

Limite:

```text
L(a) < L(b)  non implica  a -> b
```

## Esempio Lamport con messaggio

```text
A local event      L=1
A send m to B      L=2
B local event      L=1
B receive m        L=max(1,2)+1=3
B local event      L=4
```

Il receive ha timestamp maggiore del send.

L'evento locale di `B` con `L=1` non è ordinabile causalmente rispetto
all'evento locale di `A` con `L=1`.

## Esempio Lamport con catena causale

```text
A: e1 local              L=1
A: send m1 to B          L=2
B: receive m1            L=max(0,2)+1=3
B: send m2 to C          L=4
C: receive m2            L=max(0,4)+1=5
```

La catena:

```text
A.e1 -> A.send -> B.receive -> B.send -> C.receive
```

è rispettata da timestamp crescenti.

Questo è l'uso corretto di Lamport: se la causalità esiste nel modello, il
clock la rispetta numericamente.

## Esempio Lamport: falso indizio di causalità

```text
A: SET x 1       L=5
B: SET y 1       L=7
```

Da `5 < 7` non segue automaticamente:

```text
A.SET -> B.SET
```

Potrebbero essere eventi indipendenti. Lamport preserva causalità nota, ma non
ricostruisce causalità non osservata.

## Esempio Lamport con concorrenza

```text
A: SET x 1      L=1
B: SET x 2      L=1
```

Se non esiste messaggio tra i due eventi:

```text
A_event || B_event
```

Lamport può imporre un ordine solo aggiungendo un tie-breaker.

## Ordine totale con Lamport

Per alcune applicazioni serve ordinare tutti gli eventi.

Si usa:

```text
(lamport_time, process_id)
```

Esempio:

```text
(1,A) < (1,B)
```

se `A < B`.

Questo ordine è deterministico, ma può essere artificiale.
Non dimostra causalità.

## Esempio: mutua esclusione

Tre processi chiedono una risorsa:

```text
B: request kv:x at L=1
A: request kv:x at L=1
C: request kv:x at L=1
```

Con tie-breaker:

```text
A < B < C
```

l'ordine comune è:

```text
(1,A) < (1,B) < (1,C)
```

Safety: non entrano due processi insieme nella sezione critica.

Liveness: ogni richiesta corretta prima o poi entra, se i messaggi arrivano e i
processi rispondono.

## Clock vettoriali

I vector clock servono a distinguere causalità e concorrenza.

Prima si fissa una membership ordinata:

```text
P = [A, B, C]
```

Un vector clock ha una componente per processo:

```text
V(e) = [clock_A, clock_B, clock_C]
```

La componente `clock_A` parla degli eventi prodotti da `A`.
Solo `A` incrementa direttamente quella componente.

## Regole dei vector clock

Evento locale su `A`:

```text
A increments clock_A
```

Send da `A`:

```text
A increments clock_A
A attaches vector clock to message
```

Receive su `B`:

```text
B merges component-wise max
B increments clock_B
```

## Esempio vector clock

```text
P = [A, B, C]

A local event:     [1,0,0]
A sends m to B:    [2,0,0]
B before receive:  [0,1,0]

B merges:          max([0,1,0], [2,0,0]) = [2,1,0]
B receive event:   [2,2,0]
```

Il vettore finale dice che `B` conosce due eventi di `A`, due eventi di `B` e
nessun evento di `C`.

## Esempio vector clock: causalità

```text
a = [2,0,0]
b = [2,2,0]
```

`a <= b` componente per componente e almeno una componente cresce.

Quindi:

```text
a -> b
```

Il vettore di `b` include la conoscenza rappresentata da `a`.

## Esempio vector clock: concorrenza

```text
a = [1,0,0]
b = [0,1,0]
```

Nessuno dei due vettori domina l'altro.

Quindi:

```text
a || b
```

Questa è informazione progettuale: l'applicazione può decidere di mostrare un
conflitto, effettuare un merge oppure imporre un ordine artificiale.

## Confronto tra vector clock

```text
V(a) <= V(b)
```

se ogni componente di `V(a)` è minore o uguale alla corrispondente componente di
`V(b)`.

```text
V(a) < V(b)
```

se `V(a) <= V(b)` e almeno una componente è strettamente minore.

Se né `V(a) < V(b)` né `V(b) < V(a)`, gli eventi sono concorrenti.

## Causal delivery

Causal delivery distingue:

```text
receive(m) = il nodo riceve il messaggio
deliver(m) = il nodo lo rende visibile all'applicazione
```

Il layer può stare tra trasporto e applicazione:

```text
transport -> causal delivery -> application
```

Contratto:

```text
deliver solo quando le dipendenze causali sono soddisfatte
```

## Predicato di consegna

Qui bisogna distinguere due concetti.

Un vector clock generale:

```text
VC_event(e)
```

conta gli eventi del processo: computazioni locali, aggiornamenti di stato,
send e receive.

Il predicato semplice di causal delivery usato qui non usa direttamente quel
vector clock generale. Usa un vettore specializzato di messaggi:

```text
MC(m)
```

dove `MC(m)[k]` conta i messaggi di `k` che sono causalmente noti al messaggio
`m`.

Questo evita di confondere:

- eventi locali interni al processo;
- messaggi che il receiver può consegnare all'applicazione;
- dipendenze causali tra messaggi.

Ogni nodo ricevente mantiene inoltre un vettore locale `delivered`.

Se la membership è:

```text
P = [A, B, C]
```

allora:

```text
delivered = [delivered[A], delivered[B], delivered[C]]
```

`delivered[k]` significa:

```text
numero di messaggi inviati da k che questo nodo ha già consegnato
all'applicazione
```

Non è uno stato globale.
Non conta i messaggi soltanto ricevuti dalla rete.
Conta solo i messaggi già resi visibili all'applicazione locale.

Esempio dal punto di vista del nodo `C`:

```text
delivered[A] = 1  => C ha già consegnato 1 messaggio inviato da A
delivered[B] = 0  => C non ha ancora consegnato messaggi inviati da B
delivered[C] = 0  => C non conta messaggi propri consegnati da rete
```

Un messaggio `m` inviato da `s` con message vector `MC(m)` è consegnabile se:

```text
MC(m)[s] = delivered[s] + 1
for every k != s:
  MC(m)[k] <= delivered[k]
```

Se il predicato è falso, il messaggio resta in buffer.

La prima condizione dice che `m` è il prossimo messaggio atteso dal mittente
`s`.

La seconda condizione dice che tutte le cause conosciute da `m`, prodotte dagli
altri processi, sono già state consegnate localmente.

### Perché `=` e non `>`

In questo modello `MC(m)[s]` e `delivered[s]` parlano entrambi di messaggi del
mittente `s`.

Quindi:

```text
MC(m)[s] = delivered[s] + 1
```

significa:

```text
m è esattamente il prossimo messaggio atteso da s
```

Se usassimo:

```text
MC(m)[s] > delivered[s]
```

allora potremmo consegnare un messaggio più recente saltando un messaggio
precedente dello stesso mittente.

Esempio dal punto di vista di `C`:

```text
delivered[A] = 0
m2 inviato da A ha MC(m2)[A] = 2
```

Con `>` la condizione sarebbe vera, ma `C` consegnerebbe `m2` senza aver
consegnato `m1`.

Questo violerebbe l'ordine locale di `A`, che è una relazione di
happened-before:

```text
A sends m1 -> A sends m2
```

Se invece stiamo usando un vector clock generale `VC_event`, che conta anche
aggiornamenti locali e computazioni interne, allora questo predicato non è
applicabile così com'è.

Esempio:

```text
A local update      VC_event[A] = 1
A sends m1          VC_event[A] = 2
```

`m1` può essere il primo messaggio di `A`, ma `VC_event(m1)[A] = 2`.
Confrontarlo con `delivered[A] = 0` non dice che manchi un messaggio: dice che
nel clock di A esiste anche un evento locale.

In quel caso servono due informazioni distinte:

```text
VC_event(m)  = causalità tra eventi generali
seq_s(m)     = numero progressivo dei messaggi inviati da s
```

oppure bisogna modellare ogni aggiornamento locale rilevante come messaggio o
entry del log da consegnare.

## Traccia di causal delivery

Supponiamo tre nodi `A`, `B`, `C`.

```text
m1: A pubblica x
m2: B reagisce a x
```

Se `C` riceve `m2` prima di `m1`, il layer di causal delivery non consegna
subito `m2` all'applicazione.

```text
receive(m2) -> buffer
receive(m1) -> deliver(m1)
buffer check -> deliver(m2)
```

Safety:

```text
non consegnare una reazione prima della causa
```

Liveness:

```text
se le cause mancanti arrivano, il messaggio bufferizzato deve essere consegnato
```

## Sintesi

| Meccanismo | Domanda |
| --- | --- |
| Wall-clock locale | Che ora legge questo nodo? |
| Clock monotono | Quanto tempo è passato localmente? |
| Clock sincronizzato | In quale intervallo reale è avvenuto? |
| Happened-before | Quale relazione causale posso dimostrare? |
| Lamport clock | Quale timestamp rispetta la causalità nota? |
| Ordine totale Lamport | Quale ordine deterministico imposto? |
| Vector clock | Gli eventi sono causali o concorrenti? |
| Causal delivery | Posso consegnare questo messaggio ora? |
