# Lab: KV Store con Failover a Due Nodi

Questa tappa introduce heartbeat, timeout e promozione del follower.

L'obiettivo non e' costruire subito un sistema corretto in senso forte, ma
rendere osservabili:

- failure detection tramite heartbeat;
- failover locale basato su timeout;
- rischio di split brain;
- ambiguita' del leader in assenza di quorum.

## File

- `node.py`: nodo che puo' partire come `primary` o `secondary`
- `client.py`: client interattivo per collegarsi a uno dei due nodi

## Topologia del laboratorio

Configurazione tipica:

- nodo A client su `127.0.0.1:6400`, peer su `127.0.0.1:6500`
- nodo B client su `127.0.0.1:6401`, peer su `127.0.0.1:6501`

Avvio nodo A come primary:

```bash
python3 labs/kv_store/failover_pair/node.py \
  --node-id A \
  --client-port 6400 \
  --peer-port 6500 \
  --peer-peer-port 6501 \
  --initial-role primary
```

Avvio nodo B come secondary:

```bash
python3 labs/kv_store/failover_pair/node.py \
  --node-id B \
  --client-port 6401 \
  --peer-port 6501 \
  --peer-peer-port 6500 \
  --initial-role secondary
```

## Comandi client

- `PING`
- `STATUS`
- `ROLE`
- `GET <key>`
- `SET <key> <value...>`
- `DELETE <key>`
- `EXISTS <key>`
- `KEYS`
- `INCR <key>`
- `PAUSE_HEARTBEATS`
- `RESUME_HEARTBEATS`
- `CRASH`
- `QUIT`

## Semantica minima

- solo il nodo che si crede `primary` accetta scritture;
- il follower replica gli update che riceve dal leader;
- se il follower non riceve heartbeat entro il timeout, si promuove a
  `primary`;
- non esiste alcun meccanismo che impedisca a due nodi di credersi entrambi
  `primary`.

## Esperimento 1: failover

1. avviare A come primary e B come secondary;
2. osservare `STATUS` su entrambi;
3. eseguire `CRASH` su A;
4. attendere piu' del timeout;
5. verificare che B si promuova a primary.

## Esperimento 2: split brain

1. avviare A come primary e B come secondary;
2. eseguire `PAUSE_HEARTBEATS` su A e anche su B;
3. attendere la promozione di B;
4. osservare che i due nodi possono attraversare una fase di leadership
   ambigua;
5. provare scritture sui due nodi e discutere cosa possa accadere.

Aspettativa:

- A puo' continuare a credersi primary;
- B si promuove a primary;
- il sistema entra in una zona in cui l'unicita' del leader non e' piu'
  difesa in modo robusto.

## Domande tecniche da discutere

- Un timeout e' una prova di crash o solo un sospetto?
- Cosa succede se un heartbeat arriva in ritardo?
- Quando il follower e' legittimato a promuoversi?
- Perche' due nodi non bastano per impedire split brain?
- Quale meccanismo servira' nella tappa successiva per decidere chi puo'
  davvero scrivere?
