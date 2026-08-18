from stage2.task5.evidence import Evidence, EvidenceStore, build_evidence_fingerprint
def extract_web_search_evidence(
    tool_result: dict,
    store: EvidenceStore,
) -> list[Evidence]:
    if not tool_result.get("success"):
        return []
    data=tool_result.get("data")#type: ignore
    if not tool_result.get("data").get("content"):#type: ignore
        return store.all()
    store.add(
        source_type="web_search",
        content=data.get("content"),
        title=data.get("title"),
        uri=data.get("url"),
        locator=None,
        citation_eligible=False,
        metadata={
            "score": data.get("score"),
            "query": tool_result.get("meta").get("raw_result").get("query")#type: ignore
        }
    ))
    return store.all()

def extract_webpage_evidence(
    tool_result: dict,
    store: EvidenceStore,
) -> list[Evidence]:
    if not tool_result.get("success"):
        return []
    data=tool_result.get("data")#type: ignore
    if not tool_result.get("data").get("content"):#type: ignore
        return store.all()
    store.add(
        source_type="fetch_webpage",
        content=data.get("content"),
        title=data.get("title"),
        uri=data.get("url"),
        locator=None,
        citation_eligible=True,
        metadata={}
    ))
    return store.all()