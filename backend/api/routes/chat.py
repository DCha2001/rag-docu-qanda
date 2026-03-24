import structlog

from fastapi import APIRouter, Depends, HTTPException

from core.client import get_anthropic_client
from db.dbconnect import get_db
from services.retrieval import search_simliar_chunks
from services.augment_utils import combine_chunks, build_user_message

from core.config import CLAUDE_MODEL
from schemas.chat import QueryRequest, QueryResponse
from db.models import Message, Session

logger = structlog.get_logger(__name__)

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


# BEFORE: `query: str` was a URL query parameter (?query=...).
# AFTER:  `body: QueryRequest` is a JSON request body.
#
# FastAPI knows the difference by type:
#   - Primitive types (str, int) with no default → URL query param
#   - A Pydantic BaseModel subclass → JSON request body
#
# WHY the change?
#   1. Pydantic validates the body (min_length, max_length) before your code runs
#   2. POST bodies don't appear in server access logs (queries might be sensitive)
#   3. Special characters don't need URL encoding
#
# response_model=QueryResponse tells FastAPI to validate and serialize the
# return value. The Anthropic SDK TextBlock objects are read via from_attributes.
@router.post("/query", response_model=QueryResponse)
def query(body: QueryRequest, client=Depends(get_anthropic_client), db=Depends(get_db)):
    log = logger.bind(endpoint="POST /query", query=body.query, model=CLAUDE_MODEL)
    try:
        # Verify session exists
        session = db.query(Session).filter(Session.id == body.session_id).first()
        if not session:
            log.warning("query.session_not_found", session_id=body.session_id)
            raise HTTPException(status_code=404, detail="Session not found")

        # Get session's attached document IDs for filtered retrieval
        doc_ids = [doc.id for doc in session.documents if doc.status == "completed"]

        # Load conversation history for the session
        history = (
            db.query(Message)
            .filter(Message.session_id == body.session_id)
            .order_by(Message.created_at)
            .limit(20)
            .all()
        )
        is_first_message = len(history) == 0

        # Save user message to DB BEFORE calling Claude
        user_msg = Message(
            session_id=body.session_id,
            role="user",
            content=body.query,
        )
        db.add(user_msg)
        db.commit()

        # Auto-title the session from the first message if title is None
        if session.title is None and is_first_message:
            session.title = body.query[:60].strip()
            db.commit()

        # Build conversation history for Claude (excluding the just-saved user msg,
        # since we append it below after augmentation)
        conversation = [{"role": msg.role, "content": msg.content} for msg in history]
        log.debug("Session history loaded", message_count=len(conversation))

        # Retrieve relevant chunks filtered to the session's documents
        chunks = search_simliar_chunks(
            query=body.query,
            top_k=5,
            db=db,
            document_ids=doc_ids if doc_ids else None,
        )
        if "error" in chunks:
            log.error("Error during retrieval", error=chunks["error"])
            raise HTTPException(status_code=500, detail=chunks["error"])

        combined_content = combine_chunks(chunks["chunks"])
        user_message = build_user_message(combined_content, body.query)

        log.debug(user_message)

        conversation.append({"role": "user", "content": user_message})

        # Call Claude — use `response` to avoid shadowing the `messages` history list
        response = client.messages.create(
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=conversation,
            model=CLAUDE_MODEL,
        )

        log.info("query.response", usage=str(response.usage))

        # Extract text from response content blocks
        assistant_text = "".join(
            block.text for block in response.content if block.type == "text"
        )

        # Save assistant message to DB AFTER getting response
        assistant_msg = Message(
            session_id=body.session_id,
            role="assistant",
            content=assistant_text,
        )
        db.add(assistant_msg)
        db.commit()

        return {"response": response.content}
    except HTTPException as e:
        raise e
    except Exception as e:
        log.error("query.error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
