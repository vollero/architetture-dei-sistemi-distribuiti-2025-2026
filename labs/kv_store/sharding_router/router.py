#!/usr/bin/env python3
"""
Router con hashing della chiave verso piu' shard.
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
class ShardEndpoint:
    shard_id: str
    host: str
    port: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=6430)
    parser.add_argument(
        "--shards",
        nargs="+",
        default=["S0:127.0.0.1:6431", "S1:127.0.0.1:6432"],
    )
    return parser.parse_args()


def stable_hash(key: str) -> int:
    return sum(key.encode("utf-8"))


class ShardingRouter:
    def __init__(self, shards: list[ShardEndpoint]) -> None:
        self._shards = shards
        self._handlers: dict[str, CommandHandler] = {
            "PING": self._handle_ping,
            "SET": self._handle_set,
            "GET": self._handle_get,
            "DELETE": self._handle_delete,
            "EXISTS": self._handle_exists,
            "INCR": self._handle_incr,
            "KEYS": self._handle_keys,
            "WHERE": self._handle_where,
            "STATS": self._handle_stats,
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

    def _rpc(self, shard: ShardEndpoint, message: dict[str, object]) -> dict[str, object] | None:
        try:
            with socket.create_connection((shard.host, shard.port), timeout=1.0) as connection:
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

    def _select_shard(self, key: str) -> ShardEndpoint:
        index = stable_hash(key) % len(self._shards)
        return self._shards[index]

    def _forward_keyed(self, key: str, op: str, value: str | None = None) -> tuple[str, bool]:
        shard = self._select_shard(key)
        payload: dict[str, object] = {"op": op, "key": key}
        if value is not None:
            payload["value"] = value
        response = self._rpc(shard, payload)
        if response is None:
            return f"ERR shard unreachable shard={shard.shard_id}", False
        status = str(response.get("status"))
        if status == "OK":
            if op == "GET":
                return f"OK {response['value']} shard={shard.shard_id}", False
            if op == "EXISTS":
                return f"OK {response['exists']} shard={shard.shard_id}", False
            if op == "INCR":
                return f"OK {response['value']} shard={shard.shard_id}", False
            return f"OK shard={shard.shard_id}", False
        if status == "NOT_FOUND":
            return "NOT_FOUND", False
        return f"ERR {response.get('error', 'shard error')}", False

    def _handle_ping(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: PING", False
        return "OK PONG", False

    def _handle_set(self, argument_blob: str) -> tuple[str, bool]:
        parts = argument_blob.split(" ", 1)
        if len(parts) != 2 or not parts[0]:
            return "ERR usage: SET <key> <value>", False
        return self._forward_keyed(parts[0], "SET", parts[1])

    def _handle_get(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: GET <key>", False
        return self._forward_keyed(key, "GET")

    def _handle_delete(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: DELETE <key>", False
        return self._forward_keyed(key, "DELETE")

    def _handle_exists(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: EXISTS <key>", False
        return self._forward_keyed(key, "EXISTS")

    def _handle_incr(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: INCR <key>", False
        return self._forward_keyed(key, "INCR")

    def _handle_keys(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: KEYS", False
        all_keys: list[str] = []
        for shard in self._shards:
            response = self._rpc(shard, {"op": "KEYS"})
            if response is None or response.get("status") != "OK":
                return f"ERR shard unreachable shard={shard.shard_id}", False
            all_keys.extend(str(key) for key in response.get("keys", []))
        return f"OK {' '.join(sorted(all_keys))}".rstrip(), False

    def _handle_where(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: WHERE <key>", False
        shard = self._select_shard(key)
        return f"OK shard={shard.shard_id} port={shard.port}", False

    def _handle_stats(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: STATS", False
        parts: list[str] = []
        for shard in self._shards:
            response = self._rpc(shard, {"op": "STATS"})
            if response is None or response.get("status") != "OK":
                return f"ERR shard unreachable shard={shard.shard_id}", False
            parts.append(
                f"{shard.shard_id}:keys={response['keys']}:ops={json.dumps(response['ops'], separators=(',', ':'))}"
            )
        return f"OK {' | '.join(parts)}", False

    def _handle_quit(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: QUIT", False
        return "OK BYE", True


def handle_client(
    connection: socket.socket,
    address: tuple[str, int],
    router: ShardingRouter,
) -> None:
    log(f"client connection from {address[0]}:{address[1]}")
    with connection:
        connection_file = connection.makefile("rwb")
        while True:
            raw_line = connection_file.readline()
            if not raw_line:
                break
            line = raw_line.decode("utf-8", errors="replace")
            response, should_close = router.execute(line)
            connection_file.write((response + "\n").encode("utf-8"))
            connection_file.flush()
            if should_close:
                break


def serve() -> None:
    args = parse_args()
    shards = []
    for entry in args.shards:
        shard_id, host, port = entry.split(":", 2)
        shards.append(ShardEndpoint(shard_id=shard_id, host=host, port=int(port)))
    router = ShardingRouter(shards)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((args.host, args.port))
        server_socket.listen()
        log(f"router listening on {args.host}:{args.port} with {len(shards)} shards")

        while True:
            connection, address = server_socket.accept()
            threading.Thread(
                target=handle_client,
                args=(connection, address, router),
                daemon=True,
            ).start()


if __name__ == "__main__":
    serve()
