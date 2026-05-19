#!/usr/bin/env python3
"""
Simulazione di vector clock per distinguere causalità e concorrenza.
"""

from dataclasses import dataclass


ProcessId = str
Vector = dict[ProcessId, int]


def compare(left: Vector, right: Vector) -> str:
    left_le_right = all(left[p] <= right[p] for p in left)
    right_le_left = all(right[p] <= left[p] for p in left)
    left_lt_right = left_le_right and any(left[p] < right[p] for p in left)
    right_lt_left = right_le_left and any(right[p] < left[p] for p in left)
    if left_lt_right:
        return "before"
    if right_lt_left:
        return "after"
    if left == right:
        return "same"
    return "concurrent"


@dataclass
class Process:
    process_id: ProcessId
    clock: Vector

    def local_event(self) -> Vector:
        self.clock[self.process_id] += 1
        return dict(self.clock)

    def send(self) -> Vector:
        return self.local_event()

    def receive(self, message_clock: Vector) -> Vector:
        for process_id, value in message_clock.items():
            self.clock[process_id] = max(self.clock[process_id], value)
        self.clock[self.process_id] += 1
        return dict(self.clock)


def main() -> None:
    initial = {"A": 0, "B": 0, "C": 0}
    a = Process("A", dict(initial))
    b = Process("B", dict(initial))

    a1 = a.local_event()
    b1 = b.local_event()

    print("Due eventi locali indipendenti:")
    print(f"A1 = {a1}")
    print(f"B1 = {b1}")
    print(f"relazione: {compare(a1, b1)}")
    print()

    message_clock = a.send()
    b_receive = b.receive(message_clock)

    print("Dopo un messaggio da A a B:")
    print(f"A send = {message_clock}")
    print(f"B receive = {b_receive}")
    print(f"relazione: A send is {compare(message_clock, b_receive)} B receive")
    print()
    print("Conclusione: i vector clock distinguono concorrenza e causalità.")


if __name__ == "__main__":
    main()

