import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.environ["DATABASE_URL"]
ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]
CLAUDE_MODEL: str = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
VOYAGE_API_KEY: str = os.environ["VOYAGE_API_KEY"]
UNSTRUCTURED_API_KEY: str = os.environ["UNSTRUCTURED_API_KEY"]
SUPABASE_URL: str = os.environ["SUPABASE_URL"]
