"""Stage3 第一节：补齐 run_loop；其余是本节提供的运行样板。"""
import argparse
import json
import os
from pathlib import Path
from uuid import uuid4

FIXTURES = Path(__file__).resolve().parent / "fixtures"
QUESTION = "读取 project_notes.txt，告诉我当前阶段、暂缓任务和练习标记。"
TOOLS = [{
    "type": "function",
    "name": "read_file",
    "description": "读取教学 fixtures 目录内的文本文件，例如 project_notes.txt。",
    "parameters": {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
        "additionalProperties": False,
    },
    "strict": True,
}]


def emit(event, **fields):
    """输出可观察事件；不输出模型的隐藏推理或鉴权信息。"""
    print(json.dumps({"event": event, **fields}, ensure_ascii=False))


def execute_call(call):
    """本节只接一个工具。下一节由学习者改成注册表和通用分发。"""
    emit("tool_request", name=call["name"], call_id=call["call_id"],
         arguments=call["arguments"])
    try:
        if call["name"] != "read_file":
            raise ValueError("unknown tool")
        args = json.loads(call["arguments"])
        if (not isinstance(args, dict) or set(args) != {"path"}
                or not isinstance(args["path"], str) or not args["path"].strip()):
            raise ValueError("expected exactly one nonempty string argument: path")
        path = (FIXTURES / args["path"]).resolve()
        if not path.is_relative_to(FIXTURES.resolve()) or path.suffix != ".txt":
            raise ValueError("path must be a .txt file inside fixtures")
        output = path.read_text(encoding="utf-8")[:8000]
    except (ValueError, OSError) as exc:
        output = f"ERROR: {exc}"
    emit("tool_result", call_id=call["call_id"], output=output)
    return output


def run_loop(ask_model, history, max_turns=6):
    """ask_model(history, TOOLS) 返回 {output: list[dict], output_text: str}。

    TODO：自己写完整循环，预计 15～25 行。
    - 最多请求模型 max_turns 次；ask_model 是可调用的本地函数。
    - 每次先调用 ask_model，再把完整 output 逐项加入 history。
    - 只筛选 type == "function_call" 的条目供执行。
    - 没有调用：返回 {stop_reason: "no_tool_calls", answer: 文本,
      model_calls: 实际请求数}。这里的停止不代表答案已被验证。
    - 有调用：按顺序用 execute_call(call) 得到字符串结果；每个结果
      追加一个 function_call_output，call_id 对应 call["call_id"]。
      全部结果追加完，才进入下一次模型请求。
    - 达到上限仍未结束：返回 {stop_reason: "max_turns", answer: "",
      model_calls: max_turns}；最后一轮的调用结果也要配对保存。
    不在这里创建客户端、重置 history 或重试模型请求。
    """
    if max_turns < 1:
        raise ValueError("max_turns must be positive")
    raise NotImplementedError("请完成 run_loop 后再运行 check 或 live")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["probe", "live"])
    parser.add_argument("--question", default=QUESTION)
    parser.add_argument("--max-turns", type=int, default=6)
    args = parser.parse_args()

    from dotenv import load_dotenv
    from .adapter import MODEL, build_client, call_model
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    if os.getenv("LLM_MODEL", MODEL) != MODEL:
        raise ValueError(f"本节约定模型为 {MODEL}，请检查 LLM_MODEL")
    # 沿用此前请求头方案。它是 HTTP 会话标识，本节尚无 Session Store。
    session_id = os.getenv("OPENCODE_SESSION_ID") or str(uuid4())
    history = [{"role": "user", "content": args.question}]
    with build_client(api_key=os.environ["LLM_API_KEY"],
                      base_url=os.environ["LLM_BASE_URL"],
                      session_id=session_id) as client:
        request_count = 0

        def ask_model(items, tools):
            nonlocal request_count
            request_count += 1
            emit("model_request", number=request_count, history_items=len(items))
            turn = call_model(client, items, tools)
            emit("model_response", types=[item["type"] for item in turn["output"]])
            return turn

        if args.mode == "probe":
            # 一次真实请求，查看协议；不执行返回的工具，也不宣称跑通循环。
            turn = ask_model(history, TOOLS)
            calls = [item for item in turn["output"] if item["type"] == "function_call"]
            emit("probe", calls=calls, text=turn["output_text"], tools_executed=0)
        else:
            result = run_loop(ask_model, history, args.max_turns)
            emit("stop", **result)


if __name__ == "__main__":
    main()
