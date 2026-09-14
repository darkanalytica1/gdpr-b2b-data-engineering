"""
Provenance: the flagship pattern of this repository.

The rule this module encodes: no record derived from a third-party source
enters the warehouse without three things attached to it:

1. source_url: where the fact came from (a specific page or document, not
   a vague "the internet").
2. retrieved_at: when we looked at it, in UTC. Facts age. A phone number
   or a director's name that was correct in 2022 may not be correct now,
   and "we do not know when we learned this" is not an answer you want to
   give a data subject or a regulator.
3. legal_basis: which GDPR Article 6(1) basis justifies processing this
   specific fact, for this specific purpose. Not "we have a basis
   somewhere", but a basis you can name for this record.

Provenance is attached at the point of ingest, travels with the record for
its whole life in the warehouse, and is what makes an Article 14 notice,
a subject access request, or a regulator's question ("why do you have
this, and since when") answerable in seconds instead of requiring an
archaeological dig through old scraper logs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from urllib.parse import urlparse


class LegalBasis(str, Enum):
    """The six Article 6(1) GDPR legal bases.

    In a B2B prospecting context, LEGITIMATE_INTEREST is the realistic
    basis for most contact data collected about employees of other
    businesses (see docs/LEGAL_BASIS.md). CONSENT matters separately for
    electronic marketing under ePrivacy-derived national law (see
    docs/EPRIVACY_ROMANIA.md): a record can be lawfully *held* under
    legitimate interest and still be unlawful to *email* without the
    right marketing-consent or soft opt-in status. This module only
    governs the "may we hold this fact" question.
    """

    LEGITIMATE_INTEREST = "legitimate_interest"
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTEREST = "vital_interest"
    PUBLIC_TASK = "public_task"


# Legal bases that are realistic for a B2B prospecting database. VITAL_INTEREST
# is included in the enum for completeness (it exists in the law) but a
# prospecting pipeline should never plausibly need it; the ingest gate flags
# it for review rather than rejecting outright, since blanket rejection of a
# valid enum value would hide a data-entry mistake worth looking at by hand.
UNUSUAL_BASES_FOR_PROSPECTING = frozenset({LegalBasis.VITAL_INTEREST})


@dataclass(frozen=True)
class Provenance:
    """Immutable provenance envelope attached to every third-party-derived record.

    Fields:
        source_url: the exact URL or document reference the fact was read from.
        retrieved_at: UTC timestamp of when the fact was retrieved.
        legal_basis: the Article 6(1) basis relied on for this fact.
        source_name: optional human-readable label for the source register
            (e.g. "national companies registry", "official tender portal").
            Kept separate from source_url so the URL can rot or be
            restructured without losing the ability to say broadly where
            data came from.
        notes: optional free-text, e.g. "director name changed since last
            retrieval" or a cross-reference to an LIA.

    This dataclass deliberately does not raise on construction: a value that
    fails validation (an empty source_url, a naive timestamp, a bad legal
    basis) is still a real Python object you can inspect and reject with a
    structured reason. The ingest gate (ingest_gate.py) is the layer that
    turns validation failures into a rejection decision; keeping the two
    concerns separate means the check in validate_provenance() below is the
    single source of truth, called by the gate rather than duplicated in an
    exception path.
    """

    source_url: str
    retrieved_at: datetime
    legal_basis: LegalBasis
    source_name: str = ""
    notes: str = ""


@dataclass(frozen=True)
class ProvenanceError:
    """A single, structured reason a Provenance (or record) failed validation."""

    code: str
    message: str


def validate_provenance(prov: Provenance | None) -> list[ProvenanceError]:
    """Validate a Provenance instance and return a list of structured errors.

    An empty list means the provenance is valid. This function never raises;
    it is the pure check that both Provenance.__post_init__ and the ingest
    gate call, so the two never drift out of sync.
    """

    errors: list[ProvenanceError] = []

    if prov is None:
        errors.append(ProvenanceError("MISSING_PROVENANCE", "no provenance attached to record"))
        return errors

    if not prov.source_url or not prov.source_url.strip():
        errors.append(ProvenanceError("MISSING_SOURCE_URL", "source_url is empty"))
    else:
        parsed = urlparse(prov.source_url)
        if not parsed.scheme or not parsed.netloc:
            errors.append(
                ProvenanceError(
                    "MALFORMED_SOURCE_URL",
                    f"source_url does not look like a URL: {prov.source_url!r}",
                )
            )

    if prov.retrieved_at is None:
        errors.append(ProvenanceError("MISSING_RETRIEVED_AT", "retrieved_at is missing"))
    else:
        if prov.retrieved_at.tzinfo is None:
            errors.append(
                ProvenanceError(
                    "NAIVE_RETRIEVED_AT",
                    "retrieved_at has no timezone; store all timestamps in UTC",
                )
            )
        else:
            now = datetime.now(timezone.utc)
            if prov.retrieved_at > now:
                errors.append(
                    ProvenanceError(
                        "FUTURE_RETRIEVED_AT",
                        f"retrieved_at ({prov.retrieved_at.isoformat()}) is in the future",
                    )
                )

    if prov.legal_basis is None:
        errors.append(ProvenanceError("MISSING_LEGAL_BASIS", "legal_basis is missing"))
    elif not isinstance(prov.legal_basis, LegalBasis):
        errors.append(
            ProvenanceError(
                "INVALID_LEGAL_BASIS",
                f"legal_basis {prov.legal_basis!r} is not a recognised LegalBasis value",
            )
        )

    return errors
