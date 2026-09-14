from gdpr_pipeline.tombstone import TombstoneStore


def test_erase_and_is_tombstoned(tmp_path):
    store = TombstoneStore(salt="salt-a", path=tmp_path / "tombstone.json")
    assert store.is_tombstoned("erase.me@example.test") is False
    store.erase("erase.me@example.test", reason="Article 17 request")
    assert store.is_tombstoned("erase.me@example.test") is True


def test_tombstone_never_persists_plaintext(tmp_path):
    path = tmp_path / "tombstone.json"
    store = TombstoneStore(salt="salt-a", path=path)
    store.erase("person.name@example.test", reason="Article 17 request")
    raw = path.read_text(encoding="utf-8")
    assert "person.name" not in raw
    assert "example.test" not in raw


def test_apply_to_incoming_blocks_matching_records(tmp_path):
    store = TombstoneStore(salt="salt-a", path=tmp_path / "tombstone.json")
    store.erase("erased@example.test", reason="Article 17 request")

    incoming = [
        {"company_name": "A SRL", "email": "erased@example.test"},
        {"company_name": "B SRL", "email": "kept@example.test"},
    ]
    kept, blocked = store.apply_to_incoming(incoming, key_field="email")

    assert len(kept) == 1
    assert kept[0]["email"] == "kept@example.test"
    assert len(blocked) == 1
    assert blocked[0]["email"] == "erased@example.test"


def test_erasure_survives_simulated_nightly_reingest(tmp_path):
    """The zombie-record problem: a nightly re-ingest that reintroduces
    the exact same source facts must not resurrect an erased record."""
    path = tmp_path / "tombstone.json"

    store_run_1 = TombstoneStore(salt="salt-a", path=path)
    store_run_1.erase("zombie@example.test", reason="Article 17 request")

    # Simulate the next day's process: a brand-new store instance,
    # loaded fresh from disk, receiving the harvester's output again.
    store_run_2 = TombstoneStore(salt="salt-a", path=path)
    nightly_batch = [
        {"company_name": "Zombie SRL", "email": "zombie@example.test"},
        {"company_name": "Fine SRL", "email": "fine@example.test"},
    ]
    kept, blocked = store_run_2.apply_to_incoming(nightly_batch, key_field="email")

    assert [r["email"] for r in kept] == ["fine@example.test"]
    assert [r["email"] for r in blocked] == ["zombie@example.test"]


def test_sweep_removes_records_that_slipped_past_the_pre_filter(tmp_path):
    store = TombstoneStore(salt="salt-a", path=tmp_path / "tombstone.json")
    store.erase("slipped-through@example.test", reason="Article 17 request")

    warehouse = [
        {"company_name": "Slipped SRL", "email": "slipped-through@example.test"},
        {"company_name": "Ok SRL", "email": "ok@example.test"},
    ]
    survivors = store.sweep(warehouse, key_field="email")

    assert [r["email"] for r in survivors] == ["ok@example.test"]


def test_erasure_is_additive_only_across_reload(tmp_path):
    path = tmp_path / "tombstone.json"
    store1 = TombstoneStore(salt="salt-a", path=path)
    store1.erase("first@example.test", reason="Article 17 request")

    store2 = TombstoneStore(salt="salt-a", path=path)
    store2.erase("second@example.test", reason="Article 17 request")

    store3 = TombstoneStore(salt="salt-a", path=path)
    assert store3.is_tombstoned("first@example.test") is True
    assert store3.is_tombstoned("second@example.test") is True
    assert len(store3) == 2
