# Approfondimento: Paxos Single-Decree

## Perche' serve Paxos

I clock logici aiutano a ordinare eventi.

Paxos affronta un problema diverso:

> piu' nodi devono decidere lo stesso valore, anche se messaggi arrivano in
> ordine diverso, alcuni nodi non rispondono e piu' proposer competono.

Esempi:

- scegliere un leader;
- scegliere la prossima entry di un log replicato;
- scegliere la configurazione valida del cluster;
- decidere quale valore accettare in caso di conflitto.

Un ordine totale sui messaggi puo' aiutare, ma non basta.
Il rischio e' che due gruppi diversi di nodi accettino due valori diversi e che
il sistema non abbia piu' una singola storia condivisa.

## Rischio senza consenso

Supponiamo tre nodi che devono decidere il leader.

```text
A1 accetta leader=P1
A2 accetta leader=P1
A2 accetta leader=P2
A3 accetta leader=P2
```

Se il protocollo non impedisce queste combinazioni, due osservatori potrebbero
concludere:

```text
quorum {A1,A2} ha scelto P1
quorum {A2,A3} ha scelto P2
```

Questo rompe la safety: il sistema ha scelto due valori.

Paxos impedisce questa situazione imponendo regole su:

- quorum;
- numeri di proposta;
- memoria degli acceptor;
- valore che un proposer puo' proporre dopo aver letto le promise.

## Specifica desiderata

Nel Paxos single-decree vogliamo decidere un solo valore.

### Safety

1. Solo valori proposti possono essere scelti.
2. Al massimo un valore puo' essere scelto.
3. Se un valore e' scelto, ogni learner corretto che apprende una decisione deve apprendere quel valore.

La proprieta' centrale e' la seconda:

```text
non possono essere scelti due valori diversi
```

### Liveness

La liveness minima desiderata e':

```text
se un proposer stabile riesce a comunicare con un quorum di acceptor,
prima o poi un valore viene scelto
```

Paxos base non garantisce progresso sotto competizione infinita tra proposer.
Per questo, nei sistemi reali, si tende a stabilizzare un leader e si arriva a
Multi-Paxos.

## Modello

Assumiamo:

- messaggi asincroni;
- messaggi che possono arrivare in ritardo o essere persi;
- nodi che possono fermarsi e non rispondere;
- nodi non bizantini, cioe' non mentono e non inventano stati;
- storage locale degli acceptor abbastanza stabile da ricordare promise e accept dopo retry.

Paxos classico tollera crash-stop, non nodi malevoli.

## Ruoli

### Proposer

Un proposer prova a far scegliere un valore.

Mantiene o genera un proposal number unico e crescente:

```text
n = (round, proposer_id)
```

### Acceptor

Un acceptor conserva due pezzi di stato:

```text
promised_n
accepted_n
accepted_value
```

Il suo compito e' rispettare le promise e non accettare proposte vecchie.

### Learner

Un learner apprende il valore scelto osservando accept da un quorum.

Nei prototipi didattici il proposer puo' comportarsi anche da learner.

## Stato formale

Indichiamo:

```text
A = insieme degli acceptor
Q = insieme dei quorum
N = insieme dei proposal number
V = insieme dei valori proponibili
```

Per ogni acceptor `a`:

```text
promised[a] in N or none
accepted[a] in (N x V) or none
```

Un valore `v` e' scelto se:

```text
exists n, exists q in Q:
  for every a in q:
    accepted[a] = (n, v)
```

Proprieta' dei quorum:

```text
for every q1, q2 in Q:
  q1 intersection q2 != empty
```

Per maggioranze semplici questa proprieta' vale automaticamente.

## Invarianti utili

### Invariante 1: promise monotona

Per ogni acceptor `a`, `promised[a]` non diminuisce mai.

```text
promised[a] := max(promised[a], n)
```

Conseguenza:

- dopo una promise a `n`, l'acceptor rifiuta accept con proposal number minore di `n`.

### Invariante 2: accept rispetta promise

Un acceptor accetta `(n, v)` solo se:

```text
promised[a] <= n
```

Dopo aver accettato:

```text
accepted[a] = (n, v)
promised[a] >= n
```

### Invariante 3: valore sicuro per una proposta

Un proposer che ha ricevuto promise da un quorum `q` per la proposta `n` puo'
proporre:

- il proprio valore, se nessun acceptor in `q` aveva gia' accettato valori;
- altrimenti il valore associato al massimo `accepted_n` riportato nelle promise.

Questa e' la regola che conserva la safety.

## Protocollo

### Fase 1A: Prepare

Il proposer sceglie un proposal number `n` e invia:

```text
PREPARE(n)
```

a un insieme di acceptor.

### Fase 1B: Promise

Un acceptor `a` riceve `PREPARE(n)`.

Se:

```text
promised[a] is none or n > promised[a]
```

allora aggiorna:

```text
promised[a] = n
```

e risponde:

```text
PROMISE(n, accepted[a])
```

Altrimenti rifiuta o ignora.

### Fase 2A: Accept request

Il proposer attende promise da un quorum.

Poi sceglie il valore `v` con la regola:

```text
if no promise reports accepted value:
    v = own_value
else:
    v = value with highest accepted_n among promises
```

e invia:

```text
ACCEPT(n, v)
```

### Fase 2B: Accepted

Un acceptor `a` riceve `ACCEPT(n, v)`.

Se:

```text
promised[a] <= n
```

allora accetta:

```text
accepted[a] = (n, v)
promised[a] = n
```

e risponde:

```text
ACCEPTED(n, v)
```

Quando un learner vede `ACCEPTED(n, v)` da un quorum, considera `v` scelto.

## Argomento di correttezza

Vogliamo sostenere:

```text
se un valore v e' scelto, nessun valore diverso v' puo' essere scelto dopo.
```

Supponiamo che `v` sia scelto con proposal number `n` da un quorum `q`.

Ora consideriamo una proposta successiva `n' > n` che riesce a ottenere promise
da un quorum `q'`.

Poiche' i quorum si intersecano:

```text
q intersection q' contiene almeno un acceptor a
```

Quell'acceptor `a` aveva accettato `(n, v)` oppure, piu' in generale, il quorum
di `n'` deve riportare il valore accettato con proposal number massimo tra quelli
noti.

La regola della fase 2A obbliga il proposer di `n'` a scegliere il valore
accettato con proposal number massimo tra le promise ricevute.

Quindi una proposta successiva non puo' liberamente scegliere un valore diverso
se esiste gia' un valore potenzialmente scelto da un quorum precedente.

Questo e' il cuore della safety.

## Perche' una soluzione sbagliata rompe la safety

Errore tipico:

```text
un proposer con numero piu' alto propone sempre il proprio valore
```

Scenario:

1. `P1` propone `(1,P1)` con valore `v1`;
2. `A1` e `A2` accettano `v1`, quindi `v1` e' scelto;
3. `P1` cade prima di informare tutti;
4. `P2` propone `(2,P2)` con valore `v2`;
5. `A2` e `A3` rispondono a `P2`;
6. se `P2` ignora che `A2` aveva accettato `v1`, potrebbe far scegliere `v2`.

Risultato:

```text
v1 scelto da {A1,A2}
v2 scelto da {A2,A3}
```

Safety violata.

La promise deve quindi trasportare la memoria del passato:

```text
last_accepted
```

## Paxos e temporalita'

Paxos usa numeri ordinabili, ma non sta cercando di misurare il tempo.

La temporalita' qui e' logica:

- una proposal piu' alta supera una promise precedente;
- una promise vincola accept futuri;
- un quorum successivo deve conoscere abbastanza storia da non contraddire una decisione precedente.

Quindi Paxos non sostituisce i clock logici.
Risolve una domanda diversa:

```text
quale valore puo' diventare decisione comune?
```

## Cosa osservare nello script

Eseguire:

```bash
python3 labs/logical_clocks/paxos_single_decree.py
```

Osservare:

- `P1` propone `SET x=1`;
- un quorum accetta quel valore;
- `P2` arriva con proposal number piu' alto e vorrebbe proporre `SET x=2`;
- durante la fase prepare scopre un valore gia' accettato;
- per rispettare la safety, ripropone `SET x=1`.

Domanda per la classe:

```text
quale riga del protocollo impedisce di scegliere SET x=2?
```

La risposta corretta e':

```text
la regola che, dopo le promise, impone di usare il valore accettato
con proposal number massimo.
```

