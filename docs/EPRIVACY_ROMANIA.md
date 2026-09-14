# ePrivacy and electronic marketing: Romania as a worked example

> Educational reference material, not legal advice. See the disclaimer in the
> repository [README](../README.md#disclaimer). Electronic marketing law
> varies by member state and changes over time; verify the current rule in
> every jurisdiction you actually operate in, do not assume this document
> stays current or that another country's rule matches Romania's.

## Why this needs its own document

GDPR governs whether you may hold and process personal data. It does not,
by itself, govern whether you may send someone an unsolicited marketing
email or place an unsolicited marketing call. That second question sits in
a separate, older body of EU law: the ePrivacy Directive (2002/58/EC,
commonly called "the ePrivacy Directive," predating GDPR and not yet
replaced by the long-discussed ePrivacy Regulation), implemented separately
by each member state into national law.

The practical consequence that trips up B2B teams: a contact record can be
entirely lawful to hold under GDPR legitimate interest, and the act of
emailing that contact without the right marketing status can still be
unlawful under national ePrivacy-derived law. These are two different
gates, and passing one does not mean you have passed the other.

## The Romanian implementation

Romania implements the ePrivacy Directive's electronic-marketing rules
primarily through two laws that a compliance-minded engineering team
should know by name:

- **Legea nr. 506/2004** on the processing of personal data and the
  protection of privacy in the electronic communications sector (the
  Romanian ePrivacy transposition).
- **Legea nr. 365/2002** on electronic commerce, which also addresses
  unsolicited commercial communications ("spam") sent by electronic means.

Romania's transposition, notably, has historically extended some of the
unsolicited-communication protections beyond natural persons to legal
persons in specific respects, which is not universal across the EU: some
member states restrict these ePrivacy-derived marketing protections to
natural persons only. This is precisely why the answer for one member
state does not automatically travel to another, and why "B2B, so ePrivacy
does not apply" is not a safe assumption anywhere without checking the
specific national rule.

## Consent, soft opt-in, and the direction from CJEU case law

The general rule under this framework is that unsolicited electronic
marketing communications require the recipient's prior consent (an
"opt-in" model), not merely an opportunity to opt out after the fact.

There is a recognised "soft opt-in" exception in EU law and in national
implementations for existing customer relationships: broadly, where a
business obtained a contact's electronic address in the context of a sale
or negotiation of a sale, it may market similar products or services to
that same contact without fresh consent, provided the contact was clearly
and distinctly given an opportunity to object, free of charge and easily,
both when the address was collected and with every subsequent
communication.

CJEU case law (the Court has addressed the scope and interpretation of
consent and the soft opt-in mechanism in the electronic-communications
context, including in the *Inteligo* line of reasoning referenced in this
space) has generally reinforced that consent-style mechanisms must be
specific, informed, and genuinely optional, and that the soft opt-in is a
narrow exception tied to an existing relationship, not a general licence
for B2B marketing. Treat any specific case citation as something to verify
against the current text and your own facts rather than as a settled
shortcut; case law in this area continues to develop.

## The practical consequence for a prospecting pipeline

Because the marketing-channel rules and the "may we hold this data" rules
are separate, the practical, defensible posture looks like this:

| Channel | Typical rule of thumb | Caveat |
|---|---|---|
| Cold, unsolicited marketing email | Not automatically safe in B2B; treat as requiring consent or a genuine soft opt-in basis, verified per jurisdiction | The riskiest channel to assume is fine by default |
| Cold, unsolicited automated call (robocall/auto-dialler) | Generally treated like electronic marketing; same consent-style constraints | Live human calls are usually treated differently from automated ones; verify locally |
| Cold postal mail | Generally outside ePrivacy's scope (ePrivacy targets electronic communications) | GDPR still applies to any personal data used to address the mail |
| Live telephone contact by a human | Often subject to different, sometimes lighter, national rules than automated electronic marketing, though do-not-call registers and general fairness/transparency obligations still apply | Verify the local telemarketing rule; do not assume "phone equals safe" |
| Inbound contact / soft opt-in from an existing relationship | The narrow exception described above, when its specific conditions are genuinely met | Do not stretch "existing relationship" to cover a contact you have never actually transacted with |

The one-line takeaway: **do not treat "it is just B2B" as a blanket
exemption from electronic-marketing consent rules.** The safer default for
a prospecting pipeline that wants to stay clearly inside the law is to
architect around genuine opt-in and soft opt-in paths (an inbound signup,
a real prior transaction, a clear and honoured objection mechanism) rather
than defaulting to unsolicited cold email as the primary outbound channel,
and to make that decision jurisdiction by jurisdiction.

## What this means for the code in this repository

- [`gdpr_pipeline/provenance.py`](../gdpr_pipeline/provenance.py) tracks the
  legal basis for **holding** a record (GDPR Article 6). It does not, on
  its own, tell you whether a specific marketing channel is currently
  authorised for that contact; a real deployment needs a separate,
  explicit marketing-consent/soft-opt-in status field, checked before any
  send, in addition to the suppression check.
- [`gdpr_pipeline/suppression.py`](../gdpr_pipeline/suppression.py) models
  the "must never contact again" side of this (an objection or a hard
  opt-out). It is necessary but not sufficient: the absence of a
  suppression entry is not the same as the presence of a valid marketing
  basis to contact that address in the first place.

## Verify before you rely on this

This document describes the general shape of a well-known area of EU and
Romanian law as background for engineering decisions. It is not a
substitute for reading the current text of Legea 506/2004 and Legea
365/2002, current guidance from the Romanian data protection authority
(ANSPDCP), and current CJEU jurisprudence, nor for asking a qualified
lawyer about your specific campaign, channel, and contact population
before you launch it.
