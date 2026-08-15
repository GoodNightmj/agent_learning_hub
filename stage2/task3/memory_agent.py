def get_user_memory(
    memory_store,
    user_id:str
)->dict:
    return memory_store.get_memories(user_id)

if __name__ == "__main__":
    from stage2.task3.memory_store import MemoryStore
    from pathlib import Path
    path= Path(__file__).resolve().parent / "data" / "memory_store.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    memory_store = MemoryStore(str(path))
    memory_store.set_memory(
    "user_001",
    "language",
    "Python"
)
    print(get_user_memory(memory_store, "user_001"))
