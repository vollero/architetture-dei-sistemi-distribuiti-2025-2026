#!/usr/bin/env python3
"""
Simulazione minima dei clock logici di Lamport.
"""

from dataclasses import dataclass


@dataclass
class Message:
    sender: str
    receiver: str
    payload: str
    lamport_time: int


class Process:
    def __init__(self, process_id: str) -> None:
        self.process_id = process_id
        self.clock = 0

    def local_event(self, label: str) -> tuple[str, int, str]:
        self.clock += 1
        return (self.process_id, self.clock, label)

    def send(self, receiver: str, payload: str) -> Message:
        self.clock += 1
        return Message(
            sender=self.process_id,
            receiver=receiver,
            payload=payload,
            lamport_time=self.clock,
        )

    def receive(self, message: Message) -> tuple[str, int, str]:
        self.clock = max(self.clock, message.lamport_time) + 1
        return (
            self.process_id,
            self.clock,
            f"receive {message.payload} from {message.sender}",
        )


def print_event(event: tuple[str, int, str]) -> None:
    process_id, clock, label = event
    print(f"{process_id}: L={clock:<2} {label}")


def main() -> None:
    a = Process("A")
    b = Process("B")

    print("Simulazione Lamport clock")
    print()
    print_event(a.local_event("local compute"))
    message = a.send("B", "m1")
    print(f"A: L={message.lamport_time:<2} send {message.payload} to B")
    print_event(b.local_event("independent local event"))
    print_event(b.receive(message))
    print_event(b.local_event("after receive"))
    print()
    print("Garanzia: se evento1 happened-before evento2, allora L(evento1) < L(evento2).")
    print("Limite: L(evento1) < L(evento2) non dimostra causalità.")


if __name__ == "__main__":
    main()

