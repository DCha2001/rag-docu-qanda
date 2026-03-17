from anthropic import Anthropic

from core.config import ANTHROPIC_API_KEY

_client = Anthropic(api_key=ANTHROPIC_API_KEY)


def get_anthropic_client():
    return _client
