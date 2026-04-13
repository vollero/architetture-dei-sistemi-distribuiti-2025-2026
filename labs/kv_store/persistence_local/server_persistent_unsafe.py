#!/usr/bin/env python3
"""
KV store con persistenza locale unsafe.

Il server aggiorna subito lo stato in RAM e risponde OK al client, ma salva
su disco solo tramite snapshot periodici in background. Dopo un crash possono
quindi perdersi scritture gia' confermate.
"""

import argparse
import json
import os
import socket
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable


HOST = "127.0.0.1"
PORT = 6384
SNAPSHOT_INTERVAL_SECONDS = 2.0

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
        default="/tmp/kv_store_persistence_unsafe",
        help="directory usata per lo snapshot locale",
    )
    return parser.parse_args()


class SnapshotKVStore:
    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._snapshot_path = data_dir / "snapshot.json"
        self._data: dict[str, str] = {}
        self._lock = threading.Lock()
        self._dirty = False
        self._stop_event = threading.Event()
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
        self._load_snapshot()
        self._flusher = threading.Thread(target=self._flush_loop, daemon=True, name="snapshot-flusher")
        self._flusher.start()

    def _load_snapshot(self) -> None:
        if not self._snapshot_path.exists():
            log("no snapshot found, starting with empty state")
            return

        with self._snapshot_path.open("r", encoding="utf-8") as snapshot_file:
            loaded = json.load(snapshot_file)

        if not isinstance(loaded, dict):
            raise ValueError("snapshot root must be a dictionary")

        self._data = {str(key): str(value) for key, value in loaded.items()}
        log(f"loaded snapshot with {len(self._data)} keys")

    def close(self) -> None:
        self._stop_event.set()
        self._flusher.join(timeout=0.2)

    def _flush_loop(self) -> None:
        while not self._stop_event.wait(SNAPSHOT_INTERVAL_SECONDS):
            persisted = self.flush_snapshot()
            if persisted:
                log("background snapshot completed")

    def flush_snapshot(self) -> bool:
        with self._lock:
            if not self._dirty:
                return False
            snapshot = dict(self._data)
            self._dirty = False

        tmp_path = self._snapshot_path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as snapshot_file:
            json.dump(snapshot, snapshot_file, sort_keys=True)
            snapshot_file.flush()
            os.fsync(snapshot_file.fileno())

        os.replace(tmp_path, self._snapshot_path)
        return True

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
            self._data[key] = value
            self._dirty = True
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
            del self._data[key]
            self._dirty = True
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
            self._data[key] = str(numeric_value)
            self._dirty = True
        return f"OK {numeric_value}", False

    def _handle_sync(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: SYNC", False
        persisted = self.flush_snapshot()
        if persisted:
            return "OK SNAPSHOT_SAVED", False
        return "OK SNAPSHOT_ALREADY_CLEAN", False

    def _handle_crash(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: CRASH", False
        log("forced crash requested")
        os._exit(1)

    def _handle_quit(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: QUIT", False
        return "OK BYE", True


def handle_client(connection: socket.socket, address: tuple[str, int], store: SnapshotKVStore) -> None:
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
    store = SnapshotKVStore(Path(args.data_dir))

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((args.host, args.port))
            server_socket.listen()
            log(f"unsafe persistent kv store listening on {args.host}:{args.port}")
            log(f"snapshot dir: {args.data_dir}")

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
