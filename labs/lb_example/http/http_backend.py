#!/usr/bin/env python3
"""
HTTP Backend Server — Distributed Systems Lab (HTTP Redirect)
=============================================================
Un semplice server HTTP che risponde alle richieste identificandosi
con il proprio numero di porta. Serve come backend per il load balancer
basato su HTTP redirect.

Uso:
    python http_backend.py <porta>

Esempio:
    python http_backend.py 8001
    python http_backend.py 8002

Poi aprire nel browser:
    http://127.0.0.1:8001/

NOTA DIDATTICA:
    Questo server usa http.server dalla libreria standard di Python.
    In produzione si userebbero framework come Flask, FastAPI o Django,
    ma per comprendere il protocollo HTTP a basso livello, la libreria
    standard è ideale.
"""

import json
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


def log(port: int, msg: str) -> None:
    """Log con timestamp e identificativo del server."""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] BACKEND:{port} — {msg}")


class BackendHandler(BaseHTTPRequestHandler):
    """
    Handler HTTP che gestisce le richieste in arrivo.

    Ogni risposta include chiaramente l'identità del server (porta),
    in modo che lo studente possa osservare a quale backend è stato
    instradato dopo il redirect.

    Endpoint:
      GET /           → Pagina HTML con identità del server
      GET /api/info   → Risposta JSON con metadati del server
      GET /api/echo   → Echo dei query parameters in JSON
      GET /health     → Health check (risponde sempre 200 OK)
    """

    # La porta viene iniettata dalla factory create_handler_class()
    server_port = 0

    def do_GET(self):
        """
        Gestisce le richieste HTTP GET.

        Il metodo HTTP GET è usato per richiedere una risorsa.
        Secondo la specifica HTTP/1.1 (RFC 7231), GET deve essere:
          - Safe: non deve modificare lo stato del server
          - Idempotent: richieste ripetute producono lo stesso risultato

        Il parsing dell'URL avviene con urllib.parse.urlparse che
        decompone l'URL nei suoi componenti (scheme, netloc, path,
        params, query, fragment).
        """
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        log(self.server_port, f"GET {self.path} da {self.client_address[0]}:{self.client_address[1]}")

        # ── Mostriamo gli header della richiesta per scopi didattici ──
        # In particolare, l'header "Host" ci dice a quale host:porta
        # il client pensava di connettersi. Dopo un redirect, il valore
        # di Host cambierà rispetto a quello originale verso il LB.
        host_header = self.headers.get("Host", "N/A")
        referer = self.headers.get("Referer", "N/A")
        user_agent = self.headers.get("User-Agent", "N/A")

        log(self.server_port, f"  Host: {host_header} | Referer: {referer}")

        if path == "/" or path == "/index.html":
            self._serve_html(host_header, user_agent)
        elif path == "/api/info":
            self._serve_json_info(host_header)
        elif path == "/api/echo":
            self._serve_json_echo(query)
        elif path == "/health":
            self._serve_health()
        else:
            self._serve_404()

    def _serve_html(self, host_header: str, user_agent: str):
        """
        Serve la pagina HTML principale con l'identità del server.

        La pagina include:
          - Il numero di porta del backend (per verificare il routing)
          - L'header Host ricevuto (per osservare il cambio dopo redirect)
          - Un timestamp (per verificare che non si tratta di cache)
          - Un pulsante per fare una nuova richiesta (utile per 302)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Backend Server :{self.server_port}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 700px;
            margin: 60px auto;
            background: #f5f7fa;
            color: #333;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        }}
        .server-id {{
            font-size: 3em;
            font-weight: bold;
            color: #1B4F72;
            text-align: center;
            margin: 10px 0;
        }}
        .badge {{
            display: inline-block;
            background: #2E75B6;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
        }}
        td:first-child {{
            font-weight: bold;
            width: 40%;
            color: #555;
        }}
        code {{
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Consolas', monospace;
            font-size: 0.9em;
        }}
        .btn {{
            display: inline-block;
            background: #2E75B6;
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 6px;
            font-size: 1em;
            cursor: pointer;
            text-decoration: none;
            margin-top: 10px;
        }}
        .btn:hover {{ background: #1B4F72; }}
        .note {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 12px 16px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
            font-size: 0.9em;
        }}
        h2 {{ color: #1B4F72; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; }}
    </style>
</head>
<body>
    <div class="card">
        <div style="text-align:center">
            <span class="badge">HTTP Backend</span>
        </div>
        <div class="server-id">Server :{self.server_port}</div>

        <h2>Dettagli della Richiesta</h2>
        <table>
            <tr><td>Porta del backend</td><td><code>{self.server_port}</code></td></tr>
            <tr><td>Header <code>Host</code></td><td><code>{host_header}</code></td></tr>
            <tr><td>Timestamp</td><td><code>{timestamp}</code></td></tr>
            <tr><td>Client IP</td><td><code>{self.client_address[0]}:{self.client_address[1]}</code></td></tr>
            <tr><td>User-Agent</td><td style="font-size:0.8em"><code>{user_agent[:80]}</code></td></tr>
        </table>

        <div class="note">
            <strong>Osserva:</strong> L'header <code>Host</code> riflette l'indirizzo a cui
            il browser si è connesso <em>dopo</em> il redirect. Con <strong>302</strong>, ogni
            nuova richiesta passa dal load balancer. Con <strong>301</strong>, il browser
            memorizza il redirect e va direttamente al backend.
        </div>

        <div style="text-align:center; margin-top:20px">
            <a class="btn" href="javascript:location.reload()">Ricarica questa pagina</a>
            <a class="btn" href="http://127.0.0.1:8080/" style="background:#27ae60">
                Torna al Load Balancer (:8080)
            </a>
        </div>
    </div>
</body>
</html>"""

        self._send_response(200, "text/html; charset=utf-8", html.encode("utf-8"))

    def _serve_json_info(self, host_header: str):
        """Endpoint JSON con metadati del server (utile per test programmatici)."""
        info = {
            "server_port": self.server_port,
            "host_header": host_header,
            "timestamp": datetime.now().isoformat(),
            "client": f"{self.client_address[0]}:{self.client_address[1]}"
        }
        body = json.dumps(info, indent=2).encode("utf-8")
        self._send_response(200, "application/json", body)

    def _serve_json_echo(self, query: dict):
        """Echo dei query parameters (utile per testare redirect con parametri)."""
        echo = {
            "server_port": self.server_port,
            "query_params": {k: v[0] if len(v) == 1 else v for k, v in query.items()},
            "timestamp": datetime.now().isoformat()
        }
        body = json.dumps(echo, indent=2).encode("utf-8")
        self._send_response(200, "application/json", body)

    def _serve_health(self):
        """Health check endpoint. Risponde 200 OK se il server è attivo."""
        body = json.dumps({"status": "healthy", "port": self.server_port}).encode()
        self._send_response(200, "application/json", body)

    def _serve_404(self):
        """Risorsa non trovata."""
        body = f"404 Not Found (Backend:{self.server_port})".encode()
        self._send_response(404, "text/plain", body)

    def _send_response(self, status: int, content_type: str, body: bytes):
        """
        Invia una risposta HTTP completa.

        Una risposta HTTP è composta da:
          1. Status line:  HTTP/1.1 200 OK
          2. Headers:      Content-Type, Content-Length, ecc.
          3. Riga vuota:   separa headers dal body
          4. Body:         il contenuto della risposta

        L'header "X-Served-By" è un header custom (non standard) che
        i load balancer reali (es. Varnish, Fastly) usano per il
        debugging. Qui lo usiamo per lo stesso scopo didattico.
        """
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        # Header custom per debugging del load balancing
        self.send_header("X-Served-By", f"backend-{self.server_port}")
        # Cache-Control: no-store impedisce al browser di cachare la risposta.
        # Importante per osservare correttamente il comportamento del redirect.
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """Override per sopprimere il log di default di BaseHTTPRequestHandler."""
        pass  # Usiamo il nostro log() personalizzato


def create_handler_class(port: int):
    """
    Factory che crea una classe handler con la porta iniettata.

    Questo pattern è necessario perché BaseHTTPRequestHandler viene
    istanziata dal server HTTP per ogni richiesta, e non possiamo
    passare parametri al costruttore direttamente. Usiamo quindi
    una variabile di classe come meccanismo di iniezione.
    """
    class Handler(BackendHandler):
        server_port = port
    return Handler


def main():
    if len(sys.argv) != 2:
        print(f"Uso: {sys.argv[0]} <porta>")
        print(f"Esempio: {sys.argv[0]} 8001")
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        if not (1024 <= port <= 65535):
            raise ValueError
    except ValueError:
        print("Errore: la porta deve essere un intero tra 1024 e 65535.")
        sys.exit(1)

    handler_class = create_handler_class(port)
    server = HTTPServer(("127.0.0.1", port), handler_class)

    print("=" * 55)
    print(f"  HTTP Backend Server — porta {port}")
    print("=" * 55)
    print(f"  URL:       http://127.0.0.1:{port}/")
    print(f"  API info:  http://127.0.0.1:{port}/api/info")
    print(f"  Health:    http://127.0.0.1:{port}/health")
    print(f"  Ctrl+C per terminare")
    print("=" * 55)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log(port, "Arresto del server (Ctrl+C)")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

