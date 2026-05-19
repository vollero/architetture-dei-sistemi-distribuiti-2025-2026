#!/usr/bin/env python3
"""
Funzioni di supporto per vector clock.

Il laboratorio usa i vector clock come version vector per singola chiave:
ogni componente conta gli aggiornamenti prodotti da una replica per quella
chiave, non tutti gli eventi locali del processo.
"""

from __future__ import annotations


NodeId = str
VectorClock = dict[NodeId, int]


def new_clock(members: list[NodeId]) -> VectorClock:
    return {member: 0 for member in members}


def normalize(clock: VectorClock, members: list[NodeId]) -> VectorClock:
    normalized = {member: int(clock.get(member, 0)) for member in members}
    for node_id, value in clock.items():
        if node_id not in normalized:
            normalized[node_id] = int(value)
    return normalized


def merge(left: VectorClock, right: VectorClock, members: list[NodeId]) -> VectorClock:
    left = normalize(left, members)
    right = normalize(right, members)
    all_members = sorted(set(left) | set(right))
    return {member: max(left.get(member, 0), right.get(member, 0)) for member in all_members}


def increment(clock: VectorClock, node_id: NodeId, members: list[NodeId]) -> VectorClock:
    next_clock = normalize(clock, members)
    next_clock[node_id] = next_clock.get(node_id, 0) + 1
    return next_clock


def compare(left: VectorClock, right: VectorClock) -> str:
    """
    Confronta due vector clock.

    Ritorna:
    - "before" se left precede causalmente right;
    - "after" se left segue causalmente right;
    - "same" se i clock sono identici;
    - "concurrent" se nessuno dei due domina l'altro.
    """

    all_members = sorted(set(left) | set(right))
    left_le_right = all(left.get(member, 0) <= right.get(member, 0) for member in all_members)
    right_le_left = all(right.get(member, 0) <= left.get(member, 0) for member in all_members)
    left_lt_right = left_le_right and any(
        left.get(member, 0) < right.get(member, 0) for member in all_members
    )
    right_lt_left = right_le_left and any(
        right.get(member, 0) < left.get(member, 0) for member in all_members
    )

    if left_lt_right:
        return "before"
    if right_lt_left:
        return "after"
    if left_le_right and right_le_left:
        return "same"
    return "concurrent"


def dominates(left: VectorClock, right: VectorClock) -> bool:
    return compare(left, right) in {"after", "same"}


def encode(clock: VectorClock) -> str:
    return ",".join(f"{member}:{clock[member]}" for member in sorted(clock))
