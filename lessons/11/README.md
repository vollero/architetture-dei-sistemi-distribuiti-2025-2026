# Lezione 11: KV Store con Persistenza Locale

Questa lezione aggiunge durabilita' locale al key-value store.

Finora il problema centrale era:

- prima il contratto del nodo singolo;
- poi la safety in presenza di piu' thread.

Ora la domanda diventa:

- quando una scrittura puo' essere considerata davvero confermata?

## Materiale

- [Handout tecnico](./handout.md)
- [Contratto del protocollo](./api-contract.md)
- [Lab persistenza locale](../../labs/kv_store/persistence_local/README.md)
- [Slide della lezione](../../slides/11-kv-store-persistence.pdf)

## Obiettivi

Alla fine della lezione dovresti saper:

- distinguere ack in RAM e ack durable;
- descrivere una finestra di crash e le sue conseguenze osservabili;
- motivare l'uso di un write-ahead log;
- discutere coerenza interna tra stato in memoria e stato ricostruibile;
- ragionare sui trade-off tra durabilita' e liveness.
