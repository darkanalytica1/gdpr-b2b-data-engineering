# Legal basis for B2B prospecting data

> Educational reference material, not legal advice. See the disclaimer in the
> repository [README](../README.md#disclaimer). Verify against your own
> facts, your DPO, and a qualified lawyer before relying on any of this.

## The question this document answers

A prospecting database holds facts about companies and, unavoidably, about
the people who work at them: a director's name, a sales inbox address, a
phone number for the front desk. GDPR applies the moment any of that
identifies a natural person, even when the context is entirely commercial
and the person is acting in a professional capacity, not a private one.

So: on what legal basis can a business lawfully hold and process that data?

## The six bases, and which ones are realistic here

GDPR Article 6(1) lists six legal bases. In a B2B prospecting context, most
of them do not apply:

| Basis | Typical use | Realistic for B2B prospecting? |
|---|---|---|
| (a) Consent | The data subject affirmatively agreed | Rarely, at collection time. Relevant later for marketing (see below). |
| (b) Contract | Necessary to perform a contract with the data subject | No: the data subject (an employee) is not your counterparty; their employer is. |
| (c) Legal obligation | A law requires the processing | Occasionally, e.g. AML/KYC checks, but not the general case. |
| (d) Vital interests | Life-or-death situations | No. Never plausibly the basis for prospecting data. |
| (e) Public task | Performing an official public function | No, unless you are a public body. |
| (f) Legitimate interests | A balanced interest that does not override the data subject's rights | **Yes: this is the realistic basis for most B2B contact data.** |

## Why legitimate interest, and what it actually requires

Recital 47 of the GDPR explicitly names direct marketing as a potential
legitimate interest, and processing personal data about a person acting in
a professional capacity, for a purpose that also serves that business's own
commercial interest (being findable and contactable by other businesses),
sits squarely in the kind of processing legitimate interest was designed to
cover.

But "legitimate interest" is not a rubber stamp. It requires you to actually
do the work: a documented Legitimate Interest Assessment (LIA), not a
one-line note in a privacy policy claiming the basis. This repository ships
a full LIA template and a worked example precisely because this is the step
most teams skip, and skipping it is the difference between "we assessed
this and can show our reasoning" and "we assumed this was fine."

See:
- [`LIA_TEMPLATE.md`](LIA_TEMPLATE.md): a blank, reusable LIA structure.
- [`LIA_WORKED_EXAMPLE.md`](LIA_WORKED_EXAMPLE.md): the same template, filled
  in for a fictional company, showing what a real answer looks like.

## The basis for holding data is not the basis for contacting someone

This is the single most common confusion in this space, so it gets its own
section.

**Holding** a business contact record under legitimate interest is a
different question from **using** that record to send an unsolicited
marketing email or make an unsolicited marketing call. The second question
is governed by a separate body of law: national implementations of the
ePrivacy Directive, layered on top of GDPR, and in several member states
those national rules extend some protections to legal persons, not only
natural persons. That means a cold email to `office@company.example` can be
GDPR-compliant to hold as a record and still be unlawful to send, depending
on the jurisdiction and the recipient's status.

This repository works through Romania as a concrete example in
[`EPRIVACY_ROMANIA.md`](EPRIVACY_ROMANIA.md). The mechanism generalises, the
specific rules do not: every member state has its own transposition of the
ePrivacy Directive, and you must check the rule for each jurisdiction you
operate in rather than assuming Romania's answer travels.

## A practical decision path

1. Are you holding a fact about a company (registration number, address,
   sector)? This is likely not personal data at all; Article 6 does not
   apply to data that does not identify a natural person.
2. Are you holding a fact that identifies a person (a name, a personal
   email, a direct phone line)? Run an LIA. Document it before you rely on
   it, not after a regulator asks.
3. Is the address a role/functional mailbox (`sales@`, `office@`) rather
   than a named person? The privacy expectation and the practical risk are
   lower, but the LIA and the provenance requirement still apply; see
   [`../gdpr_pipeline/email_class.py`](../gdpr_pipeline/email_class.py) for
   how this repository tells the two apart programmatically.
4. Do you intend to send unsolicited marketing to this contact, by email,
   SMS, or automated call? Stop and check the ePrivacy rule for that
   recipient's jurisdiction. Holding the record and marketing to it are
   governed by different rules, and the marketing rule is usually stricter.
5. Whatever basis you land on, attach it to the record at ingest time, as
   part of its provenance, so the answer to "why do we have this, and under
   what basis" is a lookup, not an investigation. See the main
   [README](../README.md) for why provenance is the architectural spine of
   this repository.
