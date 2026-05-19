# Approfondimento: Basic Paxos

Questo documento segue la struttura della voce
[Paxos (computer science)](https://en.wikipedia.org/wiki/Paxos_(computer_science)):
consenso, assunzioni, proprietà, deployment tipico, ruoli e flusso dei messaggi
di Basic Paxos.

Il testo è adattato al corso e al KV store distribuito.

## Consenso

Il consenso è il problema di far concordare un gruppo di partecipanti su un solo
risultato.

Nel KV store distribuito:

```text
log[42] = SET x 1
```

deve essere vero per tutte le repliche corrette che apprendono la decisione.

Se per lo stesso slot una replica apprende `SET x 1` e un'altra apprende
`SET x 2`, il sistema non ha più una storia condivisa.

Basic Paxos decide un solo valore per una singola istanza:

```text
istanza i -> un valore scelto
```

Un log replicato usa molte istanze:

```text
istanza 40 -> log[40]
istanza 41 -> log[41]
istanza 42 -> log[42]
```

## Assunzioni

### Processi

I processi:

- possono procedere a velocità arbitraria;
- possono fallire;
- possono rientrare dopo un crash se conservano stato stabile;
- non mentono e non colludono per sovvertire il protocollo.

Basic Paxos non tollera guasti bizantini.

### Rete

La rete:

- è asincrona;
- può ritardare i messaggi arbitrariamente;
- può perdere, duplicare o riordinare messaggi;
- non corrompe messaggi in modo malevolo.

### Quanti processi servono

Con quorum di maggioranza, per tollerare `F` fallimenti simultanei servono
tipicamente:

```text
N = 2F + 1
```

Esempi:

```text
F = 1 -> N = 3
F = 2 -> N = 5
```

## Proprietà

### Validity

Solo valori proposti possono essere scelti e appresi.

```text
learned(v) => proposed(v)
```

### Agreement

Due learner non possono apprendere valori diversi.

```text
learned(l1, v1) and learned(l2, v2) => v1 = v2
```

### Termination

Nel modello asincrono con guasti Paxos non garantisce termination in ogni
schedulazione possibile. Garantisce safety; il progresso richiede condizioni
operative favorevoli.

## Deployment tipico

Nella pratica un processo può assumere più ruoli:

```text
proposer
acceptor
learner
```

Un client invia un comando a un leader. Il leader assegna il comando a una
istanza di consenso e avvia il protocollo verso gli acceptor.

Nel KV store:

```text
client -> leader: SET x 1
leader -> consenso per log[42]
learner -> log[42] = SET x 1
repliche -> applicano log[42]
```

## Ruoli

### Client

Richiede una decisione.

### Proposer

Tenta di far scegliere un valore.

Ogni tentativo usa un proposal number univoco e ordinabile:

```text
n = (round, proposer_id)
```

Il proposal number non è il valore proposto e non è un clock fisico.

### Acceptor

Conserva stato persistente:

```text
promised_n
accepted_n
accepted_value
```

Significato:

- `promised_n`: massimo proposal number per cui l'acceptor ha promesso di non
  accettare proposte precedenti;
- `accepted_n`: proposal number dell'ultimo valore accettato;
- `accepted_value`: valore associato a `accepted_n`.

### Learner

Apprende il valore scelto quando osserva `ACCEPTED` da un quorum.

## Quorum

Con tre acceptor:

```text
A1, A2, A3
```

i quorum di maggioranza sono:

```text
{A1,A2}
{A1,A3}
{A2,A3}
```

Ogni quorum interseca ogni altro quorum.

L'intersezione è il meccanismo che porta memoria da un round precedente a un
round successivo.

## Basic Paxos

Un round riuscito ha quattro passi:

```text
Phase 1a: Prepare
Phase 1b: Promise
Phase 2a: Accept
Phase 2b: Accepted
```

### Phase 1a: Prepare

Il proposer invia:

```text
PREPARE(n)
```

ad almeno un quorum di acceptor.

Il valore applicativo non è necessario in questa fase.

### Phase 1b: Promise

Un acceptor riceve `PREPARE(n)`.

Se `n` è maggiore dei proposal number già visti, risponde:

```text
PROMISE(n, accepted_n, accepted_value)
```

e promette:

```text
non accetterò richieste con proposal number minore di n
```

Inoltre non concederà una nuova promise a `PREPARE` con numero non maggiore
di `n`.

Se non aveva accettato nulla:

```text
PROMISE(n, none, none)
```

Se `n` non è abbastanza alto, l'acceptor può ignorare o rifiutare.

### Scelta del valore

Il proposer può proseguire solo dopo promise da un quorum.

Regola:

```text
if nessuna promise contiene accepted_value:
    value = valore inizialmente voluto dal proposer
else:
    value = accepted_value associato al massimo accepted_n ricevuto
```

### Phase 2a: Accept

Il proposer invia:

```text
ACCEPT(n, value)
```

a un quorum.

### Phase 2b: Accepted

Un acceptor accetta `ACCEPT(n, value)` se non ha già promesso di considerare
solo proposte con numero maggiore di `n`.

Se accetta:

```text
accepted_n = n
accepted_value = value
```

e invia:

```text
ACCEPTED(n, value)
```

Quando un learner riceve `ACCEPTED(n, value)` da un quorum, apprende il valore.

## Esempio senza conflitti

```text
P1 -> A1,A2: PREPARE((1,P1))
A1 -> P1: PROMISE((1,P1), none, none)
A2 -> P1: PROMISE((1,P1), none, none)

P1 -> A1,A2: ACCEPT((1,P1), SET x 1)
A1 -> learners: ACCEPTED((1,P1), SET x 1)
A2 -> learners: ACCEPTED((1,P1), SET x 1)
```

`A1` e `A2` sono un quorum, quindi `SET x 1` è scelto.

## Esempio con proposer successivo

Stato precedente:

```text
A1 accepted_n=(1,P1), accepted_value=SET x 1
A2 accepted_n=(1,P1), accepted_value=SET x 1
A3 accepted_n=none,   accepted_value=none
```

Arriva `P2`:

```text
n = (2,P2)
valore desiderato = SET x 2
```

`P2` invia:

```text
P2 -> A2,A3: PREPARE((2,P2))
```

Risposte:

```text
A2 -> P2: PROMISE((2,P2), (1,P1), SET x 1)
A3 -> P2: PROMISE((2,P2), none, none)
```

`P2` deve proporre:

```text
ACCEPT((2,P2), SET x 1)
```

e non:

```text
ACCEPT((2,P2), SET x 2)
```

## Round falliti

Un round può fallire se:

- più proposer competono;
- non arrivano promise da un quorum;
- non arrivano accepted da un quorum;
- un altro proposer ottiene promise con proposal number più alto;
- la rete perde o ritarda troppo i messaggi.

Si può aprire un nuovo round con proposal number più alto.

Se il conflitto continua per sempre, Basic Paxos può non progredire.

## Perché la safety regge

La safety dipende da tre elementi:

- i quorum si intersecano;
- gli acceptor riportano `accepted_n` e `accepted_value` nelle promise;
- il proposer deve scegliere il valore associato al massimo `accepted_n`.

Un proposer successivo può superare round precedenti, ma non può cancellare
arbitrariamente un valore che potrebbe già essere stato scelto.
