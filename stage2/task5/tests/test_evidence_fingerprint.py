from stage2.task5.evidence import build_evidence_fingerprint


def test_same_evidence_has_same_fingerprint():
    arguments = {
        "source_type": "web_page",
        "uri": "https://example.com/mcp",
        "locator": "section-1",
        "content": "MCP 是一种开放协议。",
    }

    first = build_evidence_fingerprint(**arguments)
    second = build_evidence_fingerprint(**arguments)

    assert first == second
    assert len(first) == 64
import pytest


@pytest.mark.parametrize(
    ("field_name", "new_value"),
    [
        ("source_type", "document"),
        ("uri", "https://example.com/other"),
        ("locator", "section-2"),
        ("content", "另一段内容"),
    ],
)
def test_identity_field_change_changes_fingerprint(field_name, new_value):
    base = {
        "source_type": "web_page",
        "uri": "https://example.com/mcp",
        "locator": "section-1",
        "content": "MCP 是一种开放协议。",
    }

    original = build_evidence_fingerprint(**base)

    changed = base.copy()
    changed[field_name] = new_value

    modified = build_evidence_fingerprint(**changed)

    assert original != modified