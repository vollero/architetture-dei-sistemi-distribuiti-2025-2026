#!/usr/bin/env python3
"""
KV store versionato con compare-and-set.
"""

import socket
import threading
from datetime import datetime
from typing import Callable


HOST = "127.0.0.1"
PORT = 6450

CommandHandler = Callable[[str], tuple[str, bool]]


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    thread_name = threading.current_thread().name
    print(f"[{timestamp}] [{thread_name}] {message}")


class VersionedStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: dict[str, tuple[str, int]] = {}
        self._handlers: dict[str, CommandHandler] = {
            "PING": self._handle_ping,
            "GET": self._handle_get,
            "GETV": self._handle_getv,
            "SET": self._handle_set,
            "CAS": self._handle_cas,
            "DELETE": self._handle_delete,
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

    def _handle_get(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: GET <key>", False
        with self._lock:
            record = self._data.get(key)
        if record is None:
            return "NOT_FOUND", False
        return f"OK {record[0]}", False

    def _handle_getv(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: GETV <key>", False
        with self._lock:
            record = self._data.get(key)
        if record is None:
            return "NOT_FOUND", False
        value, version = record
        return f"OK {value} version={version}", False

    def _handle_set(self, argument_blob: str) -> tuple[str, bool]:
        parts = argument_blob.split(" ", 1)
        if len(parts) != 2 or not parts[0]:
            return "ERR usage: SET <key> <value>", False
        key, value = parts
        with self._lock:
            _, current_version = self._data.get(key, ("", -1))
            next_version = current_version + 1
            self._data[key] = (value, next_version)
        return f"OK version={next_version}", False

    def _handle_cas(self, argument_blob: str) -> tuple[str, bool]:
        parts = argument_blob.split(" ", 2)
        if len(parts) != 3 or not parts[0]:
            return "ERR usage: CAS <key> <expected_version> <value>", False
        key, expected_text, value = parts
        try:
            expected_version = int(expected_text)
        except ValueError:
            return "ERR expected_version must be an integer", False

        with self._lock:
            record = self._data.get(key)
            current_version = -1 if record is None else record[1]
            if current_version != expected_version:
                return f"ERR version_mismatch current={current_version}", False
            next_version = current_version + 1
            self._data[key] = (value, next_version)
        return f"OK version={next_version}", False

    def _handle_delete(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: DELETE <key>", False
        with self._lock:
            if key not in self._data:
                return "NOT_FOUND", False
            del self._data[key]
        return "OK", False

    def _handle_quit(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: QUIT", False
        return "OK BYE", True


def handle_client(connection: socket.socket, address: tuple[str, int], store: VersionedStore) -> None:
    log(f"connection from {address[0]}:{address[1]}")
    with connection:
        connection_file = connection.makefile("rwb")
        while True:
            raw_line = connection_file.readline()
            if not raw_line:
                break
            line = raw_line.decode("utf-8", errors="replace")
            response, should_close = store.execute(line)
            connection_file.write((response + "\n").encode("utf-8"))
            connection_file.flush()
            if should_close:
                break


def serve() -> None:
    store = VersionedStore()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        log(f"versioned kv store listening on {HOST}:{PORT}")
        while True:
            connection, address = server_socket.accept()
            threading.Thread(
                target=handle_client,
                args=(connection, address, store),
                daemon=True,
            ).start()


if __name__ == "__main__":
    serve()
