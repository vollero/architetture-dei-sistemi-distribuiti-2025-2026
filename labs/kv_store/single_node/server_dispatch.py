#!/usr/bin/env python3
"""
KV Store v0 - variante con command dispatch table.

Questa versione espone lo stesso protocollo di server.py, ma sostituisce
la catena di if con un dizionario che mappa il nome del comando al relativo
handler. E' utile per discutere progettazione dell'interprete dei comandi.
"""

import socket
from datetime import datetime
from typing import Callable


HOST = "127.0.0.1"
PORT = 6381

CommandHandler = Callable[[str], tuple[str, bool]]


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")


class KVStore:
    def __init__(self) -> None:
        self._data: dict[str, str] = {}
        self._handlers: dict[str, CommandHandler] = {
            "PING": self._handle_ping,
            "SET": self._handle_set,
            "GET": self._handle_get,
            "DELETE": self._handle_delete,
            "EXISTS": self._handle_exists,
            "KEYS": self._handle_keys,
            "QUIT": self._handle_quit,
        }

    def execute(self, line: str) -> tuple[str, bool]:
        stripped = line.strip()
        if not stripped:
            return "ERR empty command", False

        command, *rest = stripped.split(" ", 1)
        command = command.upper()
        argument_blob = rest[0] if rest else ""

        handler = self._handlers.get(command)
        if handler is None:
            return "ERR unknown command", False

        return handler(argument_blob)

    def _handle_ping(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: PING", False
        return "OK PONG", False

    def _handle_set(self, argument_blob: str) -> tuple[str, bool]:
        parts = argument_blob.split(" ", 1)
        if len(parts) != 2 or not parts[0]:
            return "ERR usage: SET <key> <value>", False
        key, value = parts
        self._data[key] = value
        return "OK", False

    def _handle_get(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: GET <key>", False
        if key not in self._data:
            return "NOT_FOUND", False
        return f"OK {self._data[key]}", False

    def _handle_delete(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: DELETE <key>", False
        if key not in self._data:
            return "NOT_FOUND", False
        del self._data[key]
        return "OK", False

    def _handle_exists(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: EXISTS <key>", False
        return f"OK {1 if key in self._data else 0}", False

    def _handle_keys(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: KEYS", False
        keys = " ".join(sorted(self._data.keys()))
        return f"OK {keys}".rstrip(), False

    def _handle_quit(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: QUIT", False
        return "OK BYE", True


def serve() -> None:
    store = KVStore()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        log(f"KV store with dispatch table listening on {HOST}:{PORT}")

        while True:
            connection, address = server_socket.accept()
            log(f"connection from {address[0]}:{address[1]}")
            with connection:
                connection_file = connection.makefile("rwb")
                while True:
                    raw_line = connection_file.readline()
                    if not raw_line:
                        log(f"client disconnected {address[0]}:{address[1]}")
                        break

                    line = raw_line.decode("utf-8", errors="replace")
                    log(f"request: {line.rstrip()}")

                    response, should_close = store.execute(line)
                    connection_file.write((response + "\n").encode("utf-8"))
                    connection_file.flush()
                    log(f"response: {response}")

                    if should_close:
                        break


if __name__ == "__main__":
    serve()
