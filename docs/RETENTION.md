# Retention and minimisation

> Educational reference material, not legal advice. See the disclaimer in the
> repository [README](../README.md#disclaimer).

## The principle

GDPR Article 5(1)(c) (data minimisation) and 5(1)(e) (storage limitation)
together say: collect only what the purpose requires, and keep it only for
as long as the purpose requires it. Neither of those is a data-quantity
target to hit once at design time; both are ongoing constraints that a
pipeline needs to enforce continuously, because purposes and data both
change.

## "We might need it later" is not a purpose

This is the sentence to watch for in your own team's reasoning, because it
is almost never true in the way it is meant. A purpose is a specific,
current, statable reason: "to identify the commercial department to send
this quarter's product update." "We might need it later" describes no
current activity at all; it is a placeholder for a purpose that does not
yet exist, applied to data you already hold. If a future purpose
materialises, that is the moment to assess whether the existing data
(if still accurate) or freshly collected data (if not) should be
processed for it, with its own basis and its own reasoning, not a
retroactive justification for having kept everything indefinitely.

The practical test: if you cannot name the current purpose a field serves,
right now, in one sentence, the field should not still be sitting in the
warehouse.

## Field classes, not one retention period per record

A single retention period for an entire record is usually wrong, because
different fields on the same record serve different purposes and decay at
different rates. This repository's retention engine
([`gdpr_pipeline/retention.py`](../gdpr_pipeline/retention.py)) assigns
every field to one of four classes, each with its own default TTL:

| Field class | Example fields | Default TTL | Why |
|---|---|---|---|
| Identity | company name, registration number | 730 days | Slow-changing; the purpose (know which entity this is) stays valid longest, but even identity facts should be re-verified periodically against the source. |
| Contact | email, phone | 365 days | People change roles, mailboxes get reorganised; a contact field that has not been re-verified in a year is a plausible source of a wrong-number or wrong-person contact, which is itself a fairness and accuracy problem (Article 5(1)(d)), not just a compliance one. |
| Behavioural | site visits, email opens, campaign responses | 180 days | Short natural shelf life; old behavioural signal actively misleads a scoring or prioritisation process rather than merely being unhelpful. |
| Derived | a computed score, a segment label | 90 days | Cheapest to recompute from source data, so the shortest defensible retention: there is rarely a purpose served by keeping a stale derived value once its inputs have moved on. |

These defaults are a documented starting point, not a legal requirement;
tune them for your own purposes and be ready to justify the numbers you
land on, the same way you would justify a legal basis.

## What "expire" means in practice

The retention engine marks a field for expiry once it exceeds its class's
TTL, measured from when that specific field was last verified or updated,
not from when the record was first created. What happens on expiry is a
policy choice with real trade-offs:

- **Drop the field, keep the rest of the record.** Appropriate for a
  contact field that has simply gone stale: you may still have a
  legitimate reason to know the company exists, without a reason to keep
  an unverified, ageing phone number attached to it.
- **Drop the whole record.** Appropriate when the expired field was the
  entire reason the record existed (e.g. a behavioural signal record
  whose only purpose was short-term scoring).
- **Re-verify instead of dropping.** Often the right answer for identity
  and contact fields: treat expiry as a trigger to re-fetch from the
  source with a fresh `retrieved_at`, rather than an automatic deletion,
  provided the underlying purpose for holding the fact at all is still
  active.

This repository's `RetentionEngine.apply()` implements the simplest of
these (drop the expired field, keep the record) because it is the safest
default to demonstrate; a real deployment should route expiry events to
whichever of the three responses fits the field and the purpose.

## Minimisation is a collection-time decision, not just a deletion-time one

Retention TTLs clean up what should not have been kept this long.
Minimisation is upstream of that: deciding, at ingest, which fields to
collect at all. The ingest gate
([`gdpr_pipeline/ingest_gate.py`](../gdpr_pipeline/ingest_gate.py)) is the
natural place to enforce this in code (reject or strip fields outside an
allow-list for the declared purpose), even though the version in this
repository focuses on provenance and legal-basis checks; extending it with
a purpose-scoped field allow-list is a natural next step for a production
system and is called out explicitly here so it is not mistaken for
something already solved.
