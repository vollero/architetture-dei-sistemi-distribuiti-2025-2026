# Handout: Quorum, Versioni e Letture Stantie

## Obiettivo della tappa

La lezione precedente ha mostrato che heartbeat e timeout non bastano a
decidere in modo robusto chi possa scrivere.

Qui cambiamo prospettiva:

- invece di chiedere "chi e' il leader?";
- chiediamo "quante copie devono partecipare a una decisione?".

## Tre numeri fondamentali

Definiamo:

- `N`: numero totale di repliche;
- `W`: numero minimo di ack richiesti per completare una scrittura;
- `R`: numero minimo di repliche interrogate per completare una lettura.

Questi tre numeri definiscono il contratto del servizio piu' della sola API.

## Versioni

Per decidere quale valore sia piu' recente, ogni scrittura porta con se':

- un valore;
- una `version`.

La lettura non si limita a "chiedere un valore". Deve anche sapere quale delle
risposte osservate sia piu' aggiornata.

## Quorum debole

Con `W=1` e `R=1`:

- una scrittura puo' riuscire dopo un solo ack;
- una lettura puo' fermarsi alla prima replica disponibile.

Questo e' molto favorevole alla liveness, ma espone a letture stantie.

## Quorum forte

Con `N=3`, `W=2`, `R=2`:

- una scrittura deve toccare almeno due repliche;
- una lettura deve osservare almeno due repliche.

La regola importante e':

```text
R + W > N
```

Perche' garantisce intersezione tra l'insieme che ha visto l'ultima scrittura
e l'insieme consultato dalla lettura.

## Letture stantie

Una stale read nasce quando:

1. una scrittura recente ha raggiunto solo una parte delle repliche;
2. la lettura consulta un sottoinsieme che non include nessuna replica fresca;
3. il coordinator si ferma troppo presto.

Questo e' il caso tipico di `R=1`.

## Safety e liveness

### Safety

Quorum piu' forti migliorano la safety osservabile:

- riducono la probabilita' di leggere versioni vecchie;
- rendono piu' difendibile la nozione di commit.

### Liveness

Ma costano:

- una replica in meno puo' impedire il raggiungimento di `W`;
- una lettura puo' fallire se non raggiunge `R`.

## Esperimento consigliato

### Configurazione debole

1. avviare tre repliche;
2. avviare coordinator con `R=1`, `W=1`;
3. introdurre disponibilita' parziale;
4. osservare una lettura che non vede l'ultima versione.

### Configurazione forte

1. avviare coordinator con `R=2`, `W=2`;
2. ripetere l'esperimento;
3. osservare il miglioramento in consistenza e il costo in disponibilita'.

## Limite ancora aperto

In questo laboratorio una nuova versione viene prodotta da un coordinator
sotto controllo. Ma in generale due writer concorrenti possono generare:

- versioni concorrenti;
- ordini parziali;
- conflitti da riconciliare.

Questo prepara il terreno per ragionare su versioni piu' ricche e su scelte di
consistenza ancora piu' esplicite.

## Messaggio da portare a casa

Con i quorum il contratto del sistema non e' piu' descritto solo da ruoli
(`leader`, `follower`), ma anche da cardinalita':

- quante repliche servono per scrivere;
- quante servono per leggere;
- quale intersezione minima deve esistere tra i due insiemi.
