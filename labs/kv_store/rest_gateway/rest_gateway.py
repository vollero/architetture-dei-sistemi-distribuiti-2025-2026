#!/usr/bin/env python3
"""
REST gateway per la capstone del KV store.
"""

import argparse
import json
import socket
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import unquote, urlparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=6470)
    parser.add_argument("--router-host", default="127.0.0.1")
    parser.add_argument("--router-port", type=int, default=6460)
    return parser.parse_args()


class RouterClient:
    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port

    def command(self, line: str) -> str:
        try:
            with socket.create_connection((self._host, self._port), timeout=2.0) as connection:
                connection_file = connection.makefile("rwb")
                connection_file.write((line + "\n").encode("utf-8"))
                connection_file.flush()
                response = connection_file.readline().decode("utf-8", errors="replace").strip()
        except OSError as exc:
            raise GatewayError(f"router unavailable: {exc}") from exc
        if not response:
            raise GatewayError("router closed connection")
        return response


class GatewayError(Exception):
    pass


def parse_versioned_response(response: str) -> dict[str, Any]:
    if not response.startswith("OK "):
        raise ValueError(response)
    payload = response[3:]
    version_marker = " version="
    shard_marker = " shard="
    version_index = payload.rfind(version_marker)
    shard_index = payload.rfind(shard_marker)
    if version_index < 0 or shard_index < 0 or shard_index < version_index:
        raise ValueError(response)
    value = payload[:version_index]
    version = int(payload[version_index + len(version_marker) : shard_index])
    shard = payload[shard_index + len(shard_marker) :]
    return {"value": value, "version": version, "shard": shard}


def parse_mutation_response(response: str) -> dict[str, Any]:
    if not response.startswith("OK "):
        raise ValueError(response)
    parts = response.split()
    result: dict[str, Any] = {}
    for part in parts[1:]:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        result[key] = int(value) if key == "version" else value
    return result


def parse_location_response(response: str) -> dict[str, Any]:
    if not response.startswith("OK "):
        raise ValueError(response)
    result: dict[str, Any] = {}
    for part in response.split()[1:]:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        result[key] = int(value) if key == "port" else value
    return result


class RestGatewayHandler(BaseHTTPRequestHandler):
    router: RouterClient

    def do_GET(self) -> None:
        path = self._path_parts()
        if path == ["health"]:
            self._handle_health()
            return
        if path == ["kv"]:
            self._handle_keys()
            return
        if len(path) == 2 and path[0] == "kv":
            self._handle_get_key(path[1])
            return
        if len(path) == 3 and path[0] == "kv" and path[2] == "location":
            self._handle_location(path[1])
            return
        if path == ["cluster", "status"]:
            self._handle_status()
            return
        self._json_response(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint"})

    def do_PUT(self) -> None:
        path = self._path_parts()
        if len(path) == 2 and path[0] == "kv":
            self._handle_put_key(path[1])
            return
        self._json_response(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint"})

    def do_PATCH(self) -> None:
        path = self._path_parts()
        if len(path) == 2 and path[0] == "kv":
            self._handle_patch_key(path[1])
            return
        self._json_response(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint"})

    def do_DELETE(self) -> None:
        path = self._path_parts()
        if len(path) == 2 and path[0] == "kv":
            self._handle_delete_key(path[1])
            return
        self._json_response(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint"})

    def do_POST(self) -> None:
        path = self._path_parts()
        if path == ["cluster", "shards"]:
            self._handle_add_shard()
            return
        if path == ["cluster", "rebalance"]:
            self._handle_rebalance()
            return
        self._json_response(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint"})

    def _handle_health(self) -> None:
        try:
            response = self.router.command("PING")
        except GatewayError as exc:
            self._json_response(HTTPStatus.BAD_GATEWAY, {"error": str(exc)})
            return
        self._json_response(HTTPStatus.OK, {"status": "ok", "router": response})

    def _handle_keys(self) -> None:
        try:
            response = self.router.command("KEYS")
        except GatewayError as exc:
            self._json_response(HTTPStatus.BAD_GATEWAY, {"error": str(exc)})
            return
        if response == "OK":
            keys: list[str] = []
        elif response.startswith("OK "):
            keys = response[3:].split()
        else:
            self._router_error(response)
            return
        self._json_response(HTTPStatus.OK, {"keys": keys})

    def _handle_get_key(self, key: str) -> None:
        try:
            response = self.router.command(f"GETV {key}")
        except GatewayError as exc:
            self._json_response(HTTPStatus.BAD_GATEWAY, {"error": str(exc)})
            return
        if response == "NOT_FOUND":
            self._json_response(HTTPStatus.NOT_FOUND, {"key": key, "error": "not_found"})
            return
        try:
            parsed = parse_versioned_response(response)
        except ValueError:
            self._router_error(response)
            return
        self._json_response(HTTPStatus.OK, {"key": key, **parsed})

    def _handle_put_key(self, key: str) -> None:
        payload = self._read_json()
        if payload is None:
            return
        value = payload.get("value")
        if not isinstance(value, str):
            self._json_response(HTTPStatus.BAD_REQUEST, {"error": "value must be a string"})
            return

        existing = self._router_command_or_502(f"GETV {key}")
        if existing is None:
            return
        if existing != "NOT_FOUND":
            try:
                parsed = parse_versioned_response(existing)
            except ValueError:
                self._router_error(existing)
                return
            if parsed["value"] == value:
                self._json_response(HTTPStatus.OK, {"key": key, "unchanged": True, **parsed})
                return

        response = self._router_command_or_502(f"SET {key} {value}")
        if response is None:
            return
        try:
            parsed = parse_mutation_response(response)
        except ValueError:
            self._router_error(response)
            return
        status = HTTPStatus.CREATED if existing == "NOT_FOUND" else HTTPStatus.OK
        self._json_response(status, {"key": key, **parsed})

    def _handle_patch_key(self, key: str) -> None:
        payload = self._read_json()
        if payload is None:
            return
        value = payload.get("value")
        expected_version = payload.get("expected_version")
        if not isinstance(value, str) or not isinstance(expected_version, int):
            self._json_response(
                HTTPStatus.BAD_REQUEST,
                {"error": "expected_version must be an integer and value must be a string"},
            )
            return
        response = self._router_command_or_502(f"CAS {key} {expected_version} {value}")
        if response is None:
            return
        if response.startswith("ERR version_mismatch"):
            current = response.split("current=", 1)[1].split()[0]
            self._json_response(
                HTTPStatus.CONFLICT,
                {"key": key, "error": "version_mismatch", "current": int(current)},
            )
            return
        try:
            parsed = parse_mutation_response(response)
        except ValueError:
            self._router_error(response)
            return
        self._json_response(HTTPStatus.OK, {"key": key, **parsed})

    def _handle_delete_key(self, key: str) -> None:
        response = self._router_command_or_502(f"DELETE {key}")
        if response is None:
            return
        if response == "NOT_FOUND":
            self._json_response(HTTPStatus.NOT_FOUND, {"key": key, "error": "not_found"})
            return
        if response.startswith("OK"):
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return
        self._router_error(response)

    def _handle_location(self, key: str) -> None:
        response = self._router_command_or_502(f"WHERE {key}")
        if response is None:
            return
        try:
            parsed = parse_location_response(response)
        except ValueError:
            self._router_error(response)
            return
        self._json_response(HTTPStatus.OK, parsed)

    def _handle_status(self) -> None:
        response = self._router_command_or_502("STATUS")
        if response is None:
            return
        if not response.startswith("OK "):
            self._router_error(response)
            return
        self._json_response(HTTPStatus.OK, {"status": response[3:]})

    def _handle_add_shard(self) -> None:
        payload = self._read_json()
        if payload is None:
            return
        shard_id = payload.get("id")
        host = payload.get("host")
        port = payload.get("port")
        if not isinstance(shard_id, str) or not isinstance(host, str) or not isinstance(port, int):
            self._json_response(
                HTTPStatus.BAD_REQUEST,
                {"error": "id and host must be strings, port must be an integer"},
            )
            return
        response = self._router_command_or_502(f"ADD_SHARD {shard_id} {host} {port}")
        if response is None:
            return
        if response.startswith("OK "):
            self._json_response(HTTPStatus.CREATED, {"status": response[3:]})
            return
        self._router_error(response)

    def _handle_rebalance(self) -> None:
        response = self._router_command_or_502("REBALANCE")
        if response is None:
            return
        if response.startswith("OK "):
            moved = int(response.split("moved=", 1)[1])
            self._json_response(HTTPStatus.ACCEPTED, {"moved": moved})
            return
        self._router_error(response)

    def _router_command_or_502(self, command: str) -> str | None:
        try:
            return self.router.command(command)
        except GatewayError as exc:
            self._json_response(HTTPStatus.BAD_GATEWAY, {"error": str(exc)})
            return None

    def _read_json(self) -> dict[str, Any] | None:
        length = int(self.headers.get("Content-Length", "0"))
        try:
            body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._json_response(HTTPStatus.BAD_REQUEST, {"error": "invalid json"})
            return None
        if not isinstance(payload, dict):
            self._json_response(HTTPStatus.BAD_REQUEST, {"error": "json object expected"})
            return None
        return payload

    def _path_parts(self) -> list[str]:
        parsed = urlparse(self.path)
        return [unquote(part) for part in parsed.path.split("/") if part]

    def _router_error(self, response: str) -> None:
        status = HTTPStatus.BAD_GATEWAY if "unreachable" in response else HTTPStatus.BAD_REQUEST
        self._json_response(status, {"error": "router_error", "detail": response})

    def _json_response(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    args = parse_args()
    RestGatewayHandler.router = RouterClient(args.router_host, args.router_port)
    server = ThreadingHTTPServer((args.host, args.port), RestGatewayHandler)
    print(f"REST gateway listening on {args.host}:{args.port}")
    print(f"Forwarding to capstone router on {args.router_host}:{args.router_port}")
    server.serve_forever()


if __name__ == "__main__":
    main()

