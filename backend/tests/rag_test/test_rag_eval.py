import csv
import os
from pathlib import Path

from dotenv import load_dotenv

import pytest
from anthropic import Anthropic
from ragas.llms import llm_factory
from .config import my_metric

DATASET_PATH = Path(__file__).parent / "dataset.csv"

pytestmark = pytest.mark.integration

load_dotenv(override=True)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _load_dataset() -> list[dict]:
    with open(DATASET_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def ragas_llm():
    """Anthropic-backed LLM for ragas metric scoring."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or api_key == "test-key":
        pytest.skip("Real ANTHROPIC_API_KEY required for RAG eval tests")

    client = Anthropic(api_key=api_key)
    llm = llm_factory(
        model=os.environ.get("claude_model", "claude-haiku-4-5-20251001"),
        provider="anthropic",
        client=client,
    )
    # Anthropic rejects requests that include both temperature and top_p.
    # ragas adds top_p=0.1 by default, so remove it after construction.
    llm.model_args.pop("top_p", None)
    return llm


@pytest.fixture(scope="module")
def rag_responses(ragas_llm) -> list[dict]:
    """
    Run each question in the dataset through the full RAG pipeline and return
    a list of dicts with keys: question, response, grading_notes.
    """
    from anthropic import Anthropic as _Anthropic
    from api.routes.chat import SYSTEM_PROMPT
    from core.config import CLAUDE_MODEL
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from services.augment_utils import build_user_message, combine_chunks
    from services.retrieval import search_simliar_chunks

    rows = _load_dataset()
    if not rows:
        pytest.skip("dataset.csv is empty")

    anthropic_client = _Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Build a fresh engine from the current env var — the module-level engine in
    # db.dbconnect was created at import time and may still hold the @db hostname.
    _engine = create_engine(os.environ["DATABASE_URL"])
    db = sessionmaker(bind=_engine)()
    results = []

    try:
        for row in rows:
            question = row["question"]
            grading_notes = row["grading_notes"]

            retrieval = search_simliar_chunks(query=question, top_k=5, db=db)
            if "error" in retrieval:
                pytest.fail(f"Retrieval failed — is the DB running? ({retrieval['error']})")

            combined = combine_chunks(retrieval["chunks"])
            if not combined:
                response_text = (
                    "I don't have enough information in the provided documents to answer this."
                )
            else:
                user_message = build_user_message(combined, question)
                msg = anthropic_client.messages.create(
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_message}],
                    model=CLAUDE_MODEL,
                )
                response_text = (
                    msg.content[0].text if msg.content else ""
                )

            results.append(
                {
                    "question": question,
                    "response": response_text,
                    "grading_notes": grading_notes,
                }
            )
    finally:
        db.close()

    return results


# ─── Tests ────────────────────────────────────────────────────────────────────

def test_rag_correctness(ragas_llm, rag_responses):
    """Every RAG response must pass the correctness check."""
    failures = []

    for item in rag_responses:
        result = my_metric.score(
            llm=ragas_llm,
            response=item["response"],
            grading_notes=item["grading_notes"],
        )
        if result.value != "pass":
            failures.append(
                {
                    "question": item["question"],
                    "response": item["response"],
                    "reason": result.reason,
                }
            )

    assert not failures, (
        "RAG correctness failures:\n"
        + "\n\n".join(
            f"Q: {f['question']}\nA: {f['response']}\nReason: {f['reason']}"
            for f in failures
        )
    )


def test_rag_all_questions_answered(rag_responses):
    """Pipeline must return a non-empty response for every question."""
    for item in rag_responses:
        assert item["response"].strip(), (
            f"Empty response for question: {item['question']}"
        )
