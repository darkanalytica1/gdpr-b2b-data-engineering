from datetime import datetime, timedelta, timezone

from gdpr_pipeline.retention import FieldClass, RetentionEngine


def make_engine(ttl_overrides=None):
    field_map = {
        "company_name": FieldClass.IDENTITY,
        "email": FieldClass.CONTACT,
        "last_campaign_open": FieldClass.BEHAVIORAL,
        "lead_score": FieldClass.DERIVED,
    }
    return RetentionEngine(field_map=field_map, ttl_overrides=ttl_overrides)


def test_field_within_ttl_is_kept():
    now = datetime.now(timezone.utc)
    engine = make_engine()
    decision = engine.evaluate_field("email", now - timedelta(days=10), now=now)
    assert decision.action == "keep"


def test_field_past_ttl_is_expired():
    now = datetime.now(timezone.utc)
    engine = make_engine()
    decision = engine.evaluate_field("email", now - timedelta(days=400), now=now)
    assert decision.action == "expire"


def test_different_classes_have_different_default_ttls():
    now = datetime.now(timezone.utc)
    engine = make_engine()
    age = now - timedelta(days=200)
    contact_decision = engine.evaluate_field("email", age, now=now)
    identity_decision = engine.evaluate_field("company_name", age, now=now)
    behavioral_decision = engine.evaluate_field("last_campaign_open", age, now=now)

    assert contact_decision.action == "keep"  # CONTACT default is 365 days
    assert identity_decision.action == "keep"  # IDENTITY default is 730 days
    assert behavioral_decision.action == "expire"  # BEHAVIORAL default is 180 days


def test_ttl_override_is_respected():
    now = datetime.now(timezone.utc)
    engine = make_engine({FieldClass.CONTACT: 30})
    decision = engine.evaluate_field("email", now - timedelta(days=45), now=now)
    assert decision.action == "expire"


def test_unclassified_field_is_kept_and_reported():
    now = datetime.now(timezone.utc)
    engine = make_engine()
    decision = engine.evaluate_field("some_unmapped_field", now - timedelta(days=9999), now=now)
    assert decision.action == "keep"
    assert decision.ttl_days is None


def test_apply_scrubs_expired_fields_and_leaves_others():
    now = datetime.now(timezone.utc)
    engine = make_engine({FieldClass.CONTACT: 30})
    record = {"company_name": "Synthetic SRL", "email": "office@synthetic.test"}
    field_timestamps = {
        "company_name": now - timedelta(days=10),
        "email": now - timedelta(days=60),
    }
    scrubbed, decisions = engine.apply(record, field_timestamps, now=now)

    assert scrubbed["company_name"] == "Synthetic SRL"
    assert scrubbed["email"] is None
    actions = {d.field: d.action for d in decisions}
    assert actions["company_name"] == "keep"
    assert actions["email"] == "expire"


def test_apply_ignores_fields_with_no_timestamp():
    now = datetime.now(timezone.utc)
    engine = make_engine()
    record = {"company_name": "Synthetic SRL", "email": "office@synthetic.test"}
    scrubbed, decisions = engine.apply(record, field_timestamps={}, now=now)
    assert scrubbed == record
    assert decisions == []
