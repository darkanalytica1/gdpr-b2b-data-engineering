# Data subject rights inside a re-ingesting pipeline

> Educational reference material, not legal advice. See the disclaimer in the
> repository [README](../README.md#disclaimer).

Most write-ups of data subject rights describe the legal right and stop.
This document is about the specific engineering problem that shows up when
you try to actually honour those rights inside a pipeline that regularly
re-ingests data from external sources, which is exactly the shape of a
prospecting database built on official registers and public sites.

## The three rights that matter most for a prospecting pipeline

### Access (Article 15)

The data subject can ask what you hold about them and why. In this
architecture, that request is answerable directly from the record's
provenance (see [`gdpr_pipeline/provenance.py`](../gdpr_pipeline/provenance.py)):
which fact, from which source, retrieved when, under which legal basis. A
pipeline that cannot answer "since when, from where, under what basis"
without a manual investigation has effectively made this right expensive to
honour, which tends to mean it gets honoured badly under time pressure.

A practical access response for a prospecting record should include:
- Every field held about the person.
- The source and retrieval date for each field (its provenance).
- The legal basis relied on.
- Whether the address is on the suppression list, and since when.
- Retention: when the field is due to expire under the applicable TTL.

### Erasure (Article 17) and the zombie record problem

Erasure looks simple until you have a nightly job that re-ingests from the
same source register the person's data originally came from. Delete the
record today, and if nothing else changes, tomorrow's re-ingest of the same
public register brings the same fact straight back in. The person is
erased and un-erased on a 24-hour cycle. That is not compliance with an
erasure request; it is a very short retention period dressed up as one.

The fix implemented in this repository is the **tombstone pattern**, in
[`gdpr_pipeline/tombstone.py`](../gdpr_pipeline/tombstone.py):

1. Erasure deletes the record from the active warehouse.
2. Erasure also writes a tombstone: a persistent marker, independent of the
   warehouse tables that get rebuilt, keyed by a salted hash of the
   person's identifier (never the plaintext identifier itself, for the
   same reason the suppression list avoids storing plaintext).
3. Every re-ingest run checks incoming records against the tombstone
   store **before** they reach the ingest gate or the warehouse
   (`TombstoneStore.apply_to_incoming`), so a record that matches a
   tombstone never gets the chance to become a new "current" record.
4. A periodic sweep (`TombstoneStore.sweep`) catches anything that slipped
   in through a path that bypassed the pre-filter (a manual fix, a bulk
   restore), so the tombstone is a durable guarantee, not a single
   checkpoint that can be routed around.

One caveat worth stating plainly: a tombstone stops *your* pipeline from
re-displaying the fact. It does not, and cannot, erase the fact from the
original public register, which is usually outside your control and often
has its own separate legal basis for holding the record (e.g. a companies
registry maintained under company law). Erasure requests aimed at the
primary public source itself need to be directed to that source, not to a
downstream consumer of it; be honest with the data subject about what your
erasure can and cannot reach.

### Objection (Article 21)

For processing based on legitimate interest, an objection is not
automatically overridden; you must either stop the processing for that
individual or demonstrate compelling legitimate grounds that override
their interests, rights, and freedoms, or that the processing is needed to
establish, exercise, or defend legal claims. For direct marketing
specifically, an objection under Article 21(2) must be honoured
unconditionally: there is no override available for marketing once someone
has objected to it.

This repository models the marketing-specific case, the one with no
override, as the **suppression list**
([`gdpr_pipeline/suppression.py`](../gdpr_pipeline/suppression.py)):
additive-only, checked at send time on every future campaign
(`check_at_send`), never silently cleared by a fresh import. A general
objection to non-marketing processing under legitimate interest (the case
that does allow an override on compelling grounds) is a case-by-case
determination this repository does not attempt to automate; it needs a
documented, individual decision, referencing the relevant LIA.

## Why both patterns exist and are kept separate

Suppression answers "may we send this address anything." Tombstone answers
"does this record exist in our warehouse at all." They are related but not
interchangeable: you can suppress an address for marketing while still
lawfully holding the underlying company record (e.g. because a legal
obligation requires it), and you can erase a record entirely while having
no separate marketing relationship with it to suppress. Keeping them as two
independent stores, both hash-keyed and both additive-only, means each
right is honoured on its own terms instead of one mechanism being stretched
to (incompletely) cover both.

## Turning this into an operational process

Code enforces the mechanism; it does not run the process around it. A real
deployment still needs:
- An intake channel for rights requests (a monitored inbox, a form) with a
  defined response deadline (one month under GDPR, extendable in defined
  circumstances).
- Identity verification proportionate to the request, so erasure or access
  cannot be triggered by anyone claiming to be someone else.
- A logged record of every request and its resolution, itself subject to
  its own retention policy.
- Escalation for requests that are not the simple case (e.g. a request
  that would require removing data a legal obligation requires you to
  keep, which needs a documented, reasoned refusal rather than either
  silent non-compliance or automatic deletion).
