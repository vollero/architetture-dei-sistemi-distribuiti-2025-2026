#!/usr/bin/env python3
"""
Stress test concorrente per il comando INCR.
"""

import argparse
import socket
import threading
from queue import Queue


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=6382)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--increments-per-thread", type=int, default=100)
    parser.add_argument("--key", default="counter")
    return parser.parse_args()


def send_command(host: str, port: int, command: str) -> str:
    with socket.create_connection((host, port)) as connection:
        connection.sendall((command + "\n").encode("utf-8"))
        response = b""
        while not response.endswith(b"\n"):
            chunk = connection.recv(1024)
            if not chunk:
                break
            response += chunk
        return response.decode("utf-8", errors="replace").strip()


def worker(host: str, port: int, key: str, increments: int, results: Queue[str]) -> None:
    for _ in range(increments):
        results.put(send_command(host, port, f"INCR {key}"))


def main() -> None:
    args = parse_args()
    results: Queue[str] = Queue()

    reset_response = send_command(args.host, args.port, f"SET {args.key} 0")
    print(f"reset: {reset_response}")

    threads: list[threading.Thread] = []
    for index in range(args.threads):
        thread = threading.Thread(
            target=worker,
            args=(args.host, args.port, args.key, args.increments_per_thread, results),
            name=f"load-{index}",
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    total = args.threads * args.increments_per_thread
    final_response = send_command(args.host, args.port, f"GET {args.key}")
    print(f"expected increments: {total}")
    print(f"responses received: {results.qsize()}")
    print(f"final value: {final_response}")


if __name__ == "__main__":
    main()
