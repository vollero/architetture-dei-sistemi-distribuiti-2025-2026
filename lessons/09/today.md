# Esercitazione di Oggi: KV Store Single Node

La lezione di oggi deve essere volutamente "piccola" dal punto di vista implementativo e "grande" dal punto di vista concettuale.

Gli studenti costruiscono un server key-value minimale, ma vengono valutati soprattutto sulla chiarezza del contratto esposto dall'interfaccia.

## Obiettivi della lezione

Entro la fine dell'incontro, gli studenti devono avere chiaro che:

- una interfaccia non e' solo sintassi dei comandi;
- ogni operazione promette una certa semantica;
- se il contratto non e' definito bene, la distribuzione amplifica l'ambiguita';
- prima di replicare o shardare un sistema, bisogna sapere esattamente cosa sta promettendo il nodo singolo.

## Domanda guida

"Che cosa significa davvero che una `SET k v` e' andata a buon fine?"

Se oggi la risposta e' "il processo ha aggiornato un dizionario in RAM", nelle prossime lezioni quella stessa domanda si trasformera' in:

- e' stata scritta su disco?
- e' stata replicata?
- e' visibile su tutte le repliche?
- resiste a un crash immediato?
- e' linearizzabile oppure no?

## Sequenza suggerita dell'incontro

### Parte 1: Disegno del contratto

Prima di scrivere codice, far definire agli studenti:

- set di operazioni supportate;
- formato di richiesta e risposta;
- codifica degli errori;
- gestione delle chiavi mancanti;
- vincoli sui tipi e sugli spazi;
- semantica di `KEYS`, che oggi e' banale ma domani diventa problematica.

Domande utili da porre:

- `GET k` su chiave assente deve restituire errore o `NULL`?
- `SET k ""` e `GET k` devono distinguersi da chiave assente?
- `DELETE k` su chiave assente e' errore o no-op?
- `KEYS` fa parte del contratto principale o e' solo diagnostica?
- il protocollo deve essere "human-friendly" o "machine-friendly"?

### Parte 2: Implementazione minima

Implementare:

- server TCP single-threaded;
- dizionario in memoria;
- parser dei comandi linea per linea;
- ciclo richiesta-risposta;
- logging minimo.

### Parte 3: Test manuali e ambiguita'

Far provare:

- comandi validi;
- chiavi mancanti;
- valori vuoti;
- input malformato;
- piu' client in rapida successione.

Obiettivo: far emergere dove il contratto e' incompleto.

### Parte 4: Debrief verso il distribuito

Chiudere la lezione collegando ogni scelta locale a un problema distribuito futuro:

- ack locale -> commit distribuito;
- stato in RAM -> durabilita';
- ordine dei comandi su un solo nodo -> ordine globale;
- `KEYS` locale -> aggregazione su cluster;
- assenza di concorrenza -> race e conflitti.

## Consegna per oggi

Gli studenti devono:

1. Implementare il server base.
2. Scrivere il contratto del protocollo in modo esplicito.
3. Documentare almeno 5 casi limite.
4. Giustificare una scelta semantica discutibile, ad esempio `GET` su chiave assente.

## Consegna per casa o per il prossimo incontro

Evolvere il sistema in almeno una di queste direzioni:

- server multi-client concorrente;
- persistenza con file di log;
- TTL sulle chiavi;
- replica primary-secondary simulata su localhost.

## Criteri di valutazione consigliati

- 30% chiarezza dell'interfaccia;
- 25% correttezza del protocollo e degli errori;
- 20% pulizia dell'implementazione;
- 15% test o script di prova;
- 10% qualita' della riflessione sui limiti del nodo singolo.
