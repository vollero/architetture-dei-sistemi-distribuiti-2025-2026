#!/usr/bin/env python3
"""
Replica multi-master di un KV store con version vector.

Il nodo espone un protocollo testuale per i client e un piccolo protocollo JSON
interno per la sincronizzazione tra repliche.
"""

from __future__ import annotations

import argparse
import json
import socket
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from vector_clock import VectorClock, compare, encode, increment, merge, new_clock, normalize


HOST = "127.0.0.1"
DEFAULT_MEMBERS = "A,B,C"
DEFAULT_TIMEOUT = 2.0

CommandHandler = Callable[[str], tuple[str, bool]]


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    thread_name = threading.current_thread().name
    print(f"[{timestamp}] [{thread_name}] {message}", flush=True)


@dataclass(frozen=True)
class Version:
    value: str
    clock: VectorClock
    origin: str
    deleted: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "value": self.value,
            "clock": dict(sorted(self.clock.items())),
            "origin": self.origin,
            "deleted": self.deleted,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, object], members: list[str]) -> "Version":
        raw_clock = raw.get("clock", {})
        if not isinstance(raw_clock, dict):
            raise ValueError("version clock must be an object")
        return cls(
            value=str(raw.get("value", "")),
            clock=normalize({str(k): int(v) for k, v in raw_clock.items()}, members),
            origin=str(raw.get("origin", "?")),
            deleted=bool(raw.get("deleted", False)),
        )

    def identity(self) -> tuple[str, str, str, bool]:
        clock_key = json.dumps(dict(sorted(self.clock.items())), sort_keys=True)
        return (clock_key, self.value, self.origin, self.deleted)


class VectorClockKVStore:
    def __init__(self, node_id: str, members: list[str]) -> None:
        if node_id not in members:
            raise ValueError(f"node_id {node_id!r} is not present in members {members}")

        self._node_id = node_id
        self._members = list(dict.fromkeys(members))
        self._lock = threading.Lock()
        self._data: dict[str, list[Version]] = {}
        self._handlers: dict[str, CommandHandler] = {
            "PING": self._handle_ping,
            "GET": self._handle_get,
            "SET": self._handle_set,
            "DELETE": self._handle_delete,
            "RESOLVE": self._handle_resolve,
            "SYNC": self._handle_sync,
            "DUMP": self._handle_dump,
            "MEMBERS": self._handle_members,
            "QUIT": self._handle_quit,
        }

    def execute(self, line: str) -> tuple[str, bool]:
        stripped = line.strip()
        if not stripped:
            return "ERR empty command", False
        command, *rest = stripped.split(" ", 1)
        handler = self._handlers.get(command.upper())
        if handler is None:
            return "ERR unknown command", False
        return handler(rest[0] if rest else "")

    def handle_rpc(self, raw_line: str) -> str:
        try:
            message = json.loads(raw_line)
        except json.JSONDecodeError:
            return self._json({"status": "ERR", "error": "invalid json"})

        message_type = message.get("type")
        if message_type == "snapshot":
            return self._json({"status": "OK", "snapshot": self.snapshot()})

        if message_type == "merge":
            snapshot = message.get("snapshot")
            if not isinstance(snapshot, dict):
                return self._json({"status": "ERR", "error": "missing snapshot"})
            try:
                changed = self.merge_snapshot(snapshot)
            except ValueError as exc:
                return self._json({"status": "ERR", "error": str(exc)})
            return self._json({"status": "OK", "node": self._node_id, "changed": changed})

        return self._json({"status": "ERR", "error": "unknown rpc type"})

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            items = {
                key: [version.to_dict() for version in versions]
                for key, versions in sorted(self._data.items())
            }
        return {
            "node": self._node_id,
            "members": self._members,
            "items": items,
        }

    def merge_snapshot(self, snapshot: dict[str, object]) -> bool:
        raw_items = snapshot.get("items")
        if not isinstance(raw_items, dict):
            raise ValueError("snapshot.items must be an object")

        changed = False
        with self._lock:
            for key, raw_versions in raw_items.items():
                if not isinstance(raw_versions, list):
                    raise ValueError(f"snapshot item {key!r} must be a list")
                incoming = [
                    Version.from_dict(raw_version, self._members)
                    for raw_version in raw_versions
                    if isinstance(raw_version, dict)
                ]
                previous = self._data.get(str(key), [])
                merged = self._compact_versions(previous + incoming)
                if self._version_identities(previous) != self._version_identities(merged):
                    changed = True
                    self._data[str(key)] = merged
        return changed

    def _handle_ping(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: PING", False
        return f"OK PONG node={self._node_id}", False

    def _handle_members(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: MEMBERS", False
        return f"OK node={self._node_id} members={','.join(self._members)}", False

    def _handle_get(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: GET <key>", False

        with self._lock:
            versions = list(self._data.get(key, []))

        if not versions:
            return f"NOT_FOUND key={key}", False

        if len(versions) == 1:
            version = versions[0]
            if version.deleted:
                return f"NOT_FOUND key={key} tombstone_clock={encode(version.clock)}", False
            return (
                f"OK key={key} value={version.value} "
                f"clock={encode(version.clock)} origin={version.origin}",
                False,
            )

        siblings = " | ".join(
            f"[{index}] {self._format_version(version)}"
            for index, version in enumerate(versions)
        )
        return f"CONFLICT key={key} siblings={len(versions)} | {siblings}", False

    def _handle_set(self, argument_blob: str) -> tuple[str, bool]:
        parts = argument_blob.split(" ", 1)
        if len(parts) != 2 or not parts[0]:
            return "ERR usage: SET <key> <value>", False
        key, value = parts

        with self._lock:
            versions = self._data.get(key, [])
            if len(versions) > 1:
                return f"ERR conflict_exists key={key} use RESOLVE <key> <value>", False
            next_clock = self._next_clock_for_key(key)
            version = Version(
                value=value,
                clock=next_clock,
                origin=self._node_id,
                deleted=False,
            )
            self._data[key] = self._compact_versions(versions + [version])

        return f"OK key={key} value={value} clock={encode(next_clock)}", False

    def _handle_delete(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: DELETE <key>", False

        with self._lock:
            next_clock = self._next_clock_for_key(key)
            tombstone = Version(
                value="",
                clock=next_clock,
                origin=self._node_id,
                deleted=True,
            )
            self._data[key] = self._compact_versions(self._data.get(key, []) + [tombstone])

        return f"OK deleted key={key} clock={encode(next_clock)}", False

    def _handle_resolve(self, argument_blob: str) -> tuple[str, bool]:
        parts = argument_blob.split(" ", 1)
        if len(parts) != 2 or not parts[0]:
            return "ERR usage: RESOLVE <key> <value>", False
        key, value = parts

        with self._lock:
            versions = self._data.get(key, [])
            if len(versions) < 2:
                return f"ERR no_conflict key={key}", False
            next_clock = self._next_clock_for_key(key)
            resolved = Version(
                value=value,
                clock=next_clock,
                origin=self._node_id,
                deleted=False,
            )
            self._data[key] = self._compact_versions(versions + [resolved])

        return f"OK resolved key={key} value={value} clock={encode(next_clock)}", False

    def _handle_sync(self, argument_blob: str) -> tuple[str, bool]:
        parts = argument_blob.split()
        if len(parts) == 1:
            peer_host = HOST
            peer_port_text = parts[0]
        elif len(parts) == 2:
            peer_host, peer_port_text = parts
        else:
            return "ERR usage: SYNC [host] <port>", False

        try:
            peer_port = int(peer_port_text)
        except ValueError:
            return "ERR port must be an integer", False

        try:
            remote_response = send_rpc(peer_host, peer_port, {"type": "snapshot"})
            if remote_response.get("status") != "OK":
                return f"ERR peer_snapshot_failed response={remote_response}", False

            remote_snapshot = remote_response.get("snapshot")
            if not isinstance(remote_snapshot, dict):
                return "ERR peer_snapshot_invalid", False

            local_changed = self.merge_snapshot(remote_snapshot)
            local_snapshot = self.snapshot()
            merge_response = send_rpc(
                peer_host,
                peer_port,
                {"type": "merge", "snapshot": local_snapshot},
            )
            if merge_response.get("status") != "OK":
                return f"ERR peer_merge_failed response={merge_response}", False
        except OSError as exc:
            return f"ERR sync_failed peer={peer_host}:{peer_port} error={exc}", False

        peer_node = remote_snapshot.get("node", "?")
        peer_changed = bool(merge_response.get("changed", False))
        return (
            f"OK synced peer={peer_node}@{peer_host}:{peer_port} "
            f"local_changed={local_changed} peer_changed={peer_changed}",
            False,
        )

    def _handle_dump(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: DUMP", False
        return self._json(self.snapshot()), False

    def _handle_quit(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: QUIT", False
        return "OK BYE", True

    def _next_clock_for_key(self, key: str) -> VectorClock:
        base = new_clock(self._members)
        for version in self._data.get(key, []):
            base = merge(base, version.clock, self._members)
        return increment(base, self._node_id, self._members)

    def _compact_versions(self, versions: list[Version]) -> list[Version]:
        unique_versions = list({version.identity(): version for version in versions}.values())
        compacted: list[Version] = []

        for candidate in unique_versions:
            is_dominated = False
            for other in unique_versions:
                if candidate.identity() == other.identity():
                    continue
                if compare(candidate.clock, other.clock) == "before":
                    is_dominated = True
                    break
            if not is_dominated:
                compacted.append(candidate)

        return sorted(compacted, key=lambda item: (encode(item.clock), item.deleted, item.value))

    @staticmethod
    def _version_identities(versions: list[Version]) -> set[tuple[str, str, str, bool]]:
        return {version.identity() for version in versions}

    @staticmethod
    def _format_version(version: Version) -> str:
        value = "<deleted>" if version.deleted else version.value
        return f"value={value} clock={encode(version.clock)} origin={version.origin}"

    @staticmethod
    def _json(payload: dict[str, object]) -> str:
        return json.dumps(payload, sort_keys=True)


def send_rpc(host: str, port: int, message: dict[str, object]) -> dict[str, object]:
    with socket.create_connection((host, port), timeout=DEFAULT_TIMEOUT) as connection:
        connection_file = connection.makefile("rwb")
        connection_file.write((json.dumps(message, sort_keys=True) + "\n").encode("utf-8"))
        connection_file.flush()
        raw_response = connection_file.readline()
    if not raw_response:
        raise OSError("empty response")
    response = json.loads(raw_response.decode("utf-8", errors="replace"))
    if not isinstance(response, dict):
        raise OSError("invalid response type")
    return response


def handle_connection(
    connection: socket.socket,
    address: tuple[str, int],
    store: VectorClockKVStore,
) -> None:
    log(f"connection from {address[0]}:{address[1]}")
    with connection:
        connection_file = connection.makefile("rwb")
        while True:
            raw_line = connection_file.readline()
            if not raw_line:
                break
            line = raw_line.decode("utf-8", errors="replace").strip()
            if line.startswith("{"):
                response = store.handle_rpc(line)
                should_close = False
            else:
                response, should_close = store.execute(line)
            connection_file.write((response + "\n").encode("utf-8"))
            connection_file.flush()
            if should_close:
                break


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node-id", required=True)
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--members", default=DEFAULT_MEMBERS)
    return parser.parse_args()


def parse_members(raw_members: str) -> list[str]:
    members = [member.strip() for member in raw_members.split(",") if member.strip()]
    if not members:
        raise ValueError("members cannot be empty")
    return members


def serve() -> None:
    args = parse_args()
    members = parse_members(args.members)
    store = VectorClockKVStore(args.node_id, members)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((args.host, args.port))
        server_socket.listen()
        log(
            f"vector-clock kv node {args.node_id} listening on "
            f"{args.host}:{args.port} members={','.join(members)}"
        )

        while True:
            connection, address = server_socket.accept()
            threading.Thread(
                target=handle_connection,
                args=(connection, address, store),
                daemon=True,
            ).start()


if __name__ == "__main__":
    serve()
