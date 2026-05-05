# Lezione 19: Chiusura del Percorso KV Store

Questa lezione chiude il percorso sul KV store distribuito.

Il punto non e' aggiungere un'altra feature, ma ricostruire il filo tecnico:

- come una piccola interfaccia nasconde un contratto;
- come il contratto viene stressato da concorrenza, crash, replica e migrazione;
- come ogni soluzione migliora una proprieta' e ne rende piu' costosa un'altra;
- come valutare criticamente un piccolo sistema distribuito.

## Materiale

- [Handout di sintesi](./handout.md)
- [Checklist di review](./review-checklist.md)
- [Proposte di homework](./homework-proposals.md)
- [Slide della lezione](../../slides/19-kv-store-conclusion.pdf)
- [Capstone exercise](../../labs/kv_store/capstone_exercise/README.md)

## Obiettivi

Alla fine della lezione dovresti saper:

- ricostruire l'evoluzione del KV store dalla versione locale alla capstone;
- collegare ogni avanzamento a una proprieta' tecnica: safety, liveness,
  durabilita', consistenza, disponibilita', scalabilita';
- distinguere interfaccia, contratto osservabile e meccanismo implementativo;
- valutare una soluzione non solo perche' "funziona", ma per cosa promette;
- individuare i limiti residui e proporre evoluzioni coerenti.
