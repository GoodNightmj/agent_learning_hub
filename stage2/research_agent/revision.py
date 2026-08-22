from stage2.task5.claim_support import AnswerSupportResult
from stage2.task5.evidence import EvidenceStore
from stage2.task5.citation import format_evidence_context

def revise_answer(
    client,
    *,
    model: str,
    user_query: str,
    draft_answer: str,
    validation: AnswerSupportResult,
    store: EvidenceStore,
) -> str:
    evidence_context = format_evidence_context(store.all())
    validation_text=validation.model_dump_json(indent=2, ensure_ascii=False)
    prompt = f"""
你负责修正一个证据型回答。

原始问题：
{user_query}

原始回答：
{draft_answer}

验证结果：
{validation_text}

当前允许引用的 Evidence：
{evidence_context}

修正规则：

1. 只允许使用给出的 Evidence。
2. 不得创造新的 Evidence ID。
3. 每个事实性 Claim 必须在句末直接引用 Evidence。
4. 如果 Validation 指出某个 Claim 没有证据：
   - 有 Evidence 支持则补正确 Citation；
   - Evidence 只支持部分内容，则弱化 Claim；
   - 没有 Evidence 支持则删除 Claim 或明确说明证据不足。
5. 不得为了通过验证添加 Evidence 无法支持的新事实。
6. 只输出修正后的最终答案。"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": f"请修正原始回答，使其符合验证结果和修正规则。"
            }
        ],)
    content = response.choices[0].message.content
    return content or draft_answer