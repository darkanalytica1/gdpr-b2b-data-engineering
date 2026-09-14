import pytest

from gdpr_pipeline.email_class import EmailKind, classify_batch, classify_email


@pytest.mark.parametrize(
    "address",
    [
        "office@acme.example",
        "info@acme.example",
        "contact@acme.example",
        "sales@acme.example",
        "vanzari@acme.example",
        "support@acme.example",
        "hr@acme.example",
        "secretariat@acme.example",
        "birou@acme.example",
        "billing@acme.example",
        "sales2@acme.example",
        "support-eu@acme.example",
    ],
)
def test_role_addresses_are_classified_as_role(address):
    result = classify_email(address)
    assert result.kind == EmailKind.ROLE


@pytest.mark.parametrize(
    "address",
    [
        "jane.doe@acme.example",
        "j.doe@acme.example",
        "jane_doe@acme.example",
        "jane-doe@acme.example",
    ],
)
def test_firstname_lastname_patterns_are_classified_as_nominal(address):
    result = classify_email(address)
    assert result.kind == EmailKind.NOMINAL


@pytest.mark.parametrize(
    "address",
    [
        "test@acme.example",
        "example@acme.example",
        "asdf@acme.example",
        "placeholder@acme.example",
        "someone@example.com",
        "someone@mailinator.com",
    ],
)
def test_junk_addresses_are_classified_as_junk(address):
    result = classify_email(address)
    assert result.kind == EmailKind.JUNK


def test_malformed_address_is_junk():
    result = classify_email("not-an-email")
    assert result.kind == EmailKind.JUNK


def test_empty_address_is_junk():
    result = classify_email("")
    assert result.kind == EmailKind.JUNK


def test_ambiguous_bare_localpart_is_unknown_not_a_guess():
    result = classify_email("jdoe@acme.example")
    assert result.kind == EmailKind.UNKNOWN


def test_plus_tag_is_ignored_for_role_detection():
    result = classify_email("sales+newyork@acme.example")
    assert result.kind == EmailKind.ROLE


def test_classify_batch_preserves_order_and_length():
    addresses = ["office@acme.example", "jane.doe@acme.example", "test@acme.example"]
    results = classify_batch(addresses)
    assert [r.kind for r in results] == [EmailKind.ROLE, EmailKind.NOMINAL, EmailKind.JUNK]


def test_classification_is_case_insensitive_on_local_part():
    result = classify_email("OFFICE@acme.example")
    assert result.kind == EmailKind.ROLE
