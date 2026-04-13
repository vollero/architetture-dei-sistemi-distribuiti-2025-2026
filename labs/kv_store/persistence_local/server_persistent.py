#!/usr/bin/env python3
"""
KV store con persistenza locale safe.

La risposta positiva alle operazioni mutanti arriva solo dopo che l'intento
e' stato scritto su append-only log e forzato su disco con fsync.
"""

import argparse
import json
import os
import socket
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable


HOST = "127.0.0.1"
PORT = 6385

CommandHandler = Callable[[str], tuple[str, bool]]


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    thread_name = threading.current_thread().name
    print(f"[{timestamp}] [{thread_name}] {message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument(
        "--data-dir",
        default="/tmp/kv_store_persistence_safe",
        help="directory usata per il write-ahead log locale",
    )
    return parser.parse_args()


class WriteAheadLogKVStore:
    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._log_path = data_dir / "operations.jsonl"
        self._data: dict[str, str] = {}
        self._lock = threading.Lock()
        self._handlers: dict[str, CommandHandler] = {
            "PING": self._handle_ping,
            "SET": self._handle_set,
            "GET": self._handle_get,
            "DELETE": self._handle_delete,
            "EXISTS": self._handle_exists,
            "KEYS": self._handle_keys,
            "INCR": self._handle_incr,
            "SYNC": self._handle_sync,
            "CRASH": self._handle_crash,
            "QUIT": self._handle_quit,
        }
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._recover()
        self._log_file = self._log_path.open("a", encoding="utf-8")

    def _recover(self) -> None:
        if not self._log_path.exists():
            log("no log found, starting with empty state")
            return

        with self._log_path.open("r", encoding="utf-8") as log_file:
            for line_number, raw_line in enumerate(log_file, start=1):
                stripped = raw_line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError:
                    log(f"stopped recovery at truncated record on line {line_number}")
                    break
                self._apply_record(record)

        log(f"recovered {len(self._data)} keys from log")

    def close(self) -> None:
        self._log_file.close()

    def _append_record(self, record: dict[str, str]) -> None:
        encoded = json.dumps(record, separators=(",", ":")) + "\n"
        self._log_file.write(encoded)
        self._log_file.flush()
        os.fsync(self._log_file.fileno())

    def _apply_record(self, record: dict[str, str]) -> None:
        operation = record["op"]
        key = record["key"]

        if operation == "SET":
            self._data[key] = record["value"]
            return

        if operation == "DELETE":
            self._data.pop(key, None)
            return

        if operation == "INCR":
            self._data[key] = record["value"]
            return

        raise ValueError(f"unknown log operation: {operation}")

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
        with self._lock:
            self._append_record({"op": "SET", "key": key, "value": value})
            self._data[key] = value
        return "OK", False

    def _handle_get(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: GET <key>", False
        with self._lock:
            if key not in self._data:
                return "NOT_FOUND", False
            value = self._data[key]
        return f"OK {value}", False

    def _handle_delete(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: DELETE <key>", False
        with self._lock:
            if key not in self._data:
                return "NOT_FOUND", False
            self._append_record({"op": "DELETE", "key": key})
            del self._data[key]
        return "OK", False

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

    def _handle_incr(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: INCR <key>", False
        with self._lock:
            current = self._data.get(key, "0")
            try:
                numeric_value = int(current)
            except ValueError:
                return "ERR value is not an integer", False
            numeric_value += 1
            encoded_value = str(numeric_value)
            self._append_record({"op": "INCR", "key": key, "value": encoded_value})
            self._data[key] = encoded_value
        return f"OK {numeric_value}", False

    def _handle_sync(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: SYNC", False
        with self._lock:
            self._log_file.flush()
            os.fsync(self._log_file.fileno())
        return "OK ALREADY_DURABLE", False

    def _handle_crash(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: CRASH", False
        log("forced crash requested")
        os._exit(1)

    def _handle_quit(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: QUIT", False
        return "OK BYE", True


def handle_client(connection: socket.socket, address: tuple[str, int], store: WriteAheadLogKVStore) -> None:
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


def serve() -> None:
    args = parse_args()
    store = WriteAheadLogKVStore(Path(args.data_dir))

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((args.host, args.port))
            server_socket.listen()
            log(f"safe persistent kv store listening on {args.host}:{args.port}")
            log(f"log dir: {args.data_dir}")

            while True:
                connection, address = server_socket.accept()
                worker = threading.Thread(
                    target=handle_client,
                    args=(connection, address, store),
                    daemon=True,
                )
                worker.start()
    finally:
        store.close()


if __name__ == "__main__":
    serve()
