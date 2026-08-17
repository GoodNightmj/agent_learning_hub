from stage2.task5 import evidence
from stage2.task5.evidence import EvidenceStore 
def test_new_store_is_empty():
    store = EvidenceStore()

    assert len(store) == 0
    assert store.all() == []
    evidence1=store.add(
        source_type="web_page",
        content="MCP 是一种连接 AI 应用与外部系统的开放协议。",
        title="MCP Introduction",
        uri="https://example.com/mcp"
    )
    assert evidence1.evidence_id == "E1"
    evidence2=store.add(
        source_type="document",
        content="MCP 是一种连接 AI 应用与外部系统的开放协议。",
        title="MCP Document",
        uri="https://example.com/mcp_doc"
    )
    assert evidence2.evidence_id == "E2"
    assert len(store) == 2
    assert store.get("E1") == evidence1
    assert store.get("E999") == None
    assert store.contains("E1") == True
    assert store.contains("E999") == False
    assert type(store.all())==type([evidence1,evidence2])
    assert [e.evidence_id for e in store.all()]==["E1","E2"]
    evidence_list=store.all()
    evidence_list.clear()
    assert len(store.all())==2
    assert id(evidence1.metadata) == id(evidence2.metadata)