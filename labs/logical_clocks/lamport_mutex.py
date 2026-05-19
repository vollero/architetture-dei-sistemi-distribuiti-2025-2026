#!/usr/bin/env python3
"""
Mutua esclusione distribuita semplificata con ordine totale di Lamport.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True, order=True)
class Request:
    lamport_time: int
    process_id: str
    resource: str = field(compare=False)


class Process:
    def __init__(self, process_id: str) -> None:
        self.process_id = process_id
        self.clock = 0

    def request_lock(self, resource: str) -> Request:
        self.clock += 1
        return Request(self.clock, self.process_id, resource)


def main() -> None:
    processes = [Process("A"), Process("B"), Process("C")]

    requests = [
        processes[1].request_lock("kv:x"),
        processes[0].request_lock("kv:x"),
        processes[2].request_lock("kv:x"),
    ]

    print("Richieste arrivate in ordine di rete:")
    for request in requests:
        print(f"{request.process_id}: request {request.resource} at L={request.lamport_time}")

    print()
    print("Ordine comune usando (lamport_time, process_id):")
    for position, request in enumerate(sorted(requests), start=1):
        print(
            f"{position}. {request.process_id} enters critical section "
            f"for {request.resource} with key={(request.lamport_time, request.process_id)}"
        )

    print()
    print("Il tie-breaker sul process_id rende l'ordine totale e riproducibile.")
    print("Questo non dimostra causalità: serve a decidere chi entra prima.")


if __name__ == "__main__":
    main()

