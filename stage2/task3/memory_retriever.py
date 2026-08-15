def memory_dict_to_records(memories: dict) -> list[dict]:
    list_of_records = []
    for key, value in memories.items():
        list_of_records.append({"key": key, "value": value,"text": f"{key}: {value}"})
    return list_of_records
def records_to_memory_dict(records: list[dict]) -> dict:
    memories = {}
    for record in records:
        key = record.get("key")
        value = record.get("value")
        if key is not None and value is not None:
            memories[key] = value
    return memories