from sentence_transformers import SentenceTransformer

from stage2.task1.chunker import chunk_text
from stage2.task1.retriever import retrieve
from stage2.task1.embedder import load_embedding_model
from stage2.task5.evidence import EvidenceStore, Evidence
def build_rag_evidence(
    *,
    query: str,
    document_text: str,
    document_title: str,
    document_uri: str,
    embedding_model,
    store: EvidenceStore,
    chunk_size: int = 500,
    overlap: int = 50,
    top_k: int = 3,
) -> list[Evidence]:
    chunks = chunk_text(
        text=document_text,
        chunk_size=chunk_size,
        overlap=overlap
    )
    retrieved_chunks=retrieve(
        model=embedding_model,
        query=query,
        chunks=chunks,
        top_k=top_k
    )
    evidences = []
    for retrieved in retrieved_chunks:
        chunk_info = retrieved["chunk_information"]
        score = retrieved["score"]
        evidence = store.add(
            locator=f"chunk_id={chunk_info['chunk_id']};chars={chunk_info['start']}-{chunk_info['end']}",
            source_type="local_document",
            content=chunk_info["text"],
            title=document_title ,
            uri=document_uri,
            metadata={
                "score":score,
                "chunk_id": chunk_info["chunk_id"],
                "start": chunk_info["start"],
                "end": chunk_info["end"]
            },
            citation_eligible=True
        )

        evidences.append(evidence)

    return evidences

if __name__ == "__main__":
    # 示例用法
    store = EvidenceStore()
    document_text = "这是一个示例文档，包含一些文本内容。"
    document_title = "示例文档"
    document_uri = "http://example.com/document"
    query = "示例查询"
    embedding_model = load_embedding_model()

    evidences = build_rag_evidence(
        query=query,
        document_text=document_text,
        document_title=document_title,
        document_uri=document_uri,
        embedding_model=embedding_model,
        store=store
    )

    for evidence in evidences:
        print(f"Evidence ID: {evidence.evidence_id}, Content: {evidence.content}, Score: {evidence.metadata['score']}")