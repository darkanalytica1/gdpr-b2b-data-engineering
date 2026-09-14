"""
IngestGate: the enforcement point for provenance-as-architecture.

The idea is simple and, in most pipelines, not actually done: a record
does not get a code review's worth of judgment applied to it once, at
design time. It gets checked every time it tries to enter the warehouse,
by code that cannot be skipped under deadline pressure. This module is
that checkpoint.

A record is rejected, with a structured, listable set of reasons, if it:

  * has no provenance at all, or provenance that fails validation
    (see provenance.validate_provenance), or
  * declares a legal basis that is theoretically valid but unusual for a
    prospecting context (flagged as a WARNING, not a hard rejection: see
    provenance.UNUSUAL_BASES_FOR_PROSPECTING), or
  * is missing the minimum identifying fields the pipeline needs to act
    on it (configurable; the default requires a non-empty "company_name"
    and at least one contact field), or
  * matches a hashed suppression entry, when a SuppressionStore is passed in.

The gate does not decide *how* to fix a rejected record. It decides
whether the record is allowed past the door, and it always says why.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .provenance import Provenance, ProvenanceError, UNUSUAL_BASES_FOR_PROSPECTING, validate_provenance
from .suppression import SuppressionStore


@dataclass
class GateResult:
    """Outcome of running one record through the ingest gate."""

    accepted: bool
    record: Mapping[str, Any]
    errors: list[ProvenanceError] = field(default_factory=list)
    warnings: list[ProvenanceError] = field(default_factory=list)

    @property
    def reason_codes(self) -> list[str]:
        return [e.code for e in self.errors]


REQUIRED_RECORD_FIELDS = ("company_name",)
CONTACT_FIELDS = ("email", "phone", "address")


class IngestGate:
    """Evaluates raw candidate records before they are written to the warehouse.

    A "raw candidate record" is expected to be a mapping with at least:
        - the business fields (company_name, email, ...)
        - a "provenance" key holding a Provenance instance (or None)

    Usage:
        gate = IngestGate(suppression_store=store)
        result = gate.evaluate(record)
        if result.accepted:
            warehouse.write(result.record)
        else:
            quarantine.write(record, reasons=result.reason_codes)
    """

    def __init__(self, suppression_store: SuppressionStore | None = None) -> None:
        self.suppression_store = suppression_store

    def evaluate(self, record: Mapping[str, Any]) -> GateResult:
        errors: list[ProvenanceError] = []
        warnings: list[ProvenanceError] = []

        prov = record.get("provenance")
        errors.extend(validate_provenance(prov if isinstance(prov, Provenance) else None))

        if isinstance(prov, Provenance) and prov.legal_basis in UNUSUAL_BASES_FOR_PROSPECTING:
            warnings.append(
                ProvenanceError(
                    "UNUSUAL_LEGAL_BASIS",
                    f"legal_basis={prov.legal_basis.value} is unusual for a prospecting "
                    "record; flagged for manual review, not auto-rejected",
                )
            )

        for f in REQUIRED_RECORD_FIELDS:
            value = record.get(f)
            if not value or not str(value).strip():
                errors.append(
                    ProvenanceError("MISSING_REQUIRED_FIELD", f"required field missing: {f}")
                )

        if not any(record.get(c) for c in CONTACT_FIELDS):
            errors.append(
                ProvenanceError(
                    "NO_CONTACT_FIELD",
                    f"record has none of the contact fields {CONTACT_FIELDS}",
                )
            )

        email = record.get("email")
        if email and self.suppression_store is not None:
            if self.suppression_store.is_suppressed(email):
                errors.append(
                    ProvenanceError(
                        "SUPPRESSED",
                        f"email is on the suppression list and must not be (re)ingested "
                        f"as an active contact target",
                    )
                )

        accepted = len(errors) == 0
        return GateResult(accepted=accepted, record=record, errors=errors, warnings=warnings)

    def evaluate_batch(self, records: list[Mapping[str, Any]]) -> tuple[list[GateResult], list[GateResult]]:
        """Convenience wrapper: returns (accepted_results, rejected_results)."""
        results = [self.evaluate(r) for r in records]
        accepted = [r for r in results if r.accepted]
        rejected = [r for r in results if not r.accepted]
        return accepted, rejected
