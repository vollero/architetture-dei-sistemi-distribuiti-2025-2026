#!/usr/bin/env python3
"""
Simulazione semplificata di causal delivery.

Il metadata `message_clock` non è un vector clock completo di tutti gli eventi
locali: conta i messaggi multicast/update conosciuti. Se un sistema incrementa
un vector clock anche per aggiornamenti locali non consegnabili come messaggi,
serve anche un sequence number per mittente.
"""

from dataclasses import dataclass


ProcessId = str
Vector = dict[ProcessId, int]


@dataclass(frozen=True)
class Message:
    sender: ProcessId
    payload: str
    message_clock: Vector


class Receiver:
    def __init__(self, process_id: ProcessId, processes: list[ProcessId]) -> None:
        self.process_id = process_id
        self.delivered: Vector = {process: 0 for process in processes}
        self.buffer: list[Message] = []

    def can_deliver(self, message: Message) -> bool:
        sender = message.sender
        expected_sender_count = self.delivered[sender] + 1
        # Equality is intentional: the receiver must not skip an earlier
        # message from the same sender.
        if message.message_clock[sender] != expected_sender_count:
            return False
        for process_id, value in message.message_clock.items():
            if process_id == sender:
                continue
            if value > self.delivered[process_id]:
                return False
        return True

    def receive(self, message: Message) -> None:
        print(
            f"{self.process_id}: received {message.payload} "
            f"with message_clock={message.message_clock}"
        )
        self.buffer.append(message)
        self._drain_buffer()

    def _drain_buffer(self) -> None:
        made_progress = True
        while made_progress:
            made_progress = False
            for message in list(self.buffer):
                if self.can_deliver(message):
                    self.buffer.remove(message)
                    self.delivered[message.sender] += 1
                    print(f"{self.process_id}: delivered {message.payload}")
                    made_progress = True


def main() -> None:
    receiver = Receiver("C", ["A", "B", "C"])

    m1 = Message(
        sender="A",
        payload="m1: A publishes x",
        message_clock={"A": 1, "B": 0, "C": 0},
    )
    m2 = Message(
        sender="B",
        payload="m2: B reacts to x",
        message_clock={"A": 1, "B": 1, "C": 0},
    )

    print("Consegna fuori ordine: arriva prima m2, poi m1.")
    print()
    receiver.receive(m2)
    print(f"buffer after m2: {[message.payload for message in receiver.buffer]}")
    print()
    receiver.receive(m1)
    print(f"buffer after m1: {[message.payload for message in receiver.buffer]}")
    print()
    print("m2 viene consegnato solo dopo m1, perché dipende causalmente da m1.")


if __name__ == "__main__":
    main()
