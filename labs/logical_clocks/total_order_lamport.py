#!/usr/bin/env python3
"""
Ordine totale ottenuto con coppie (lamport_time, process_id).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    process_id: str
    lamport_time: int
    label: str

    @property
    def order_key(self) -> tuple[int, str]:
        return (self.lamport_time, self.process_id)


def main() -> None:
    events = [
        Event("B", 4, "SET x 2"),
        Event("A", 4, "SET x 1"),
        Event("C", 5, "GET x"),
        Event("A", 6, "CAS x 4 3"),
    ]

    print("Eventi non ordinati:")
    for event in events:
        print(f"{event.process_id}: L={event.lamport_time} {event.label}")

    print()
    print("Ordine totale con (lamport_time, process_id):")
    for event in sorted(events, key=lambda item: item.order_key):
        print(f"{event.order_key}: {event.process_id} {event.label}")

    print()
    print("Nota: questo ordine è deterministico, ma può ordinare eventi concorrenti.")
    print("Non va confuso con una prova di causalità.")


if __name__ == "__main__":
    main()

