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

## Scelte di progetto che dovete esplicitare

L'esercitazione lascia intenzionalmente aperte alcune decisioni. Non sono buchi
del testo: fanno parte del lavoro.

La soluzione di riferimento del lab adotta una scelta precisa:

- versione per chiave conservata nello shard;
- router responsabile di routing e migrazione;
- `ADD_SHARD` visibile subito;
- `REBALANCE` stop-the-world rispetto alle operazioni del router;
- migrazione copy-before-delete di `(value, version)`.

Questa scelta non e' l'unica possibile, ma e' abbastanza piccola da essere
analizzabile in aula.

### Dove vive la versione

Possibili opzioni:

- nello shard che possiede la chiave;
- nel router;
- in metadata trasferiti insieme alla chiave durante il rebalance.

Qualunque scelta facciate, dovete spiegare:

- chi e' autorevole sulla versione corrente;
- come si evita di perderla o resettarla in migrazione.

### Quando il nuovo routing diventa vincolante

Possibili contratti:

- subito dopo `ADD_SHARD`;
- solo dopo `REBALANCE`;
- in due fasi, con una finestra dichiarata di transizione.

Questa decisione cambia direttamente il significato osservabile di `WHERE`,
`GET`, `GETV` e `CAS`.

### Come gestire una `CAS` durante migrazione

Almeno tre possibilita':

- bloccarla temporaneamente;
- inoltrarla dove la chiave risiede davvero;
- permetterla solo dopo che la migrazione e' dichiarata conclusa.

Non esiste una risposta obbligata, ma deve esserci una risposta coerente.

## Criterio di accettazione implicito

Una soluzione e' accettabile se:

- il contratto e' chiaro;
- il comportamento del codice lo rispetta;
- i test mostrano i casi nominali e almeno una finestra critica;
- i limiti residui sono dichiarati invece che nascosti.
