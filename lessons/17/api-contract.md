# Contratto del Protocollo: KV Store v8 con Versioni e CAS

Questa versione espone esplicitamente la nozione di versione di una chiave.

## Trasporto

- Protocollo testuale su TCP.
- Una richiesta per riga.
- Una risposta per riga.

## Comandi

- `PING`
- `GET <key>`
- `GETV <key>`
- `SET <key> <value...>`
- `CAS <key> <expected_version> <value...>`
- `DELETE <key>`
- `QUIT`

## Semantica

### `GETV`

- restituisce valore e versione corrente della chiave;
- espone al client lo stato osservato su cui puo' basare una decisione.

### `SET`

- aggiorna il valore senza vincolare l'operazione a una versione attesa;
- produce una nuova versione.

### `CAS`

- aggiorna il valore solo se la versione corrente coincide con
  `expected_version`;
- se la versione non coincide, fallisce con `ERR version_mismatch current=<v>`.

## Punto chiave della tappa

La versione non e' piu' solo un dettaglio di implementazione. Diventa parte
del contratto osservabile tra client e server, perche' influenza la legittimita'
di una scrittura.

## Decisioni di contratto da rendere esplicite

Questa tappa e' piccola solo in apparenza. In realta' obbliga a fissare alcune
scelte semantiche molto precise.

### Versione della chiave assente

Nel laboratorio la chiave assente e' trattata come versione implicita `-1`.
Quindi:

- `SET` su chiave assente produce `version=0`;
- `CAS key -1 value` equivale a una forma di `create-if-absent`.

Questa non e' una convenzione neutra. Se la cambiamo, cambiamo il significato
del protocollo.

### Effetto di `DELETE`

Bisogna chiarire se `DELETE`:

- elimina soltanto il valore;
- oppure azzera anche la storia della chiave.

Nel laboratorio, dopo `DELETE`, la chiave torna a comportarsi come assente.
Quindi una nuova creazione riparte da `-1 -> 0`.

### Valore di `current=` nel mismatch

La risposta:

```text
ERR version_mismatch current=<v>
```

puo' essere letta in due modi:

- come puro messaggio diagnostico;
- come informazione che il client e' autorizzato a usare per decidere il passo successivo.

Un contratto piu' rigoroso deve dichiarare quale delle due interpretazioni sia corretta.

## Strategie implementative possibili

### 1. Sezione critica unica

- leggere versione corrente;
- confrontarla con quella attesa;
- eventualmente aggiornare valore e versione;
- fare tutto sotto lock.

Pregio:

- semplice e corretto in nodo singolo.

Costo:

- serializza tutti gli aggiornamenti della chiave, e in questo prototipo anche dell'intero store.

### 2. Versioning piu' lock piu' fine

- lock per chiave o striped locking;
- stessa semantica esterna;
- meno contesa globale.

Pregio:

- migliore parallelismo.

Costo:

- implementazione piu' complessa;
- piu' attenzione a struttura dati e lifecycle delle lock.

### 3. Primitive atomiche o storage sottostante transazionale

- la verifica della versione e l'update possono essere delegati a uno storage che supporti operazioni atomiche;
- il server diventa soprattutto traduttore di contratto.

Pregio:

- base migliore per sistemi piu' grandi.

Costo:

- dipendenza da un motore piu' ricco del semplice dizionario in memoria.
