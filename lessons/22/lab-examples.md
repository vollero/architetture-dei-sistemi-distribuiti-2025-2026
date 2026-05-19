# Esempi Eseguibili: Basic Paxos

Eseguire dalla radice del repository:

```bash
python3 labs/logical_clocks/paxos_single_decree.py
```

## Cosa osservare

- `P1` propone `SET x=1` e raggiunge il quorum `{A1,A2}`;
- `A1` e `A2` rispondono inizialmente con `accepted_n=None`;
- `P1` invia `ACCEPT` e il valore viene scelto;
- `P2` prova `SET x=2` con proposal number più alto;
- `P2` raggiunge `{A2,A3}`;
- `A2` riporta `accepted_n=(1,P1)` e `accepted_value='SET x=1'`;
- `P2` deve riproporre `SET x=1`.

## Domande

- Quale messaggio trasporta memoria del passato?
- Perché il proposal number più alto non basta a cambiare valore?
- Quale proprietà dei quorum rende sicura la convergenza?
- Quale scenario potrebbe impedire la liveness?
