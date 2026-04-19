#!/usr/bin/env python3
"""
Coordinator con quorum di lettura e scrittura.
"""

import argparse
import json
import socket
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Callable


CommandHandler = Callable[[str], tuple[str, bool]]


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    thread_name = threading.current_thread().name
    print(f"[{timestamp}] [{thread_name}] {message}")


@dataclass(frozen=True)
class ReplicaEndpoint:
    host: str
    port: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=6420)
    parser.add_argument("--read-quorum", type=int, default=2)
    parser.add_argument("--write-quorum", type=int, default=2)
    parser.add_argument(
        "--replicas",
        nargs="+",
        default=["127.0.0.1:6421", "127.0.0.1:6422", "127.0.0.1:6423"],
    )
    return parser.parse_args()


class QuorumCoordinator:
    def __init__(self, replicas: list[ReplicaEndpoint], read_quorum: int, write_quorum: int) -> None:
        self._replicas = replicas
        self._read_quorum = read_quorum
        self._write_quorum = write_quorum
        self._handlers: dict[str, CommandHandler] = {
            "PING": self._handle_ping,
            "STATUS": self._handle_status,
            "SET": self._handle_set,
            "GET": self._handle_get,
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

    def _rpc(self, replica: ReplicaEndpoint, message: dict[str, object]) -> dict[str, object] | None:
        try:
            with socket.create_connection((replica.host, replica.port), timeout=1.0) as connection:
                connection_file = connection.makefile("rwb")
                payload = json.dumps(message) + "\n"
                connection_file.write(payload.encode("utf-8"))
                connection_file.flush()
                response = connection_file.readline().decode("utf-8", errors="replace").strip()
        except OSError:
            return None
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return None

    def _collect_reads(self, key: str, limit: int | None = None) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        for replica in self._replicas:
            response = self._rpc(replica, {"type": "read", "key": key})
            if response is None or response.get("status") != "OK":
                continue
            results.append(response)
            if limit is not None and len(results) >= limit:
                break
        return results

    def _highest_version(self, reads: list[dict[str, object]]) -> tuple[int, str | None]:
        best_version = -1
        best_value: str | None = None
        for read in reads:
            if not bool(read.get("found", False)):
                continue
            version = int(read.get("version", -1))
            if version > best_version:
                best_version = version
                best_value = str(read.get("value", ""))
        return best_version, best_value

    def _handle_ping(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: PING", False
        return "OK PONG", False

    def _handle_status(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: STATUS", False
        return (
            f"OK N={len(self._replicas)} R={self._read_quorum} W={self._write_quorum}",
            False,
        )

    def _handle_set(self, argument_blob: str) -> tuple[str, bool]:
        parts = argument_blob.split(" ", 1)
        if len(parts) != 2 or not parts[0]:
            return "ERR usage: SET <key> <value>", False
        key, value = parts
        reads = self._collect_reads(key)
        current_version, _ = self._highest_version(reads)
        next_version = current_version + 1

        acknowledgements = 0
        for replica in self._replicas:
            response = self._rpc(
                replica,
                {"type": "write", "key": key, "value": value, "version": next_version},
            )
            if response is not None and response.get("status") == "ACK":
                acknowledgements += 1
                if acknowledgements >= self._write_quorum:
                    return f"OK version={next_version} acks={acknowledgements}", False

        return f"ERR write quorum not reached acks={acknowledgements}", False

    def _handle_get(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: GET <key>", False

        reads = self._collect_reads(key, limit=self._read_quorum)
        if len(reads) < self._read_quorum:
            return f"ERR read quorum not reached responses={len(reads)}", False

        version, value = self._highest_version(reads)
        if version < 0 or value is None:
            return "NOT_FOUND", False
        return f"OK {value} version={version}", False

    def _handle_quit(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: QUIT", False
        return "OK BYE", True


def handle_client(
    connection: socket.socket,
    address: tuple[str, int],
    coordinator: QuorumCoordinator,
) -> None:
    log(f"client connection from {address[0]}:{address[1]}")
    with connection:
        connection_file = connection.makefile("rwb")
        while True:
            raw_line = connection_file.readline()
            if not raw_line:
                break
            line = raw_line.decode("utf-8", errors="replace")
            log(f"request: {line.rstrip()}")
            response, should_close = coordinator.execute(line)
            connection_file.write((response + "\n").encode("utf-8"))
            connection_file.flush()
            log(f"response: {response}")
            if should_close:
                break


def serve() -> None:
    args = parse_args()
    replicas = [
        ReplicaEndpoint(host=entry.split(":", 1)[0], port=int(entry.split(":", 1)[1]))
        for entry in args.replicas
    ]
    coordinator = QuorumCoordinator(replicas, args.read_quorum, args.write_quorum)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((args.host, args.port))
        server_socket.listen()
        log(
            f"quorum coordinator listening on {args.host}:{args.port} "
            f"N={len(replicas)} R={args.read_quorum} W={args.write_quorum}"
        )

        while True:
            connection, address = server_socket.accept()
            threading.Thread(
                target=handle_client,
                args=(connection, address, coordinator),
                daemon=True,
            ).start()


if __name__ == "__main__":
    serve()
