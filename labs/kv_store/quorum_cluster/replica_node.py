#!/usr/bin/env python3
"""
Replica node per laboratorio quorum.
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
    parser.add_argument("--node-id", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    return parser.parse_args()


class ReplicaNode:
    def __init__(self, node_id: str) -> None:
        self._node_id = node_id
        self._lock = threading.Lock()
        self._data: dict[str, dict[str, object]] = {}

    def handle_message(self, raw_line: str) -> str:
        try:
            message = json.loads(raw_line)
        except json.JSONDecodeError:
            return json.dumps({"status": "ERR", "error": "invalid json"})

        message_type = message.get("type")
        if message_type == "read":
            key = str(message.get("key", ""))
            if not key:
                return json.dumps({"status": "ERR", "error": "missing key"})
            with self._lock:
                record = self._data.get(key)
            if record is None:
                return json.dumps(
                    {"status": "OK", "found": False, "node": self._node_id, "key": key}
                )
            return json.dumps(
                {
                    "status": "OK",
                    "found": True,
                    "node": self._node_id,
                    "key": key,
                    "value": record["value"],
                    "version": record["version"],
                }
            )

        if message_type == "write":
            key = str(message.get("key", ""))
            value = str(message.get("value", ""))
            version = int(message.get("version", 0))
            if not key:
                return json.dumps({"status": "ERR", "error": "missing key"})
            with self._lock:
                current = self._data.get(key)
                current_version = int(current["version"]) if current else -1
                if version >= current_version:
                    self._data[key] = {"value": value, "version": version}
            return json.dumps({"status": "ACK", "node": self._node_id, "version": version})

        if message_type == "status":
            with self._lock:
                keys = sorted(self._data.keys())
            return json.dumps({"status": "OK", "node": self._node_id, "keys": keys})

        return json.dumps({"status": "ERR", "error": "unknown type"})


def handle_connection(
    connection: socket.socket,
    address: tuple[str, int],
    replica: ReplicaNode,
) -> None:
    log(f"connection from {address[0]}:{address[1]}")
    with connection:
        connection_file = connection.makefile("rwb")
        while True:
            raw_line = connection_file.readline()
            if not raw_line:
                break
            response = replica.handle_message(raw_line.decode("utf-8", errors="replace").strip())
            connection_file.write((response + "\n").encode("utf-8"))
            connection_file.flush()
            log(f"response: {response}")


def serve() -> None:
    args = parse_args()
    replica = ReplicaNode(args.node_id)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((args.host, args.port))
        server_socket.listen()
        log(f"replica {args.node_id} listening on {args.host}:{args.port}")

        while True:
            connection, address = server_socket.accept()
            threading.Thread(
                target=handle_connection,
                args=(connection, address, replica),
                daemon=True,
            ).start()


if __name__ == "__main__":
    serve()
