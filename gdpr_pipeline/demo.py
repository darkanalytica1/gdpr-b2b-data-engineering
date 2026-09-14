"""
demo: an end-to-end, runnable story that exercises every module.

Run it with:

    python -m gdpr_pipeline.demo

Everything in this script is synthetic. "Acme Distribution SRL",
"Northgate Traders SRL", and every name, email, and phone number below
are invented for this demo; none of it refers to a real company or
person. No network calls are made and nothing here reaches outside a
temporary directory created for the run.

The story, in order:

  1. A batch of synthetic candidate records arrives, as if from a
     nightly harvester reading a public companies register and a public
     tenders portal. Some records carry good provenance, some do not.
  2. The ingest gate accepts the good records and rejects the bad ones,
     with structured reasons for each rejection.
  3. The email classifier sorts the accepted contacts into role,
     nominal, and junk buckets.
  4. A data subject exercises their right to object to marketing contact
     for one address; it goes on the suppression list.
  5. A different data subject exercises their right to erasure; a
     tombstone is created and their record is removed from the
     warehouse.
  6. The nightly harvester runs again and, unchanged, tries to
     re-introduce the exact same two records. The demo proves both the
     suppression and the tombstone hold: the suppressed address is
     still refused by the ingest gate, and the erased record is blocked
     before it reaches the warehouse at all.
  7. The retention engine is run over the surviving warehouse and shows
     which fields would expire under the example TTL policy.
"""

from __future__ import annotations

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .email_class import classify_email
from .ingest_gate import IngestGate
from .provenance import LegalBasis, Provenance
from .retention import FieldClass, RetentionEngine
from .suppression import SuppressionStore
from .tombstone import TombstoneStore

SEPARATOR = "-" * 72


def _p(title: str) -> None:
    print()
    print(SEPARATOR)
    print(title)
    print(SEPARATOR)


def build_synthetic_batch(now: datetime) -> list[dict]:
    """A synthetic first-run batch. Every fact here is invented."""
    return [
        {
            "company_name": "Acme Distribution SRL",
            "email": "office@acme-distribution.example",
            "phone": "+40 21 000 0001",
            "provenance": Provenance(
                source_url="https://registry.example.gov/entity/RO0000001",
                retrieved_at=now - timedelta(days=3),
                legal_basis=LegalBasis.LEGITIMATE_INTEREST,
                source_name="synthetic national companies registry",
            ),
        },
        {
            "company_name": "Northgate Traders SRL",
            "email": "jane.doe@northgate-traders.example",
            "phone": "+40 21 000 0002",
            "provenance": Provenance(
                source_url="https://tenders.example.gov/notice/2026-000123",
                retrieved_at=now - timedelta(days=1),
                legal_basis=LegalBasis.LEGITIMATE_INTEREST,
                source_name="synthetic public tenders portal",
            ),
        },
        {
            # No provenance at all: this must be rejected.
            "company_name": "Shadowfax Logistics SRL",
            "email": "contact@shadowfax-logistics.example",
            "provenance": None,
        },
        {
            # Provenance present but source_url malformed: rejected.
            "company_name": "Ferrous Metalworks SRL",
            "email": "sales@ferrous-metalworks.example",
            "provenance": Provenance(
                source_url="not-a-url",
                retrieved_at=now - timedelta(days=1),
                legal_basis=LegalBasis.LEGITIMATE_INTEREST,
            ),
        },
        {
            # No contact field at all: rejected regardless of provenance.
            "company_name": "Bare Facts SRL",
            "provenance": Provenance(
                source_url="https://registry.example.gov/entity/RO0000099",
                retrieved_at=now - timedelta(days=2),
                legal_basis=LegalBasis.LEGITIMATE_INTEREST,
            ),
        },
    ]


def run() -> None:
    now = datetime.now(timezone.utc)
    workdir = Path(tempfile.mkdtemp(prefix="gdpr_pipeline_demo_"))
    suppression_path = workdir / "suppression_store.json"
    tombstone_path = workdir / "tombstone_store.json"
    salt = "demo-salt-not-a-real-secret"  # a real deployment loads this from a secret store

    _p("STEP 1: synthetic candidate batch arrives (nightly harvester, run #1)")
    batch = build_synthetic_batch(now)
    for r in batch:
        print(f"  candidate: {r['company_name']!r} <{r.get('email', 'no email')}>")

    _p("STEP 2: ingest gate evaluates the batch")
    suppression_store = SuppressionStore(salt=salt, path=suppression_path)
    gate = IngestGate(suppression_store=suppression_store)
    accepted, rejected = gate.evaluate_batch(batch)

    print(f"  accepted: {len(accepted)}")
    for r in accepted:
        print(f"    OK   {r.record['company_name']!r}")
    print(f"  rejected: {len(rejected)}")
    for r in rejected:
        print(f"    FAIL {r.record['company_name']!r}: {', '.join(r.reason_codes)}")

    warehouse: dict[str, dict] = {r.record["email"]: dict(r.record) for r in accepted if r.record.get("email")}

    _p("STEP 3: classify accepted contacts as role / nominal / junk")
    for email in warehouse:
        classification = classify_email(email)
        print(f"  {email:45s} -> {classification.kind.value:8s} ({classification.reason})")

    _p("STEP 4: a data subject objects to marketing contact (suppression)")
    suppressed_address = "office@acme-distribution.example"
    suppression_store.add(suppressed_address, reason="data subject objected to marketing contact (Art. 21)")
    print(f"  suppressed: {suppressed_address}")
    print(f"  suppression store now holds {len(suppression_store)} hashed entr{'y' if len(suppression_store) == 1 else 'ies'}")

    _p("STEP 5: a different data subject exercises the right to erasure")
    erased_address = "jane.doe@northgate-traders.example"
    tombstone_store = TombstoneStore(salt=salt, path=tombstone_path)
    tombstone_store.erase(erased_address, reason="data subject requested erasure (Art. 17)")
    if erased_address in warehouse:
        del warehouse[erased_address]
    print(f"  erased and removed from warehouse: {erased_address}")
    print(f"  tombstone store now holds {len(tombstone_store)} hashed entr{'y' if len(tombstone_store) == 1 else 'ies'}")
    print(f"  warehouse now holds {len(warehouse)} record(s)")

    _p("STEP 6: nightly harvester runs again (run #2), same source facts, unchanged")
    # Fresh SuppressionStore / TombstoneStore instances loaded from disk,
    # to prove persistence survives a process restart, not just an
    # in-memory object staying alive.
    suppression_store_2 = SuppressionStore(salt=salt, path=suppression_path)
    tombstone_store_2 = TombstoneStore(salt=salt, path=tombstone_path)

    batch_2 = build_synthetic_batch(datetime.now(timezone.utc))
    kept, blocked_by_tombstone = tombstone_store_2.apply_to_incoming(batch_2, key_field="email")
    print(f"  tombstone pre-filter: kept {len(kept)}, blocked {len(blocked_by_tombstone)}")
    for r in blocked_by_tombstone:
        print(f"    BLOCKED BY TOMBSTONE  {r['company_name']!r} <{r.get('email')}>")

    gate_2 = IngestGate(suppression_store=suppression_store_2)
    accepted_2, rejected_2 = gate_2.evaluate_batch(kept)
    print(f"  ingest gate on run #2: accepted {len(accepted_2)}, rejected {len(rejected_2)}")
    for r in rejected_2:
        print(f"    FAIL {r.record['company_name']!r}: {', '.join(r.reason_codes)}")

    still_suppressed = not suppression_store_2.check_at_send(suppressed_address)
    still_tombstoned = tombstone_store_2.is_tombstoned(erased_address)
    print(f"  suppression held across restart: {still_suppressed}")
    print(f"  tombstone held across restart:    {still_tombstoned}")
    assert still_suppressed, "suppression did not survive re-ingest, this is a bug"
    assert still_tombstoned, "tombstone did not survive re-ingest, this is a bug"

    _p("STEP 7: retention engine over the surviving warehouse")
    field_map = {
        "company_name": FieldClass.IDENTITY,
        "email": FieldClass.CONTACT,
        "phone": FieldClass.CONTACT,
    }
    engine = RetentionEngine(field_map=field_map, ttl_overrides={FieldClass.CONTACT: 30})
    remaining_email = "office@acme-distribution.example"
    remaining_record = {"company_name": "Acme Distribution SRL", "email": remaining_email, "phone": "+40 21 000 0001"}
    field_timestamps = {
        "company_name": now - timedelta(days=10),
        "email": now - timedelta(days=45),  # older than the 30-day CONTACT override
        "phone": now - timedelta(days=10),
    }
    scrubbed, decisions = engine.apply(remaining_record, field_timestamps, now=now)
    for d in decisions:
        print(f"  {d.field:15s} class={d.field_class.value:10s} age_days={d.age_days:6.1f} ttl_days={d.ttl_days} -> {d.action}")
    print(f"  scrubbed record: {scrubbed}")

    _p("DONE")
    print(f"  demo artifacts written under: {workdir}")
    print("  (this directory is temporary and safe to delete)")


if __name__ == "__main__":
    run()
