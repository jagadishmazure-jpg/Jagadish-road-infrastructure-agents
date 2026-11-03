from road_agents.redaction import redact


def test_phone_redacted():
    assert "[PHONE]" in redact("call 555-123-4567 for the crew")
    assert "555-123-4567" not in redact("call 555-123-4567 for the crew")


def test_ssn_redacted():
    assert redact("ssn 123-45-6789 on file") == "ssn [SSN] on file"


def test_card_number_redacted():
    assert redact("card 4111 1111 1111 1111 charged") == "card [CARD] charged"


def test_email_redacted():
    assert redact("contact jane.doe@example.com") == "contact [EMAIL]"


def test_all_four_categories_in_one_note():
    note = ("Reach 555-123-4567, ssn 123-45-6789, card 4111111111111111, "
            "mail jane.doe@example.com")
    out = redact(note)
    assert "[PHONE]" in out and "[SSN]" in out
    assert "[CARD]" in out and "[EMAIL]" in out
    for secret in ("555-123-4567", "123-45-6789", "4111111111111111",
                   "jane.doe@example.com"):
        assert secret not in out


def test_clean_text_unchanged():
    text = "Segment S5 needs resurfacing before winter."
    assert redact(text) == text
