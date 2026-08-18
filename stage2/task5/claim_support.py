import re

from pydantic import BaseModel

from stage2.task5.citation import extract_citation_ids


class CitedClaim(BaseModel):
    text: str
    citation_ids: list[str]


def extract_cited_claims(answer: str) -> list[CitedClaim]:
    sentences = re.split(r'(?<=[。！？])', answer)
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
if __name__ == "__main__":
    answer = (
        "Python 是一种编程语言 [E1]。"
        "它支持面向对象编程 [E1][E2]。"
        "它非常受欢迎。"
    )

    print(extract_cited_claims(answer))