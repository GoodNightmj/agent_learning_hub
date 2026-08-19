import re

from pydantic import BaseModel

from stage2.task5.evidence import Evidence, EvidenceStore


class CitationValidationResult(BaseModel):
    cited_ids: list[str]
    valid_ids: list[str]
    invalid_ids: list[str]
    ineligible_ids: list[str]
    is_valid: bool


def format_evidence_context( #将证据列表格式化为字符串喂给模型
    evidences: list[Evidence],
) -> str:
    context_list = []
    for evidence in evidences:
        if evidence.citation_eligible is True:
            context_list.append(f"""
            [{evidence.evidence_id}]\n
            标题: {evidence.title}\n
            内容: {evidence.content}\n
            来源: {evidence.uri}\n
            位置: {evidence.locator}\n""")
        else:
            continue
    return "\n\n".join(context_list)

def extract_citation_ids(answer: str) -> list[str]:#提取答案中的证据id
    pattern=r"\[(E\d+)\]"
    matches=re.findall(pattern,answer)
    results=list(dict.fromkeys(matches))
    return results


def validate_citations(# 验证答案中的证据id是否有效
    answer: str,
    store: EvidenceStore,
) -> CitationValidationResult:
    cited_ids=extract_citation_ids(answer)
    valid_ids=[]
    invalid_ids=[]
    ineligible_ids=[]
    for evidence_id in cited_ids:
        evidence=store.get(evidence_id)
        if evidence is None:
            invalid_ids.append(evidence_id)
        else:
            if evidence.citation_eligible is True:
                valid_ids.append(evidence_id)
            else:
                ineligible_ids.append(evidence_id)
    is_valid=len(invalid_ids)==0 and len(ineligible_ids)==0 and len(valid_ids)>0
    return CitationValidationResult(
        cited_ids=cited_ids,
        valid_ids=valid_ids,
        invalid_ids=invalid_ids,
        ineligible_ids=ineligible_ids,
        is_valid=is_valid
    )