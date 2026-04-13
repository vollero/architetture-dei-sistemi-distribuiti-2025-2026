# Handout: Replica Primary-Secondary, Commit e Letture Stantie

## Obiettivo della tappa

Finora il problema centrale era:

- prima il contratto del nodo singolo;
- poi la safety in presenza di concorrenza;
- poi la durabilita' locale dopo crash.

Ora il focus si sposta su una domanda nuova:

> che cosa significa che una scrittura e' stata davvero completata quando
> esistono piu' copie dello stato?

## Un solo comando, due semantiche diverse

Il client continua a inviare:

```text
SET course ads
```

Ma il significato di `OK` puo' cambiare molto.

### Replica asincrona

Sequenza astratta:

```text
ApplyPrimary -> ReplyOK -> ReplicateLater
```

Qui il client sa che il primary ha applicato l'update. Non sa ancora se il
secondario l'abbia visto.

### Replica sincrona

Sequenza astratta:

```text
SendReplica -> WaitAck -> ApplyPrimary -> ReplyOK
```

Qui `OK` significa qualcosa di piu' forte: almeno il primary e il secondario
hanno concordato sull'update.

## Commit locale contro commit replicato

Questa lezione serve a far emergere una distinzione importante:

- commit locale: l'update e' presente sul primary;
- commit replicato: l'update e' presente anche sul secondario.

Se il contratto verso il client non esplicita quale dei due stia promettendo,
la semantica della `SET` resta ambigua.

## Letture dal secondario

Una volta introdotto il secondario, anche `GET` cambia significato operativo.

Due letture con la stessa sintassi:

```text
GET course
```

possono produrre risposte diverse se una legge dal primary e l'altra dal
secondario.

Questo non e' necessariamente un bug. Puo' essere una precisa conseguenza del
protocollo di replica.

## Variante async: perche' nascono letture stantie

Nel primary async la replica avviene dopo la risposta positiva al client.

Sequenza:

```text
Primary: apply local -> reply OK
Secondary: receive update later
Client: read from secondary before apply
```

Il secondario puo' quindi rispondere:

```text
NOT_FOUND
```

anche se il client ha gia' visto:

```text
OK
```

dal primary.

La proprieta' violata non e' la coerenza locale del nodo, ma l'aspettativa del
client di vedere subito lo stesso stato su tutte le copie.

## Variante sync: cosa migliora

Nel primary sync la scrittura e' piu' costosa ma piu' forte:

1. il primary invia l'update;
2. il secondario applica e risponde `ACK`;
3. il primary completa e risponde `OK`.

In questa variante, subito dopo `OK`, una lettura dal secondario dovrebbe
vedere lo stesso aggiornamento.

## Safety e liveness della replica

### Safety

Esempi di safety in questa tappa:

- il secondario non applica update diversi da quelli ordinati dal primary;
- il primary sync non promette una scrittura non ancora ackata dal secondario;
- i due nodi convergono sullo stesso stato se non ci sono nuovi update.

### Liveness

Costi introdotti:

- la replica sincrona aggiunge latenza alla scrittura;
- se il secondario e' giu', il primary sync non puo' fare progresso sulle
  scritture;
- la replica asincrona migliora disponibilita' apparente ma indebolisce il
  contratto osservabile.

## Esperimento 1: stale read

Configurazione:

- secondario con `--apply-delay 1.0`;
- primary async.

Passi:

1. `SET course ads` sul primary;
2. lettura immediata `GET course` sul secondario;
3. seconda lettura dopo circa un secondo.

L'output atteso rende visibile il lag di replica.

## Esperimento 2: secondary down

Passi:

1. fermare il secondario;
2. inviare `SET course ads` al primary async;
3. ripetere sul primary sync.

Osservazione attesa:

- il primary async puo' ancora rispondere `OK`;
- il primary sync deve fallire.

Questa differenza e' il cuore del trade-off consistenza/liveness della tappa.

## Split brain: il problema che ancora non stiamo risolvendo

Questa lezione introduce anche il vocabolario giusto per la tappa successiva.

Domanda:

> cosa succede se due nodi credono entrambi di essere primary?

In quel caso non basta piu' parlare di replica. Serve:

- rilevare guasti;
- coordinare i ruoli;
- impedire aggiornamenti divergenti.

Per ora non lo risolviamo. Ma e' importante nominare esplicitamente il rischio.

## Messaggio da portare a casa

Con un solo nodo il contratto di `SET` dipendeva da RAM, lock e disco locale.

Con due nodi il contratto dipende anche da:

- quando la replica viene inviata;
- quando viene ackata;
- da quale copia arrivano le letture.

La stessa API resta quasi immutata, ma il suo contenuto semantico continua a
spostarsi con l'architettura.
