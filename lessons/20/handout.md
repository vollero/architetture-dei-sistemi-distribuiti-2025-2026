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

## Domande da portare in aula

1. Se due eventi hanno timestamp fisico diverso, siamo sicuri del loro ordine causale?
2. Se due eventi hanno timestamp Lamport diverso, siamo sicuri che uno abbia causato l'altro?
3. Quando e' accettabile imporre un ordine totale artificiale?
4. Che cosa succede se un nodo riceve un messaggio con timestamp logico molto piu' alto?
5. Quando il costo dei vector clock e' giustificato?

## Collegamento con il KV store

Nel KV store i clock possono essere usati per:

- ordinare update replicati;
- riconoscere scritture concorrenti;
- decidere una regola deterministicamente condivisa di conflitto;
- annotare log distribuiti;
- ricostruire una storia plausibile durante il debugging;
- implementare causal read o causal delivery.

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
- vector clock per riconoscere concorrenza.

La domanda progettuale corretta non e':

```text
che timestamp metto?
```

ma:

```text
quale proprieta' temporale voglio promettere?
```

