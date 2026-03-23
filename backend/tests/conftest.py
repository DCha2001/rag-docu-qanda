import os
from unittest.mock import MagicMock, patch

# Load .env first so real values take precedence, then fall back to stubs so
# config.py doesn't raise during unit-test collection when .env is absent.
from dotenv import load_dotenv
load_dotenv(override=True)
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/testdb")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

import pytest
from fastapi.testclient import TestClient

from main import app
from db.dbconnect import get_db
from core.client import get_anthropic_client


@pytest.fixture
def mock_db():
    """SQLAlchemy session mock — individual tests configure return values."""
    return MagicMock()


@pytest.fixture
def mock_anthropic():
    """Anthropic client mock with a sensible default message response."""
    client = MagicMock()
    content_block = MagicMock()
    content_block.type = "text"
    content_block.text = "Mock answer from Claude."
    message = MagicMock()
    message.content = [content_block]
    message.usage = MagicMock()
    client.messages.create.return_value = message
    return client


@pytest.fixture
def client(mock_db, mock_anthropic):
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_anthropic_client] = lambda: mock_anthropic

    with patch("main.init_db"):
        with TestClient(app) as c:
            yield c

    app.dependency_overrides.clear()
