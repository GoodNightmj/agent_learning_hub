def load():
    import os
    from dotenv import load_dotenv
    from openai import OpenAI
    load_dotenv()
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL")
    return OpenAI(api_key=api_key, base_url=base_url), model
