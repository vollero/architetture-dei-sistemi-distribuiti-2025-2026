#!/usr/bin/env python3
"""
Caso di studio su Paxos single-decree.

La simulazione mostra due proposer concorrenti e tre acceptor. Il protocollo
sceglie un solo valore usando quorum di maggioranza.
"""

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class ProposalNumber:
    round_number: int
    proposer_id: str


@dataclass(frozen=True)
class AcceptedValue:
    proposal_number: ProposalNumber
    value: str


@dataclass(frozen=True)
class Promise:
    acceptor_id: str
    accepted: AcceptedValue | None


@dataclass(frozen=True)
class Accepted:
    acceptor_id: str
    proposal_number: ProposalNumber
    value: str


class Acceptor:
    def __init__(self, acceptor_id: str) -> None:
        self.acceptor_id = acceptor_id
        self.promised: ProposalNumber | None = None
        self.accepted: AcceptedValue | None = None

    def prepare(self, proposal_number: ProposalNumber) -> Promise | None:
        if self.promised is not None and proposal_number <= self.promised:
            print(f"{self.acceptor_id}: rifiuta prepare {proposal_number}, promised {self.promised}")
            return None
        self.promised = proposal_number
        if self.accepted is None:
            accepted_state = "accepted_n=None, accepted_value=None"
        else:
            accepted_state = (
                f"accepted_n={self.accepted.proposal_number}, "
                f"accepted_value={self.accepted.value!r}"
            )
        print(f"{self.acceptor_id}: PROMISE {proposal_number}, {accepted_state}")
        return Promise(self.acceptor_id, self.accepted)

    def accept(self, proposal_number: ProposalNumber, value: str) -> Accepted | None:
        if self.promised is not None and proposal_number < self.promised:
            print(f"{self.acceptor_id}: rifiuta accept {proposal_number}, promised {self.promised}")
            return None
        self.promised = proposal_number
        self.accepted = AcceptedValue(proposal_number, value)
        print(f"{self.acceptor_id}: ACCEPTED {proposal_number}, value={value!r}")
        return Accepted(self.acceptor_id, proposal_number, value)


class Proposer:
    def __init__(self, proposer_id: str, round_number: int, value: str) -> None:
        self.proposer_id = proposer_id
        self.proposal_number = ProposalNumber(round_number, proposer_id)
        self.initial_value = value

    def run(self, acceptors: list[Acceptor], quorum_size: int) -> str | None:
        print()
        print(f"Proposer {self.proposer_id}: propone {self.initial_value!r} con {self.proposal_number}")

        print("  Phase 1a - PREPARE: il proposer chiede promise a un quorum")
        promises = [
            promise
            for acceptor in acceptors
            if (promise := acceptor.prepare(self.proposal_number)) is not None
        ]
        if len(promises) < quorum_size:
            print(f"Proposer {self.proposer_id}: nessun quorum in prepare")
            return None

        print("  Phase 1b - PROMISE: il quorum riporta accepted_n e accepted_value")
        previously_accepted = [
            promise.accepted for promise in promises if promise.accepted is not None
        ]
        if previously_accepted:
            highest = max(previously_accepted, key=lambda accepted: accepted.proposal_number)
            value = highest.value
            print(
                f"Proposer {self.proposer_id}: deve usare accepted_value={value!r} "
                f"associato al massimo accepted_n={highest.proposal_number}"
            )
        else:
            value = self.initial_value
            print(f"Proposer {self.proposer_id}: nessun valore precedente, può tenere {value!r}")

        print("  Phase 2a - ACCEPT: il proposer invia il valore sicuro")
        accepted = [
            response
            for acceptor in acceptors
            if (response := acceptor.accept(self.proposal_number, value)) is not None
        ]
        if len(accepted) < quorum_size:
            print(f"Proposer {self.proposer_id}: nessun quorum in accept")
            return None

        print("  Phase 2b - ACCEPTED: il quorum ha accettato il valore")
        print(f"Proposer {self.proposer_id}: valore scelto = {value!r}")
        return value


def main() -> None:
    acceptors = [Acceptor("A1"), Acceptor("A2"), Acceptor("A3")]
    quorum_size = 2

    print("Paxos single-decree con 3 acceptor, quorum=2")
    print("Due proposer vogliono scegliere valori diversi.")
    print("Configurazione: il primo quorum è {A1,A2}, il secondo è {A2,A3}.")
    print("L'intersezione tra quorum trasferisce memoria da un tentativo al successivo.")

    proposer_a = Proposer("P1", 1, "SET x=1")
    proposer_b = Proposer("P2", 2, "SET x=2")

    chosen_a = proposer_a.run(acceptors[:2], quorum_size)
    chosen_b = proposer_b.run(acceptors[1:], quorum_size)

    print()
    print("Risultati:")
    print(f"P1 osserva valore scelto: {chosen_a}")
    print(f"P2 osserva valore scelto: {chosen_b}")
    print()
    print("Anche se P2 voleva proporre 'SET x=2', deve riproporre il valore già accettato.")
    print("La safety di Paxos impedisce che due valori diversi siano scelti.")


if __name__ == "__main__":
    main()
