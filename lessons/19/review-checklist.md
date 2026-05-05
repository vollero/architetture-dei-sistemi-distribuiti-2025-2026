# Checklist di Review: KV Store Distribuito

Questa checklist serve per discutere la capstone e, piu' in generale, qualunque
evoluzione del KV store.

## 1. Interfaccia

- I comandi supportati sono elencati esplicitamente?
- Ogni comando ha sintassi, risposta di successo e risposte di errore definite?
- Le risposte sono stabili o cambiano a seconda dell'implementazione?
- Il client puo' distinguere errore tecnico ed esito semantico?

## 2. Contratto osservabile

- Che cosa significa `OK` per una scrittura?
- Che cosa significa `NOT_FOUND`?
- Che cosa significa `version_mismatch`?
- Il contratto cambia durante replica, failover o migrazione?
- Le finestre in cui il contratto e' piu' debole sono dichiarate?

## 3. Stato interno

- Dove vive lo stato autorevole?
- Lo stato in memoria e lo stato persistente possono divergere?
- La versione e' per chiave, per shard o globale?
- Durante migrazione vengono trasferiti valore, versione e metadata necessari?

## 4. Concorrenza

- Quali operazioni sono read-only?
- Quali operazioni sono read-modify-write?
- Quali sezioni critiche difendono gli invarianti?
- Il lock scelto e' globale, per chiave o per struttura?
- Esistono rischi di starvation o deadlock?

## 5. Crash e recovery

- Quali operazioni sopravvivono a un crash?
- Quando una scrittura puo' essere ackata?
- Il recovery e' idempotente?
- Cosa succede se il crash avviene a meta' protocollo?

## 6. Replica

- Le scritture sono ackate localmente o dopo replica?
- Le letture possono essere stantie?
- Chi decide quale replica e' autorevole?
- Cosa succede se una replica e' lenta o irraggiungibile?

## 7. Failover

- Come viene rilevato un guasto?
- Quale timeout viene usato e perche'?
- Cosa impedisce lo split brain?
- Il sistema privilegia disponibilita' o unicita' del leader?

## 8. Quorum

- Quali sono `N`, `R` e `W`?
- Vale `R + W > N`?
- Come viene scelta la versione piu' recente?
- Cosa succede se non si raggiunge il quorum?

## 9. Sharding e routing

- La funzione di routing e' dichiarata?
- `WHERE` mostra il target teorico o la posizione reale?
- Le operazioni globali sono definite e sostenibili?
- Esistono hotspot?

## 10. Rebalancing

- Quando il nuovo routing diventa visibile?
- Durante la migrazione il client puo' osservare incoerenze?
- Il protocollo copia prima di cancellare?
- Esistono retry o resume se il rebalance fallisce?
- Le scritture concorrenti durante migrazione sono bloccate, inoltrate o accettate?

## 11. Versioni e CAS

- La versione osservata da `GETV` e' stabile semanticamente?
- `CAS` confronta e aggiorna atomicamente?
- `DELETE` resetta o avanza la storia della chiave?
- Un `CAS` dopo migrazione conserva il significato della versione letta prima?
- Il client ha una strategia di retry?

## 12. Test

- Esistono test nominali?
- Esistono test sui conflitti?
- Esistono test su crash o riavvio?
- Esistono test su migrazione e post-migrazione?
- Ogni promessa importante del contratto ha almeno un test che la colpisce?

## 13. Limiti dichiarati

- I limiti della soluzione sono scritti esplicitamente?
- Il sistema promette meno di quanto il codice sembri fare?
- Le semplificazioni didattiche sono riconoscibili?
- Le possibili evoluzioni sono coerenti con il contratto attuale?

## Domanda conclusiva

Se una persona esterna usa questo KV store solo leggendo il contratto pubblico,
puo' prevedere correttamente il comportamento del sistema nei casi difficili?

Se la risposta e' no, il problema non e' solo nel codice. E' nella specifica.

