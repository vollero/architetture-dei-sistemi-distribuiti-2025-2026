#!/usr/bin/env python3
"""
Client interattivo per KV Store v0.
"""

import socket


HOST = "127.0.0.1"
PORT = 6380


def main() -> None:
    with socket.create_connection((HOST, PORT)) as connection:
        connection_file = connection.makefile("rwb")
        print(f"Connected to kv store on {HOST}:{PORT}")

        while True:
            try:
                line = input("kv> ")
            except EOFError:
                line = "QUIT"
                print()

            connection_file.write((line + "\n").encode("utf-8"))
            connection_file.flush()

            response = connection_file.readline()
            if not response:
                print("Connection closed by server.")
                break

            decoded = response.decode("utf-8", errors="replace").rstrip("\n")
            print(decoded)

            if line.strip().upper() == "QUIT":
                break


if __name__ == "__main__":
    main()
