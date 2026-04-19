# Handout: Sharding, Routing e Hotspot

## Obiettivo della tappa

Dopo avere visto replica e quorum, introduciamo una domanda diversa:

> come faccio a distribuire il dataset quando non voglio piu' tenere tutte le
> chiavi ovunque?

La risposta di questa lezione e':

- partizionare il key space;
- introdurre un router;
- trattare ogni shard come proprietario di un sottoinsieme di chiavi.

## Router e shard

Il router e' il punto che traduce:

- API uniforme verso il client;
- topologia partizionata del backend.

Dato `key`, il router decide:

```text
shard = hash(key) mod numero_di_shard
```

Questo significa che il contratto del client resta uniforme, ma il percorso
interno di esecuzione cambia in base alla chiave.

## Operazioni locali

Comandi come:

- `GET <key>`
- `SET <key> <value>`
- `DELETE <key>`
- `INCR <key>`

restano locali a uno shard.

Questo e' il vantaggio principale del partizionamento: molte richieste non
devono piu' toccare l'intero cluster.

## Operazioni globali

Comandi come:

- `KEYS`
- `STATS`

non hanno un solo shard naturale. Il router deve:

- interrogare tutte le partizioni;
- raccogliere le risposte;
- comporre un risultato unico.

Quindi il partizionamento cambia anche il costo osservabile delle operazioni.

## Hotspot

Anche con molti shard, una chiave molto calda resta confinata su una singola
partizione.

Questo genera hotspot:

- una partizione puo' saturarsi;
- il resto del cluster puo' restare relativamente scarico;
- il collo di bottiglia non e' piu' globale ma locale allo shard.

## Esperimento consigliato

### Routing

1. eseguire `WHERE alpha` e `WHERE beta`;
2. scrivere le due chiavi;
3. osservare `STATS`.

### Hotspot

1. ripetere molti `INCR` sulla stessa chiave;
2. osservare che il carico cresce sempre sullo stesso shard.

### Costo di `KEYS`

1. distribuire chiavi su piu' shard;
2. eseguire `KEYS`;
3. discutere perche' questa operazione non puo' piu' essere locale.

## Limite ancora aperto

Aggiungere un nuovo shard non e' gratis.

Occorre:

- cambiare la funzione di routing o il suo dominio;
- spostare chiavi gia' esistenti;
- evitare inconsistenze durante la migrazione.

Questa lezione quindi introduce il partizionamento, ma lascia aperto il tema
del rebalancing dinamico.

## Messaggio da portare a casa

Con lo sharding il contratto della stessa API dipende anche dalla topologia del
key space:

- alcune operazioni sono locali;
- altre sono globali;
- il costo non e' piu' uniforme;
- un cluster con piu' nodi puo' comunque soffrire di squilibri forti.
