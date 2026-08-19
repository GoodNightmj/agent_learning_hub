from math import e
from pyexpat.errors import messages
import re

from pydantic import BaseModel

from stage2.task5.citation import extract_citation_ids


class CitedClaim(BaseModel):
    text: str
    citation_ids: list[str]


def extract_cited_claims(answer: str) -> list[CitedClaim]: #提取答案中的主张和对应的证据id
    sentences = re.split(r"(?<=[。！？.!?])\s*", answer.strip())
    cited_claims = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        citation_ids = extract_citation_ids(sentence)
        # Remove citation ids from the sentence
        claimed_text=re.sub(r'\[E\d+\]', '', sentence).strip()
        cited_claims.append(CitedClaim(text=claimed_text, citation_ids=citation_ids))
    return cited_claims


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


class ClaimSupportResult(BaseModel):
    claim: str
    citation_ids: list[str]
    verdict: Literal["supported", "partial", "unsupported"]
    reason: str


class AnswerSupportResult(BaseModel):
    citation_validation: CitationValidationResult
    claim_results: list[ClaimSupportResult]
    is_valid: bool
def  judge_claim_support(
    client,
    model: str,
    claim: CitedClaim,
    store: EvidenceStore,
) -> ClaimSupportResult:
    for citation_id in claim.citation_ids:
        evidence = store.get(citation_id)
        if evidence is not None and evidence.citation_eligible is True:
            evidence_context = format_evidence_context([evidence])
            prompt = f"""
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
            }
            """
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Claim: {claim.text}\nEvidence: {evidence_context}"}
            ]
            response = client.chat.complete.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            if response is None:
                raise ValueError("No response from the model.")
            try:
                judgment=SupportJudgment.model_validate_json(response.choices[0].message.content)
            except ValueError as e:
                raise ValueError(f"json 解析失败: {e}\nResponse content: {response.choices[0].message.content}")
            verdict = judgment.verdict  
            reason = judgment.reason    
            return ClaimSupportResult(
                claim=claim.text,
                citation_ids=claim.citation_ids,
                verdict=verdict,
                reason=reason
            )
        elif evidence is not None and evidence.citation_eligible is False:
            return ClaimSupportResult(
                claim=claim.text,
                citation_ids=claim.citation_ids,
                verdict="unsupported",
                reason="没有可用的引用证据支持该主张",
            )
        else:
            return ClaimSupportResult(
                            claim=claim.text,
                            citation_ids=claim.citation_ids,
                            verdict="unsupported",
                            reason="没有可用的引用证据支持该主张",
            )


def validate_answer_support(
    client,
    model: str,
    answer: str,
    store: EvidenceStore,
) -> AnswerSupportResult:
    validation_result = validate_citations(answer, store)
    cited_claims = extract_cited_claims(answer)
    claim_results = []
    for claim in cited_claims:
        claim_result = judge_claim_support(client, model, claim, store)
        if claim.citation_ids is None:
            
        