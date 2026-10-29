from app.services.privacy import redact_payload, stable_hash


def test_redact_payload_removes_contact_and_secret_values():
    payload = {
        "email": "owner@example.com",
        "phone": "+1 425 555 0100",
        "api_key": "super-secret",
        "nested": {"authorization": "Bearer token"},
    }

    redacted = redact_payload(payload)

    assert redacted["email"] == "[email]"
    assert redacted["phone"] == "[phone]"
    assert redacted["api_key"] == "[secret]"
    assert redacted["nested"]["authorization"] == "[secret]"


def test_stable_hash_is_deterministic_and_short():
    assert stable_hash("CFO@example.com") == stable_hash(" cfo@example.com ")
    assert len(stable_hash("CFO@example.com")) == 16
