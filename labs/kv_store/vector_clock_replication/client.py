#!/usr/bin/env python3
"""
Client interattivo per il KV store distribuito con vector clock.
"""

from __future__ import annotations

import argparse
import socket


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with socket.create_connection((args.host, args.port)) as connection:
        connection_file = connection.makefile("rwb")
        print(f"Connected to vector-clock kv node on {args.host}:{args.port}")

        while True:
            try:
                line = input("kv-vc> ")
            except EOFError:
                line = "QUIT"
                print()

            connection_file.write((line + "\n").encode("utf-8"))
            connection_file.flush()
            response = connection_file.readline()
            if not response:
                print("Connection closed by server.")
                break
            print(response.decode("utf-8", errors="replace").rstrip("\n"))
            if line.strip().upper() == "QUIT":
                break


if __name__ == "__main__":
    main()
