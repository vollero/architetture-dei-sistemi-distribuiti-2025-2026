# Handout: Rebalancing, Routing e Posizione Reale dei Dati

## Obiettivo della tappa

Lo sharding della lezione precedente introduceva un'assunzione implicita:

> la funzione di routing e la posizione reale del dato coincidono.

Questa lezione mostra che l'assunzione si rompe non appena cambia la topologia.

## Due nozioni da separare

Da ora in poi vanno tenute distinte:

- destinazione teorica di una chiave secondo il routing corrente;
- posizione reale della chiave negli shard.

Finche' la topologia e' statica, le due nozioni coincidono.
Dopo `ADD_SHARD`, non piu'.

## `ADD_SHARD` non sposta dati

Aggiungere uno shard cambia il risultato della funzione:

```text
target = hash(key) mod numero_di_shard
```

Ma non cambia automaticamente dove il dato e' gia' stato scritto.

Nasce quindi una finestra in cui:

- il router crede che una chiave debba stare su un certo shard;
- il valore reale e' ancora altrove.

## Rebalance come protocollo

Il rebalance non e' solo "copiare chiavi".

Deve almeno:

1. individuare le chiavi che hanno cambiato destinazione;
2. importarle nello shard corretto;
3. rimuoverle da quello vecchio;
4. riportare il sistema a uno stato coerente.

## Domanda centrale

Durante il rebalance, che cosa dovrebbe osservare il client?

Opzioni possibili:

- routing nuovo, ma dato vecchio non ancora spostato;
- blocco temporaneo di alcune operazioni;
- doppia presenza transitoria;
- protocollo piu' complesso con fasi esplicite.

Il laboratorio usa una versione semplice, ma serve proprio a far emergere il
problema.

## Messaggio da portare a casa

Con il rebalancing la topologia del cluster diventa dinamica. A quel punto il
contratto dell'interfaccia non riguarda piu' solo "dove dovrebbe andare una
chiave", ma anche "quando il sistema puo' dire che la migrazione e' conclusa".
