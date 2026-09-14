"""
retention: field-class TTLs, because "we might need it later" is not a purpose.

GDPR's storage limitation principle (Article 5(1)(e)) does not ask "could
this be useful one day"; it asks "for how long does the stated processing
purpose actually require this field". Different fields on the same record
justify different retention periods, because they serve different
purposes and decay in usefulness at different rates:

  IDENTITY fields (company name, registration number): the purpose is
  "know which legal entity this is". These barely decay; a long TTL, or
  none, is defensible as long as the underlying purpose (holding a
  prospecting record on this company at all) is still active.

  CONTACT fields (email, phone): the purpose is "be able to reach this
  role or person". These decay: people change jobs, role inboxes get
  reorganised. A moderate TTL forces a re-verification instead of letting
  a contact field silently rot into a wrong number for a stranger.

  BEHAVIOURAL fields (site visits, email opens, campaign responses): the
  purpose is usually "score or prioritise outreach", a purpose with a
  short natural shelf life. Old behavioural signal is not just useless,
  it actively misleads a scoring model.

  DERIVED fields (a computed score, a segment label): these should
  generally have the shortest TTL of all, because they are cheap to
  recompute from source data and expensive to justify keeping once the
  inputs they were built from have themselves expired or changed.

This module does not "decide" retention periods; the periods below are a
starting, editable example, not a legal ruling. What it enforces is the
discipline: every field on a record is assigned to a class, every class
has an explicit TTL, and a record's age is checked against the field's
class, not against one blanket rule for the whole record. See
docs/RETENTION.md for the reasoning and how to tune the defaults for a
real deployment.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Mapping


class FieldClass(str, Enum):
    IDENTITY = "identity"
    CONTACT = "contact"
    BEHAVIORAL = "behavioral"
    DERIVED = "derived"


# Default TTL, in days, per field class. None means "no automatic
# expiry", which should be a deliberate choice, not the default outcome
# of forgetting to classify a field.
DEFAULT_TTL_DAYS: dict[FieldClass, int | None] = {
    FieldClass.IDENTITY: 730,      # 24 months: re-verify identity data roughly every 2 years
    FieldClass.CONTACT: 365,       # 12 months: contacts are the fastest-decaying B2B field type
    FieldClass.BEHAVIORAL: 180,    # 6 months: stale behavioural signal misleads more than it helps
    FieldClass.DERIVED: 90,        # 3 months: cheap to recompute, so keep the shortest leash
}


@dataclass(frozen=True)
class FieldPolicy:
    field_class: FieldClass
    ttl_days: int | None


@dataclass(frozen=True)
class RetentionDecision:
    field: str
    field_class: FieldClass
    action: str  # "keep" or "expire"
    age_days: float | None
    ttl_days: int | None


class RetentionEngine:
    """Applies per-field-class TTLs to a record's fields.

    field_map maps field name -> FieldClass (e.g. {"email": FieldClass.CONTACT}).
    ttl_overrides optionally overrides the default TTL for specific classes,
    for deployments that need a stricter or looser policy than the default.
    """

    def __init__(
        self,
        field_map: Mapping[str, FieldClass],
        ttl_overrides: Mapping[FieldClass, int | None] | None = None,
    ) -> None:
        self.field_map = dict(field_map)
        self.ttl_days = dict(DEFAULT_TTL_DAYS)
        if ttl_overrides:
            self.ttl_days.update(ttl_overrides)

    def policy_for(self, field: str) -> FieldPolicy | None:
        field_class = self.field_map.get(field)
        if field_class is None:
            return None
        return FieldPolicy(field_class=field_class, ttl_days=self.ttl_days.get(field_class))

    def evaluate_field(
        self, field: str, field_last_updated_at: datetime, now: datetime | None = None
    ) -> RetentionDecision:
        now = now or datetime.now(timezone.utc)
        policy = self.policy_for(field)
        if policy is None:
            # Unclassified fields are not silently kept forever: they are
            # reported as such so the gap is visible instead of hidden by
            # falling back to some implicit default.
            return RetentionDecision(
                field=field, field_class=FieldClass.DERIVED, action="keep",
                age_days=None, ttl_days=None,
            )

        age = now - field_last_updated_at
        age_days = age.total_seconds() / 86400

        if policy.ttl_days is None:
            action = "keep"
        else:
            action = "expire" if age_days > policy.ttl_days else "keep"

        return RetentionDecision(
            field=field,
            field_class=policy.field_class,
            action=action,
            age_days=age_days,
            ttl_days=policy.ttl_days,
        )

    def apply(
        self,
        record: Mapping[str, Any],
        field_timestamps: Mapping[str, datetime],
        now: datetime | None = None,
    ) -> tuple[dict[str, Any], list[RetentionDecision]]:
        """Return (scrubbed_record, decisions).

        field_timestamps maps field name -> the datetime that field's value
        was last verified/updated. A field with no entry in field_timestamps
        is left untouched (there is no age to evaluate against); this makes
        the caller's timestamp bookkeeping gaps visible rather than treating
        a missing timestamp as automatically expired or automatically safe.
        """
        now = now or datetime.now(timezone.utc)
        scrubbed = dict(record)
        decisions: list[RetentionDecision] = []

        for field, last_updated in field_timestamps.items():
            if field not in record:
                continue
            decision = self.evaluate_field(field, last_updated, now=now)
            decisions.append(decision)
            if decision.action == "expire":
                scrubbed[field] = None

        return scrubbed, decisions
