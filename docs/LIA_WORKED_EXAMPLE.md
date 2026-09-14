# Legitimate Interest Assessment: worked example (fictional)

> Educational reference material, not legal advice. See the disclaimer in the
> repository [README](../README.md#disclaimer). Every company, person, and
> figure below is invented for this example. This is a template filled in
> to show what a real answer looks like, not a certified determination for
> any actual processing activity.

This example uses "DataScope Analytics SRL", a fictional B2B
market-intelligence vendor, and its fictional prospect "Meridian
Industrial SRL". Neither company exists.

---

## 0. Metadata

- **Processing activity assessed:** Collecting and holding the company
  name, registered address, sector code, and the `office@` and
  `sales@` mailboxes of Romanian manufacturing SMEs, sourced from the
  national companies registry and each company's own public website, for
  the purpose of commercial prospecting by DataScope Analytics SRL's sales
  team.
- **Author:** M. Ionescu, Data Protection Lead, DataScope Analytics SRL (fictional)
- **Date:** 2026-03-01 (fictional)
- **Review date:** 2027-03-01, or sooner if the processing changes
- **Related records of processing:** ROPA entry "Prospecting database, manufacturing vertical" (fictional)

## 1. Purpose test

- **1.1 Purpose in one sentence.** Identify manufacturing SMEs that are
  plausible buyers of DataScope's market-intelligence subscription, and
  reach their commercial department to offer a product demonstration.
- **1.2 Whose interest is this?** Primarily DataScope's own commercial
  interest. There is a secondary benefit to the prospect (learning about a
  relevant product), but the assessment does not lean on that to justify
  the processing; it stands or falls on DataScope's interest and the
  balancing test below.
- **1.3 Specific and lawful?** Yes: the purpose is a defined activity
  (identify + contact a specific department, for a specific commercial
  offer), not an open-ended "grow the business." It is lawful: prospecting
  is a normal, legal commercial activity.
- **1.4 Real-world benefit.** Estimated addressable population: roughly 4,000
  manufacturing SMEs in the relevant registry segment (fictional figure).
  Expected outreach-to-meeting conversion, based on DataScope's past
  campaigns: approximately 2 percent (fictional figure). The benefit is
  concrete and measurable, not speculative.

## 2. Necessity test

- **2.1 Does the processing help achieve the purpose?** Yes: without a
  contact point, there is no channel to reach the prospect at all.
- **2.2 Less intrusive alternative?** Two alternatives were considered and
  rejected for stated reasons:
  - *Buying a pre-built marketing list from a third-party broker.* Rejected
    because DataScope cannot verify that broker's own legal basis and
    provenance, which would leave DataScope holding data it cannot account
    for; this repository's provenance requirement (see the main
    [README](../README.md)) exists specifically to avoid inheriting an
    unverifiable basis from someone else's process.
  - *Contacting only via the company's public contact form instead of
    storing an email address.* Rejected as impractical at the scale needed
    (4,000 companies), but retained as the preferred channel where a
    company's site only exposes a contact form and no direct address.
  - Conclusion: no equivalent, meaningfully-less-intrusive method is
    available at the scale required, given the safeguards adopted in
    section 3.7.
- **2.3 Minimal fields?** Fields collected: company name, registered
  address, sector code, `office@`/`sales@` mailbox, source URL, retrieval
  date, legal basis. Each maps directly to the purpose (identify + reach +
  account for the record). Fields explicitly **not** collected: named
  employee data beyond what a role mailbox implies, financial data beyond
  the public registry status, any behavioural or third-party-inferred
  data about individuals.

## 3. Balancing test

- **3.1 Nature of the data.** Ordinary business contact data. No
  special-category data, no financial account data, no data about
  individuals' private lives.
- **3.2 Reasonable expectations.** A company publishing an `office@` or
  `sales@` address on its own public website should reasonably expect
  other businesses to use that address for commercial contact; that is
  the address's evident purpose.
- **3.3 Source of the data.** Two sources only: the national companies
  registry (a public register maintained for exactly this kind of
  identification) and the company's own published website. Both are
  first-party or official sources; neither involves inference, brokered
  data, or aggregation beyond what the company itself published.
- **3.4 Role vs nominal address.** Both collected addresses are role
  mailboxes (`office@`, `sales@`), not named individuals'. This favours
  the processing significantly: no specific natural person's inbox,
  reading habits, or identity is being profiled.
- **3.5 Potential impact on the individual.** Realistic worst case: the
  department that reads the role mailbox receives one relevant commercial
  email. There is no natural person singled out, no repeated unwanted
  contact planned (see the retention and suppression safeguards below),
  and no data shared onward to third parties.
- **3.6 Power imbalance.** None identified. Meridian Industrial SRL is a
  business counterparty of comparable commercial standing, not a
  vulnerable individual or a dependent party.
- **3.7 Safeguards in place.**
  - Every record carries `source_url`, `retrieved_at`, and `legal_basis`,
    enforced at ingest by `gdpr_pipeline.ingest_gate` before it can enter
    the warehouse; see the main [README](../README.md).
  - An unsubscribe/objection link on every commercial email adds the
    address to `gdpr_pipeline.suppression`, checked at send time on every
    future campaign, not just at the time the list was built.
  - Contact fields carry a 12-month retention TTL by default (see
    [`RETENTION.md`](RETENTION.md)); stale contact data is not kept "in
    case."
  - Outbound frequency is capped (no more than one prospecting contact per
    quarter to the same address in this campaign).
  - Access to the underlying warehouse is restricted to the sales and data
    teams; no onward sale or sharing with third parties.
- **3.8 Conclusion.** The balance favours the processing for role
  addresses collected under these safeguards. This conclusion is
  specific to role/functional mailboxes; it does not extend automatically
  to named individuals' personal addresses, which would need their own,
  stricter pass through sections 3.2 to 3.7 (see
  [`LEGAL_BASIS.md`](LEGAL_BASIS.md) for why the two are treated
  differently, and [`../gdpr_pipeline/email_class.py`](../gdpr_pipeline/email_class.py)
  for how this repository tells them apart).

## 4. Outcome

- **Basis confirmed:** Legitimate interest, for role/functional business
  contact addresses collected from the national registry and the
  company's own published website, under the safeguards in 3.7.
- **Conditions attached:** No expansion to named-individual addresses
  without a separate LIA. No onward sharing with third parties without a
  separate assessment. Suppression and retention mechanisms must remain
  active; this approval does not hold if those safeguards are removed.
- **Mitigations required before go-live:** Ingest gate enforcing
  provenance (implemented), suppression list wired into the send pipeline
  (implemented), 12-month contact-field TTL configured (implemented).
- **Next review date:** 2027-03-01, or immediately if the purpose, the
  population, or the safeguards change.
- **Sign-off:** M. Ionescu, Data Protection Lead (fictional); reviewed by
  fictional legal counsel prior to go-live.

## 5. What this example is not

This worked example does not, on its own, license processing named
individuals' personal addresses, does not license sending unsolicited
marketing without checking the applicable ePrivacy rule for the
recipient's jurisdiction (see [`EPRIVACY_ROMANIA.md`](EPRIVACY_ROMANIA.md)),
and does not substitute for running this assessment against your own
actual facts.
