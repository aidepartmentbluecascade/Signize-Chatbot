import os
from dotenv import load_dotenv

def load_environment():
    load_dotenv()
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("OpenAI API key is missing in the environment variables.")
    return openai_key
