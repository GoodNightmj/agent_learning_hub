from stage2.task5.evidence import EvidenceStore


def test_new_store_is_empty():
    store = EvidenceStore()

    assert len(store) == 0
    assert store.all() == []


def test_add_assigns_sequential_ids():
    store = EvidenceStore()
    evidence1 = store.add(
        source_type="web_page",
        content="MCP 是一种连接 AI 应用与外部系统的开放协议。",
        title="MCP Introduction",
        uri="https://example.com/mcp",
    )
    evidence2 = store.add(
        source_type="document",
        content="MCP 是一种连接 AI 应用与外部系统的开放协议。",
        title="MCP Document",
        uri="https://example.com/mcp_doc",
    )

    assert evidence1.evidence_id == "E1"
    assert evidence2.evidence_id == "E2"


def test_get_and_contains():
    store = EvidenceStore()
    evidence = store.add(
        source_type="web_page",
        content="MCP 是一种连接 AI 应用与外部系统的开放协议。",
        title="MCP Introduction",
        uri="https://example.com/mcp",
    )

    assert store.get("E1") == evidence
    assert store.get("E999") is None
    assert store.contains("E1")
    assert not store.contains("E999")


def test_all_returns_independent_list():
    store = EvidenceStore()
    store.add(
        source_type="web_page",
        content="MCP 是一种连接 AI 应用与外部系统的开放协议。",
    )
    store.add(
        source_type="document",
        content="MCP 是一种连接 AI 应用与外部系统的开放协议。",
    )

    evidence_list = store.all()

    assert isinstance(evidence_list, list)
    evidence_list.clear()
    assert len(store.all()) == 2


def test_default_metadata_is_not_shared():
    store = EvidenceStore()
    evidence1 = store.add(
        source_type="web_page",
        content="MCP 是一种连接 AI 应用与外部系统的开放协议。",
    )
    evidence2 = store.add(
        source_type="document",
        content="MCP 是一种连接 AI 应用与外部系统的开放协议。",
    )

    evidence1.metadata["author"] = "John Doe"

    assert evidence2.metadata == {}
