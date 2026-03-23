#!/usr/bin/env python3
"""
TCP Load Balancer — Distributed Systems Lab
============================================
Un load balancer TCP Layer-4 che distribuisce le connessioni in ingresso
tra un pool di server backend usando una strategia round-robin.

Il load balancer opera come un proxy trasparente:
  1. Accetta una connessione dal client.
  2. Sceglie un backend secondo la strategia configurata.
  3. Apre una connessione verso il backend scelto.
  4. Inoltra bidirezionalmente i dati tra client e backend.

Architettura del forwarding (per ogni connessione client):

    Client ──▶ [LB:8080] ──▶ Backend (9001 o 9002)
    Client ◀── [LB:8080] ◀── Backend

    Due thread gestiscono il forwarding bidirezionale:
      - Thread A: client → backend  (ciò che il client digita)
      - Thread B: backend → client  (ciò che il server risponde)

Uso:
    python load_balancer.py [porta_lb]

    porta_lb: porta su cui il LB accetta connessioni (default: 8080)

Esempio:
    # Terminale 1: avviare il primo backend
    python tcp_server.py 9001

    # Terminale 2: avviare il secondo backend
    python tcp_server.py 9002

    # Terminale 3: avviare il load balancer
    python load_balancer.py

    # Terminale 4, 5, ...: connettersi al load balancer
    telnet 127.0.0.1 8080
"""

import socket
import sys
import threading
from datetime import datetime
from itertools import cycle
from typing import List, Tuple


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAZIONE
# ═══════════════════════════════════════════════════════════════════════════

# Lista dei server backend (indirizzo, porta).
# In un sistema reale questi verrebbero letti da un file di configurazione
# o da un service registry (es. Consul, etcd, ZooKeeper).
BACKENDS: List[Tuple[str, int]] = [
    ("127.0.0.1", 9001),
    ("127.0.0.1", 9002),
    ("127.0.0.1", 9003),
]

# Porta di default del load balancer
DEFAULT_LB_PORT = 9000

# Dimensione del buffer per la lettura dei dati (in byte).
# 4096 è un buon compromesso per un lab didattico.
BUFFER_SIZE = 4096

# Timeout per la connessione ai backend (secondi).
BACKEND_CONNECT_TIMEOUT = 5.0


# ═══════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════

# Lock per evitare che i messaggi di log di thread diversi si sovrappongano.
_log_lock = threading.Lock()


def log(msg: str, level: str = "INFO") -> None:
    """Log thread-safe con timestamp."""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    tid = threading.current_thread().name
    with _log_lock:
        print(f"[{ts}] [{level}] [{tid}] {msg}")


# ═══════════════════════════════════════════════════════════════════════════
# STRATEGIA DI BILANCIAMENTO
# ═══════════════════════════════════════════════════════════════════════════

class RoundRobinBalancer:
    """
    Strategia Round-Robin per la selezione dei backend.

    Il round-robin è l'algoritmo di load balancing più semplice:
    assegna le connessioni ai backend in ordine ciclico.

    Connessione 1 → Backend A
    Connessione 2 → Backend B
    Connessione 3 → Backend A
    Connessione 4 → Backend B
    ...

    Vantaggi:
      - Semplicissimo da implementare e comprendere.
      - Distribuzione uniforme se i backend sono omogenei.

    Svantaggi:
      - Non tiene conto del carico effettivo dei backend.
      - Non considera la "pesantezza" delle connessioni attive.
      - Se un backend è più lento, accumula connessioni attive.

    Alternative comuni in produzione:
      - Weighted Round-Robin: backend con pesi diversi.
      - Least Connections: sceglie il backend con meno connessioni attive.
      - IP Hash: stessa sorgente IP → stesso backend (session affinity).
      - Random: scelta casuale (sorprendentemente efficace con molti backend).

    NOTA SULLA THREAD-SAFETY:
    itertools.cycle è un generatore. next() su un generatore condiviso
    tra thread richiede un lock per evitare race condition.
    In CPython il GIL rende next() atomico nella pratica, ma un lock
    esplicito è la soluzione corretta e portabile.
    """

    def __init__(self, backends: List[Tuple[str, int]]):
        if not backends:
            raise ValueError("La lista dei backend non può essere vuota")
        self._backends = backends
        self._cycle = cycle(backends)
        self._lock = threading.Lock()
        self._counter = 0  # contatore per logging

    def next_backend(self) -> Tuple[str, int]:
        """
        Restituisce il prossimo backend in ordine round-robin.
        Thread-safe grazie al lock esplicito.
        """
        with self._lock:
            backend = next(self._cycle)
            self._counter += 1
            log(f"Connessione #{self._counter} → {backend[0]}:{backend[1]}")
            return backend

    @property
    def backends(self) -> List[Tuple[str, int]]:
        return list(self._backends)


# ═══════════════════════════════════════════════════════════════════════════
# HEALTH CHECK (versione semplificata)
# ═══════════════════════════════════════════════════════════════════════════

def check_backend_health(host: str, port: int, timeout: float = 2.0) -> bool:
    """
    Verifica se un backend è raggiungibile tentando una connessione TCP.

    In un sistema reale, l'health check potrebbe:
      - Inviare una richiesta HTTP GET /health
      - Verificare un protocollo applicativo specifico
      - Controllare metriche come latenza e tasso di errore
      - Essere eseguito periodicamente in background

    Per questo lab, ci limitiamo a verificare che il backend
    accetti connessioni TCP (L4 health check).
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════
# FORWARDING BIDIREZIONALE
# ═══════════════════════════════════════════════════════════════════════════

def forward(source: socket.socket, destination: socket.socket,
            label: str, shutdown_event: threading.Event) -> None:
    """
    Inoltra dati da source a destination fino a chiusura.

    Questa funzione implementa un singolo verso del "pipe" bidirezionale
    tra client e backend. Viene eseguita in un thread dedicato.

    Il pattern "two-thread bidirectional forwarding" è il modo classico
    di implementare un proxy TCP:

        Thread 1: client_socket → backend_socket  (forward)
        Thread 2: backend_socket → client_socket   (forward)

    Quando uno dei due versi rileva la chiusura (recv ritorna b''),
    segnala all'altro verso tramite un threading.Event e chiude
    la propria direzione con shutdown(SHUT_WR), che invia un FIN TCP.

    Parametri
    ---------
    source : socket connesso da cui leggere
    destination : socket connesso su cui scrivere
    label : stringa descrittiva per il logging (es. "client→backend")
    shutdown_event : evento condiviso per coordinare la chiusura
    """
    try:
        while not shutdown_event.is_set():
            data = source.recv(BUFFER_SIZE)
            if not data:
                # La sorgente ha chiuso la connessione (FIN ricevuto).
                log(f"{label}: connessione chiusa dalla sorgente")
                break
            destination.sendall(data)
    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        log(f"{label}: errore di rete — {e}")
    finally:
        # Segnala all'altro thread di terminare.
        shutdown_event.set()
        # shutdown(SHUT_WR) invia un FIN, segnalando alla controparte
        # che non invieremo più dati su questa direzione.
        try:
            destination.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def handle_connection(client_socket: socket.socket, client_addr: tuple,
                      balancer: RoundRobinBalancer) -> None:
    """
    Gestisce una connessione client: sceglie un backend e avvia il forwarding.

    Flusso:
    1. Seleziona il prossimo backend (round-robin).
    2. Apre una connessione TCP verso il backend.
    3. Avvia due thread di forwarding (bidirezionale).
    4. Attende che entrambi i thread terminino.
    5. Chiude entrambe le socket.
    """
    client_id = f"{client_addr[0]}:{client_addr[1]}"
    log(f"Nuova connessione da {client_id}")

    # ── 1. Selezione del backend ────────────────────────────────────────
    backend_host, backend_port = balancer.next_backend()

    # ── 2. Connessione al backend ───────────────────────────────────────
    backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    backend_socket.settimeout(BACKEND_CONNECT_TIMEOUT)

    try:
        backend_socket.connect((backend_host, backend_port))
        # Dopo la connessione, rimuoviamo il timeout per il forwarding
        # (il forwarding usa recv bloccante senza timeout).
        backend_socket.settimeout(None)
        log(f"Connesso al backend {backend_host}:{backend_port} "
            f"per il client {client_id}")
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        log(f"Impossibile connettersi al backend "
            f"{backend_host}:{backend_port}: {e}", "ERROR")
        # Invia un messaggio di errore al client e chiudi.
        error_msg = (
            f"\r\n[LOAD BALANCER] Errore: backend {backend_host}:{backend_port} "
            f"non raggiungibile.\r\n"
            f"[LOAD BALANCER] Assicurarsi che il server sia in esecuzione.\r\n"
        )
        try:
            client_socket.sendall(error_msg.encode())
        except OSError:
            pass
        client_socket.close()
        backend_socket.close()
        return

    # ── 3. Forwarding bidirezionale ─────────────────────────────────────
    shutdown_event = threading.Event()

    # Thread: client → backend (ciò che il client digita va al server)
    t_c2b = threading.Thread(
        target=forward,
        args=(client_socket, backend_socket, f"{client_id}→backend", shutdown_event),
        daemon=True,
        name=f"fwd-c2b-{client_id}"
    )

    # Thread: backend → client (le risposte del server vanno al client)
    t_b2c = threading.Thread(
        target=forward,
        args=(backend_socket, client_socket, f"backend→{client_id}", shutdown_event),
        daemon=True,
        name=f"fwd-b2c-{client_id}"
    )

    t_c2b.start()
    t_b2c.start()

    # ── 4. Attesa della terminazione ────────────────────────────────────
    # join() blocca finché entrambi i thread non terminano.
    t_c2b.join()
    t_b2c.join()

    # ── 5. Cleanup ──────────────────────────────────────────────────────
    client_socket.close()
    backend_socket.close()
    log(f"Sessione terminata per {client_id}")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    lb_port = DEFAULT_LB_PORT
    if len(sys.argv) > 1:
        try:
            lb_port = int(sys.argv[1])
        except ValueError:
            print(f"Uso: {sys.argv[0]} [porta]")
            sys.exit(1)

    balancer = RoundRobinBalancer(BACKENDS)

    # ── Banner informativo ──────────────────────────────────────────────
    print("=" * 60)
    print("  TCP LOAD BALANCER — Distributed Systems Lab")
    print("=" * 60)
    print(f"  Porta di ascolto : 127.0.0.1:{lb_port}")
    print(f"  Strategia        : Round-Robin")
    print(f"  Backend pool     :")
    for host, port in balancer.backends:
        healthy = check_backend_health(host, port)
        status = "✓ UP" if healthy else "✗ DOWN"
        print(f"    - {host}:{port}  [{status}]")
    print("=" * 60)
    print(f"  Per connettersi:  telnet 127.0.0.1 {lb_port}")
    print(f"  Per terminare:    Ctrl+C")
    print("=" * 60)
    print()

    # ── Creazione del socket del load balancer ──────────────────────────
    lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lb_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lb_socket.bind(("127.0.0.1", lb_port))
    lb_socket.listen(10)

    log(f"Load balancer in ascolto su 127.0.0.1:{lb_port}")

    try:
        while True:
            client_socket, client_addr = lb_socket.accept()
            # Ogni connessione client viene gestita in un thread separato.
            t = threading.Thread(
                target=handle_connection,
                args=(client_socket, client_addr, balancer),
                daemon=True,
                name=f"conn-{client_addr[1]}"
            )
            t.start()

    except KeyboardInterrupt:
        log("Arresto del load balancer (Ctrl+C)")
    finally:
        lb_socket.close()


if __name__ == "__main__":
    main()

