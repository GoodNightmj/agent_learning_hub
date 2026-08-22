import time 


class SessionManager:
    def __init__(self):
        self.sessions = {}
    def get_or_create_session(self, session_id: str) -> dict:
        if session_id in self.sessions:
            return self.sessions[session_id]
        else:
            # 创建一个新的会话
            new_session = {
                "session_id": session_id,
                "messages": [{
                        "role": "system",
                        "content": """你是一个研究助理，用户会给你一个问题和一些参考资料，你需要根据这些参考资料来回答用户的问题。
                                请严格按照以下要求来回答问题：
                                1. 已提供的 Local Evidence 可以直接引用。
                        
                                2. web_search 只能用于找候选网页，
                                Search Evidence 不能作为最终引用。
                        
                                3. 如果本地资料不足，可以调用 web_search。
                        
                                4. 找到合适网页后使用 fetch_webpage 获取正文。
                        
                                5. 只有 citation_eligible=true 的 Evidence 才能引用。
                        
                                6. 最终事实性主张后必须使用 [E编号]。
                        
                                7. 不得编造 Evidence ID。
                        
                                8. 证据不足要明确说明。
                                9.如果标题本身表达事实，不要把标题和证据拆开；每个事实性句子都必须在本句末尾引用 Evidence。
                                举个例子，不要这样回答：
                                **web_search 搜索摘要不能作为最终引用。**
                                本地项目规定……。[E1]
                                而应该这样回答：
                                1. web_search 搜索摘要不能作为最终引用，因为本地项目规定它只用于发现候选网页。[E1]
                                10. 每个事实性 Claim 必须在同一句末尾附带 Evidence ID；
                                    不要创建没有 Citation 的事实性标题。
                                如果使用列表，列表编号本身不包含语义。"""
                }],
                "created_at": time.time(),
                "summary": "",
            }
            self.sessions[session_id] = new_session
            return new_session
    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False