# Legitimate Interest Assessment (LIA): blank template

> Educational reference material, not legal advice. See the disclaimer in the
> repository [README](../README.md#disclaimer). This template is a starting
> structure, not a certification; adapt it to your facts and have it
> reviewed by your DPO or legal counsel before relying on it.

This is the single most valuable artifact in this repository. A
Legitimate Interest Assessment is the documented reasoning that turns
"we think legitimate interest applies" into an auditable decision. Most
organisations that claim legitimate interest as their basis have never
written one down. Writing it down, honestly, including the parts that
cut against you, is the actual compliance work; the label "legitimate
interest" is not.

Fill in every section. If a section feels awkward to answer honestly,
that discomfort is signal, not an obstacle to route around.

See [`LIA_WORKED_EXAMPLE.md`](LIA_WORKED_EXAMPLE.md) for a completed
version of this same template.

---

## 0. Metadata

- **Processing activity assessed:**
- **Author:**
- **Date:**
- **Review date (recommended: 12 months, or sooner if the processing changes):**
- **Related records of processing (Article 30):**

## 1. Purpose test: what are you trying to achieve, and why does it matter?

- **1.1 Describe the purpose in one plain sentence.** Not "marketing", but
  the specific activity: e.g. "identify and contact the commercial
  department of companies in sector X to offer product Y."
- **1.2 Whose interest is this? Yours, a third party's, or both?**
- **1.3 Is the purpose specific and lawful?** Vague purposes ("grow the
  business") do not pass a balancing test because they cannot be weighed
  against anything concrete. Narrow the purpose until it is falsifiable:
  a reader should be able to say "this processing does or does not serve
  that purpose."
- **1.4 What is the real-world benefit, and to whom?** Quantify if you can
  (expected reach, expected conversion, cost avoided).

## 2. Necessity test: is this processing actually required for the purpose?

- **2.1 Does the processing actually help achieve the purpose?** Not "would
  it help", but does the causal link hold.
- **2.2 Is there a less intrusive way to achieve the same purpose?**
  Consider: fewer fields, a shorter retention period, contacting a role
  address instead of a named individual, or not processing this data at
  all. If a less intrusive method exists and is reasonably practical, use
  it instead; legitimate interest fails if a genuinely equivalent, less
  intrusive alternative was available and ignored.
- **2.3 Are you collecting only what is needed, and no more?** List every
  field. For each, state why the purpose requires it. A field with no
  answer here should be dropped, not retained "in case."

## 3. Balancing test: do your interests override the individual's rights?

This is the test that actually decides the outcome. Work through each
sub-question specifically; do not skip to a conclusion.

- **3.1 Nature of the data.** Is it business contact data (lower
  sensitivity) or does it touch anything special-category, financial, or
  otherwise sensitive (higher sensitivity, generally not appropriate for
  this basis)?
- **3.2 Reasonable expectations.** Would the data subject reasonably expect
  a business to hold this fact about them, given their public role? A
  company director's name being known to other businesses is generally
  expected; a home address or personal mobile number generally is not.
- **3.3 Source of the data.** Was it published by the person or their
  employer (a company website, an official register), or did it come from
  somewhere the person would not expect (a data broker, a breach,
  aggregation across many small signals into a profile they never
  anticipated)?
- **3.4 Role vs nominal address.** Is the contact point a role/functional
  mailbox or a named individual's address? See
  [`../gdpr_pipeline/email_class.py`](../gdpr_pipeline/email_class.py). A
  role address shifts the balance meaningfully in your favour; a nominal
  address does not, on its own, shift it against you, but it removes that
  point in your favour and raises the bar for the rest of the test.
- **3.5 Potential impact on the individual.** What is the realistic worst
  case for the person if this processing goes ahead: one commercial email
  a quarter, or a persistent, hard-to-escape contact pattern? Be specific
  and honest, not reassuring.
- **3.6 Power imbalance.** Is there a dependency or imbalance between you
  and the data subject (e.g. they are a job applicant, a vulnerable
  individual, or otherwise not in a position to push back)? A prospecting
  contact at another company is usually not in this position, but state
  why, do not assume it.
- **3.7 Safeguards you are putting in place.** List them concretely:
  provenance tracking, an accessible objection/opt-out mechanism, a
  suppression list that is actually checked at send time (see
  [`../gdpr_pipeline/suppression.py`](../gdpr_pipeline/suppression.py)),
  retention limits, restricted access within your organisation.
- **3.8 Conclusion.** Does the balance favour the processing, once every
  factor above is weighed together? Say so explicitly, and say what would
  change the answer (e.g. "this holds for a role address; the answer for a
  nominal address is closer, and depends on safeguard 3.7 items X and Y
  being genuinely in place").

## 4. Outcome

- **Basis confirmed:** legitimate interest / other basis needed / do not process
- **Conditions attached to this approval:**
- **Mitigations required before go-live:**
- **Next review date:**
- **Sign-off:**

## 5. What invalidates this assessment

An LIA is not a one-time document. Re-run it, or at minimum re-check it,
when any of the following change:

- The purpose changes (e.g. from "prospecting" to "reselling the list to a
  third party": a materially different purpose needs its own assessment).
- The data collected expands (new fields, especially anything moving from
  role-level to individual-level detail).
- The population changes in a way that shifts the balance (e.g. from
  company directors to all employees, or into a jurisdiction with a
  materially different marketing law).
- A data subject objects. An objection under Article 21 does not
  automatically end the processing for everyone, but it must be evaluated
  for that individual and, if you cannot demonstrate compelling
  legitimate grounds that override their objection, honoured.
