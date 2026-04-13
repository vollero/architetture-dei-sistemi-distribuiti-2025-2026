#!/usr/bin/env python3
"""
Nodo secondario per replica primary-secondary.

Espone:
- protocollo client per letture;
- protocollo interno di replica per applicare update dal primary.
"""

import argparse
import json
import socket
import threading
import time
from datetime import datetime
from typing import Callable


HOST = "127.0.0.1"
PORT = 6391
APPLY_DELAY_SECONDS = 0.0

ClientHandler = Callable[[str], tuple[str, bool]]


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    thread_name = threading.current_thread().name
    print(f"[{timestamp}] [{thread_name}] {message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--apply-delay", type=float, default=APPLY_DELAY_SECONDS)
    return parser.parse_args()


class SecondaryStore:
    def __init__(self, apply_delay_seconds: float) -> None:
        self._data: dict[str, str] = {}
        self._lock = threading.Lock()
        self._apply_delay_seconds = apply_delay_seconds
        self._client_handlers: dict[str, ClientHandler] = {
            "PING": self._handle_ping,
            "GET": self._handle_get,
            "EXISTS": self._handle_exists,
            "KEYS": self._handle_keys,
            "QUIT": self._handle_quit,
        }

    def execute_client(self, line: str) -> tuple[str, bool]:
        stripped = line.strip()
        if not stripped:
            return "ERR empty command", False

        command, *rest = stripped.split(" ", 1)
        command = command.upper()
        argument_blob = rest[0] if rest else ""

        handler = self._client_handlers.get(command)
        if handler is None:
            return "ERR read-only secondary", False
        return handler(argument_blob)

    def apply_replication(self, record: dict[str, str]) -> str:
        operation = record.get("op")
        key = record.get("key", "")
        if operation not in {"SET", "DELETE", "INCR"} or not key:
            return "ERR invalid replication record"

        if self._apply_delay_seconds > 0:
            time.sleep(self._apply_delay_seconds)

        with self._lock:
            if operation == "SET":
                self._data[key] = record["value"]
                return "ACK"

            if operation == "DELETE":
                self._data.pop(key, None)
                return "ACK"

            current = self._data.get(key, "0")
            try:
                int(current)
            except ValueError:
                return "ERR replica value is not an integer"

            self._data[key] = record["value"]
            return "ACK"

    def _handle_ping(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: PING", False
        return "OK PONG", False

    def _handle_get(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: GET <key>", False
        with self._lock:
            if key not in self._data:
                return "NOT_FOUND", False
            value = self._data[key]
        return f"OK {value}", False

    def _handle_exists(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: EXISTS <key>", False
        with self._lock:
            exists = 1 if key in self._data else 0
        return f"OK {exists}", False

    def _handle_keys(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: KEYS", False
        with self._lock:
            keys = " ".join(sorted(self._data.keys()))
        return f"OK {keys}".rstrip(), False

    def _handle_quit(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: QUIT", False
        return "OK BYE", True


def handle_client_connection(
    connection: socket.socket,
    address: tuple[str, int],
    store: SecondaryStore,
) -> None:
    log(f"client connection from {address[0]}:{address[1]}")
    with connection:
        connection_file = connection.makefile("rwb")
        while True:
            raw_line = connection_file.readline()
            if not raw_line:
                break

            line = raw_line.decode("utf-8", errors="replace")
            log(f"client request: {line.rstrip()}")
            response, should_close = store.execute_client(line)
            connection_file.write((response + "\n").encode("utf-8"))
            connection_file.flush()
            log(f"client response: {response}")
            if should_close:
                break


def handle_replica_connection(
    connection: socket.socket,
    address: tuple[str, int],
    store: SecondaryStore,
) -> None:
    log(f"replication connection from {address[0]}:{address[1]}")
    with connection:
        connection_file = connection.makefile("rwb")
        while True:
            raw_line = connection_file.readline()
            if not raw_line:
                break

            line = raw_line.decode("utf-8", errors="replace").strip()
            log(f"replication request: {line}")
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                response = "ERR invalid json"
            else:
                response = store.apply_replication(record)

            connection_file.write((response + "\n").encode("utf-8"))
            connection_file.flush()
            log(f"replication response: {response}")


def serve() -> None:
    args = parse_args()
    store = SecondaryStore(args.apply_delay)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.bind((args.host, args.port))
        client_socket.listen()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as replica_socket:
            replica_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            replica_socket.bind((args.host, args.port + 100))
            replica_socket.listen()

            log(f"secondary client endpoint on {args.host}:{args.port}")
            log(f"secondary replication endpoint on {args.host}:{args.port + 100}")

            def accept_loop(
                server_socket: socket.socket,
                handler: Callable[[socket.socket, tuple[str, int], SecondaryStore], None],
            ) -> None:
                while True:
                    connection, address = server_socket.accept()
                    worker = threading.Thread(
                        target=handler,
                        args=(connection, address, store),
                        daemon=True,
                    )
                    worker.start()

            client_thread = threading.Thread(
                target=accept_loop,
                args=(client_socket, handle_client_connection),
                daemon=True,
                name="secondary-client-acceptor",
            )
            client_thread.start()

            accept_loop(replica_socket, handle_replica_connection)


if __name__ == "__main__":
    serve()
