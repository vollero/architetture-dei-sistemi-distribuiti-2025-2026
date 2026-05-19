# Handout: Consenso Distribuito e Basic Paxos

## Perché serve consenso

I clock logici rispondono a domande di ordine:

```text
questo evento può aver causato quello?
quale ordine deterministico posso imporre?
questi eventi sono concorrenti?
```

Il consenso risponde a una domanda diversa:

```text
quale valore decidono insieme i nodi?
```

Nel KV store distribuito il consenso serve per decisioni come:

- leader corrente;
- entry di un log replicato;
- configurazione valida del cluster;
- proprietario di un lock distribuito;
- valore da usare durante recovery.

Esempio:

```text
log[42] = SET x 1
```

Se una replica decide `SET x 1` e un'altra decide `SET x 2` per lo stesso slot,
il sistema non ha più una storia condivisa.

## Specifica del consenso

Un insieme di processi propone valori e deve scegliere un solo risultato.

```text
propose(p, v) = il processo p propone v
learn(l, v)   = il learner l apprende v come valore scelto
```

### Validity

Solo valori proposti possono essere scelti e appresi.

```text
learn(l, v) => proposed(v)
```

### Agreement

Due learner non possono apprendere valori diversi.

```text
learn(l1, v1) and learn(l2, v2) => v1 = v2
```

### Termination

Idealmente, se un valore viene proposto e restano abbastanza processi corretti,
qualche learner prima o poi apprende un valore.

Nel modello asincrono con guasti questa proprietà non è garantibile in ogni
schedulazione. Paxos garantisce safety; la liveness richiede condizioni pratiche
favorevoli.

## Assunzioni di Basic Paxos

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

### Numero di processi

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

## Ruoli

### Client

Il client richiede una decisione.

```text
append log[42] = SET x 1
```

### Proposer

Il proposer prova a far scegliere un valore.

Ogni tentativo usa un proposal number univoco e ordinabile:

```text
n = (round, proposer_id)
```

Il proposal number non è il valore proposto e non è un clock fisico. Serve a
ordinare i tentativi.

### Acceptor

L'acceptor conserva stato persistente:

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

Il learner apprende il valore scelto quando osserva `ACCEPTED` da un quorum.

## Quorum

Con tre acceptor:

```text
A1, A2, A3
```

i quorum di maggioranza sono:

```text
{A1,A2}, {A1,A3}, {A2,A3}
```

Ogni quorum interseca ogni altro quorum.

Questa intersezione è il canale attraverso cui un round successivo può scoprire
memoria di un round precedente.

## Basic Paxos

Ogni istanza di Basic Paxos decide un solo valore.

Un round riuscito ha quattro passi logici:

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

Il proposer può proseguire solo se riceve promise da un quorum.

Regola:

```text
if nessuna promise contiene accepted_value:
    value = valore inizialmente voluto dal proposer
else:
    value = accepted_value associato al massimo accepted_n ricevuto
```

Questa regola impedisce a un proposer con numero più alto di cancellare la
memoria di un valore già accettato.

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

## Esecuzione senza conflitti

```text
P1 -> A1,A2: PREPARE((1,P1))
A1 -> P1: PROMISE((1,P1), none, none)
A2 -> P1: PROMISE((1,P1), none, none)

P1 -> A1,A2: ACCEPT((1,P1), SET x 1)
A1 -> learners: ACCEPTED((1,P1), SET x 1)
A2 -> learners: ACCEPTED((1,P1), SET x 1)
```

`A1` e `A2` sono un quorum, quindi `SET x 1` è scelto.

## Esecuzione con proposer successivo

Supponiamo che `A1` e `A2` abbiano già accettato:

```text
accepted_n = (1,P1)
accepted_value = SET x 1
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

Il quorum nuovo interseca il quorum precedente in `A2`, che riporta memoria del
valore già accettato.

## Round falliti e liveness

Un round può fallire se:

- più proposer competono;
- non arrivano promise da un quorum;
- non arrivano accepted da un quorum;
- un altro proposer ottiene promise con proposal number più alto;
- la rete perde o ritarda troppo i messaggi.

Il proposer può aprire un nuovo round con numero più alto.

Se i proposer continuano a disturbarsi, Basic Paxos può non progredire.
Per questo in pratica si usa spesso un leader stabile.

## Messaggio finale

Basic Paxos non ordina tutti gli eventi.

Basic Paxos decide un valore per una istanza.

La safety nasce da:

- quorum che si intersecano;
- memoria persistente degli acceptor;
- regola che obbliga il proposer a conservare il valore con `accepted_n` massimo.
