import structlog

from fastapi import APIRouter, Depends, HTTPException

from db.dbconnect import get_db
from db.models import Session, Message, Document, SessionDocument
from schemas.chat import SessionCreate, SessionOut, MessageOut
from schemas.documents import DocumentResponse

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(db=Depends(get_db)):
    log = logger.bind(endpoint="GET /sessions")
    log.info("list_sessions.started")
    try:
        sessions = db.query(Session).order_by(Session.created_at.desc()).all()
        log.info("list_sessions.success", count=len(sessions))
        return sessions
    except Exception as e:
        log.error("list_sessions.error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch sessions")


@router.post("/sessions", response_model=SessionOut)
def create_session(body: SessionCreate, db=Depends(get_db)):
    log = logger.bind(endpoint="POST /sessions")
    log.info("create_session.started")
    try:
        session = Session(title=body.title)
        db.add(session)
        db.commit()
        db.refresh(session)
        log.info("create_session.success", session_id=session.id)
        return session
    except Exception as e:
        log.error("create_session.error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, db=Depends(get_db)):
    log = logger.bind(endpoint="DELETE /sessions/{session_id}", session_id=session_id)
    log.info("delete_session.started")
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            log.warning("delete_session.not_found")
            raise HTTPException(status_code=404, detail="Session not found")
        db.delete(session)
        db.commit()
        log.info("delete_session.success")
        return {"detail": "Session deleted"}
    except HTTPException as e:
        raise e
    except Exception as e:
        log.error("delete_session.error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete session")


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
def get_session_messages(session_id: str, db=Depends(get_db)):
    log = logger.bind(endpoint="GET /sessions/{session_id}/messages", session_id=session_id)
    log.info("get_session_messages.started")
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            log.warning("get_session_messages.not_found")
            raise HTTPException(status_code=404, detail="Session not found")
        messages = (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at)
            .all()
        )
        log.info("get_session_messages.success", count=len(messages))
        return messages
    except HTTPException as e:
        raise e
    except Exception as e:
        log.error("get_session_messages.error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch messages")


@router.get("/sessions/{session_id}/documents", response_model=list[DocumentResponse])
def get_session_documents(session_id: str, db=Depends(get_db)):
    log = logger.bind(endpoint="GET /sessions/{session_id}/documents", session_id=session_id)
    log.info("get_session_documents.started")
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            log.warning("get_session_documents.not_found")
            raise HTTPException(status_code=404, detail="Session not found")
        log.info("get_session_documents.success", count=len(session.documents))
        return session.documents
    except HTTPException as e:
        raise e
    except Exception as e:
        log.error("get_session_documents.error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch session documents")


@router.post("/sessions/{session_id}/documents/{document_id}", response_model=DocumentResponse)
def attach_document(session_id: str, document_id: str, db=Depends(get_db)):
    log = logger.bind(
        endpoint="POST /sessions/{session_id}/documents/{document_id}",
        session_id=session_id,
        document_id=document_id,
    )
    log.info("attach_document.started")
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            log.warning("attach_document.session_not_found")
            raise HTTPException(status_code=404, detail="Session not found")

        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            log.warning("attach_document.document_not_found")
            raise HTTPException(status_code=404, detail="Document not found")

        # Idempotent: only attach if not already attached
        already_attached = (
            db.query(SessionDocument)
            .filter(
                SessionDocument.session_id == session_id,
                SessionDocument.document_id == document_id,
            )
            .first()
        )
        if not already_attached:
            link = SessionDocument(session_id=session_id, document_id=document_id)
            db.add(link)
            db.commit()
            log.info("attach_document.success")
        else:
            log.info("attach_document.already_attached")

        return document
    except HTTPException as e:
        raise e
    except Exception as e:
        log.error("attach_document.error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to attach document to session")


@router.delete("/sessions/{session_id}/documents/{document_id}")
def detach_document(session_id: str, document_id: str, db=Depends(get_db)):
    log = logger.bind(
        endpoint="DELETE /sessions/{session_id}/documents/{document_id}",
        session_id=session_id,
        document_id=document_id,
    )
    log.info("detach_document.started")
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            log.warning("detach_document.session_not_found")
            raise HTTPException(status_code=404, detail="Session not found")

        link = (
            db.query(SessionDocument)
            .filter(
                SessionDocument.session_id == session_id,
                SessionDocument.document_id == document_id,
            )
            .first()
        )
        if not link:
            log.warning("detach_document.not_attached")
            raise HTTPException(status_code=404, detail="Document not attached to session")

        db.delete(link)
        db.commit()
        log.info("detach_document.success")
        return {"detail": "Document detached from session"}
    except HTTPException as e:
        raise e
    except Exception as e:
        log.error("detach_document.error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to detach document from session")
