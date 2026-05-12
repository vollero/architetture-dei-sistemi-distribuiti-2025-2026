#!/usr/bin/env python3
"""
Test end-to-end del REST gateway.
"""

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


HOST = "127.0.0.1"
ROUTER_PORT = 6460
GATEWAY_PORT = 6470


def wait_for_port(port: int, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((HOST, port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError(f"port {port} did not open")


def request(method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://{HOST}:{GATEWAY_PORT}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=3.0) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            return response.status, parsed
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        parsed = json.loads(raw) if raw else {}
        return exc.code, parsed


def expect(method: str, path: str, status: int, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    actual_status, actual_payload = request(method, path, payload)
    print(f"{method} {path} -> {actual_status} {actual_payload}")
    if actual_status != status:
        raise AssertionError(f"expected HTTP {status}, got {actual_status}: {actual_payload}")
    return actual_payload


def main() -> None:
    repo = Path(__file__).resolve().parents[3]
    capstone = repo / "labs" / "kv_store" / "capstone_exercise"
    gateway = repo / "labs" / "kv_store" / "rest_gateway"
    processes: list[subprocess.Popen[bytes]] = []
    try:
        for shard_id, port in [("S0", 6461), ("S1", 6462)]:
            processes.append(
                subprocess.Popen(
                    [
                        sys.executable,
                        str(capstone / "shard_node.py"),
                        "--shard-id",
                        shard_id,
                        "--port",
                        str(port),
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            )
            wait_for_port(port)

        processes.append(
            subprocess.Popen(
                [
                    sys.executable,
                    str(capstone / "router.py"),
                    "--port",
                    str(ROUTER_PORT),
                    "--shards",
                    f"S0:{HOST}:6461",
                    f"S1:{HOST}:6462",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        )
        wait_for_port(ROUTER_PORT)

        processes.append(
            subprocess.Popen(
                [
                    sys.executable,
                    str(gateway / "rest_gateway.py"),
                    "--port",
                    str(GATEWAY_PORT),
                    "--router-port",
                    str(ROUTER_PORT),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        )
        wait_for_port(GATEWAY_PORT)

        expect("GET", "/health", 200)
        created = expect("PUT", "/kv/course", 201, {"value": "ads"})
        assert created["version"] == 0
        unchanged = expect("PUT", "/kv/course", 200, {"value": "ads"})
        assert unchanged["version"] == 0 and unchanged["unchanged"] is True
        read = expect("GET", "/kv/course", 200)
        assert read["value"] == "ads" and read["version"] == 0
        patched = expect(
            "PATCH",
            "/kv/course",
            200,
            {"expected_version": 0, "value": "distributed-systems"},
        )
        assert patched["version"] == 1
        conflict = expect("PATCH", "/kv/course", 409, {"expected_version": 0, "value": "stale"})
        assert conflict["error"] == "version_mismatch"
        expect("GET", "/kv", 200)
        expect("GET", "/kv/course/location", 200)

        processes.append(
            subprocess.Popen(
                [
                    sys.executable,
                    str(capstone / "shard_node.py"),
                    "--shard-id",
                    "S2",
                    "--port",
                    "6463",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        )
        wait_for_port(6463)
        expect("POST", "/cluster/shards", 201, {"id": "S2", "host": HOST, "port": 6463})
        expect("POST", "/cluster/rebalance", 202)
        expect("GET", "/kv/course", 200)
        expect("DELETE", "/kv/course", 204)
        expect("GET", "/kv/course", 404)
        print("REST gateway acceptance test passed")
    finally:
        for process in reversed(processes):
            process.terminate()
        for process in reversed(processes):
            try:
                process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2.0)


if __name__ == "__main__":
    main()

