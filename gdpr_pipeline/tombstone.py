"""
tombstone: erasure that survives a warehouse that re-ingests from source.

The "zombie record" problem: a data subject asks for erasure, you delete
the record, everyone is happy, and then the nightly job that re-ingests
company data from the source register (the register itself was never
asked to erase anything, and generally cannot be: it is the primary,
public record) pulls the exact same fact back in tomorrow morning. The
person is erased and un-erased on a schedule, which is not erasure at
all; it is a data retention policy of one day.

The fix is a tombstone: a persistent marker, independent of the
warehouse tables that get rebuilt or re-ingested, that says "this
identifier has been erased, do not let it back in, and if you already
let it back in before this tombstone existed, take it back out." A
tombstone is checked at three points:

  1. Before ingest: pending records matching a tombstone are dropped
     before they ever reach the warehouse (see apply_to_incoming).
  2. After ingest, as a sweep: in case a record slipped in through a
     path that did not check the tombstone (a bulk import, a manual
     fix), a periodic sweep removes anything tombstoned that is present.
  3. At any read/export path that assembles a contact list, as a last
     defence.

A tombstone is not itself the erasure of the personal data (the fact of
"this address must be blocked" is retained, deliberately, because it is
the only way honour the request going forward). What is erased is the
underlying company/contact record that carried the personal data. The
tombstone entry itself should follow the same hashed-identifier
principle as the suppression list, for the same reason: a tombstone
store should not become a second place the plaintext personal data lives.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .suppression import hash_identifier, normalize_email


@dataclass(frozen=True)
class TombstoneEntry:
    reason: str
    erased_at: str  # ISO-8601 UTC timestamp


@dataclass
class TombstoneStore:
    """Persistent record of erasure requests, keyed by a salted hash.

    Parameters mirror SuppressionStore deliberately: both are
    "hash now, persist independently, never let re-ingest overwrite"
    stores, and keeping their shapes consistent makes the pattern
    easier to recognise and reuse for a third case later (e.g. a
    do-not-call registry) without inventing a new design.
    """

    salt: str
    path: Path | None = None
    _entries: dict[str, TombstoneEntry] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if self.path is not None and self.path.exists():
            self._load()

    def _load(self) -> None:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        for h, meta in raw.items():
            self._entries[h] = TombstoneEntry(reason=meta["reason"], erased_at=meta["erased_at"])

    def save(self) -> None:
        if self.path is None:
            raise ValueError("cannot save an in-memory-only TombstoneStore (no path set)")
        payload = {
            h: {"reason": e.reason, "erased_at": e.erased_at} for h, e in self._entries.items()
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def erase(self, identifier: str, reason: str) -> str:
        """Record an erasure request for an identifier (typically an email).

        Returns the stored hash. Like SuppressionStore.add, this is
        additive-only: there is no operation that clears the whole store,
        so a fresh source re-ingest can never wipe out an erasure record.
        """
        h = hash_identifier(normalize_email(identifier), self.salt)
        self._entries[h] = TombstoneEntry(
            reason=reason, erased_at=datetime.now(timezone.utc).isoformat()
        )
        if self.path is not None:
            self.save()
        return h

    def is_tombstoned(self, identifier: str) -> bool:
        h = hash_identifier(normalize_email(identifier), self.salt)
        return h in self._entries

    def apply_to_incoming(
        self,
        records: list[Mapping[str, Any]],
        key_field: str = "email",
    ) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
        """Split a batch of freshly re-ingested records into (kept, blocked).

        Call this on every re-ingest run, before records reach the ingest
        gate or the warehouse. `key_field` is the field on each record to
        check against the tombstone (email by default; pass a different
        field, or wrap this function, for a non-email identifier).
        """
        kept: list[Mapping[str, Any]] = []
        blocked: list[Mapping[str, Any]] = []
        for record in records:
            identifier = record.get(key_field)
            if identifier and self.is_tombstoned(identifier):
                blocked.append(record)
            else:
                kept.append(record)
        return kept, blocked

    def sweep(
        self,
        existing_records: list[Mapping[str, Any]],
        key_field: str = "email",
    ) -> list[Mapping[str, Any]]:
        """Remove any already-warehoused record that matches a tombstone.

        This is the periodic safety net for records that entered through
        a path that skipped apply_to_incoming (a manual fix, a bulk
        restore from backup). Returns the list of records that survive
        the sweep; the caller is responsible for actually deleting the
        dropped ones from wherever they are stored.
        """
        survivors, _dropped = self.apply_to_incoming(existing_records, key_field=key_field)
        return survivors

    def __len__(self) -> int:
        return len(self._entries)
