#!/usr/bin/env python3
"""
HTTP Redirect Load Balancer — Distributed Systems Lab
=====================================================
Un load balancer HTTP che distribuisce il traffico ai backend tramite
redirect HTTP (codici 3xx), anziché fare proxy dei dati.

Due modalità operative:
  - 302 Found (Temporary Redirect)
  - 301 Moved Permanently

La differenza tra le due modalità è FONDAMENTALE e ha implicazioni
architetturali profonde, come spiegato nel handout.

Uso:
    python http_redirect_lb.py [--mode 302|301] [--port PORTA]

Esempio:
    python http_redirect_lb.py --mode 302       # default: redirect temporaneo
    python http_redirect_lb.py --mode 301       # redirect permanente

Poi aprire nel browser:
    http://127.0.0.1:8080/

PREREQUISITI:
    Prima avviare i due backend:
        python http_backend.py 8001
        python http_backend.py 8002

ARCHITETTURA:
    A differenza del load balancer TCP (proxy L4) che inoltra i byte
    in modo trasparente, questo LB opera a livello HTTP (L7) e non
    trasferisce mai il contenuto: dice semplicemente al client
    "vai a parlare con quel server là" tramite l'header Location.

    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    │   Client                        Load Balancer (:8080)   │
    │     │                                │                  │
    │     │── GET / ──────────────────────▶│                  │
    │     │                                │  (round-robin)   │
    │     │◀── 302 Location: :8001/ ────-──│                  │
    │     │                                                   │
    │     │── GET / ──────────────────────────▶ Backend :8001 │
    │     │◀── 200 OK ◀──────────────────────  (contenuto)    │
    │                                                         │
    └─────────────────────────────────────────────────────────┘

    Con 302: ogni nuova richiesta riparte dal LB.
    Con 301: il browser memorizza e va diretto al backend.
"""

import argparse
import json
import sys
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from itertools import cycle
from typing import List, Tuple


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAZIONE
# ═══════════════════════════════════════════════════════════════════════════

BACKENDS: List[Tuple[str, int]] = [
    ("127.0.0.1", 8001),
    ("127.0.0.1", 8002),
]

DEFAULT_LB_PORT = 8080

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════

_log_lock = threading.Lock()

def log(msg: str, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    with _log_lock:
        print(f"[{ts}] [{level}] LB — {msg}")


# ═══════════════════════════════════════════════════════════════════════════
# ROUND-ROBIN BALANCER (riutilizzato dal lab precedente)
# ═══════════════════════════════════════════════════════════════════════════

class RoundRobinBalancer:
    """Seleziona il prossimo backend in ordine ciclico (thread-safe)."""

    def __init__(self, backends: List[Tuple[str, int]]):
        self._backends = backends
        self._cycle = cycle(backends)
        self._lock = threading.Lock()
        self._counter = 0

    def next_backend(self) -> Tuple[str, int]:
        with self._lock:
            backend = next(self._cycle)
            self._counter += 1
            return backend

    @property
    def counter(self) -> int:
        with self._lock:
            return self._counter


# ═══════════════════════════════════════════════════════════════════════════
# HTTP REDIRECT HANDLER
# ═══════════════════════════════════════════════════════════════════════════

class RedirectHandler(BaseHTTPRequestHandler):
    """
    Handler HTTP che implementa il load balancing tramite redirect.

    Il meccanismo è semplice ma potente:
    1. Il client invia una richiesta al load balancer.
    2. Il LB sceglie un backend (round-robin).
    3. Il LB risponde con un codice 3xx e l'header Location
       che punta al backend scelto.
    4. Il client (browser) segue automaticamente il redirect
       e si connette direttamente al backend.

    ┌──────────────────────────────────────────────────────────────┐
    │  DIFFERENZA CRITICA TRA 301 E 302                            │
    │                                                              │
    │  302 Found (Temporary Redirect):                             │
    │    • Il browser NON memorizza il redirect.                   │
    │    • Ogni nuova richiesta passa dal LB.                      │
    │    • Il LB mantiene il controllo su OGNI richiesta.          │
    │    • Più flessibile: il LB può cambiare backend ad ogni      │
    │      richiesta.                                              │
    │    • Overhead: doppia connessione per ogni richiesta         │
    │      (client→LB, poi client→backend).                        │
    │                                                              │
    │  301 Moved Permanently:                                      │
    │    • Il browser MEMORIZZA il redirect nella sua cache.       │
    │    • Le richieste successive vanno DIRETTAMENTE al backend.  │
    │    • Il LB perde il controllo dopo il primo redirect.        │
    │    • Meno overhead: una sola connessione dopo la prima.      │
    │    • Rischio: se il backend cade, il client continua a       │
    │      tentare di raggiungerlo (finché non svuota la cache).   │
    │    • Assomiglia a un "DNS-based load balancing" nel suo      │
    │      effetto pratico.                                        │
    └──────────────────────────────────────────────────────────────┘

    NOTA: in HTTP/1.1 esiste anche:
      - 307 Temporary Redirect: come 302 ma garantisce che il metodo
        HTTP non cambi (POST resta POST). 302 in teoria potrebbe
        cambiare POST→GET, ma i browser moderni trattano 302 come 307.
      - 308 Permanent Redirect: come 301 ma preserva il metodo HTTP.
    """

    # Iniettati dalla factory
    balancer: RoundRobinBalancer = None
    redirect_code: int = 302

    def do_GET(self):
        """
        Gestisce ogni richiesta GET con un redirect al backend scelto.

        Endpoint speciali:
          GET /status   → Pagina di stato del LB (non redirige)
          GET /stats    → Statistiche JSON del LB
          GET /*        → Redirect al backend
        """
        if self.path == "/status":
            self._serve_status_page()
            return

        if self.path == "/stats":
            self._serve_stats()
            return

        # ── Selezione del backend e redirect ─────────────────────────
        host, port = self.balancer.next_backend()
        # Costruiamo l'URL di destinazione preservando il path originale
        # Esempio: GET /api/info → Location: http://127.0.0.1:8001/api/info
        target_url = f"http://{host}:{port}{self.path}"

        log(f"Richiesta #{self.balancer.counter}: "
            f"{self.client_address[0]}:{self.client_address[1]} "
            f"GET {self.path} → {self.redirect_code} → {target_url}")

        # ── Invio della risposta redirect ─────────────────────────────
        # La risposta HTTP di redirect è composta da:
        #   Status: HTTP/1.1 302 Found  (oppure 301 Moved Permanently)
        #   Location: http://127.0.0.1:8001/path
        #
        # L'header "Location" è l'istruzione chiave: dice al client
        # dove trovare la risorsa richiesta. Il browser interpreta
        # questo header e automaticamente effettua una nuova richiesta
        # GET all'URL indicato.
        self.send_response(self.redirect_code)
        self.send_header("Location", target_url)

        # ── Header anti-cache (importante per 301!) ───────────────────
        # Se stiamo usando 302, l'header Cache-Control non è strettamente
        # necessario (302 non viene cachato di default), ma lo aggiungiamo
        # per sicurezza.
        #
        # Se stiamo usando 301, il browser per specifica HTTP DEVE cachare
        # il redirect. L'header Cache-Control potrebbe convincere alcuni
        # browser a non cacharlo, ma NON è garantito dalla specifica.
        # Questo è un punto didattico importante: 301 è "permanente" e
        # i browser lo trattano come tale.
        if self.redirect_code == 302:
            self.send_header("Cache-Control", "no-store, no-cache")
        else:
            # Per 301, NON mettiamo Cache-Control: vogliamo che lo studente
            # osservi il comportamento di caching del browser.
            pass

        # Header custom per debugging
        self.send_header("X-LB-Mode", f"redirect-{self.redirect_code}")
        self.send_header("X-LB-Backend", f"{host}:{port}")
        self.send_header("X-LB-Request-Count", str(self.balancer.counter))

        # Body opzionale: HTML di fallback per client che non seguono
        # automaticamente i redirect (es. curl senza -L).
        body = (
            f'<html><body>'
            f'<p>Redirect ({self.redirect_code}) a '
            f'<a href="{target_url}">{target_url}</a></p>'
            f'</body></html>'
        ).encode("utf-8")

        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_status_page(self):
        """
        Pagina di stato del load balancer (non redirige).

        Mostra la modalità operativa, il contatore di richieste,
        e permette allo studente di confrontare i comportamenti
        di 301 vs 302.
        """
        mode_name = "302 Found (Temporary)" if self.redirect_code == 302 else "301 Moved Permanently"
        mode_color = "#27ae60" if self.redirect_code == 302 else "#e74c3c"

        html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Load Balancer Status</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 750px; margin: 40px auto;
            background: #f5f7fa; color: #333;
        }}
        .card {{
            background: white; border-radius: 12px;
            padding: 35px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            margin-bottom: 20px;
        }}
        h1 {{ color: #1B4F72; text-align: center; }}
        .mode {{
            text-align: center; font-size: 1.5em; font-weight: bold;
            color: {mode_color}; margin: 15px 0;
        }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        td, th {{
            padding: 10px 12px; border-bottom: 1px solid #eee; text-align: left;
        }}
        th {{ background: #1B4F72; color: white; }}
        code {{
            background: #f0f0f0; padding: 2px 6px; border-radius: 4px;
            font-family: Consolas, monospace;
        }}
        .btn {{
            display: inline-block; padding: 10px 20px; border-radius: 6px;
            color: white; text-decoration: none; margin: 5px;
            font-size: 0.95em;
        }}
        .btn-primary {{ background: #2E75B6; }}
        .btn-success {{ background: #27ae60; }}
        .btn-warning {{ background: #f39c12; }}
        .btn:hover {{ opacity: 0.85; }}
        .compare {{
            background: #fff3cd; border-left: 4px solid #ffc107;
            padding: 15px; border-radius: 0 8px 8px 0; margin: 20px 0;
        }}
        .experiment {{
            background: #d4edda; border-left: 4px solid #28a745;
            padding: 15px; border-radius: 0 8px 8px 0; margin: 15px 0;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>HTTP Redirect Load Balancer</h1>
        <div class="mode">Modalit&agrave;: {mode_name}</div>

        <table>
            <tr><th colspan="2">Stato</th></tr>
            <tr><td>Porta LB</td><td><code>8080</code></td></tr>
            <tr><td>Redirect code</td><td><code>{self.redirect_code}</code></td></tr>
            <tr><td>Richieste servite</td><td><code>{self.balancer.counter}</code></td></tr>
            <tr><td>Strategia</td><td>Round-Robin</td></tr>
        </table>

        <table>
            <tr><th colspan="2">Backend Pool</th></tr>
            <tr><td>Backend A</td><td><code>http://127.0.0.1:8001</code></td></tr>
            <tr><td>Backend B</td><td><code>http://127.0.0.1:8002</code></td></tr>
        </table>

        <h2 style="color:#1B4F72">Test il redirect</h2>
        <p>Clicca per essere rediretto a un backend:</p>
        <div style="text-align:center">
            <a class="btn btn-primary" href="/">Redirect a /</a>
            <a class="btn btn-success" href="/api/info">Redirect a /api/info</a>
            <a class="btn btn-warning" href="/api/echo?lab=redirect&mode={self.redirect_code}">
                Redirect a /api/echo
            </a>
        </div>

        <div class="compare">
            <strong>Confronto 301 vs 302:</strong><br>
            Per osservare la differenza, esegui il LB prima in modalit&agrave; 302
            e poi in 301. Con 302, ogni click sul pulsante passa dal LB
            (il contatore aumenta). Con 301, solo il primo click passa dal LB;
            i successivi vanno direttamente al backend (il contatore non aumenta).
            <br><br>
            <strong>Suggerimento:</strong> Usa gli strumenti sviluppatore del browser
            (F12 &rarr; Network) per osservare i codici di stato HTTP.
        </div>

        <div class="experiment">
            <strong>Esperimento con curl:</strong><br>
            <code>curl -v http://127.0.0.1:8080/</code> &mdash; mostra il redirect senza seguirlo<br>
            <code>curl -v -L http://127.0.0.1:8080/</code> &mdash; segue il redirect (-L = --location)
        </div>
    </div>
</body>
</html>"""
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_stats(self):
        """Statistiche JSON del load balancer."""
        stats = {
            "mode": self.redirect_code,
            "requests_served": self.balancer.counter,
            "backends": [f"{h}:{p}" for h, p in BACKENDS],
            "timestamp": datetime.now().isoformat()
        }
        body = json.dumps(stats, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # Usiamo il nostro log()


def create_redirect_handler(balancer: RoundRobinBalancer, redirect_code: int):
    """Factory che crea la classe handler con configurazione iniettata."""
    class Handler(RedirectHandler):
        pass
    Handler.balancer = balancer
    Handler.redirect_code = redirect_code
    return Handler


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="HTTP Redirect Load Balancer — Distributed Systems Lab"
    )
    parser.add_argument(
        "--mode", type=int, choices=[301, 302], default=302,
        help="Codice di redirect: 302 (temporaneo, default) o 301 (permanente)"
    )
    parser.add_argument(
        "--port", type=int, default=DEFAULT_LB_PORT,
        help=f"Porta del load balancer (default: {DEFAULT_LB_PORT})"
    )
    args = parser.parse_args()

    balancer = RoundRobinBalancer(BACKENDS)
    handler_class = create_redirect_handler(balancer, args.mode)
    server = HTTPServer(("127.0.0.1", args.port), handler_class)

    mode_desc = {
        302: "302 Found (Temporary Redirect)",
        301: "301 Moved Permanently (Permanent Redirect)"
    }

    print("=" * 62)
    print("  HTTP REDIRECT LOAD BALANCER — Distributed Systems Lab")
    print("=" * 62)
    print(f"  Porta:        http://127.0.0.1:{args.port}/")
    print(f"  Modalità:     {mode_desc[args.mode]}")
    print(f"  Status page:  http://127.0.0.1:{args.port}/status")
    print(f"  Backends:")
    for h, p in BACKENDS:
        print(f"    → http://{h}:{p}/")
    print("=" * 62)

    if args.mode == 301:
        print()
        print("  ⚠  ATTENZIONE: modalità 301 (permanente)")
        print("     Il browser cacherà il redirect. Per resettare:")
        print("     - Chrome: Ctrl+Shift+Del → Cached images and files")
        print("     - Firefox: Ctrl+Shift+Del → Cache")
        print("     - Oppure usare una finestra in Incognito/Private")
        print()

    print(f"  Per connettersi: aprire http://127.0.0.1:{args.port}/")
    print(f"  Per terminare:   Ctrl+C")
    print("=" * 62)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Arresto del load balancer (Ctrl+C)")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

