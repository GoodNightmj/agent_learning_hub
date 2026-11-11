# Stage3 / s01 最小运行练习

源码依据：learn-claude-code `0dcafa2ae053a1ddd6a72f265431104b08a5aa13` 的
[s01](https://github.com/shareAI-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/s01_agent_loop/code.py)
与 [s02](https://github.com/shareAI-lab/learn-claude-code/blob/0dcafa2ae053a1ddd6a72f265431104b08a5aa13/s02_tool_use/code.py)。
这是配合源码阅读的本地练习，不是 Anthropic 协议的原样运行，也不是 Claude Code 产品源码。

- 原教程：Anthropic SDK，s01 的单工具是 bash。
- 本节提供：Responses API 边界、一个读取教学文件的工具、终端事件、离线验收。
- 学习者实现：`exercise.py` 的 `run_loop`；其余文件可以先略读。
- 暂未实现：完整权限判断、Session Store、压缩、持久化 Trace。
- 后续 s02 练习再扩展工具注册与检索工具，不在本节引入检索模型。

## 启动

从个人仓库根目录运行，沿用根目录 Python >=3.14、pyproject.toml、uv.lock：

```bash
uv sync --locked
uv run --locked python -m stage3.s01_loop.check adapter
```

根目录 `.env` 沿用 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL=gpt-5.6-luna`。
不复制、不覆盖已有 `.env`，不提交密钥。适配器直接使用 `client.responses.create()`；
`use_responses_api=True` 是 LangChain 的选项，不是这个 SDK 方法的参数。

`x-opencode-session` 在创建客户端时固定；默认生成 UUID，可用 `OPENCODE_SESSION_ID`
显式指定。User-Agent 使用本项目名称。这沿用之前的请求头方案，是否被当前供应商接受
仍需真实请求验证。HTTP 会话标识不提供本地保存/恢复能力。

先看一次真实响应（只调用模型一次，不执行工具，不要求完成 TODO）：

```bash
uv run --locked python -m stage3.s01_loop.exercise probe
```

完成 `run_loop` 后：

```bash
uv run --locked python -m stage3.s01_loop.check loop
uv run --locked python -m stage3.s01_loop.exercise live
```

预期事件形状（不是已发生的真实模型记录）：
`model_request → model_response → tool_request → tool_result → model_request → model_response → stop`。
最终回答应包含教学文件中的练习标记，并准确说出当前阶段和暂缓任务。
模型可能请求多次工具；以实际输出为准。`no_tool_calls` 只表示循环停止，不表示内容已验证。

保留一次真实运行输出用于 Review，可写入被根目录 `.gitignore` 忽略的 `*.log`。
若遇到协议、鉴权或网络错误，保留错误类型和状态码；不要粘贴密钥。

## 验证范围

`check adapter` 用真实 OpenAI SDK 和 httpx.MockTransport 模拟 HTTP，不连接供应商。
`check loop` 用固定响应验收学习者实现，尚未完成 TODO 时应报 NotImplementedError。
`probe` 才发送一次真实模型请求；`live` 才尝试真实完整循环。
适配代码保留完整 output 条目（含加密 reasoning 数据），但不把这些不透明数据当作 Trace 打印。
