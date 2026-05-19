# Contratto: Sincronizzazione e Clock Logici

## Domanda di contratto

Ogni meccanismo temporale promette qualcosa di diverso.

La domanda da porre non è:

```text
che timestamp uso?
```

ma:

```text
quale proprietà temporale prometto all'interfaccia?
```

## Clock fisico locale

Contratto:

```text
timestamp prodotto dal nodo locale
```

Garantisce:

- leggibilità operativa;
- ordinamento approssimato nel log locale;
- misure locali se usato correttamente.

Non garantisce:

- ordine globale;
- causalità;
- confronto sicuro tra nodi diversi.

## Clock monotono

Contratto:

```text
tempo locale non decrescente per misurare durate
```

Uso:

- timeout;
- retry;
- misure di latenza locale;
- deadline interne.

Non usare per:

- timestamp civili;
- audit;
- confronto diretto tra nodi.

## Clock sincronizzato

Contratto:

```text
tempo reale dentro [t - epsilon, t + epsilon]
```

Garantisce solo se `epsilon` è noto e rispettato.

Uso:

- lease;
- scadenze;
- audit distribuito;
- ordinamento fisico quando gli intervalli non si sovrappongono.

## Happened-before

Contratto:

```text
a -> b indica causalità dimostrabile
```

Deriva da:

- ordine locale;
- invio prima della ricezione;
- transitività.

## Lamport clock

Contratto:

```text
a -> b => L(a) < L(b)
```

Non promette:

```text
L(a) < L(b) => a -> b
```

## Ordine totale Lamport

Contratto:

```text
ordine deterministico su tutti gli eventi osservati
```

Si ottiene con:

```text
(lamport_time, process_id)
```

È utile per code distribuite, lock e merge deterministici.
Non dimostra causalità.

## Vector clock

Contratto:

```text
distinguere causalità e concorrenza
```

Confronto:

```text
V(a) < V(b)  =>  a happened-before b
V(a) || V(b) =>  eventi concorrenti
```

Costo:

- metadata più grande;
- membership da gestire;
- confronto più costoso.

## Causal delivery

Contratto:

```text
receive(m) non implica deliver(m)
```

Un messaggio viene consegnato all'applicazione solo quando le dipendenze causali
sono già state consegnate.

Nota: un vector clock generale conta anche eventi locali e aggiornamenti di
stato. Il predicato seguente usa invece un vettore specializzato per messaggi,
qui indicato come `MC(m)`.

Il nodo ricevente mantiene uno stato locale:

```text
delivered[k] = numero di messaggi inviati da k già consegnati
               all'applicazione locale
```

`k` è un processo della membership, per esempio `A`, `B` o `C`.
Questo contatore non rappresenta messaggi globalmente consegnati e non conta i
messaggi solo ricevuti dalla rete.

Nel predicato classico:

```text
MC(m)[s] = delivered[s] + 1
```

`=` è intenzionale: il messaggio deve essere esattamente il prossimo messaggio
atteso dal mittente `s`.

Una condizione più debole come:

```text
MC(m)[s] > delivered[s]
```

permetterebbe di saltare messaggi precedenti dello stesso mittente e romperebbe
l'ordine locale del mittente.

Se invece `VC(m)` è un vector clock completo degli eventi, il confronto con
`delivered[s]` non è ben tipato: una componente può crescere per aggiornamenti
locali che non sono messaggi consegnabili. In quel caso serve anche un sequence
number per i messaggi, oppure gli aggiornamenti locali devono diventare entry
del flusso consegnato.

Nel KV store:

```text
receive replication message
buffer if dependencies are missing
deliver to replica logic
apply update
```
