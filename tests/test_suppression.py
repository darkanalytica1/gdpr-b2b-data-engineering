import json

from gdpr_pipeline.suppression import SuppressionStore, hash_identifier, normalize_email


def test_add_and_is_suppressed(tmp_path):
    store = SuppressionStore(salt="salt-a", path=tmp_path / "suppression.json")
    assert store.is_suppressed("jane.doe@example.test") is False
    store.add("Jane.Doe@Example.test", reason="objection")
    assert store.is_suppressed("jane.doe@example.test") is True  # normalisation


def test_check_at_send_is_inverse_of_is_suppressed(tmp_path):
    store = SuppressionStore(salt="salt-a", path=tmp_path / "suppression.json")
    store.add("blocked@example.test", reason="objection")
    assert store.check_at_send("blocked@example.test") is False
    assert store.check_at_send("allowed@example.test") is True


def test_store_never_persists_plaintext_email(tmp_path):
    path = tmp_path / "suppression.json"
    store = SuppressionStore(salt="salt-a", path=path)
    store.add("secret.person@example.test", reason="objection")
    raw = path.read_text(encoding="utf-8")
    assert "secret.person" not in raw
    assert "example.test" not in raw


def test_persistence_survives_a_new_store_instance(tmp_path):
    path = tmp_path / "suppression.json"
    store1 = SuppressionStore(salt="salt-a", path=path)
    store1.add("persisted@example.test", reason="objection")

    store2 = SuppressionStore(salt="salt-a", path=path)
    assert store2.is_suppressed("persisted@example.test") is True


def test_suppression_survives_simulated_reingest(tmp_path):
    """The core guarantee: a fresh import of the contact table must not
    erase or bypass an existing suppression entry."""
    path = tmp_path / "suppression.json"
    store = SuppressionStore(salt="salt-a", path=path)
    store.add("do-not-contact@example.test", reason="objection")

    # Simulate "re-ingest": a new process loads the store from disk and
    # checks a batch of freshly harvested contacts, one of which matches
    # the suppressed address.
    reloaded = SuppressionStore(salt="salt-a", path=path)
    incoming_batch = ["do-not-contact@example.test", "fresh-contact@example.test"]
    allowed = [addr for addr in incoming_batch if reloaded.check_at_send(addr)]

    assert "do-not-contact@example.test" not in allowed
    assert "fresh-contact@example.test" in allowed


def test_remove_is_explicit_and_reversible(tmp_path):
    store = SuppressionStore(salt="salt-a", path=tmp_path / "suppression.json")
    store.add("mistake@example.test", reason="added by mistake")
    assert store.is_suppressed("mistake@example.test") is True
    removed = store.remove("mistake@example.test")
    assert removed is True
    assert store.is_suppressed("mistake@example.test") is False


def test_different_salts_produce_different_hashes():
    h1 = hash_identifier(normalize_email("same@example.test"), "salt-a")
    h2 = hash_identifier(normalize_email("same@example.test"), "salt-b")
    assert h1 != h2


def test_normalize_email_lowercases_and_strips():
    assert normalize_email("  Jane.Doe@Example.TEST  ") == "jane.doe@example.test"


def test_len_reflects_entry_count(tmp_path):
    store = SuppressionStore(salt="salt-a", path=tmp_path / "suppression.json")
    assert len(store) == 0
    store.add("a@example.test", reason="x")
    store.add("b@example.test", reason="x")
    assert len(store) == 2
