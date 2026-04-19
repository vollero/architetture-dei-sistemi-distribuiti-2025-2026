# Contratto del Protocollo: KV Store v4 con Failover a Due Nodi

Questa versione introduce due nodi con ruoli dinamici:

- un nodo che si crede `primary`;
- un nodo che si crede `secondary`.

Il ruolo puo' cambiare nel tempo sulla base di heartbeat e timeout.

## Trasporto

- Protocollo testuale su TCP per i client.
- Protocollo JSON line-oriented sul canale peer-to-peer tra nodi.

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

## Semantica dei ruoli

- solo il nodo che si considera `primary` accetta scritture;
- il nodo `secondary` applica update replicati dal primary;
- il secondary si promuove a primary se non riceve heartbeat entro il timeout.

## Garanzie parziali

- in condizioni normali il follower replica gli update del leader;
- dopo crash del leader, il follower puo' diventare primary;
- `STATUS` rende osservabile ruolo, termine e leader percepito.

## Cosa non e' garantito

- il timeout non prova un crash, prova solo assenza di heartbeat;
- non esiste un meccanismo che impedisca split brain;
- non esiste quorum;
- non esiste riconciliazione automatica se due leader divergono.

## Punto chiave della tappa

Il contratto della scrittura non dipende piu' solo da chi replica, ma anche da
chi e' legittimato a comandare in quel momento. Senza un criterio condiviso
piu' forte del solo timeout, due nodi possono promettere update incompatibili.
