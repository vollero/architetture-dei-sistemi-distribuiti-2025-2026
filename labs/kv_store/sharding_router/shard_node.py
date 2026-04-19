#!/usr/bin/env python3
"""
Shard node per laboratorio di partizionamento.
"""

import argparse
import json
import socket
import threading
from datetime import datetime


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    thread_name = threading.current_thread().name
    print(f"[{timestamp}] [{thread_name}] {message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-id", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    return parser.parse_args()


class ShardNode:
    def __init__(self, shard_id: str) -> None:
        self._shard_id = shard_id
        self._lock = threading.Lock()
        self._data: dict[str, str] = {}
        self._op_counts: dict[str, int] = {
            "SET": 0,
            "GET": 0,
            "DELETE": 0,
            "EXISTS": 0,
            "INCR": 0,
            "KEYS": 0,
        }

    def handle(self, raw_line: str) -> str:
        try:
            message = json.loads(raw_line)
        except json.JSONDecodeError:
            return json.dumps({"status": "ERR", "error": "invalid json"})

        operation = str(message.get("op", "")).upper()
        key = str(message.get("key", ""))

        with self._lock:
            if operation in self._op_counts:
                self._op_counts[operation] += 1

            if operation == "SET":
                self._data[key] = str(message.get("value", ""))
                return json.dumps({"status": "OK", "shard": self._shard_id})

            if operation == "GET":
                if key not in self._data:
                    return json.dumps({"status": "NOT_FOUND", "shard": self._shard_id})
                return json.dumps(
                    {"status": "OK", "shard": self._shard_id, "value": self._data[key]}
                )

            if operation == "DELETE":
                if key not in self._data:
                    return json.dumps({"status": "NOT_FOUND", "shard": self._shard_id})
                del self._data[key]
                return json.dumps({"status": "OK", "shard": self._shard_id})

            if operation == "EXISTS":
                exists = 1 if key in self._data else 0
                return json.dumps({"status": "OK", "shard": self._shard_id, "exists": exists})

            if operation == "INCR":
                current = self._data.get(key, "0")
                try:
                    numeric = int(current)
                except ValueError:
                    return json.dumps({"status": "ERR", "error": "value is not an integer"})
                numeric += 1
                self._data[key] = str(numeric)
                return json.dumps({"status": "OK", "shard": self._shard_id, "value": numeric})

            if operation == "KEYS":
                return json.dumps(
                    {"status": "OK", "shard": self._shard_id, "keys": sorted(self._data.keys())}
                )

            if operation == "STATS":
                return json.dumps(
                    {
                        "status": "OK",
                        "shard": self._shard_id,
                        "keys": len(self._data),
                        "ops": dict(self._op_counts),
                    }
                )

        return json.dumps({"status": "ERR", "error": "unknown op"})


def handle_connection(connection: socket.socket, address: tuple[str, int], shard: ShardNode) -> None:
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
    shard = ShardNode(args.shard_id)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((args.host, args.port))
        server_socket.listen()
        log(f"shard {args.shard_id} listening on {args.host}:{args.port}")

        while True:
            connection, address = server_socket.accept()
            threading.Thread(
                target=handle_connection,
                args=(connection, address, shard),
                daemon=True,
            ).start()


if __name__ == "__main__":
    serve()
