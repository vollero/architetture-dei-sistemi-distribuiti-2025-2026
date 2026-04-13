# Handout: KV Store Multithread, Safety e Liveness

## Obiettivo della tappa

La versione `v1` del key-value store introduce un server thread-per-connection.
Ogni client ha il proprio thread, ma tutti i thread condividono lo stesso
stato interno.

Questo cambia radicalmente il problema implementativo:

- prima il tempo di esecuzione era unico;
- ora piu' tracce possono interlecciarsi;
- il contratto osservato dal client dipende dalle sezioni critiche.

## Interfaccia quasi invariata, problemi nuovi

Dal punto di vista del client, le operazioni sono quasi le stesse del `v0`.
La novita' rilevante e' `INCR <key>`, introdotta per rendere esplicito un
percorso read-modify-write.

Il punto didattico e' importante:

- la stessa interfaccia di prima, se eseguita in concorrenza, non ha piu'
  automaticamente la stessa semantica;
- il contratto dipende dall'implementazione del controllo di accesso.

## Dove nascono le race condition

Nel server multithread, i percorsi critici sono quelli che:

1. leggono stato condiviso;
2. prendono decisioni sulla base della lettura;
3. aggiornano lo stato assumendo che nulla sia cambiato nel frattempo.

Il caso classico e' `INCR`:

1. leggere il valore corrente di `counter`;
2. convertirlo in intero;
3. incrementarlo;
4. scriverlo di nuovo.

Se due thread eseguono questa sequenza senza lock, possono leggere entrambi
lo stesso valore iniziale e produrre un lost update.

## Esempio di interleaving unsafe

Stato iniziale:

```text
counter = 10
```

Interleaving:

```text
T1: read counter -> 10
T2: read counter -> 10
T1: write counter <- 11
T2: write counter <- 11
```

Risultato:

- safety violation;
- valore finale `11` invece di `12`.

## Percorsi da classificare

### Accessi read-only

- `GET`
- `EXISTS`
- `KEYS`

Anche gli accessi read-only richiedono una scelta progettuale:

- o li si protegge con lo stesso lock delle scritture;
- o si introduce un meccanismo piu' raffinato.

Per questa tappa adottiamo la soluzione semplice e difendibile:

- un lock unico;
- tutte le operazioni sul dizionario passano attraverso quel lock.

### Accessi write-only semplici

- `SET`
- `DELETE`

Questi percorsi modificano direttamente lo stato condiviso e devono essere
serializzati.

### Accessi read-modify-write

- `INCR`

Questo e' il percorso piu' interessante: il lock deve coprire l'intera
sequenza logica, non solo la singola scrittura finale.

## Safety

In questa lezione usiamo `safety` nel senso operativo di:

"non accade mai qualcosa di scorretto".

Nel nostro caso, esempi di proprieta' di safety sono:

- il dizionario non entra in uno stato impossibile per effetto di interleaving;
- due `INCR` concorrenti non perdono aggiornamenti;
- `GET` non osserva un aggiornamento parziale;
- `DELETE` e `GET` non producono risposte incoerenti rispetto alla disciplina
  di serializzazione scelta.

## Liveness

In questa lezione usiamo `liveness` nel senso operativo di:

"qualcosa di desiderato continua a poter accadere".

Esempi concreti:

- i thread non devono bloccarsi per sempre;
- il server deve continuare ad accettare nuove connessioni;
- una richiesta non dovrebbe attendere indefinitamente per colpa di una
  sezione critica troppo ampia.

## Perche' la sezione critica non deve essere enorme

Mettere un lock "ovunque" puo' aiutare la safety, ma puo' peggiorare:

- throughput;
- tempo di attesa;
- rischio di starvation;
- leggibilita' del codice;
- evolvibilita' futura del sistema.

Regola pratica della tappa:

- proteggere tutto cio' che tocca lo stato condiviso;
- non tenere il lock durante operazioni di rete;
- non introdurre lock annidati senza una ragione forte.

## Vista come automa

Gli studenti hanno gia' visto la rappresentazione di software come automi.
Qui si puo' modellare ogni richiesta come una transizione su stato condiviso.

Per `INCR`, una versione astratta e':

```text
Idle -> ReadCurrent -> ComputeNext -> WriteBack -> Reply
```

Nella versione unsafe, due automi distinti possono interlecciarsi in modo da
violare la proprieta' desiderata del sistema.

Nella versione safe, il lock forza l'esecuzione atomica della parte critica:

```text
Idle -> AcquireLock -> ReadCurrent -> ComputeNext -> WriteBack -> ReleaseLock -> Reply
```

## Lettura con automi: cosa osservare

Domande utili:

- quale parte della transizione deve essere atomica?
- quale stato e' locale al thread e quale e' condiviso?
- quali interleaving preservano safety?
- quali interleaving restano ammessi ma sono solo piu' lenti?

## Esperimento consigliato

1. Avviare `server_threaded_unsafe.py`.
2. Eseguire `stress_incr.py`.
3. Osservare un valore finale minore dell'atteso.
4. Ripetere sul server `server_threaded.py`.
5. Confrontare i risultati.

## Messaggio da portare a casa

Nel mondo concorrente il contratto del servizio non e' solo una questione di
protocollo di rete. E' anche una questione di interleavings ammessi e di
proprieta' preservate dal codice interno.
