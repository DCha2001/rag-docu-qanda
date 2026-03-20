import structlog

from fastapi import APIRouter, Depends, HTTPException

from core.client import get_anthropic_client
from db.dbconnect import get_db
from services.retrieval import search_simliar_chunks
from services.augment_utils import combine_chunks, build_user_message

from core.config import CLAUDE_MODEL

log = structlog.get_logger(__name__)

router = APIRouter()


SYSTEM_PROMPT = """You are a precise document question-answering assistant.
 
Your job is to answer the user's question based ONLY on the provided context excerpts.
 
Rules:
1. Only use information explicitly stated in the provided context.
2. If the context does not contain enough information to answer the question,
   say "I don't have enough information in the provided documents to answer this."
   Do NOT guess or use outside knowledge.
3. When you reference information, cite which source(s) you used by their
   [Source N] label.
4. Be concise. Answer the question directly, then provide supporting detail
   if relevant.
5. If different sources contain contradictory information, acknowledge the
   contradiction and present both perspectives with their source labels.
"""


@router.post("/query")
def query(query: str, client=Depends(get_anthropic_client), db=Depends(get_db)):
    try:
        log = log.bind(endpoint="POST /query", query=query, model=CLAUDE_MODEL)
        chunks = search_simliar_chunks(query=query, top_k=5, db=db)
        if "error" in chunks:
            log.error("Error during retrieval", error=chunks["error"])
            raise HTTPException(status_code=500, detail=chunks["error"])

        combined_content = combine_chunks(chunks["chunks"])
        user_message = build_user_message(combined_content, query)

        log.debug(user_message)

        messages = client.messages.create(
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message}
            ],
            model=CLAUDE_MODEL
        )

        log.info(f"Received response: {messages.usage}")
        return {"response": messages.content}
    except Exception as e:
        log.error(f"Error during query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/health")
def llm_connection_health(query: str, client=Depends(get_anthropic_client)):
    try:
        messages = client.messages.create(
            max_tokens=1024,
            messages=[
                {"role": "user", "content": query}
            ],
            model='claude-haiku-4-5-20251001'
        )

        log.info(f"Received response: {messages.usage}")
        return {"response": messages.content}
    except Exception as e:
        log.warning(f"Error during query: {e}")
        return {"error": str(e)}
