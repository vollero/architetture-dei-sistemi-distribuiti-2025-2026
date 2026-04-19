# Handout: Heartbeat, Timeout, Failover e Split Brain

## Obiettivo della tappa

La replica primary-secondary della lezione precedente lasciava aperta una
domanda inevitabile:

> chi decide se il primary esiste ancora?

Per affrontarla introduciamo:

- heartbeat dal leader al follower;
- timeout di sospetto;
- promozione del follower;
- osservazione diretta del rischio di split brain.

## Heartbeat non significa prova di vita assoluta

Un heartbeat regolare suggerisce che il leader sia vivo.

L'assenza di heartbeat, pero', non prova in modo definitivo il crash. Puo'
anche significare:

- ritardo di rete;
- perdita temporanea di messaggi;
- blocco parziale del processo;
- partizione di rete.

Questa distinzione e' il cuore della lezione: il timeout produce un sospetto,
non una verita' assoluta.

## Failover a due nodi

Nel laboratorio usiamo una coppia:

- nodo A inizialmente primary;
- nodo B inizialmente secondary.

Il primary invia heartbeat. Se il secondary non ne riceve entro una soglia,
si promuove.

Sequenza astratta:

```text
LeaderAlive -> Heartbeat -> FollowerStable
FollowerNoHeartbeat -> Timeout -> PromoteToPrimary
```

## Perche' il failover funziona... fino a un certo punto

Se il primary crasha davvero, il meccanismo e' utile:

- il secondary si accorge dell'assenza di heartbeat;
- si promuove;
- il sistema torna ad avere un nodo scrivibile.

Dal punto di vista della liveness, questo e' un progresso.

## Split brain

Il problema nasce quando il vecchio primary non e' davvero morto ma smette di
farsi percepire come tale dal follower.

Esempio:

```text
A continua a vivere ma smette di inviare heartbeat
B non riceve heartbeat e si promuove
A resta convinto di essere primary
```

Ora entrambi possono accettare scritture.

Questo e' split brain: due autorita' concorrenti sullo stesso servizio.

## Safety e liveness

### Liveness

Il timeout aiuta la liveness:

- evita di restare bloccati per sempre in attesa del leader;
- permette al follower di fare progresso.

### Safety

Ma lo stesso timeout mette a rischio la safety:

- un leader puo' essere dichiarato morto troppo presto;
- due nodi possono accettare scritture divergenti;
- il sistema non ha piu' una nozione univoca di "stato corretto".

Questa e' la tensione centrale della tappa.

## Esperimento consigliato

### Failover pulito

1. avviare A come primary e B come secondary;
2. osservare `STATUS`;
3. eseguire `CRASH` su A;
4. attendere il timeout;
5. verificare che B diventi primary.

### Split brain volontario

1. avviare A e B;
2. eseguire `PAUSE_HEARTBEATS` su A e su B;
3. attendere la promozione di B;
4. osservare la fase in cui entrambi possono ritenersi leader;
5. provare scritture e discutere la fragilita' del sistema.

Qui il sistema resta vivo, ma l'unicita' del leader non e' piu' difesa in modo robusto.

## Perche' due nodi non bastano

Con due nodi non esiste una maggioranza indipendente che possa decidere chi ha
ragione quando i ruoli si confondono.

Per questo la tappa successiva introdurra':

- piu' repliche;
- quorum di lettura e scrittura;
- una nozione piu' robusta di decisione distribuita.

## Messaggio da portare a casa

Un failover basato solo su heartbeat e timeout puo' migliorare la continuita'
del servizio, ma non basta a difendere l'unicita' del leader.

La domanda "chi puo' scrivere?" richiede un criterio piu' forte di un semplice
timer locale.
