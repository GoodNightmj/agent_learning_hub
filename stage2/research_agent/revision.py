def revise_answer(
    client,
    *,
    model: str,
    user_query: str,
    draft_answer: str,
    validation: AnswerSupportResult,
    store: EvidenceStore,
) -> str:
    ...
