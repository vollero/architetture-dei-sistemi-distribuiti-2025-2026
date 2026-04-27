# Lezione 17: KV Store con Versioni e Compare-And-Set

Questa lezione introduce un avanzamento d'interfaccia forte:

- il client osserva una versione;
- il client puo' chiedere una scrittura condizionale;
- il server deve difendere esplicitamente il contratto di aggiornamento.

## Materiale

- [Handout tecnico](./handout.md)
- [Contratto del protocollo](./api-contract.md)
- [Lab CAS e versioning](../../labs/kv_store/cas_versioning/README.md)
- [Slide della lezione](../../slides/17-kv-store-cas.pdf)

## Obiettivi

Alla fine della lezione dovresti saper:

- distinguere write cieca e write condizionale;
- motivare il significato di `GETV` e `CAS`;
- leggere il `version_mismatch` come esito di contratto e non come semplice errore;
- discutere versioni come parte dell'interfaccia osservabile;
- confrontare diverse implementazioni di `CAS` e i loro costi;
- ragionare su retry, backoff e gestione dei conflitti lato client;
- collegare il tema a migrazione, replica e conflitti.
