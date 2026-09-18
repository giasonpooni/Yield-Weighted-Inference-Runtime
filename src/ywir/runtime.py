"""Admission runtime. Tokens are control. Structure is what glues."""

from __future__ import annotations

from dataclasses import dataclass, field

from ywir.constitution import (
    DEPARTMENTS,
    ETA_BLEND,
    MAX_BURST_TOKENS,
    MIN_TOKENS,
    PACKAGE_VERSION,
)
from ywir.departments import check_department
from ywir.errors import YwirRefuse
from ywir.observation import Proposal, Settlement
from ywir.receipts import YwirReceipt, from_verdict
from ywir.spill import classify
from ywir.store import CompositionStore, Morphism


GIT_PIN_UNSET = "in_development"


@dataclass
class HostState:
    loop: str
    budget: dict[str, int]
    eta_hat: float = 0.0
    base: str = "default"
    store: CompositionStore = field(default_factory=CompositionStore)
    closed: bool = False


@dataclass(frozen=True)
class Verdict:
    status: str
    letter: str
    details: str
    refuse_code: str | None = None
    admitted: bool = False
    department: str | None = None
    tokens: int = 0
    compose_ids: tuple[str, ...] = ()

    def receipt(self, loop: str, git_pin: str = GIT_PIN_UNSET) -> YwirReceipt:
        return from_verdict(
            loop,
            self.status,
            self.letter,
            self.details,
            git_pin=git_pin,
            refuse_code=self.refuse_code,
        )


def open_host(
    loop: str,
    budget: dict[str, int] | None = None,
    *,
    eta_hat: float = 0.0,
    base: str = "default",
) -> HostState:
    if not loop:
        raise YwirRefuse("missing_loop", "loop name is required")
    raw = dict(budget) if budget is not None else {d: 0 for d in DEPARTMENTS}
    for name, value in raw.items():
        check_department(name)
        if value < 0:
            raise YwirRefuse("negative_budget", f"{name}={value}")
    for name in DEPARTMENTS:
        raw.setdefault(name, 0)
    extra = [k for k in raw if k not in DEPARTMENTS]
    if extra:
        raise YwirRefuse("unknown_department", ",".join(extra))
    return HostState(loop=loop, budget=raw, eta_hat=eta_hat, base=base)


def decide(host: HostState, proposal: Proposal) -> Verdict:
    if proposal.loop != host.loop:
        raise YwirRefuse("loop_mismatch", f"{proposal.loop} != {host.loop}")
    check_department(proposal.department)
    if host.closed:
        return Verdict(
            status="closed",
            letter="CLOSE_BUDGET",
            details="host already closed",
            refuse_code="BUDGET_CLOSED",
        )
    if proposal.close:
        host.closed = True
        return Verdict(
            status="closed",
            letter="CLOSE_BUDGET",
            details="caller closed the budget",
            refuse_code="BUDGET_CLOSED",
        )
    if proposal.reindex_base is not None:
        host.base = proposal.reindex_base
        return Verdict(
            status="reindexed",
            letter="REINDEX",
            details=f"base={host.base}",
            department=proposal.department,
        )
    if proposal.tokens < MIN_TOKENS or proposal.tokens > MAX_BURST_TOKENS:
        raise YwirRefuse(
            "burst_out_of_range",
            f"tokens={proposal.tokens} not in [{MIN_TOKENS}, {MAX_BURST_TOKENS}]",
        )

    code = classify(proposal, host.store, host.eta_hat)
    if code == "REQUEST_EVIDENCE":
        return Verdict(
            status="evidence",
            letter="REQUEST_EVIDENCE",
            details=proposal.plant_refuse or "evidence required",
            refuse_code="REQUEST_EVIDENCE",
            department=proposal.department,
        )
    if code == "COMPOSE_INSTEAD":
        present = host.store.present(proposal.compose_candidates)
        return Verdict(
            status="composed",
            letter="COMPOSE",
            details="accepted morphism already answers",
            refuse_code="COMPOSE_INSTEAD",
            department=proposal.department,
            compose_ids=present,
        )
    if code is not None:
        return Verdict(
            status="refused",
            letter="REFUSE_SPILL",
            details=code,
            refuse_code=code,
            department=proposal.department,
            tokens=proposal.tokens,
        )

    remaining = host.budget[proposal.department]
    if remaining <= 0:
        return Verdict(
            status="refused",
            letter="REFUSE_SPILL",
            details=f"{proposal.department} budget closed",
            refuse_code="BUDGET_CLOSED",
            department=proposal.department,
        )
    if proposal.tokens > remaining:
        return Verdict(
            status="refused",
            letter="REFUSE_SPILL",
            details=f"{proposal.department} has {remaining}, asked {proposal.tokens}",
            refuse_code="DEPARTMENT_STARVED",
            department=proposal.department,
            tokens=proposal.tokens,
        )
    return Verdict(
        status="admitted",
        letter="ADMIT",
        details=f"admit {proposal.tokens} on {proposal.department}",
        admitted=True,
        department=proposal.department,
        tokens=proposal.tokens,
    )


def observed_yield(settlement: Settlement) -> float:
    structure = 0.0
    if settlement.rank_delta > 0:
        structure += float(settlement.rank_delta)
    if settlement.glued:
        structure += 1.0
    if settlement.new_morphism_id:
        structure += 1.0
    structure -= settlement.similarity_to_store
    if settlement.eta_falling and settlement.confidence_rising:
        structure -= 1.0
    spent = max(settlement.tokens_spent, 1)
    return structure / float(spent)


def settle(host: HostState, proposal: Proposal, settlement: Settlement) -> None:
    if host.closed:
        raise YwirRefuse("budget_closed", "cannot settle a closed host")
    check_department(proposal.department)
    if settlement.tokens_spent < 0:
        raise YwirRefuse("negative_spend", str(settlement.tokens_spent))
    if settlement.tokens_spent > host.budget[proposal.department]:
        raise YwirRefuse(
            "overspend",
            f"spent {settlement.tokens_spent} > {host.budget[proposal.department]}",
        )
    if not settlement.glued:
        raise YwirRefuse("H1_NO_GLUE", "settlement did not restrict")
    host.budget[proposal.department] -= settlement.tokens_spent
    host.eta_hat = (1.0 - ETA_BLEND) * host.eta_hat + ETA_BLEND * observed_yield(
        settlement
    )
    if settlement.new_morphism_id:
        host.store.accept(
            Morphism(
                morphism_id=settlement.new_morphism_id,
                type_name=settlement.new_morphism_type or "undeclared",
                department=proposal.department,
                loop=host.loop,
            )
        )


def snapshot(host: HostState) -> dict[str, object]:
    return {
        "instrument": "ywir",
        "package_version": PACKAGE_VERSION,
        "loop": host.loop,
        "base": host.base,
        "closed": host.closed,
        "eta_hat": host.eta_hat,
        "budget": dict(host.budget),
        "store": list(host.store.ids()),
    }
