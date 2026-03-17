import logging

from fastapi import APIRouter, Depends

from core.client import get_anthropic_client
from db.dbconnect import get_db
from services.retrieval import search_simliar_chunks
from services.augment_utils import combine_chunks, build_user_message

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/query")
def query(query: str, client=Depends(get_anthropic_client), db=Depends(get_db)):
    try:
        chunks = search_simliar_chunks(query=query, top_k=5, db=db)
        if "error" in chunks:
            return {"error": chunks["error"]}

        combined_content = combine_chunks(chunks["chunks"])
        user_message = build_user_message(combined_content, query)

        logger.debug(user_message)

        messages = client.messages.create(
            max_tokens=1024,
            messages=[
                {"role": "user", "content": user_message}
            ],
            model='claude-haiku-4-5-20251001'
        )

        logger.info(f"Received response: {messages.usage}")
        return {"response": messages.content}
    except Exception as e:
        logger.warning(f"Error during query: {e}")
        return {"error": str(e)}


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

        logger.info(f"Received response: {messages.usage}")
        return {"response": messages.content}
    except Exception as e:
        logger.warning(f"Error during query: {e}")
        return {"error": str(e)}
