import json
from pathlib import Path
class MemoryStore:

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.memories = self.load()

    def load(self) -> dict:
        if not Path(self.file_path).exists():
            return {}
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)

    def set_memory(
        self,
        user_id: str,
        key: str,
        value: str
    ) -> None:
        if user_id not in self.memories:
            self.memories[user_id] = {}
        self.memories[user_id][key] = value
        self.save()

    def get_memories(
        self,
        user_id: str
    ) -> dict:
        if user_id not in self.memories:
            return {}
        return self.memories[user_id]