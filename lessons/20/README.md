# Lezione 20: REST, Interfacce e Logiche ACID

Questa lezione collega il KV store distribuito a un'interfaccia REST.

Il punto non e' solo "mettere HTTP davanti al codice", ma capire come cambia il
contratto quando un sistema distribuito viene esposto come insieme di risorse:

- risorse e rappresentazioni;
- metodi HTTP e loro semantica;
- codici di stato;
- idempotenza e safety delle operazioni;
- confine tra contratto REST e garanzie interne del KV store;
- proprieta' ACID e loro costo in ambiente distribuito.

## Materiale

- [Handout tecnico](./handout.md)
- [Contratto REST del KV store](./api-contract.md)
- [Scenari di discussione](./scenarios.md)
- [Lab REST gateway](../../labs/kv_store/rest_gateway/README.md)
- [Slide della lezione](../../slides/20-rest-acid-kv.pdf)

## Obiettivi

Alla fine della lezione dovresti saper:

- modellare un servizio come risorse REST;
- associare correttamente `GET`, `PUT`, `PATCH`, `DELETE` e `POST` a operazioni sul KV store;
- distinguere safety, idempotenza e cacheability nel modello HTTP;
- spiegare cosa cambia quando una API REST nasconde un sistema distribuito;
- discutere atomicita', consistenza, isolamento e durabilita' nel contesto del KV store;
- usare `CAS` come forma di controllo di concorrenza esposta via REST;
- riconoscere quali garanzie ACID sono realistiche e quali richiedono transazioni distribuite.

