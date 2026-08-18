from stage2.task5.evidence import Evidence, EvidenceStore
def extract_web_search_evidence(
    tool_result: dict,
    store: EvidenceStore,
) -> list[Evidence]:
    if tool_result.get("success")is not True:
        return []
    data=tool_result.get("data")#type: ignore
    if not isinstance(data,list):
        return []
    extracted=[]
    for item in data:
        if not isinstance(item, dict):
            continue
        content=item.get("content")
        if not content:
            continue
        meta=tool_result.get("meta",{})
        raw_result = meta.get("raw_result", {})
        query = raw_result.get("query")
        evidence=store.add(
            source_type="web_search",
            content=content,
            title=item.get("title"),
            uri=item.get("url"),
            locator=None,
            citation_eligible=False,
            metadata={"score": item.get("score"),"query": query}
        )
        extracted.append(evidence)
    return extracted

def extract_webpage_evidence(
    tool_result: dict,
    store: EvidenceStore,
) -> list[Evidence]:
    if tool_result.get("success") is not True:
        return []
    content=tool_result.get("data")
    if not isinstance(content, str):
        return []
    meta=tool_result.get("meta")
    title=tool_result.get("meta",{}).get("title")
    url=tool_result.get("meta",{}).get("url")
    source_type="web_page"
    if not content:
        return []
    evidence=store.add(
        source_type=source_type,
        content=content,
        title=title,
        uri=url,
        locator=None,
        citation_eligible=True,
        metadata={},
    )
    return [evidence]