#!/usr/bin/env python3
"""
Mostra come clock fisici locali non sincronizzati possano produrre log ingannevoli.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class NodeClock:
    node_id: str
    offset_ms: int

    def timestamp(self, real_time_ms: int) -> int:
        return real_time_ms + self.offset_ms


def format_ms(value: int) -> str:
    seconds = value // 1000
    millis = value % 1000
    return f"10:00:{seconds:02d}.{millis:03d}"


def main() -> None:
    node_a = NodeClock(node_id="A", offset_ms=+150)
    node_b = NodeClock(node_id="B", offset_ms=-120)

    send_real_time = 1_000
    network_delay = 80
    receive_real_time = send_real_time + network_delay

    send_log_time = node_a.timestamp(send_real_time)
    receive_log_time = node_b.timestamp(receive_real_time)

    print("Scenario: A invia un messaggio a B.")
    print()
    print(f"tempo reale invio:     {send_real_time} ms")
    print(f"tempo reale ricezione: {receive_real_time} ms")
    print()
    print("Log locali osservati:")
    print(f"{node_a.node_id} {format_ms(send_log_time)} send m to B")
    print(f"{node_b.node_id} {format_ms(receive_log_time)} receive m from A")
    print()
    if receive_log_time < send_log_time:
        print("Nel log fisico sembra che B riceva il messaggio prima dell'invio.")
    print("Conclusione: senza un bound sullo skew, il timestamp fisico locale non basta.")


if __name__ == "__main__":
    main()

