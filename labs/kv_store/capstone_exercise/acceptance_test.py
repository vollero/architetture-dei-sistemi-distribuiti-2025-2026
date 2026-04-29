#!/usr/bin/env python3
"""
Test di accettazione per la capstone exercise.
"""

import socket
import subprocess
import sys
import time
from pathlib import Path


HOST = "127.0.0.1"
ROUTER_PORT = 6460
SHARDS = [
    ("S0", 6461),
    ("S1", 6462),
    ("S2", 6463),
]


def wait_for_port(port: int, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((HOST, port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError(f"port {port} did not open")


def request(command: str) -> str:
    with socket.create_connection((HOST, ROUTER_PORT), timeout=2.0) as connection:
        connection_file = connection.makefile("rwb")
        connection_file.write((command + "\n").encode("utf-8"))
        connection_file.flush()
        return connection_file.readline().decode("utf-8", errors="replace").strip()


def expect(command: str, prefix: str) -> str:
    response = request(command)
    print(f"{command} -> {response}")
    if not response.startswith(prefix):
        raise AssertionError(f"{command!r}: expected {prefix!r}, got {response!r}")
    return response


def main() -> None:
    root = Path(__file__).resolve().parent
    processes: list[subprocess.Popen[bytes]] = []
    try:
        for shard_id, port in SHARDS[:2]:
            processes.append(
                subprocess.Popen(
                    [
                        sys.executable,
                        str(root / "shard_node.py"),
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
                    str(root / "router.py"),
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

        expect("PING", "OK PONG")
        expect("SET alpha one", "OK version=0")
        expect("GETV alpha", "OK one version=0")
        expect("CAS alpha 0 two", "OK version=1")
        expect("CAS alpha 0 stale", "ERR version_mismatch current=1")

        shard_id, port = SHARDS[2]
        processes.append(
            subprocess.Popen(
                [
                    sys.executable,
                    str(root / "shard_node.py"),
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

        expect("WHERE alpha", "OK key=alpha")
        expect(f"ADD_SHARD {shard_id} {HOST} {port}", "OK shard_added=S2")
        expect("WHERE alpha", "OK key=alpha target=S2")
        expect("GETV alpha", "NOT_FOUND")
        expect("REBALANCE", "OK moved=")
        expect("GETV alpha", "OK two version=1 shard=S2")
        expect("CAS alpha 1 three", "OK version=2 shard=S2")
        expect("CAS alpha 1 stale-again", "ERR version_mismatch current=2")
        expect("GETV alpha", "OK three version=2 shard=S2")

        print("acceptance test passed")
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
