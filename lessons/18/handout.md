# Handout: Esercitazione Integrata

## Scopo

L'esercitazione obbliga a mettere insieme piu' strati del percorso:

- routing;
- migrazione;
- versioni;
- scritture condizionali;
- test.

## Regola di fondo

Prima del codice dovete produrre una specifica breve ma esplicita:

1. interfaccia proposta;
2. contratto osservabile;
3. casi critici da testare.

## Milestone suggerite

### Milestone 1

- introdurre `GETV` e `CAS` in un contesto non migrante;
- dimostrare version mismatch e update corretto.

### Milestone 2

- introdurre `ADD_SHARD` e `REBALANCE`;
- mostrare il mismatch tra routing teorico e posizione reale prima della migrazione.

### Milestone 3

- preservare le versioni durante la migrazione;
- verificare che `CAS` continui a comportarsi secondo contratto anche dopo lo
  spostamento della chiave.

## Criteri di valutazione

- chiarezza del contratto;
- correttezza dei casi nominali;
- qualità dei test sui casi critici;
- capacità di motivare i limiti rimasti aperti.
