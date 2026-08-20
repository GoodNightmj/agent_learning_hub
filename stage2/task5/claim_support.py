
import re

from pydantic import BaseModel

from stage2.task5.citation import extract_citation_ids
from typing import Literal

from stage2.task5.citation import (
    CitationValidationResult,
    format_evidence_context,
    validate_citations,
)
from stage2.task5.evidence import EvidenceStore


class SupportJudgment(BaseModel):
    verdict: Literal["supported", "partial", "unsupported"]
    reason: str


class ClaimSupportResult(BaseModel):# 针对一句话
    claim: str
    citation_ids: list[str]
    verdict: Literal["supported", "partial", "unsupported"]
    reason: str


class AnswerSupportResult(BaseModel):#针对整段话
    citation_validation: CitationValidationResult
    claim_results: list[ClaimSupportResult]
    is_valid: bool

class CitedClaim(BaseModel):
    text: str
    citation_ids: list[str]


def extract_cited_claims(answer: str) -> list[CitedClaim]: #提取答案中的主张和对应的证据id
    sentences = re.findall(r".+?[。！？.!?](?:\s*\[E\d+\])*|.+$", answer.strip(),flags=re.S)
    cited_claims = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        citation_ids = extract_citation_ids(sentence)
        # Remove citation ids from the sentence
        claimed_text=re.sub(r'\[E\d+\]', '', sentence).strip()
        if not claimed_text:
            continue
        cited_claims.append(CitedClaim(text=claimed_text, citation_ids=citation_ids))
    return cited_claims



def  judge_claim_support(
    client,
    model: str,
    claim: CitedClaim,
    store: EvidenceStore,
) -> ClaimSupportResult:
    evidences=[]
    for citation_id in claim.citation_ids:
        evidence=store.get(citation_id)
        if evidence and evidence.citation_eligible:
            evidences.append(evidence)
    if not evidences:
        return ClaimSupportResult(
            claim=claim.text,
            citation_ids=claim.citation_ids,
            verdict="unsupported",
            reason="没有提供有效的证据支持该主张"
        )
    evidence_context=format_evidence_context(evidences)
    prompt="""
你是严格的证据支持度审查器，只能根据提供的证据判断 Claim，
不得使用外部知识。

判断标准：
- supported：证据直接支持 Claim 的全部内容
- partial：证据只支持 Claim 的一部分
- unsupported：证据没有提到、无法推出或与 Claim 冲突

只输出 JSON：
{
  "verdict": "supported、partial 或 unsupported",
  "reason": "简要说明依据"
}"""
    response=client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": f"Claim: {claim.text}\n\nEvidence:\n{evidence_context}"
            }
        ],
        response_format={
            "type": "json_object",}
    )
    judgment = SupportJudgment.model_validate_json(response.choices[0].message.content)
    return ClaimSupportResult(
        claim=claim.text,
        citation_ids=claim.citation_ids,
        verdict=judgment.verdict,
        reason=judgment.reason
    )
        
def validate_answer_support(
    client,
    model: str,
    answer: str,
    store: EvidenceStore,
) -> AnswerSupportResult:
    citation_validation=validate_citations(answer,store)
    cited_claims=extract_cited_claims(answer)
    claim_results=[]
    bad_ids=set(citation_validation.invalid_ids+citation_validation.ineligible_ids) 
    for claim in cited_claims:
        if not claim.citation_ids  :
            claim_results.append(ClaimSupportResult(
                claim=claim.text,
                citation_ids=[],
                verdict="unsupported",
                reason="没有提供证据"
            ))
        elif any(cid in bad_ids for cid in claim.citation_ids):
            claim_results.append(ClaimSupportResult(
                claim=claim.text,
                citation_ids=claim.citation_ids,
                verdict="unsupported",
                reason="引用了无效或不合格的证据"
            ))
        else:
            claim_results.append(judge_claim_support(client,model,claim,store))
    is_valid = (citation_validation.is_valid
    and bool(claim_results)
    and all(
        cr.verdict == "supported"
        for cr in claim_results
    )
)
    return AnswerSupportResult(
        citation_validation=citation_validation,
        claim_results=claim_results,
        is_valid=is_valid
    )