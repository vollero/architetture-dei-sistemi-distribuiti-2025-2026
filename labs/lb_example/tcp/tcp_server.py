#!/usr/bin/env python3
"""
TCP Echo Server — Distributed Systems Lab
==========================================
Un semplice server TCP che accetta connessioni, si identifica con il proprio
numero di porta e fa echo dei messaggi ricevuti dal client.

Uso:
    python tcp_server.py <porta>

Esempio:
    python tcp_server.py 9001
    python tcp_server.py 9002

Poi connettersi con:
    telnet 127.0.0.1 <porta>
"""

import socket
import sys
import threading
from datetime import datetime


def log(port: int, msg: str) -> None:
    """Stampa un messaggio di log con timestamp e porta del server."""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] SERVER:{port} — {msg}")


def handle_client(conn: socket.socket, addr: tuple, server_port: int) -> None:
    """
    Gestisce una singola connessione client in un thread dedicato.

    Protocollo (testuale, line-based):
      1. Il server invia un messaggio di benvenuto che include il proprio
         numero di porta, così lo studente può verificare su quale backend
         è stato instradato dal load balancer.
      2. Per ogni riga ricevuta dal client, il server risponde con un echo
         prefissato dalla propria identità.
      3. Il client può digitare 'quit' per chiudere la connessione.

    Parametri
    ---------
    conn : socket.socket
        Socket già connesso al client.
    addr : tuple
        Tupla (ip, porta) del client remoto.
    server_port : int
        Porta su cui è in ascolto questo server (usata per identificarsi).
    """
    client_id = f"{addr[0]}:{addr[1]}"
    log(server_port, f"Nuova connessione da {client_id}")

    # ── Messaggio di benvenuto ──────────────────────────────────────────
    # Il \r\n è necessario per la compatibilità con Telnet (protocollo NVT).
    welcome = (
        f"\r\n"
        f"╔══════════════════════════════════════════╗\r\n"
        f"║  Connesso al SERVER sulla porta {server_port:<5}    ║\r\n"
        f"╚══════════════════════════════════════════╝\r\n"
        f"\r\n"
        f"Digita un messaggio e premi INVIO. 'quit' per uscire.\r\n\r\n"
    )
    conn.sendall(welcome.encode("utf-8"))

    try:
        # ── Loop di echo ────────────────────────────────────────────────
        while True:
            # recv() è bloccante: il thread resta in attesa finché il
            # client non invia dati o la connessione non viene chiusa.
            data = conn.recv(4096)

            if not data:
                # Connessione chiusa dal client (EOF).
                log(server_port, f"Connessione chiusa da {client_id}")
                break

            # Decodifica il messaggio e rimuove spazi/newline finali.
            message = data.decode("utf-8", errors="replace").strip()

            if message.lower() == "quit":
                conn.sendall(f"[SERVER:{server_port}] Arrivederci!\r\n".encode())
                log(server_port, f"Client {client_id} ha inviato 'quit'")
                break

            # ── Echo con identificazione del server ─────────────────────
            # Questo è il punto chiave dell'esercizio: lo studente vedrà
            # nella risposta il numero di porta del backend che ha servito
            # la richiesta, dimostrando l'effetto del load balancing.
            response = f"[SERVER:{server_port}] Echo: {message}\r\n"
            conn.sendall(response.encode("utf-8"))
            log(server_port, f"Echo a {client_id}: {message}")

    except ConnectionResetError:
        log(server_port, f"Connessione resettata da {client_id}")
    except Exception as e:
        log(server_port, f"Errore con {client_id}: {e}")
    finally:
        conn.close()


def start_server(port: int) -> None:
    """
    Avvia il server TCP sulla porta specificata.

    Il server usa un modello multi-threaded: per ogni connessione accettata,
    viene creato un nuovo thread che gestisce il client in modo indipendente.
    Questo è il modello più semplice (thread-per-connection) e serve a
    illustrare il concetto senza la complessità di I/O asincrono o pool.

    NOTA DIDATTICA: in un sistema reale si preferirebbero:
      - asyncio (event loop, non-blocking I/O)
      - thread pool con dimensione limitata
      - framework come Tornado, Twisted, o Go goroutines
    Il modello thread-per-connection non scala bene (C10K problem),
    ma è perfetto per comprendere i fondamenti.
    """
    # ── Creazione del socket ────────────────────────────────────────────
    # AF_INET  = famiglia di indirizzi IPv4
    # SOCK_STREAM = socket orientato alla connessione (TCP)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # SO_REUSEADDR permette di riutilizzare la porta immediatamente dopo
    # la chiusura del server, evitando l'errore "Address already in use"
    # dovuto allo stato TIME_WAIT del TCP.
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # ── Bind e Listen ───────────────────────────────────────────────────
    # bind() associa il socket a un indirizzo (IP, porta).
    # '' (stringa vuota) equivale a 0.0.0.0 = tutte le interfacce.
    # Per questo lab usiamo 127.0.0.1 (solo loopback).
    server_socket.bind(("127.0.0.1", port))

    # listen(backlog) abilita il socket ad accettare connessioni.
    # Il backlog indica quante connessioni in attesa di accept() il
    # kernel può accodare prima di rifiutare nuove connessioni.
    server_socket.listen(5)

    log(port, f"Server TCP in ascolto su 127.0.0.1:{port}")
    log(port, "In attesa di connessioni...")

    try:
        while True:
            # accept() è bloccante: ritorna quando un client si connette.
            # Restituisce una nuova socket (per la comunicazione con quel
            # client specifico) e l'indirizzo del client.
            conn, addr = server_socket.accept()

            # Creiamo un thread daemon per gestire il client.
            # daemon=True fa sì che il thread venga terminato
            # automaticamente quando il thread principale esce.
            t = threading.Thread(
                target=handle_client,
                args=(conn, addr, port),
                daemon=True
            )
            t.start()

    except KeyboardInterrupt:
        log(port, "Arresto del server (Ctrl+C)")
    finally:
        server_socket.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Uso: {sys.argv[0]} <porta>")
        print(f"Esempio: {sys.argv[0]} 9001")
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        if not (1024 <= port <= 65535):
            raise ValueError
    except ValueError:
        print("Errore: la porta deve essere un intero tra 1024 e 65535.")
        sys.exit(1)

    start_server(port)

