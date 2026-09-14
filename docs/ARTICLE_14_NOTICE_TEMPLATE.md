# Article 14 privacy notice template: prospecting database

> Educational reference material, not legal advice. See the disclaimer in the
> repository [README](../README.md#disclaimer). This is a structural
> template, not a ready-to-publish legal document; have your own version
> reviewed by a qualified lawyer or DPO before publishing it.

## Why Article 14, specifically

Article 13 governs the notice you give when you collect data directly
from the data subject (a signup form, for instance). Article 14 governs
the notice you must give when you obtain personal data about someone from
somewhere else, which is exactly how a prospecting database built from
public registers and company websites acquires most of its data: the
person never filled in a form for you.

Article 14 requires you to provide the notice within a reasonable period,
generally at the latest within one month of obtaining the data, and it
requires two extra pieces of information beyond what Article 13 asks for:
**the categories of personal data concerned**, and **the source the data
came from** (including whether it came from a publicly accessible
source). There is a limited exemption (Article 14(5)) when providing the
notice would be impossible or involve disproportionate effort, most
relevant at genuine scale, but relying on it requires its own documented
justification and appropriate safeguards; it is not a general opt-out from
transparency.

## Template

### 1. Who is processing your data (the controller)

- Legal name and registration details of the controller.
- Contact details for privacy enquiries.
- Contact details for the Data Protection Officer, if one is appointed.

### 2. What data we hold about you

- The specific categories collected: e.g. "your name and job title as
  published on [Company]'s website; a business email address in the form
  `role@company.example`; the company's registered address and sector."
- Explicitly state whether the address held is a role/functional mailbox
  or believed to be a personal one, since this affects the rest of the
  notice's tone and the practical risk being described honestly to the
  reader.

### 3. Where we got it (the Article 14 source requirement)

- Name the source category plainly: "the [national companies registry]
  public entity record", "your employer's own published website", "a
  public tender notice published by [contracting authority]."
- State clearly that the source is publicly accessible, if it is: this is
  a specific, named requirement of Article 14(2)(f), not an optional
  flourish.
- Do not describe the source vaguely ("various public sources") if you
  can name it specifically; provenance tracking in the underlying system
  (see [`gdpr_pipeline/provenance.py`](../gdpr_pipeline/provenance.py))
  exists exactly so this section can be filled in precisely rather than
  approximately.

### 4. Why we are allowed to do this (legal basis and purpose)

- State the purpose in the same plain, specific terms used in the
  underlying Legitimate Interest Assessment: e.g. "to identify and contact
  the commercial department of companies in [sector] about [product]."
- State the legal basis: "legitimate interest, assessed and documented
  internally" (or the correct basis if different for this data).
- Offer, or link to, a summary of the balancing test's outcome; you are
  not obliged to publish the full LIA, but the reasoning should be
  available on request, and a summary here supports transparency in
  substance, not merely in form.

### 5. Who else sees it

- State plainly whether data is shared with any third party, and if so,
  which categories of recipient and for what purpose. If there is no
  sharing, say so explicitly; do not leave this section ambiguous.

### 6. How long we keep it

- State the retention approach in terms a non-specialist can follow: e.g.
  "contact details are retained for up to 12 months from when we last
  verified them, after which they are either re-verified against the
  original source or removed." Reference the retention policy
  ([`RETENTION.md`](RETENTION.md)) for the underlying reasoning if you
  want to publish more detail.

### 7. Your rights

- List each right in plain language: access, rectification, erasure,
  restriction, objection (with explicit emphasis that an objection to
  direct marketing is always honoured, no override applies), and the
  right to lodge a complaint with the relevant supervisory authority.
- Give a concrete way to exercise each right (an email address, a form),
  not just a citation to the regulation.
- If erasure is subject to the practical caveat described in
  [`DATA_SUBJECT_RIGHTS.md`](DATA_SUBJECT_RIGHTS.md) (a downstream copy
  cannot erase the original public register), say so plainly rather than
  making a promise the architecture cannot keep.

### 8. How to stop receiving marketing

- A specific, working mechanism, not a generic "contact us to opt out."
  If this maps to the suppression list in
  [`gdpr_pipeline/suppression.py`](../gdpr_pipeline/suppression.py),
  state the practical guarantee in terms the reader cares about: "once you
  opt out, we will not include this address in future campaigns, and this
  choice persists even if we later refresh our records from the same
  public sources."

## Delivery mechanics worth deciding explicitly

- **Timing.** Default to sending the notice at or near first contact
  (which also satisfies the "reasonable period" requirement and is
  simply good practice), rather than waiting up to the one-month limit.
- **Channel.** A first email to a role/functional address can reasonably
  include the notice inline or linked; document the reasoning if you rely
  on the disproportionate-effort exemption instead, since that exemption
  is the exception, not the default path.
- **Language.** Match the language of the data subject's own jurisdiction
  or business context where practical; a notice nobody can read is not
  effective transparency.
