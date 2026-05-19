#!/usr/bin/env python3
"""
Demo automatizzata: KV store distribuito con vector clock.
"""

from __future__ import annotations

import argparse
import socket
import subprocess
import sys
import time
from pathlib import Path


HOST = "127.0.0.1"
MEMBERS = "A,B,C"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-port", type=int, default=6481)
    parser.add_argument(
        "--show-node-logs",
        action="store_true",
        help="mostra anche i log delle repliche",
    )
    return parser.parse_args()


def send_command(port: int, command: str) -> str:
    with socket.create_connection((HOST, port), timeout=2.0) as connection:
        connection_file = connection.makefile("rwb")
        connection_file.write((command + "\n").encode("utf-8"))
        connection_file.flush()
        response = connection_file.readline()
    if not response:
        raise RuntimeError(f"empty response from port {port}")
    return response.decode("utf-8", errors="replace").rstrip("\n")


def wait_until_ready(port: int) -> None:
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        try:
            response = send_command(port, "PING")
        except OSError:
            time.sleep(0.1)
            continue
        if response.startswith("OK"):
            return
    raise RuntimeError(f"node on port {port} did not become ready")


def run_step(title: str, commands: list[tuple[str, int, str]]) -> None:
    print()
    print(f"== {title} ==")
    for node_id, port, command in commands:
        response = send_command(port, command)
        print(f"{node_id}> {command}")
        print(f"{node_id}< {response}")


def start_nodes(base_port: int, show_node_logs: bool) -> list[subprocess.Popen[bytes]]:
    node_script = Path(__file__).with_name("node.py")
    stdout = None if show_node_logs else subprocess.DEVNULL
    stderr = None if show_node_logs else subprocess.DEVNULL
    processes: list[subprocess.Popen[bytes]] = []

    for offset, node_id in enumerate(["A", "B", "C"]):
        port = base_port + offset
        process = subprocess.Popen(
            [
                sys.executable,
                str(node_script),
                "--node-id",
                node_id,
                "--port",
                str(port),
                "--members",
                MEMBERS,
            ],
            stdout=stdout,
            stderr=stderr,
        )
        processes.append(process)

    for offset in range(3):
        wait_until_ready(base_port + offset)
    return processes


def stop_nodes(processes: list[subprocess.Popen[bytes]]) -> None:
    for process in processes:
        process.terminate()
    for process in processes:
        try:
            process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            process.kill()


def main() -> None:
    args = parse_args()
    ports = {"A": args.base_port, "B": args.base_port + 1, "C": args.base_port + 2}
    processes = start_nodes(args.base_port, args.show_node_logs)

    try:
        print("Demo: KV store distribuito con vector clock")
        print(f"Repliche: A={ports['A']} B={ports['B']} C={ports['C']}")

        run_step(
            "1. Scrittura causale su A, poi replica verso B",
            [
                ("A", ports["A"], "SET course sistemi-distribuiti"),
                ("B", ports["B"], "GET course"),
                ("A", ports["A"], f"SYNC {ports['B']}"),
                ("B", ports["B"], "GET course"),
            ],
        )

        run_step(
            "2. Scritture concorrenti sulla stessa chiave",
            [
                ("A", ports["A"], "SET room aula-a"),
                ("B", ports["B"], "SET room aula-b"),
                ("A", ports["A"], f"SYNC {ports['B']}"),
                ("A", ports["A"], "GET room"),
                ("B", ports["B"], "GET room"),
            ],
        )

        run_step(
            "3. Il contratto rifiuta SET quando esiste un conflitto",
            [
                ("A", ports["A"], "SET room aula-c"),
            ],
        )

        run_step(
            "4. Risoluzione esplicita e convergenza",
            [
                ("A", ports["A"], "RESOLVE room aula-c"),
                ("A", ports["A"], f"SYNC {ports['B']}"),
                ("B", ports["B"], "GET room"),
                ("C", ports["C"], "GET room"),
                ("B", ports["B"], f"SYNC {ports['C']}"),
                ("C", ports["C"], "GET room"),
            ],
        )

        print()
        print("Osservazione finale:")
        print("- il clock A:1,B:0,C:0 domina A:0,B:0,C:0;")
        print("- A:1,B:0,C:0 e A:0,B:1,C:0 sono concorrenti;")
        print("- RESOLVE crea un nuovo clock che domina entrambi i conflitti.")
    finally:
        stop_nodes(processes)


if __name__ == "__main__":
    main()
