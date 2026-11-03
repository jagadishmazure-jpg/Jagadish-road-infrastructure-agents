import hashlib
import json
import re

import road_agents.redaction as redaction
from road_agents.redaction import load_blocklist, scan_for_blocked_names


def test_blocklist_is_non_empty():
    assert len(load_blocklist()) > 0


def test_blocklist_entries_are_sha256_hex():
    for entry in load_blocklist():
        assert re.fullmatch(r"[0-9a-f]{64}", entry)


def test_scan_flags_a_blocked_phrase_via_injected_blocklist(tmp_path,
                                                            monkeypatch):
    phrase = "example blocked phrase"
    digest = hashlib.sha256(phrase.encode()).hexdigest()
    path = tmp_path / "blocklist.json"
    path.write_text(json.dumps({"hashes": [digest]}))
    monkeypatch.setattr(redaction, "_blocklist_path", lambda: path)
    assert scan_for_blocked_names(f"note about {phrase} here") == [digest]


def test_scan_passes_clean_text():
    assert scan_for_blocked_names("Segment S5 needs resurfacing.") == []
