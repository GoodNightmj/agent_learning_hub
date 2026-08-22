from stage2.task1.embedder import load_embedding_model
from stage2.task3.load import load
from stage2.research_agent.research_agent import run_research_agent, ResearchAgentResult
from stage2.task2.tool_schema import TOOL_SCHEMA
from stage2.task3.session_manager import SessionManager
from stage2.task3.memory_store import MemoryStore
if __name__ == "__main__":
    client, model = load()
    embedding_model = load_embedding_model()
    document_text ="""Research Agent 项目规定：
    web_search 返回的搜索摘要只负责发现候选网页，
    不能作为最终事实引用。
    只有原始本地资料和 fetch_webpage 获取到的网页正文
    才允许作为 citation_eligible Evidence。"""
    user_query = """根据本地项目资料说明 web_search 的搜索摘要能否作为最终引用；
    同时查询 Python 官方文档，说明 dataclasses 模块的主要用途。
    请分别给出证据。"""
    session_manager = SessionManager()
    memory_store = MemoryStore("stage2/research_agent/data/memory_store.json")
    result = run_research_agent(
        client=client,

        user_id="demo_user",
        session_id="demo_session",
        session_manager=session_manager,
        memory_store=memory_store,

        user_query=user_query,
        document_text=document_text,
        document_title="Research Agent Project Guidelines",
        document_uri="https://example.com/research-agent-guidelines",
        embedding_model=embedding_model,
        tools=TOOL_SCHEMA,
        model=model
    )
    print("=== Research Agent Result ===")
    print(result.model_dump_json(indent=2, ensure_ascii=False))
