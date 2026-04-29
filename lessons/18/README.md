# Lezione 18: Esercitazione Integrata su Rebalancing e CAS

Questa lezione e' una palestra di integrazione.

Gli studenti devono combinare:

- partizionamento del dato;
- topologia che cambia;
- scritture condizionali basate su versione.

Il lab contiene anche una soluzione di riferimento eseguibile, da usare come
baseline per discutere contratto, limiti e possibili evoluzioni.

## Materiale

- [Handout dell'esercitazione](./handout.md)
- [Vincoli di contratto](./api-contract.md)
- [Traccia tecnica](../../labs/kv_store/capstone_exercise/README.md)
- [Slide della lezione](../../slides/18-kv-store-exercise.pdf)

## Obiettivi

Alla fine dell'esercitazione dovresti saper:

- formalizzare un contratto osservabile prima di implementarlo;
- difendere la semantica di `GETV`, `CAS` e `REBALANCE`;
- leggere criticamente una soluzione completa e riconoscerne i limiti;
- costruire test che colpiscano le finestre critiche del sistema;
- confrontare architetture di soluzione e motivare quella scelta;
- pianificare tempi di sviluppo e verifica in modo realistico;
- motivare i trade-off tra semplicità di implementazione e forza del contratto.
