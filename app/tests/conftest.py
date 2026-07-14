import os


# Unit and integration tests must never call a paid external provider.
os.environ["LLM_PROVIDER"] = "mock"
os.environ["GEMINI_API_KEY"] = ""
