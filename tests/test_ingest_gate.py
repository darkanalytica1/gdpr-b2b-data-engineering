from datetime import datetime, timedelta, timezone

import pytest

from gdpr_pipeline.ingest_gate import IngestGate
from gdpr_pipeline.provenance import LegalBasis, Provenance
from gdpr_pipeline.suppression import SuppressionStore


def make_good_provenance(days_ago: int = 1) -> Provenance:
    return Provenance(
        source_url="https://registry.example.gov/entity/RO1234567",
        retrieved_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        legal_basis=LegalBasis.LEGITIMATE_INTEREST,
        source_name="synthetic registry",
    )


def test_accepts_a_well_formed_record():
    gate = IngestGate()
    record = {
        "company_name": "Synthetic Example SRL",
        "email": "office@synthetic-example.test",
        "provenance": make_good_provenance(),
    }
    result = gate.evaluate(record)
    assert result.accepted is True
    assert result.errors == []


def test_rejects_record_with_no_provenance():
    gate = IngestGate()
    record = {
        "company_name": "No Provenance SRL",
        "email": "office@no-provenance.test",
        "provenance": None,
    }
    result = gate.evaluate(record)
    assert result.accepted is False
    assert "MISSING_PROVENANCE" in result.reason_codes


def test_rejects_record_missing_provenance_key_entirely():
    gate = IngestGate()
    record = {"company_name": "No Key SRL", "email": "office@no-key.test"}
    result = gate.evaluate(record)
    assert result.accepted is False
    assert "MISSING_PROVENANCE" in result.reason_codes


def test_rejects_malformed_source_url():
    gate = IngestGate()
    record = {
        "company_name": "Bad URL SRL",
        "email": "office@bad-url.test",
        "provenance": Provenance(
            source_url="not-a-url-at-all",
            retrieved_at=datetime.now(timezone.utc),
            legal_basis=LegalBasis.LEGITIMATE_INTEREST,
        ),
    }
    result = gate.evaluate(record)
    assert result.accepted is False
    assert "MALFORMED_SOURCE_URL" in result.reason_codes


def test_rejects_future_retrieved_at():
    gate = IngestGate()
    record = {
        "company_name": "Time Traveller SRL",
        "email": "office@time-traveller.test",
        "provenance": Provenance(
            source_url="https://registry.example.gov/entity/RO0000002",
            retrieved_at=datetime.now(timezone.utc) + timedelta(days=1),
            legal_basis=LegalBasis.LEGITIMATE_INTEREST,
        ),
    }
    result = gate.evaluate(record)
    assert result.accepted is False
    assert "FUTURE_RETRIEVED_AT" in result.reason_codes


def test_rejects_naive_datetime_retrieved_at():
    gate = IngestGate()
    record = {
        "company_name": "Naive Time SRL",
        "email": "office@naive-time.test",
        "provenance": Provenance(
            source_url="https://registry.example.gov/entity/RO0000003",
            retrieved_at=datetime.now(),  # no tzinfo
            legal_basis=LegalBasis.LEGITIMATE_INTEREST,
        ),
    }
    result = gate.evaluate(record)
    assert result.accepted is False
    assert "NAIVE_RETRIEVED_AT" in result.reason_codes


def test_rejects_missing_company_name():
    gate = IngestGate()
    record = {"email": "office@no-name.test", "provenance": make_good_provenance()}
    result = gate.evaluate(record)
    assert result.accepted is False
    assert "MISSING_REQUIRED_FIELD" in result.reason_codes


def test_rejects_record_with_no_contact_field():
    gate = IngestGate()
    record = {"company_name": "Contactless SRL", "provenance": make_good_provenance()}
    result = gate.evaluate(record)
    assert result.accepted is False
    assert "NO_CONTACT_FIELD" in result.reason_codes


def test_phone_or_address_alone_satisfies_contact_requirement():
    gate = IngestGate()
    record = {
        "company_name": "Phone Only SRL",
        "phone": "+40 21 000 9999",
        "provenance": make_good_provenance(),
    }
    result = gate.evaluate(record)
    assert result.accepted is True


def test_suppressed_email_is_rejected_even_with_good_provenance():
    store = SuppressionStore(salt="test-salt")
    store.add("office@suppressed.test", reason="objection")
    gate = IngestGate(suppression_store=store)
    record = {
        "company_name": "Suppressed SRL",
        "email": "office@suppressed.test",
        "provenance": make_good_provenance(),
    }
    result = gate.evaluate(record)
    assert result.accepted is False
    assert "SUPPRESSED" in result.reason_codes


def test_unusual_legal_basis_is_a_warning_not_a_rejection():
    from gdpr_pipeline.provenance import LegalBasis as LB

    gate = IngestGate()
    record = {
        "company_name": "Unusual Basis SRL",
        "email": "office@unusual-basis.test",
        "provenance": Provenance(
            source_url="https://registry.example.gov/entity/RO0000004",
            retrieved_at=datetime.now(timezone.utc),
            legal_basis=LB.VITAL_INTEREST,
        ),
    }
    result = gate.evaluate(record)
    assert result.accepted is True
    assert any(w.code == "UNUSUAL_LEGAL_BASIS" for w in result.warnings)


def test_evaluate_batch_splits_accepted_and_rejected():
    gate = IngestGate()
    records = [
        {"company_name": "Good SRL", "email": "office@good.test", "provenance": make_good_provenance()},
        {"company_name": "Bad SRL", "email": "office@bad.test", "provenance": None},
    ]
    accepted, rejected = gate.evaluate_batch(records)
    assert len(accepted) == 1
    assert len(rejected) == 1
