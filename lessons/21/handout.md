# Handout: Sincronizzazione, Temporalita' e Clock Logici

## Perche' il tempo e' un problema distribuito

In un programma sequenziale siamo abituati a pensare che esista un "prima" e un
"dopo" naturale.

In un sistema distribuito questa intuizione si rompe:

- ogni nodo esegue localmente;
- i messaggi viaggiano con ritardi variabili;
- gli orologi fisici non sono perfettamente sincronizzati;
- due eventi possono essere indipendenti.

Il problema non e' solo sapere l'ora.

Il problema e':

> quale ordine possiamo affermare con certezza?

## Scenario iniziale

Due nodi, `A` e `B`.

```text
A scrive x=1
B legge x
```

Domanda:

```text
la lettura di B e' avvenuta prima o dopo la scrittura di A?
```

Se `B` ha ricevuto un messaggio causato dalla scrittura di `A`, possiamo dire
qualcosa.

Se non esiste comunicazione tra i due eventi, l'ordine potrebbe essere solo una
scelta artificiale.

## Tempo fisico locale

Ogni nodo puo' fare:

```python
time.time()
```

e assegnare un timestamp agli eventi.

Questo e' utile per:

- logging;
- timeout;
- misure approssimate;
- audit umano.

Ma non basta per stabilire causalita'.

### Problema: clock skew

Il clock di `A` puo' essere avanti rispetto al clock di `B`.

Allora nei log potremmo vedere:

```text
B: receive message at 10:00:00.100
A: send message    at 10:00:00.200
```

Sembra che il messaggio sia stato ricevuto prima di essere inviato.
Il problema non e' il messaggio: e' il modello temporale usato per leggerlo.

## Sincronizzazione fisica

Meccanismi come NTP e PTP cercano di ridurre la distanza tra gli orologi.

Sono utili, ma non cancellano l'incertezza.

In pratica, una lettura del tempo fisico va interpretata come:

```text
il tempo reale e' probabilmente dentro un intervallo
```

non come un punto matematicamente perfetto.

Questo e' importante per:

- lease temporali;
- timeout;
- sistemi di lock basati su scadenza;
- database che espongono timestamp reali;
- sistemi di audit.

## Happened-before

Lamport introduce una relazione causale, non fisica.

Scriviamo:

```text
a -> b
```

per dire:

```text
a happened-before b
```

Regole:

1. se `a` e `b` sono eventi dello stesso processo e `a` avviene prima localmente
   di `b`, allora `a -> b`;
2. se `a` e' l'invio di un messaggio e `b` e' la ricezione dello stesso messaggio,
   allora `a -> b`;
3. la relazione e' transitiva.

Se non vale `a -> b` e non vale `b -> a`, allora `a` e `b` sono concorrenti.

## Clock logico di Lamport

Un clock di Lamport e' un contatore.

Regole operative:

```text
evento locale: clock = clock + 1
send:          clock = clock + 1, allega clock al messaggio
receive:       clock = max(clock_locale, clock_messaggio) + 1
```

Garanzia:

```text
se a -> b, allora L(a) < L(b)
```

Questa e' una garanzia di consistenza causale dei timestamp.

Limite:

```text
L(a) < L(b) non implica a -> b
```

Il clock di Lamport non distingue sempre causalita' e concorrenza.

## Esempio ragionato

```text
A: local event      L=1
A: send m to B      L=2
B: receive m        L=max(0,2)+1=3
B: local event      L=4
```

Possiamo dire:

```text
A send m -> B receive m -> B local event
```

Il clock cresce coerentemente con la causalita'.

## Ordine totale con Lamport

Per alcuni algoritmi serve ordinare tutti gli eventi, anche quelli concorrenti.

Si puo' usare:

```text
(lamport_time, process_id)
```

Esempio:

```text
(5, A) < (5, B)
```

se decidiamo che `A < B`.

Questo ordine e' utile, ma bisogna ricordare:

- e' deterministico;
- e' condivisibile da tutti;
- non dimostra che l'evento di `A` abbia causato quello di `B`.

## Clock vettoriali

I clock vettoriali estendono l'idea.

Con tre processi:

```text
[clock_A, clock_B, clock_C]
```

Ogni processo incrementa la propria componente.
Quando riceve un messaggio, fa il massimo componente per componente.

Con i vector clock possiamo distinguere:

- `v1 < v2`: evento 1 happened-before evento 2;
- `v2 < v1`: evento 2 happened-before evento 1;
- vettori non confrontabili: eventi concorrenti.

Costo:

- piu' metadata;
- serve conoscere i processi;
- gestione piu' difficile con membership dinamica.

## Forme di sincronizzazione sensate

### Sincronizzazione fisica

Usare clock fisici allineati entro una certa incertezza.

Ha senso per:

- scadenze;
- lease;
- SLA;
- audit;
- timeout.

### Sincronizzazione logica

Usare messaggi e contatori per rispettare causalita'.

Ha senso per:

- logging distribuito;
- causal delivery;
- debug;
- mutua esclusione distribuita;
- ordinamento di update.

### Sincronizzazione tramite coordinatore

Un nodo assegna sequenze o timestamp.

Ha senso per:

- ordine totale semplice;
- sistemi piccoli;
- prototipi didattici.

Limite:

- collo di bottiglia;
- single point of failure;
- disponibilita' ridotta se il coordinatore non e' raggiungibile.

### Sincronizzazione tramite quorum o consenso

Un insieme di nodi concorda l'ordine o la validita' di un evento.

Ha senso per:

- commit distribuiti;
- log replicati;
- elezione leader;
- configurazioni critiche.

Costo:

- piu' messaggi;
- latenza maggiore;
- comportamento piu' complesso in caso di partizioni.

## Perche' i clock non bastano sempre

I clock logici rispondono a domande di ordine:

- questo evento puo' aver causato quello?
- possiamo imporre un ordine totale deterministico?
- due eventi sono concorrenti?

Ma ci sono casi in cui il problema non e' solo ordinare eventi.

Esempio:

```text
Replica A vuole scegliere: primary = node1
Replica B vuole scegliere: primary = node2
Replica C riceve messaggi in ordine diverso
```

Qui serve che il sistema scelga un solo valore condiviso.

Un timestamp puo' aiutare a ordinare le proposte, ma non basta da solo a
garantire che due gruppi diversi di nodi non decidano valori diversi.

Questa e' la motivazione del consenso.

## Paxos: problema risolto

Paxos risolve il problema del consenso single-decree:

> un insieme di nodi deve scegliere un solo valore, anche se alcuni messaggi
> arrivano in ritardo, alcuni proposer competono e alcuni nodi possono non
> rispondere.

Esempi di valori da scegliere:

- chi e' il leader;
- quale comando entra nella prossima posizione del log;
- quale configurazione del cluster e' valida;
- quale valore viene deciso per una chiave in un conflitto.

Paxos non serve a leggere l'ora.
Serve a far convergere piu' nodi sulla stessa decisione.

La descrizione completa, con modello, stato formale, invarianti e argomento di
correttezza, e' in [Approfondimento su Paxos](./paxos.md).

## Ruoli in Paxos

La descrizione classica distingue tre ruoli.

### Proposer

Propone un valore.
Deve usare un proposal number unico e ordinabile.

### Acceptor

Vota secondo regole precise.
La safety di Paxos dipende dagli acceptor e dai quorum.
Ogni acceptor conserva:

```text
promised_n
accepted_n
accepted_value
```

### Learner

Scopre quale valore e' stato scelto.
In molti esempi didattici, proposer e learner coincidono.

## Specifica desiderata di Paxos

Paxos deve garantire almeno queste proprieta':

### Validity

Solo un valore proposto puo' essere scelto.

### Agreement

Non possono essere scelti due valori diversi.

### Learnability

Se un learner corretto apprende una decisione, deve apprendere il valore scelto.

La proprieta' piu' importante per questa lezione e' `Agreement`.
E' quella che impedisce split brain logici, doppie configurazioni e due entry
diverse nella stessa posizione di log.

## Quorum

Paxos usa quorum di maggioranza.

Con `N=3` acceptor:

```text
quorum = 2
```

Con `N=5`:

```text
quorum = 3
```

La proprieta' fondamentale e':

```text
due quorum di maggioranza si intersecano sempre
```

Questa intersezione e' cio' che impedisce a due valori diversi di essere scelti
indipendentemente.

Formalmente, se `Q` e' l'insieme dei quorum:

```text
for every q1, q2 in Q:
  q1 intersection q2 != empty
```

Questa proprieta' e' la base dell'argomento di correttezza.

## Numeri di proposta

Ogni proposta ha un numero crescente e unico.

Esempio:

```text
(round=7, proposer=P2)
```

Il numero di proposta non e' un clock fisico.
E' un identificatore ordinabile che permette agli acceptor di distinguere
proposte vecchie e nuove.

Regola pratica:

- un acceptor puo' promettere di non accettare piu' proposte minori di una certa proposta;
- un proposer con numero piu' alto puo' superare proposer precedenti;
- ma non puo' ignorare valori gia' accettati.

In forma astratta:

```text
proposal_number = (round, proposer_id)
```

L'ordine e' lessicografico. Il `proposer_id` serve a rendere unici numeri con lo
stesso round.

## Fase 1: Prepare / Promise

Il proposer invia:

```text
PREPARE(n)
```

agli acceptor.

Un acceptor risponde con:

```text
PROMISE(n, last_accepted)
```

se non ha gia' promesso di ignorare proposte fino a un numero maggiore.

La promessa significa:

```text
non accettero' proposte con numero minore di n
```

Se l'acceptor aveva gia' accettato un valore, lo comunica.

## Fase 2: Accept / Accepted

Se il proposer riceve promise da un quorum, sceglie il valore da mandare in
fase 2.

Regola cruciale:

- se nessun acceptor del quorum aveva gia' accettato valori, il proposer puo'
  proporre il proprio valore;
- se qualcuno aveva gia' accettato un valore, il proposer deve riproporre il
  valore associato alla proposta accettata con numero piu' alto.

Poi invia:

```text
ACCEPT(n, value)
```

Un acceptor accetta se non ha promesso una proposta piu' alta.

Quando un valore e' accettato da un quorum, e' scelto.

## Perche' questa regola e' necessaria

Supponiamo che un valore `v1` sia gia' stato accettato da un quorum, ma il
proposer che lo aveva proposto si fermi prima di comunicarlo a tutti.

Un nuovo proposer arriva con numero piu' alto e vuole proporre `v2`.

Se potesse ignorare la storia precedente, il sistema rischierebbe due decisioni:

```text
quorum precedente sceglie v1
nuovo quorum sceglie v2
```

Paxos lo impedisce perche' i quorum si intersecano.
Nel quorum del nuovo proposer ci sara' almeno un acceptor che conosce `v1`.
Quel valore deve essere riproposto.

Il punto formale e':

```text
se v e' stato scelto da un quorum q,
ogni quorum successivo q' interseca q
```

Quindi una proposta successiva deve poter incontrare memoria del valore
precedente. La fase `PROMISE` serve esattamente a trasportare questa memoria.

## Safety e liveness di Paxos

### Safety

La proprieta' centrale e':

```text
non possono essere scelti due valori diversi
```

Questa proprieta' deve valere anche con:

- proposer concorrenti;
- messaggi ritardati;
- retry;
- acceptor che rispondono solo a una parte dei messaggi.

### Liveness

Paxos base non garantisce progresso in qualunque schedulazione.

Se due proposer competono continuamente con numeri crescenti, possono disturbarsi
a vicenda.

Per ottenere progresso pratico, spesso si introduce un leader stabile:

- un proposer principale;
- meno competizione;
- Multi-Paxos per decidere molte posizioni di log.

## Paxos e clock logici

Il collegamento con la prima parte della lezione e':

- Lamport clock ordina eventi rispetto alla causalita';
- ordine totale con Lamport impone una sequenza deterministica;
- Paxos fa decidere a piu' nodi quale valore entra in una posizione condivisa.

In altre parole:

```text
clock logico: quale ordine posso rappresentare?
Paxos: quale valore possiamo decidere insieme?
```

Sono problemi collegati, ma non equivalenti.

## Esempio da eseguire

Il laboratorio contiene:

```bash
python3 labs/logical_clocks/paxos_single_decree.py
```

Lo script mostra:

- tre acceptor;
- quorum di due;
- due proposer concorrenti;
- un primo valore gia' accettato;
- un secondo proposer che deve conservare quel valore.

Il punto da osservare:

```text
un proposer con numero piu' alto non puo' scegliere liberamente un valore nuovo
se scopre che un valore precedente potrebbe gia' essere stato scelto.
```

## Scelte implementative

Per dare temporalita' certa a eventi e azioni bisogna chiarire prima la domanda.

### Voglio ordinare eventi locali

Usare un contatore locale monotono.

### Voglio rispettare causalita' tra messaggi

Usare Lamport clock.

### Voglio un ordine totale riproducibile

Usare Lamport clock piu' process id.

### Voglio rilevare concorrenza

Usare vector clock.

### Voglio scadenze reali

Usare clock fisici sincronizzati, dichiarando l'incertezza.

### Voglio una decisione condivisa resistente a proposer concorrenti

Usare un protocollo di consenso, per esempio Paxos.

## Domande da portare in aula

1. Se due eventi hanno timestamp fisico diverso, siamo sicuri del loro ordine causale?
2. Se due eventi hanno timestamp Lamport diverso, siamo sicuri che uno abbia causato l'altro?
3. Quando e' accettabile imporre un ordine totale artificiale?
4. Che cosa succede se un nodo riceve un messaggio con timestamp logico molto piu' alto?
5. Quando il costo dei vector clock e' giustificato?
6. Quando un ordine totale non basta e serve consenso?
7. Perche' Paxos costringe un proposer a riproporre un valore gia' accettato?

## Collegamento con il KV store

Nel KV store i clock possono essere usati per:

- ordinare update replicati;
- riconoscere scritture concorrenti;
- decidere una regola deterministicamente condivisa di conflitto;
- annotare log distribuiti;
- ricostruire una storia plausibile durante il debugging;
- implementare causal read o causal delivery;
- scegliere un leader;
- decidere la prossima entry di un log replicato.

Esempio:

```text
SET x 1 timestamp=(7,A)
SET x 2 timestamp=(7,B)
```

L'ordine totale puo' scegliere un vincitore.

Ma se i due eventi sono concorrenti, un sistema piu' ricco potrebbe voler
conservare il conflitto invece di nasconderlo.

## Messaggio finale

Il tempo in un sistema distribuito non e' un dato unico.

E' un contratto:

- tempo fisico per scadenze e misure;
- tempo logico per causalita';
- ordine totale per decidere;
- vector clock per riconoscere concorrenza;
- consenso per scegliere un valore condiviso.

La domanda progettuale corretta non e':

```text
che timestamp metto?
```

ma:

```text
quale proprieta' temporale voglio promettere?
```
