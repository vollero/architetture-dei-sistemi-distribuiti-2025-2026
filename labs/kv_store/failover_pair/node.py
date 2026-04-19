#!/usr/bin/env python3
"""
KV store con failover minimale a due nodi.

Obiettivo didattico:
- heartbeat dal leader al follower;
- promozione del follower dopo timeout;
- rischio di split brain se il vecchio leader non si ferma.
"""

import argparse
import json
import os
import socket
import threading
import time
from datetime import datetime
from typing import Callable


DEFAULT_HOST = "127.0.0.1"

CommandHandler = Callable[[str], tuple[str, bool]]


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    thread_name = threading.current_thread().name
    print(f"[{timestamp}] [{thread_name}] {message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node-id", required=True)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--client-port", type=int, required=True)
    parser.add_argument("--peer-port", type=int, required=True)
    parser.add_argument("--peer-host", default=DEFAULT_HOST)
    parser.add_argument("--peer-peer-port", type=int, required=True)
    parser.add_argument("--initial-role", choices=["primary", "secondary"], required=True)
    parser.add_argument("--heartbeat-interval", type=float, default=0.5)
    parser.add_argument("--election-timeout", type=float, default=1.5)
    return parser.parse_args()


class FailoverNode:
    def __init__(self, args: argparse.Namespace) -> None:
        self._node_id = args.node_id
        self._peer_host = args.peer_host
        self._peer_peer_port = args.peer_peer_port
        self._heartbeat_interval = args.heartbeat_interval
        self._election_timeout = args.election_timeout

        self._data: dict[str, str] = {}
        self._lock = threading.Lock()
        self._role = args.initial_role
        self._term = 1
        self._leader_id = args.node_id if args.initial_role == "primary" else None
        self._last_heartbeat = time.monotonic()
        self._pause_heartbeats = False

        self._handlers: dict[str, CommandHandler] = {
            "PING": self._handle_ping,
            "STATUS": self._handle_status,
            "ROLE": self._handle_role,
            "GET": self._handle_get,
            "SET": self._handle_set,
            "DELETE": self._handle_delete,
            "EXISTS": self._handle_exists,
            "KEYS": self._handle_keys,
            "INCR": self._handle_incr,
            "PAUSE_HEARTBEATS": self._handle_pause_heartbeats,
            "RESUME_HEARTBEATS": self._handle_resume_heartbeats,
            "CRASH": self._handle_crash,
            "QUIT": self._handle_quit,
        }

    def start_background_threads(self) -> None:
        heartbeat = threading.Thread(target=self._heartbeat_loop, daemon=True, name="heartbeat-loop")
        heartbeat.start()
        timeout = threading.Thread(target=self._timeout_loop, daemon=True, name="timeout-loop")
        timeout.start()

    def execute_client(self, line: str) -> tuple[str, bool]:
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

    def handle_peer_message(self, raw_line: str) -> str:
        try:
            message = json.loads(raw_line)
        except json.JSONDecodeError:
            return "ERR invalid json"

        message_type = message.get("type")
        sender_id = message.get("node_id", "unknown")
        sender_term = int(message.get("term", 0))

        with self._lock:
            if sender_term > self._term:
                self._term = sender_term
                self._role = "secondary"
                self._leader_id = sender_id

            if message_type == "heartbeat":
                if sender_term >= self._term:
                    self._role = "secondary"
                    self._leader_id = sender_id
                    self._term = sender_term
                    self._last_heartbeat = time.monotonic()
                return "ACK"

            if message_type != "replicate":
                return "ERR unknown peer message"

            if sender_term < self._term:
                return "ERR stale term"

            if self._role == "primary" and sender_id != self._node_id and sender_term == self._term:
                return "ERR split brain detected"

            self._role = "secondary"
            self._leader_id = sender_id
            self._term = sender_term
            self._last_heartbeat = time.monotonic()
            return self._apply_replication(message)

    def _apply_replication(self, message: dict[str, str]) -> str:
        operation = message.get("op")
        key = message.get("key", "")
        if not key:
            return "ERR missing key"

        if operation == "SET":
            self._data[key] = message["value"]
            return "ACK"

        if operation == "DELETE":
            self._data.pop(key, None)
            return "ACK"

        if operation == "INCR":
            self._data[key] = message["value"]
            return "ACK"

        return "ERR unknown op"

    def _heartbeat_loop(self) -> None:
        while True:
            time.sleep(self._heartbeat_interval)
            with self._lock:
                should_send = self._role == "primary" and not self._pause_heartbeats
                term = self._term
            if not should_send:
                continue

            self._send_peer_message(
                {
                    "type": "heartbeat",
                    "node_id": self._node_id,
                    "term": term,
                }
            )

    def _timeout_loop(self) -> None:
        while True:
            time.sleep(0.1)
            with self._lock:
                timed_out = (
                    self._role == "secondary"
                    and time.monotonic() - self._last_heartbeat > self._election_timeout
                )
                if not timed_out:
                    continue
                self._term += 1
                self._role = "primary"
                self._leader_id = self._node_id
                self._last_heartbeat = time.monotonic()
                new_term = self._term
            log(f"election timeout expired, promoting to primary at term {new_term}")

    def _send_peer_message(self, message: dict[str, str]) -> str:
        try:
            with socket.create_connection((self._peer_host, self._peer_peer_port), timeout=1.0) as connection:
                connection_file = connection.makefile("rwb")
                payload = json.dumps(message) + "\n"
                connection_file.write(payload.encode("utf-8"))
                connection_file.flush()
                response = connection_file.readline().decode("utf-8", errors="replace").strip()
        except OSError as exc:
            return f"ERR peer unreachable: {exc}"
        return response

    def _replicate_async(self, message: dict[str, str]) -> None:
        def worker() -> None:
            response = self._send_peer_message(message)
            log(f"replication response: {response}")

        threading.Thread(target=worker, daemon=True).start()

    def _handle_ping(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: PING", False
        return "OK PONG", False

    def _handle_status(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: STATUS", False
        with self._lock:
            leader = self._leader_id or "none"
            heartbeats = "paused" if self._pause_heartbeats else "active"
            return (
                f"OK node={self._node_id} role={self._role} term={self._term} "
                f"leader={leader} heartbeats={heartbeats}",
                False,
            )

    def _handle_role(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: ROLE", False
        with self._lock:
            return f"OK {self._role}", False

    def _handle_get(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: GET <key>", False
        with self._lock:
            if key not in self._data:
                return "NOT_FOUND", False
            value = self._data[key]
        return f"OK {value}", False

    def _handle_set(self, argument_blob: str) -> tuple[str, bool]:
        parts = argument_blob.split(" ", 1)
        if len(parts) != 2 or not parts[0]:
            return "ERR usage: SET <key> <value>", False
        key, value = parts
        with self._lock:
            if self._role != "primary":
                leader = self._leader_id or "unknown"
                return f"ERR not leader leader={leader}", False
            self._data[key] = value
            term = self._term
        self._replicate_async(
            {
                "type": "replicate",
                "node_id": self._node_id,
                "term": term,
                "op": "SET",
                "key": key,
                "value": value,
            }
        )
        return "OK", False

    def _handle_delete(self, argument_blob: str) -> tuple[str, bool]:
        key = argument_blob.strip()
        if not key:
            return "ERR usage: DELETE <key>", False
        with self._lock:
            if self._role != "primary":
                leader = self._leader_id or "unknown"
                return f"ERR not leader leader={leader}", False
            if key not in self._data:
                return "NOT_FOUND", False
            del self._data[key]
            term = self._term
        self._replicate_async(
            {
                "type": "replicate",
                "node_id": self._node_id,
                "term": term,
                "op": "DELETE",
                "key": key,
            }
        )
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
            if self._role != "primary":
                leader = self._leader_id or "unknown"
                return f"ERR not leader leader={leader}", False
            current = self._data.get(key, "0")
            try:
                numeric_value = int(current)
            except ValueError:
                return "ERR value is not an integer", False
            numeric_value += 1
            encoded = str(numeric_value)
            self._data[key] = encoded
            term = self._term
        self._replicate_async(
            {
                "type": "replicate",
                "node_id": self._node_id,
                "term": term,
                "op": "INCR",
                "key": key,
                "value": encoded,
            }
        )
        return f"OK {numeric_value}", False

    def _handle_pause_heartbeats(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: PAUSE_HEARTBEATS", False
        with self._lock:
            self._pause_heartbeats = True
        return "OK HEARTBEATS_PAUSED", False

    def _handle_resume_heartbeats(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: RESUME_HEARTBEATS", False
        with self._lock:
            self._pause_heartbeats = False
        return "OK HEARTBEATS_RESUMED", False

    def _handle_crash(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: CRASH", False
        log("forced crash requested")
        os._exit(1)

    def _handle_quit(self, argument_blob: str) -> tuple[str, bool]:
        if argument_blob.strip():
            return "ERR usage: QUIT", False
        return "OK BYE", True


def handle_client(connection: socket.socket, address: tuple[str, int], node: FailoverNode) -> None:
    log(f"client connection from {address[0]}:{address[1]}")
    with connection:
        connection_file = connection.makefile("rwb")
        while True:
            raw_line = connection_file.readline()
            if not raw_line:
                break
            line = raw_line.decode("utf-8", errors="replace")
            log(f"client request: {line.rstrip()}")
            response, should_close = node.execute_client(line)
            connection_file.write((response + "\n").encode("utf-8"))
            connection_file.flush()
            log(f"client response: {response}")
            if should_close:
                break


def handle_peer(connection: socket.socket, address: tuple[str, int], node: FailoverNode) -> None:
    log(f"peer connection from {address[0]}:{address[1]}")
    with connection:
        connection_file = connection.makefile("rwb")
        while True:
            raw_line = connection_file.readline()
            if not raw_line:
                break
            line = raw_line.decode("utf-8", errors="replace").strip()
            response = node.handle_peer_message(line)
            connection_file.write((response + "\n").encode("utf-8"))
            connection_file.flush()
            log(f"peer response: {response}")


def serve() -> None:
    args = parse_args()
    node = FailoverNode(args)
    node.start_background_threads()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.bind((args.host, args.client_port))
        client_socket.listen()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as peer_socket:
            peer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            peer_socket.bind((args.host, args.peer_port))
            peer_socket.listen()

            log(
                f"{args.node_id} client endpoint on {args.host}:{args.client_port} "
                f"role={args.initial_role}"
            )
            log(f"{args.node_id} peer endpoint on {args.host}:{args.peer_port}")

            def accept_loop(
                server_socket: socket.socket,
                handler: Callable[[socket.socket, tuple[str, int], FailoverNode], None],
            ) -> None:
                while True:
                    connection, address = server_socket.accept()
                    threading.Thread(
                        target=handler,
                        args=(connection, address, node),
                        daemon=True,
                    ).start()

            client_thread = threading.Thread(
                target=accept_loop,
                args=(client_socket, handle_client),
                daemon=True,
                name="client-acceptor",
            )
            client_thread.start()

            accept_loop(peer_socket, handle_peer)


if __name__ == "__main__":
    serve()
