#!/usr/bin/env python3
"""
Router shardato con versioni, CAS e rebalancing.
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


@dataclass(frozen=True)
class MigratedRecord:
    source: ShardEndpoint
    key: str
    value: str
    version: int


def stable_hash(key: str) -> int:
    return sum(key.encode("utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=6460)
    parser.add_argument(
        "--shards",
        nargs="+",
        default=["S0:127.0.0.1:6461", "S1:127.0.0.1:6462"],
    )
    return parser.parse_args()


def parse_shard(entry: str) -> ShardEndpoint:
    shard_id, host, port = entry.split(":", 2)
    return ShardEndpoint(shard_id=shard_id, host=host, port=int(port))


class CapstoneRouter:
    def __init__(self, shards: list[ShardEndpoint]) -> None:
        self._shards = list(shards)
        self._lock = threading.RLock()
        self._handlers: dict[str, CommandHandler] = {
            "PING": self._handle_ping,
            "STATUS": self._handle_status,
            "GET": self._handle_get,
            "GETV": self._handle_getv,
            "SET": self._handle_set,
            "CAS": self._handle_cas,
            "DELETE": self._handle_delete,
            "KEYS": self._handle_keys,
            "WHERE": self._handle_where,
            "PLAN": self._handle_plan,
            "ADD_SHARD": self._handle_add_shard,
            "REBALANCE": self._handle_rebalance,
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
                connection_file.write((json.dumps(message) + "\n").encode("utf-8"))
                connection_file.flush()
                response = connection_file.readline().decode("utf-8", errors="replace").strip()
        except OSError:
            return None
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return None

    def _select_shard(self, key: str, shards: list[ShardEndpoint] | None = None) -> ShardEndpoint:
        active = shards if shards is not None else self._shards
        return active[stable_hash(key) % len(active)]

    def _forward(self, key: str, payload: dict[str, object]) -> tuple[str, bool]:
        with self._lock:
            shard = self._select_shard(key)
            response = self._rpc(shard, payload)
            if response is None:
                return f"ERR shard_unreachable shard={shard.shard_id}", False
            return self._format_shard_response(payload["op"], shard, response), False

    def _format_shard_response(
        self,
        operation: object,
        shard: ShardEndpoint,
        response: dict[str, object],
    ) -> str:
        status = str(response.get("status"))
        if status == "OK":
            if operation == "GET":
                return f"OK {response['value']} shard={shard.shard_id}"
            if operation == "GETV":
                return f"OK {response['value']} version={response['version']} shard={shard.shard_id}"
            if operation in {"SET", "CAS"}:
                return f"OK version={response['version']} shard={shard.shard_id}"
            if operation == "DELETE":
                return f"OK shard={shard.shard_id}"
            return f"OK shard={shard.shard_id}"
        if status == "NOT_FOUND":
            return "NOT_FOUND"
        if status == "VERSION_MISMATCH":
            return f"ERR version_mismatch current={response['current']} shard={shard.shard_id}"
        return f"ERR {response.get('error', 'shard error')} shard={shard.shard_id}"

    def _handle_ping(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: PING", False
        return "OK PONG", False

    def _handle_status(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: STATUS", False
        with self._lock:
            summary = " ".join(f"{s.shard_id}@{s.port}" for s in self._shards)
        return f"OK shards={summary}", False

    def _handle_get(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: GET <key>", False
        return self._forward(key, {"op": "GET", "key": key})

    def _handle_getv(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: GETV <key>", False
        return self._forward(key, {"op": "GETV", "key": key})

    def _handle_set(self, argument_blob: str) -> tuple[str, bool]:
        parts = argument_blob.split(" ", 1)
        if len(parts) != 2 or not parts[0]:
            return "ERR usage: SET <key> <value>", False
        key, value = parts
        return self._forward(key, {"op": "SET", "key": key, "value": value})

    def _handle_cas(self, argument_blob: str) -> tuple[str, bool]:
        parts = argument_blob.split(" ", 2)
        if len(parts) != 3 or not parts[0]:
            return "ERR usage: CAS <key> <expected_version> <value>", False
        key, expected_text, value = parts
        try:
            expected_version = int(expected_text)
        except ValueError:
            return "ERR expected_version must be an integer", False
        return self._forward(
            key,
            {
                "op": "CAS",
                "key": key,
                "expected_version": expected_version,
                "value": value,
            },
        )

    def _handle_delete(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: DELETE <key>", False
        return self._forward(key, {"op": "DELETE", "key": key})

    def _handle_keys(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: KEYS", False
        with self._lock:
            keys: list[str] = []
            for shard in self._shards:
                response = self._rpc(shard, {"op": "KEYS"})
                if response is None or response.get("status") != "OK":
                    return f"ERR shard_unreachable shard={shard.shard_id}", False
                keys.extend(str(key) for key in response.get("keys", []))
        return f"OK {' '.join(sorted(set(keys)))}".rstrip(), False

    def _handle_where(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: WHERE <key>", False
        with self._lock:
            shard = self._select_shard(key)
        return f"OK key={key} target={shard.shard_id} port={shard.port}", False

    def _handle_plan(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: PLAN <key>", False
        with self._lock:
            target = self._select_shard(key)
        return f"OK key={key} hash={stable_hash(key)} target={target.shard_id}", False

    def _handle_add_shard(self, argument_blob: str) -> tuple[str, bool]:
        parts = argument_blob.split()
        if len(parts) != 3:
            return "ERR usage: ADD_SHARD <id> <host> <port>", False
        shard_id, host, port_text = parts
        try:
            port = int(port_text)
        except ValueError:
            return "ERR invalid port", False

        new_shard = ShardEndpoint(shard_id=shard_id, host=host, port=port)
        response = self._rpc(new_shard, {"op": "PING"})
        if response is None or response.get("status") != "OK":
            return f"ERR shard_unreachable shard={shard_id}", False

        with self._lock:
            if any(shard.shard_id == shard_id for shard in self._shards):
                return f"ERR duplicate_shard shard={shard_id}", False
            self._shards.append(new_shard)
        return f"OK shard_added={shard_id}", False

    def _handle_rebalance(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: REBALANCE", False
        with self._lock:
            shards = list(self._shards)
            records = self._collect_records(shards)
            if isinstance(records, str):
                return records, False

            moved = 0
            for record in records:
                target = self._select_shard(record.key, shards)
                if target.shard_id == record.source.shard_id:
                    continue
                import_response = self._rpc(
                    target,
                    {
                        "op": "IMPORT_KEY",
                        "key": record.key,
                        "value": record.value,
                        "version": record.version,
                    },
                )
                if import_response is None or import_response.get("status") != "OK":
                    return f"ERR import_failed key={record.key} target={target.shard_id}", False
                delete_response = self._rpc(
                    record.source,
                    {
                        "op": "DELETE_LOCAL",
                        "key": record.key,
                        "version": record.version,
                    },
                )
                if delete_response is None or delete_response.get("status") != "OK":
                    return f"ERR delete_failed key={record.key} source={record.source.shard_id}", False
                moved += 1
        return f"OK moved={moved}", False

    def _collect_records(
        self,
        shards: list[ShardEndpoint],
    ) -> list[MigratedRecord] | str:
        records: list[MigratedRecord] = []
        for shard in shards:
            response = self._rpc(shard, {"op": "LIST_ITEMS"})
            if response is None or response.get("status") != "OK":
                return f"ERR shard_unreachable shard={shard.shard_id}"
            items = response.get("items", {})
            if not isinstance(items, dict):
                return f"ERR invalid_items shard={shard.shard_id}"
            for key, raw_record in items.items():
                if not isinstance(raw_record, dict):
                    return f"ERR invalid_record key={key} shard={shard.shard_id}"
                records.append(
                    MigratedRecord(
                        source=shard,
                        key=str(key),
                        value=str(raw_record.get("value", "")),
                        version=int(raw_record["version"]),
                    )
                )
        return records

    def _handle_quit(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: QUIT", False
        return "OK BYE", True


def handle_client(connection: socket.socket, address: tuple[str, int], router: CapstoneRouter) -> None:
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
    router = CapstoneRouter([parse_shard(entry) for entry in args.shards])

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((args.host, args.port))
        server_socket.listen()
        log(f"capstone router listening on {args.host}:{args.port}")

        while True:
            connection, address = server_socket.accept()
            threading.Thread(
                target=handle_client,
                args=(connection, address, router),
                daemon=True,
            ).start()


if __name__ == "__main__":
    serve()
