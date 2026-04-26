# Vincoli di Contratto per l'Esercitazione

L'esercitazione richiede una proposta di contratto esplicita almeno per:

- `GETV`
- `CAS`
- `WHERE`
- `ADD_SHARD`
- `REBALANCE`

## Vincoli minimi

- la versione associata a una chiave non deve andare persa durante una migrazione;
- una `CAS` con versione vecchia deve fallire;
- dopo un `REBALANCE` completato, `WHERE` e posizione reale devono risultare coerenti;
- il comportamento osservato durante una migrazione deve essere dichiarato e
  difeso da test.

## Punto chiave

Non basta che il codice "funzioni". Dovete poter dire:

- che cosa promette il sistema;
- in quali finestre non lo promette;
- come avete verificato tali promesse.
