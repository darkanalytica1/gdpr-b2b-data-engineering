"""
gdpr_pipeline: reference implementations of GDPR compliance patterns for a
B2B prospecting / market-intelligence data pipeline.

This package is educational reference material, not legal advice. It ships
with synthetic data only. See the repository README and docs/ for the
compliance reasoning behind each module.

Modules:
    provenance   Provenance dataclass and validation (source_url, retrieved_at, legal_basis).
    ingest_gate  Rejects records without valid provenance or legal basis.
    email_class  Role vs nominal email classifier, plus junk detection.
    suppression  Hashed suppression store, checked at send time, survives re-ingest.
    tombstone    Erasure records that survive nightly re-ingest from source.
    retention    Field-class TTL engine for minimisation.
    demo         End-to-end runnable story that exercises every module.
"""

__version__ = "0.1.0"
