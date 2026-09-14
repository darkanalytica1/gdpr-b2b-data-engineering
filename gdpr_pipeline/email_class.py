"""
email_class: role vs nominal email classification.

This is the distinction that trips up most B2B data teams, because it
looks cosmetic and is not. Two email addresses at the same company carry
very different risk:

  office@acme.example
      A role (also called "functional") address. It identifies a function
      within a legal entity, not a natural person. It is addressed to
      "whoever handles this inbox today". Processing it as B2B contact
      data under legitimate interest is the comparatively low-risk case
      this repository's LIA (docs/LIA_WORKED_EXAMPLE.md) is built around.

  jane.doe@acme.example
      A nominal (personal) address. Even though it sits on a company
      domain and is used for work, it identifies a specific natural
      person and is personal data about that person, full stop. It
      deserves the fuller GDPR treatment: a real balancing test that
      weighs the individual's expectations, a lower tolerance for stale
      data, and a straightforward path to honour access/erasure/objection
      requests addressed to that person specifically (see
      docs/DATA_SUBJECT_RIGHTS.md).

Treating every address the same, in either direction, is a mistake: too
strict on role addresses starves a legitimate sales process of a lawful,
low-risk contact point; too loose on nominal addresses is exactly the
posture that turns a prospecting database into a liability.

This module classifies an address into one of ROLE, NOMINAL, JUNK, or
UNKNOWN. It is a heuristic, not an oracle: it is deliberately biased
towards NOMINAL / UNKNOWN when unsure, on the theory that over-protecting
an address costs you a slightly more cautious handling path, while
under-protecting a personal address costs you a compliance incident.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class EmailKind(str, Enum):
    ROLE = "role"
    NOMINAL = "nominal"
    JUNK = "junk"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EmailClassification:
    address: str
    kind: EmailKind
    reason: str


# Role / functional local-parts, in English and Romanian, covering the
# common department and mailbox conventions seen on RO and EU company
# sites. This list is illustrative, not exhaustive; a production system
# should let operators extend it without a code change.
ROLE_LOCAL_PARTS = frozenset(
    {
        # generic
        "office", "info", "contact", "hello", "hi", "mail", "general",
        "admin", "administrator", "webmaster", "postmaster", "noreply",
        "no-reply", "donotreply", "do-not-reply",
        # sales / marketing
        "sales", "vanzari", "marketing", "leads", "commercial",
        # support
        "support", "suport", "helpdesk", "service", "servicedeclienti",
        # billing / finance
        "billing", "facturare", "invoices", "facturi", "contabilitate",
        "accounting", "finance",
        # HR / recruiting
        "hr", "resurseumane", "jobs", "cariere", "careers", "recruiting",
        # legal / compliance
        "legal", "privacy", "gdpr", "dpo", "compliance",
        # press / media
        "press", "media", "presa",
        # RO-specific front-desk conventions
        "secretariat", "birou", "receptie", "reception", "front-desk",
        "frontdesk",
    }
)

# Local-parts that indicate placeholder, test, or otherwise non-actionable
# addresses rather than a real mailbox of any kind.
JUNK_LOCAL_PARTS = frozenset(
    {
        "test", "testing", "demo", "example", "sample", "foo", "bar",
        "asdf", "xxx", "placeholder", "user", "username", "dummy",
        "changeme", "n-a", "na", "none", "null", "undefined",
    }
)

# Domains that only ever appear in documentation, examples, or throwaway
# mailboxes and never represent a real prospecting target.
JUNK_DOMAINS = frozenset(
    {
        "example.com", "example.org", "example.net", "test.com",
        "mailinator.com", "yopmail.com", "guerrillamail.com",
        "10minutemail.com", "trashmail.com",
    }
)

# A nominal address usually separates a first and last name (or a first
# name and a first initial) with one of these characters.
NAME_SEPARATORS = r"[._-]"

# Matches patterns like "jane.doe", "j.doe", "jane_doe", "jane-doe",
# "jdoe" (no separator, handled separately below).
_NOMINAL_SEPARATED_RE = re.compile(
    rf"^[a-z]+{NAME_SEPARATORS}[a-z]+$"
)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def classify_email(address: str) -> EmailClassification:
    """Classify a single email address as ROLE, NOMINAL, JUNK, or UNKNOWN."""

    if not address or not isinstance(address, str):
        return EmailClassification(address or "", EmailKind.JUNK, "empty or non-string address")

    address = address.strip()

    if not _EMAIL_RE.match(address):
        return EmailClassification(address, EmailKind.JUNK, "does not match a basic email pattern")

    local_part, _, domain = address.rpartition("@")
    local_lower = local_part.lower()
    domain_lower = domain.lower()

    if domain_lower in JUNK_DOMAINS:
        return EmailClassification(address, EmailKind.JUNK, f"domain {domain_lower} is a known placeholder domain")

    # Strip a trailing +tag (jane.doe+newsletter@...) before matching, since
    # it does not change what kind of mailbox this is.
    local_no_tag = local_lower.split("+", 1)[0]

    if local_no_tag in JUNK_LOCAL_PARTS:
        return EmailClassification(address, EmailKind.JUNK, f"local part '{local_no_tag}' is a known placeholder")

    if local_no_tag in ROLE_LOCAL_PARTS:
        return EmailClassification(address, EmailKind.ROLE, f"local part '{local_no_tag}' matches a known role mailbox")

    # A role local-part can carry a department suffix or number, e.g.
    # "sales2", "office.uk", "support-eu". Check whether the part before
    # any separator or trailing digits is a known role word.
    stripped = re.sub(r"\d+$", "", local_no_tag)
    first_segment = re.split(NAME_SEPARATORS, stripped)[0]
    if first_segment in ROLE_LOCAL_PARTS:
        return EmailClassification(
            address, EmailKind.ROLE, f"local part '{local_no_tag}' looks like a role mailbox variant of '{first_segment}'"
        )

    if _NOMINAL_SEPARATED_RE.match(local_no_tag):
        return EmailClassification(
            address, EmailKind.NOMINAL, f"local part '{local_no_tag}' looks like firstname{NAME_SEPARATORS}lastname"
        )

    # Bare alphabetic local part with no separator and no digits, e.g.
    # "jdoe" or "janedoe": plausibly nominal (initial+surname, or
    # firstname+lastname run together), but genuinely ambiguous with a
    # short generic word. Treat as UNKNOWN rather than guessing either way.
    if local_no_tag.isalpha():
        return EmailClassification(
            address, EmailKind.UNKNOWN, f"local part '{local_no_tag}' has no separator; cannot confidently tell role from nominal"
        )

    return EmailClassification(address, EmailKind.UNKNOWN, "no rule matched; default to unknown, not a guess")


def classify_batch(addresses: list[str]) -> list[EmailClassification]:
    return [classify_email(a) for a in addresses]
