import structlog

from fastapi import APIRouter, Depends, HTTPException, Request
from core.limiter import limiter

from core.client import get_anthropic_client
from core.auth import get_current_user
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
3. When you reference information, cite which document(s) you used by their
    filename.
4. Be concise. Answer the question directly, then provide supporting detail
   if relevant.
5. If different sources contain contradictory information, acknowledge the
   contradiction and present both perspectives with their source labels.
"""


@router.post("/query", response_model=QueryResponse)
@limiter.limit("20/minute")
def query(
    request: Request,
    body: QueryRequest,
    client=Depends(get_anthropic_client),
    db=Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    log = logger.bind(endpoint="POST /query", query=body.query, model=CLAUDE_MODEL, user_id=user_id)
    try:
        # Verify session exists and belongs to the requesting user (IDOR protection)
        session = db.query(Session).filter(Session.id == body.session_id).first()
        if not session:
            log.warning("query.session_not_found", session_id=body.session_id)
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != user_id:
            log.warning("query.session_forbidden", session_id=body.session_id, session_owner=session.user_id)
            raise HTTPException(status_code=403, detail="Not authorized to query this session")

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

        # Build conversation history for Claude
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
