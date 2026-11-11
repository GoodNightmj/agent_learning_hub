"""离线验收。adapter 使用真实 SDK + 模拟 HTTP；loop 使用固定模型响应。"""
import argparse
from copy import deepcopy
import json

from .exercise import QUESTION, TOOLS, execute_call, run_loop


def tool_call(call_id):
    # id 故意不同于 call_id，避免配对时误用对象 ID。
    return {"type": "function_call", "id": f"fc_{call_id}",
            "call_id": call_id, "name": "read_file",
            "arguments": '{"path":"project_notes.txt"}', "status": "completed"}


REASONING = {"type": "reasoning", "id": "rs_mock", "summary": [],
             "encrypted_content": "opaque_mock_payload"}
FINAL = {"type": "message", "role": "assistant", "id": "msg_mock",
         "status": "completed", "content": [
             {"type": "output_text", "text": "Stage3。", "annotations": []}]}


def check_adapter():
    import httpx
    from .adapter import MODEL, build_client, call_model
    seen = []

    def handle(request):
        seen.append(json.loads(request.content))
        assert request.url.path == "/v1/responses", "必须调用 Responses API"
        assert request.headers["x-opencode-session"] == "offline-session"
        assert request.headers["User-Agent"] == "agent-learning-hub-stage3/0.1"
        output = [REASONING, tool_call("c1")] if len(seen) == 1 else [FINAL]
        status = "incomplete" if len(seen) == 3 else "completed"
        return httpx.Response(200, json={
            "id": f"resp_mock_{len(seen)}", "object": "response", "created_at": 0,
            "model": MODEL, "status": status, "output": output,
            "error": None,
            "incomplete_details": {"reason": "max_output_tokens"} if status == "incomplete" else None,
            "parallel_tool_calls": True, "tools": TOOLS, "tool_choice": "auto",
        })

    transport = httpx.MockTransport(handle)
    with build_client(api_key="offline-test-key", base_url="https://example.invalid/v1",
                      session_id="offline-session",
                      http_client=httpx.Client(transport=transport)) as client:
        history = [{"role": "user", "content": QUESTION}]
        first = call_model(client, history, TOOLS)
        assert len(history) == 1, "适配器不能自行推进历史"
        assert first["output"] == [REASONING, tool_call("c1")]
        assert first["output_text"] == ""
        history.extend(first["output"])
        history.append({"type": "function_call_output", "call_id": "c1", "output": "fixture"})
        assert call_model(client, history, TOOLS)["output_text"] == "Stage3。"
        assert seen[1]["input"] == history
        assert seen[0]["store"] is False and seen[0]["model"] == MODEL
        assert seen[0]["tools"] == TOOLS
        try:
            call_model(client, history, TOOLS)
        except RuntimeError as exc:
            assert "incomplete" in str(exc)
        else:
            raise AssertionError("截断响应不能当成正常结束")
    print("PASS adapter：真实 SDK、模拟 HTTP；请求路径、请求头、完整条目往返、文本提取、截断处理")


def check_loop():
    history = [{"role": "user", "content": QUESTION}]
    snapshots = []
    first = {"output": [REASONING, tool_call("c1"), tool_call("c2")],
             "output_text": "准备读取文件，这不是最终回答。"}
    last = {"output": [FINAL], "output_text": "Stage3。"}

    def ask_model(items, tools):
        snapshots.append(deepcopy(items))
        assert tools == TOOLS
        assert len(snapshots) <= 2, "无工具调用时应停止"
        return deepcopy(first if len(snapshots) == 1 else last)

    result = run_loop(ask_model, history, max_turns=3)
    assert result == {"stop_reason": "no_tool_calls", "answer": "Stage3。", "model_calls": 2}
    sent_again = snapshots[1]
    assert sent_again[1:4] == first["output"], "必须保留全部 output 条目"
    outputs = sent_again[4:]
    assert [item["call_id"] for item in outputs] == ["c1", "c2"], "每次调用都要返回对应结果"
    assert all(item["type"] == "function_call_output" and "S3-L1-CEDAR-27" in item["output"]
               for item in outputs)
    assert history[-1] == FINAL, "最终模型消息也进入历史"
    capped = [{"role": "user", "content": QUESTION}]
    result = run_loop(lambda items, tools: deepcopy(first), capped, max_turns=1)
    assert result == {"stop_reason": "max_turns", "answer": "", "model_calls": 1}
    assert [item["call_id"] for item in capped if item.get("type") == "function_call_output"] == ["c1", "c2"]
    broken = tool_call("bad")
    broken["arguments"] = "not JSON"
    assert execute_call(broken).startswith("ERROR:")
    print("PASS loop：模拟模型；多调用配对、完整历史、继续/停止、轮数上限、坏参数")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("part", choices=["adapter", "loop"])
    args = parser.parse_args()
    check_adapter() if args.part == "adapter" else check_loop()
