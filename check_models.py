"""
Small diagnostic script: confirms your GEMINI_API_KEY works and lists
the models available to it. Run locally with:

    python check_models.py
"""
import os

from dotenv import load_dotenv
from google import genai

dotenv_path = os.path.join(os.path.dirname(__file__), "backend", ".env")
load_dotenv(dotenv_path=dotenv_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in backend/.env.")
    raise SystemExit(1)

try:
    client = genai.Client(api_key=api_key)
    print("Models available to this API key:\n")
    for model in client.models.list():
        actions = getattr(model, "supported_actions", None) or []
        print(f"- {model.name}  (supported actions: {', '.join(actions) or 'unknown'})")
except Exception as e:
    print(f"An error occurred: {e}")
