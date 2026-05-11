# Contratto Temporale: Eventi, Ordine e Clock Logici

Questa lezione tratta la temporalita' come parte del contratto di un sistema
distribuito.

## Problema

In un sistema distribuito non esiste, in generale, un orologio globale affidabile
e immediatamente osservabile da tutti i nodi.

Ogni nodo puo' avere:

- un clock fisico locale;
- una latenza diversa verso gli altri nodi;
- messaggi in transito;
- eventi concorrenti non ordinabili causalmente.

Quindi una domanda apparentemente semplice:

```text
quale evento e' avvenuto prima?
```

puo' avere risposte diverse a seconda del modello temporale adottato.

## Modelli possibili

### Tempo fisico locale

Ogni nodo usa il proprio orologio.

Pregio:

- semplice;
- vicino all'intuizione umana;
- utile per log e timeout.

Limite:

- clock skew;
- clock drift;
- l'orologio puo' andare avanti con velocita' leggermente diverse;
- l'ordine fisico osservato nei log puo' contraddire la causalita' reale.

### Tempo fisico sincronizzato

I nodi cercano di allineare i clock tramite meccanismi come NTP, PTP o servizi
di tempo controllati.

Pregio:

- utile per timestamp reali, audit, scadenze e misure di latenza.

Limite:

- la sincronizzazione non e' perfetta;
- bisogna ragionare con intervalli di incertezza;
- non basta per dedurre sempre causalita'.

### Clock logico di Lamport

Ogni nodo mantiene un contatore logico.

Regole:

1. prima di ogni evento locale, incrementa il contatore;
2. ogni messaggio porta il timestamp logico del mittente;
3. alla ricezione, il nodo aggiorna:

```text
clock = max(clock_locale, clock_ricevuto) + 1
```

Garanzia:

```text
se a happened-before b, allora L(a) < L(b)
```

Limite:

```text
L(a) < L(b) non implica necessariamente a happened-before b
```

### Ordine totale con Lamport

Si puo' ottenere un ordine totale ordinando le coppie:

```text
(lamport_time, process_id)
```

Pregio:

- ogni evento ha una posizione ordinabile;
- utile per code distribuite, log merge, mutual exclusion.

Limite:

- l'ordine totale puo' ordinare artificialmente eventi concorrenti;
- non dimostra causalita'.

### Clock vettoriale

Ogni nodo mantiene un vettore con una componente per processo.

Pregio:

- permette di distinguere causalita' e concorrenza;
- se due vettori non sono confrontabili, gli eventi sono concorrenti.

Limite:

- metadata piu' grandi;
- serve conoscere o gestire l'insieme dei processi;
- piu' complesso da usare in sistemi dinamici.

## Contratti temporali utili

Un sistema distribuito puo' promettere cose diverse.

### Contratto 1: ordinamento locale

Ogni nodo ordina correttamente i propri eventi locali.

Esempio:

```text
eventi prodotti dallo stesso nodo hanno timestamp crescenti
```

### Contratto 2: causalita' sui messaggi

Se un evento causa l'invio di un messaggio e la ricezione del messaggio causa un
altro evento, il secondo evento deve avere timestamp logico maggiore.

### Contratto 3: ordine totale riproducibile

Tutti i nodi possono ordinare gli stessi eventi nello stesso modo usando:

```text
(lamport_time, process_id)
```

### Contratto 4: rilevazione della concorrenza

Il sistema deve poter dire:

```text
questi due eventi non sono ordinabili causalmente
```

Questo richiede clock vettoriali o metadata equivalenti.

## Collegamento con i laboratori precedenti

I clock logici aiutano a discutere:

- ordine degli update in replica;
- conflitti tra scritture concorrenti;
- debug di interleaving multithread o distribuiti;
- causal delivery dei messaggi;
- mutua esclusione distribuita;
- ricostruzione di una storia plausibile dai log.

## Punto chiave

Un timestamp non e' neutro.

Ogni timestamp risponde a una domanda precisa:

- "quando e' successo sul clock locale?"
- "da cosa dipende causalmente?"
- "in quale ordine totale lo vogliamo processare?"
- "possiamo dimostrare che due eventi sono concorrenti?"

Se il contratto non dice quale domanda il timestamp sta rispondendo, il sistema
sta esponendo un dato ambiguo.

