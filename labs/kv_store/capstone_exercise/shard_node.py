#!/usr/bin/env python3
"""
Shard versionato per la capstone exercise.
"""

import argparse
import json
import socket
import threading
from dataclasses import dataclass
from datetime import datetime


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    thread_name = threading.current_thread().name
    print(f"[{timestamp}] [{thread_name}] {message}")


@dataclass
class Record:
    value: str
    version: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-id", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    return parser.parse_args()


class VersionedShard:
    def __init__(self, shard_id: str) -> None:
        self._shard_id = shard_id
        self._lock = threading.Lock()
        self._data: dict[str, Record] = {}
        self._imports = 0

    def handle(self, raw_line: str) -> str:
        try:
            message = json.loads(raw_line)
        except json.JSONDecodeError:
            return self._json({"status": "ERR", "error": "invalid json"})

        operation = str(message.get("op", "")).upper()
        key = str(message.get("key", ""))

        with self._lock:
            if operation == "PING":
                return self._json({"status": "OK", "shard": self._shard_id})

            if operation == "GET":
                record = self._data.get(key)
                if record is None:
                    return self._json({"status": "NOT_FOUND", "shard": self._shard_id})
                return self._json(
                    {
                        "status": "OK",
                        "shard": self._shard_id,
                        "value": record.value,
                        "version": record.version,
                    }
                )

            if operation == "GETV":
                record = self._data.get(key)
                if record is None:
                    return self._json({"status": "NOT_FOUND", "shard": self._shard_id})
                return self._json(
                    {
                        "status": "OK",
                        "shard": self._shard_id,
                        "value": record.value,
                        "version": record.version,
                    }
                )

            if operation == "SET":
                value = str(message.get("value", ""))
                current = self._data.get(key)
                current_version = -1 if current is None else current.version
                next_version = current_version + 1
                self._data[key] = Record(value=value, version=next_version)
                return self._json(
                    {"status": "OK", "shard": self._shard_id, "version": next_version}
                )

            if operation == "CAS":
                try:
                    expected_version = int(message["expected_version"])
                except (KeyError, TypeError, ValueError):
                    return self._json({"status": "ERR", "error": "invalid expected_version"})
                value = str(message.get("value", ""))
                current = self._data.get(key)
                current_version = -1 if current is None else current.version
                if current_version != expected_version:
                    return self._json(
                        {
                            "status": "VERSION_MISMATCH",
                            "shard": self._shard_id,
                            "current": current_version,
                        }
                    )
                next_version = current_version + 1
                self._data[key] = Record(value=value, version=next_version)
                return self._json(
                    {"status": "OK", "shard": self._shard_id, "version": next_version}
                )

            if operation == "DELETE":
                if key not in self._data:
                    return self._json({"status": "NOT_FOUND", "shard": self._shard_id})
                deleted_version = self._data[key].version
                del self._data[key]
                return self._json(
                    {
                        "status": "OK",
                        "shard": self._shard_id,
                        "deleted_version": deleted_version,
                    }
                )

            if operation == "KEYS":
                return self._json(
                    {"status": "OK", "shard": self._shard_id, "keys": sorted(self._data)}
                )

            if operation == "LIST_ITEMS":
                items = {
                    key: {"value": record.value, "version": record.version}
                    for key, record in sorted(self._data.items())
                }
                return self._json({"status": "OK", "shard": self._shard_id, "items": items})

            if operation == "IMPORT_KEY":
                try:
                    version = int(message["version"])
                except (KeyError, TypeError, ValueError):
                    return self._json({"status": "ERR", "error": "invalid version"})
                value = str(message.get("value", ""))
                current = self._data.get(key)
                if current is not None and current.version > version:
                    return self._json(
                        {
                            "status": "ERR",
                            "error": "stale import",
                            "current": current.version,
                        }
                    )
                self._data[key] = Record(value=value, version=version)
                self._imports += 1
                return self._json(
                    {
                        "status": "OK",
                        "shard": self._shard_id,
                        "imported": key,
                        "version": version,
                    }
                )

            if operation == "DELETE_LOCAL":
                try:
                    expected_version = int(message["version"])
                except (KeyError, TypeError, ValueError):
                    return self._json({"status": "ERR", "error": "invalid version"})
                current = self._data.get(key)
                if current is None:
                    return self._json({"status": "OK", "shard": self._shard_id, "deleted": key})
                if current.version != expected_version:
                    return self._json(
                        {
                            "status": "ERR",
                            "error": "version changed before local delete",
                            "current": current.version,
                        }
                    )
                del self._data[key]
                return self._json({"status": "OK", "shard": self._shard_id, "deleted": key})

            if operation == "STATS":
                return self._json(
                    {
                        "status": "OK",
                        "shard": self._shard_id,
                        "keys": len(self._data),
                        "imports": self._imports,
                    }
                )

        return self._json({"status": "ERR", "error": "unknown op"})

    @staticmethod
    def _json(payload: dict[str, object]) -> str:
        return json.dumps(payload, sort_keys=True)


def handle_connection(
    connection: socket.socket,
    address: tuple[str, int],
    shard: VersionedShard,
) -> None:
    log(f"connection from {address[0]}:{address[1]}")
    with connection:
        connection_file = connection.makefile("rwb")
        while True:
            raw_line = connection_file.readline()
            if not raw_line:
                break
            response = shard.handle(raw_line.decode("utf-8", errors="replace").strip())
            connection_file.write((response + "\n").encode("utf-8"))
            connection_file.flush()


def serve() -> None:
    args = parse_args()
    shard = VersionedShard(args.shard_id)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((args.host, args.port))
        server_socket.listen()
        log(f"capstone shard {args.shard_id} listening on {args.host}:{args.port}")

        while True:
            connection, address = server_socket.accept()
            threading.Thread(
                target=handle_connection,
                args=(connection, address, shard),
                daemon=True,
            ).start()


if __name__ == "__main__":
    serve()
