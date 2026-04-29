# Handout: Esercitazione Integrata

## Scopo

L'esercitazione obbliga a mettere insieme piu' strati del percorso:

- routing;
- migrazione;
- versioni;
- scritture condizionali;
- test.

Il laboratorio associato contiene una soluzione di riferimento completa ma
deliberatamente conservativa. Va letta come oggetto di discussione: mostra un
contratto coerente, ma lascia aperte alternative piu' robuste.

## Regola di fondo

Prima del codice dovete produrre una specifica breve ma esplicita:

1. interfaccia proposta;
2. contratto osservabile;
3. casi critici da testare.

La reference implementation inclusa nella cartella del lab segue questa
specifica minima:

- `ADD_SHARD` cambia subito il routing teorico;
- prima di `REBALANCE`, alcune chiavi possono risultare temporaneamente non trovate;
- `REBALANCE` serializza le operazioni del router e migra valore e versione insieme;
- dopo `REBALANCE`, `GETV` e `CAS` lavorano sul nuovo shard senza perdere la storia della chiave.

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

## Due famiglie di soluzione ragionevoli

### 1. Router piu' intelligente

In questa impostazione:

- gli shard custodiscono valore e versione;
- il router conosce topologia, migrazione e possibili inoltri;
- il rebalance trasferisce coppie `(value, version)`.

Pregi:

- mantiene il controllo della topologia in un solo punto;
- facilita alcune politiche di forwarding.

Problemi:

- il router diventa piu' complesso;
- rischia di diventare il luogo in cui si accumulano troppe responsabilita'.

### 2. Shard piu' autonomi

In questa impostazione:

- ogni shard sa gestire direttamente `GETV` e `CAS`;
- il router inoltra ma non interpreta troppo la semantica locale;
- il rebalance trasferisce dati gia' completi di versione.

Pregi:

- separazione piu' pulita tra routing e stato della chiave;
- buona base per estensioni successive.

Problemi:

- il protocollo di migrazione deve essere piu' attento;
- alcune decisioni di coerenza diventano distribuite.

## Ordine di implementazione consigliato

Una sequenza pragmatica per non perdersi e':

1. rendere corretto `GETV`/`CAS` in un solo shard;
2. trasferire correttamente `(value, version)` in migrazione senza scritture concorrenti;
3. chiarire la semantica di `WHERE` prima, durante e dopo `REBALANCE`;
4. decidere cosa succede a `CAS` durante la finestra di migrazione;
5. solo alla fine discutere eventuali miglioramenti di trasparenza.

Questo ordine riduce il rischio tipico dell'esercitazione:
mescolare insieme troppi problemi e non chiuderne bene nessuno.

## Tempi di lavoro ragionevoli

Per un gruppo che parte dal materiale delle lezioni precedenti, una stima
realistica puo' essere:

1. 30-45 minuti per definire contratto e casi critici;
2. 45-60 minuti per far migrare correttamente valore e versione;
3. 30-45 minuti per integrare `CAS` nel percorso shardato;
4. 30-45 minuti per testare casi nominali e casi di conflitto;
5. tempo extra per pulizia, note tecniche e chiarimento dei limiti.

Se il gruppo salta la fase iniziale di specifica, di solito perde molto piu'
tempo dopo in debug semantico.

## Problemi che mi aspetto emergano

I piu' probabili sono:

- migrare il valore ma dimenticare la versione;
- resettare la versione quando la chiave arriva sul nuovo shard;
- non sapere chi decide la validita' di una `CAS` durante il transitorio;
- confondere target teorico e posizione reale;
- scrivere test troppo deboli per catturare le finestre critiche.

## Una strategia di test sensata

I test dovrebbero essere organizzati almeno in quattro blocchi:

- correttezza locale di `GETV` e `CAS`;
- correttezza della migrazione di valore e versione;
- coerenza di `WHERE` e delle letture dopo `REBALANCE`;
- comportamento dichiarato di `CAS` nelle finestre di transizione.

Il punto non e' avere tanti test.
Il punto e' colpire esattamente i punti in cui il contratto potrebbe rompersi.

## Cosa valutare nella nota tecnica finale

La nota tecnica dovrebbe rispondere in modo esplicito a domande come:

- dove vive la versione e perche';
- quale protocollo di migrazione avete scelto;
- quale finestra di incoerenza avete accettato o evitato;
- quali casi non avete risolto completamente;
- quali estensioni adottereste con piu' tempo.

## Criteri di valutazione

- chiarezza del contratto;
- correttezza dei casi nominali;
- qualità dei test sui casi critici;
- capacità di motivare i limiti rimasti aperti.
