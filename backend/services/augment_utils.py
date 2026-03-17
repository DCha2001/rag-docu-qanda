
def combine_chunks(chunks):
    if not chunks:
        return None
    
    context_parts = []
    for i, chunk in enumerate(chunks, start=1):
        context_parts.append(
            f"[Source {i}] (document_id: {chunk['document_id']}, "
            f"relevance: {chunk['similarity_score']})\n"
            f"{chunk['content']}"
        )
 
    return "\n---\n".join(context_parts)

def build_user_message(context_block: str, query: str) -> str:
    """
    Construct the full user message with context + question.
 
    The structure here is deliberate:
      1. Context comes FIRST — the model reads it before seeing the question,
         so it's "primed" with the relevant information.
      2. The question comes LAST — this is what the model will focus on
         generating a response to.
      3. Clear XML-style delimiters (<context>, <question>) make it
         unambiguous where source material ends and the question begins.
         Claude is specifically trained to respect these boundaries.
 
    Why XML tags specifically?
      Anthropic's prompt engineering guidelines recommend XML tags for
      structured prompts. Claude handles them better than markdown headers
      or plain text delimiters because they were part of the training
      methodology.
    """
    return (
        f"<context>\n{context_block}\n</context>\n\n"
        f"<question>\n{query}\n</question>"
    )
 