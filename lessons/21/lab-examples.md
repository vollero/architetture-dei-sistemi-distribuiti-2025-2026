# Esempi Eseguibili: Sincronizzazione e Clock Logici

Eseguire i comandi dalla radice del repository.

```bash
python3 labs/logical_clocks/physical_clock_skew.py
python3 labs/logical_clocks/lamport_clock_simulation.py
python3 labs/logical_clocks/total_order_lamport.py
python3 labs/logical_clocks/lamport_mutex.py
python3 labs/logical_clocks/vector_clock_simulation.py
python3 labs/logical_clocks/causal_delivery.py
```

## 1. Clock fisici non allineati

```bash
python3 labs/logical_clocks/physical_clock_skew.py
```

Osservare:

- il log fisico può mostrare una ricezione con timestamp minore dell'invio;
- il problema è l'interpretazione di clock locali diversi;
- un clock fisico locale non dimostra causalità.

## 2. Clock di Lamport

```bash
python3 labs/logical_clocks/lamport_clock_simulation.py
```

Osservare:

- evento locale incrementa il contatore;
- send allega timestamp;
- receive applica `max(locale, ricevuto) + 1`;
- `a -> b` implica `L(a) < L(b)`.

## 3. Ordine totale con tie-breaker

```bash
python3 labs/logical_clocks/total_order_lamport.py
```

Osservare:

- eventi concorrenti possono essere ordinati artificialmente;
- `(lamport_time, process_id)` produce un ordine deterministico;
- l'ordine non prova causalità.

## 4. Mutua esclusione distribuita

```bash
python3 labs/logical_clocks/lamport_mutex.py
```

Osservare:

- più processi chiedono la stessa risorsa;
- l'ordine totale evita ingressi simultanei;
- la safety è separata dalla liveness.

## 5. Vector clock

```bash
python3 labs/logical_clocks/vector_clock_simulation.py
```

Osservare:

- ogni componente appartiene a un processo della membership;
- solo il proprietario incrementa direttamente la propria componente;
- il merge propaga conoscenza;
- vettori non confrontabili indicano concorrenza.

## 6. Causal delivery

```bash
python3 labs/logical_clocks/causal_delivery.py
```

Osservare:

- `receive(m)` e `deliver(m)` sono eventi diversi;
- un messaggio può restare in buffer;
- `delivered[k]` è locale al nodo che valuta il messaggio;
- `k` identifica il mittente e il contatore riguarda messaggi già consegnati all'applicazione;
- lo script usa un message vector, non un vector clock completo degli eventi locali;
- la condizione `message_clock[m.sender] = delivered[m.sender] + 1` richiede il prossimo messaggio del mittente;
- sostituire `=` con `>` permetterebbe di saltare messaggi precedenti dello stesso mittente;
- il predicato di consegna usa dipendenze causali;
- la safety è non consegnare prima delle cause.
