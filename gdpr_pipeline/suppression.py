"""
suppression: a suppression list that actually holds.

A surprising number of "we honour opt-outs" systems fail in one of three
ways:

1. The suppression check happens at list-build time (when a campaign is
   assembled) instead of at send/call time. Between build and send, a
   suppression added an hour ago is silently ignored because the list
   was already frozen.
2. A nightly re-ingest from the source system reintroduces the same
   contact as "new" and nothing re-checks it against the suppression
   list, because the suppression list only ever got consulted once,
   during the original ingest.
3. The suppression list stores the raw email address in plain text,
   which means a system whose entire purpose is "remember to leave this
   person alone" is itself a new place that person's contact data lives,
   often with weaker access controls than the main record it is meant
   to protect.

This module addresses all three:

  * check_at_send(): the function a sending/dialling job is expected to
    call immediately before contacting someone, not a cache of a check
    done earlier.
  * The ingest gate (ingest_gate.py) also consults the same store, so a
    suppressed contact is rejected on re-ingest, not just at send time;
    defence in depth rather than a single choke point.
  * Records are keyed by a salted hash of the normalised address, never
    by the plaintext address. The store never regains a way to reverse
    the hash back into an email address; it can only match a candidate
    address you present against a hash it already holds.
  * Suppression entries are additive and persisted independently of the
    contact warehouse. A fresh import of the contact table has no
    mechanism to remove or shadow a suppression entry: the only way an
    entry leaves the store is an explicit, logged removal call.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def normalize_email(email: str) -> str:
    """Lowercase and strip an email address for consistent hashing.

    Real-world normalisation (dot-folding on some providers, plus-tag
    stripping, IDNA on the domain) is deliberately not attempted here:
    over-normalising can cause two genuinely different mailboxes to
    collide. Keep normalisation conservative; when in doubt, treat two
    addresses as different.
    """
    return email.strip().lower()


def hash_identifier(value: str, salt: str) -> str:
    """Salted SHA-256 hash of a normalised identifier (email, phone, etc.).

    The salt is a deployment secret, not a per-record value: it is what
    prevents a leaked suppression store from being trivially reversed
    with a rainbow table of common email patterns. Rotating the salt
    invalidates every existing hash, so treat it like any other secret
    (store it outside version control, back it up deliberately).
    """
    digest = hashlib.sha256()
    digest.update(salt.encode("utf-8"))
    digest.update(b"|")
    digest.update(value.encode("utf-8"))
    return digest.hexdigest()


@dataclass(frozen=True)
class SuppressionEntry:
    reason: str
    suppressed_at: str  # ISO-8601 UTC timestamp, stored as a string for JSON round-trips


@dataclass
class SuppressionStore:
    """A hashed, persisted suppression list.

    Parameters:
        salt: deployment-wide secret used to salt every hash. Must be
            stable across restarts or every existing entry becomes
            unmatchable (functionally: the whole list is lost).
        path: optional file path for persistence. If given, the store
            loads existing entries from this path on construction and
            save() writes back to it. If omitted, the store is
            in-memory only (useful for tests).
    """

    salt: str
    path: Path | None = None
    _entries: dict[str, SuppressionEntry] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if self.path is not None and self.path.exists():
            self._load()

    def _load(self) -> None:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        for h, meta in raw.items():
            self._entries[h] = SuppressionEntry(
                reason=meta["reason"], suppressed_at=meta["suppressed_at"]
            )

    def save(self) -> None:
        if self.path is None:
            raise ValueError("cannot save an in-memory-only SuppressionStore (no path set)")
        payload = {
            h: {"reason": e.reason, "suppressed_at": e.suppressed_at}
            for h, e in self._entries.items()
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def add(self, email: str, reason: str) -> str:
        """Add an address to the suppression list. Returns the stored hash.

        This is additive: calling add() again for an already-suppressed
        address updates the reason/timestamp but never removes the entry,
        and there is no bulk "replace the whole list" operation, on
        purpose, so a fresh import can never accidentally drop entries.
        """
        h = hash_identifier(normalize_email(email), self.salt)
        self._entries[h] = SuppressionEntry(
            reason=reason,
            suppressed_at=datetime.now(timezone.utc).isoformat(),
        )
        if self.path is not None:
            self.save()
        return h

    def remove(self, email: str) -> bool:
        """Explicitly remove a suppression entry.

        This exists for legitimate corrections (a suppression added by
        mistake) and must be a deliberate, individually logged call in any
        real deployment, never a side effect of an import job.
        """
        h = hash_identifier(normalize_email(email), self.salt)
        existed = h in self._entries
        self._entries.pop(h, None)
        if self.path is not None:
            self.save()
        return existed

    def is_suppressed(self, email: str) -> bool:
        h = hash_identifier(normalize_email(email), self.salt)
        return h in self._entries

    def check_at_send(self, email: str) -> bool:
        """Return True if it is safe to contact this address right now.

        Named distinctly from is_suppressed() to make the call site read
        as what it is: a sending or dialling job should call
        check_at_send() immediately before each contact attempt, not
        rely on a check performed when the campaign list was built.
        """
        return not self.is_suppressed(email)

    def __len__(self) -> int:
        return len(self._entries)
