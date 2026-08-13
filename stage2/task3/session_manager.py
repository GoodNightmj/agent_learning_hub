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
                        "content": "你是一个可以使用工具的智能助手。"
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