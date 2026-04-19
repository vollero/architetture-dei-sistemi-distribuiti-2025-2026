# Lab: KV Store con Quorum di Lettura e Scrittura

Questa tappa sostituisce la logica di failover a due nodi con un cluster di
repliche e una regola esplicita di quorum.

L'obiettivo e' rendere osservabili:

- differenza tra `N`, `R`, `W`;
- significato di `R + W > N`;
- letture stantie quando il quorum e' troppo debole;
- costo in disponibilita' quando il quorum e' troppo forte.

## File

- `replica_node.py`: replica che conserva coppie `(value, version)`
- `coordinator.py`: endpoint client che implementa quorum di lettura e scrittura
- `client.py`: client interattivo per il coordinator

## Topologia tipica

Tre repliche:

```bash
python3 labs/kv_store/quorum_cluster/replica_node.py --node-id A --port 6421
python3 labs/kv_store/quorum_cluster/replica_node.py --node-id B --port 6422
python3 labs/kv_store/quorum_cluster/replica_node.py --node-id C --port 6423
```

Coordinator con quorum forte:

```bash
python3 labs/kv_store/quorum_cluster/coordinator.py --port 6420 --read-quorum 2 --write-quorum 2
```

Coordinator con quorum debole:

```bash
python3 labs/kv_store/quorum_cluster/coordinator.py --port 6424 --read-quorum 1 --write-quorum 1
```

## Comandi client

- `PING`
- `STATUS`
- `SET <key> <value...>`
- `GET <key>`
- `QUIT`

## Semantica

- `SET` sceglie una nuova `version` e tenta la scrittura sulle repliche;
- la richiesta riesce solo se arrivano almeno `W` acknowledgement;
- `GET` legge da almeno `R` repliche e restituisce il valore con `version`
  massima tra le risposte osservate.

## Esperimento 1: quorum debole e stale read

1. avviare le tre repliche;
2. avviare un coordinator `R=1, W=1`;
3. fermare temporaneamente la prima replica raggiungibile dal coordinator;
4. eseguire una scrittura;
5. riavviare la replica fermata e leggere tramite coordinator `R=1, W=1`.

Con quorum debole, una lettura puo' fermarsi troppo presto e non vedere la
versione piu' recente.

## Esperimento 2: quorum forte

1. avviare il coordinator `R=2, W=2`;
2. eseguire scritture e letture con una replica fuori servizio.

Finche' resta raggiungibile una maggioranza, il sistema continua a lavorare e
una lettura su due repliche osserva la versione piu' recente.

## Domande tecniche da discutere

- Perche' `W=1` puo' essere troppo debole?
- Perche' `R=1` puo' restituire una versione vecchia?
- Cosa implica `R + W > N`?
- Quale disponibilita' perdiamo quando alziamo `R` e `W`?
- Quale problema resta aperto se due coordinator producono versioni concorrenti?
