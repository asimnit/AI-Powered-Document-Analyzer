"""
Prompt Templates for RAG Chat

Contains system prompts and formatting utilities for chat conversations.
"""

# System prompt for the AI assistant
SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions based on provided document context.

Your responsibilities:
- Answer questions accurately using ONLY the information from the provided context
- If the answer is not in the context, clearly state "I don't have enough information in the documents to answer that question"
- Cite your sources by mentioning the document name when referencing information
- Be concise and clear in your responses
- If asked about multiple topics, address each one based on available context
- Maintain a professional and helpful tone

Important guidelines:
- DO NOT make up or infer information that is not in the context
- DO NOT use external knowledge - only use what's provided in the document context
- If the context is empty or insufficient, admit it honestly
- When citing, use the format: "According to [document name]..."
"""

# User prompt template with context
USER_PROMPT_TEMPLATE = """Context from documents:
---
{context}
---

Question: {question}

Please answer based on the context provided above. If the context doesn't contain relevant information, please say so."""


def format_context_from_chunks(chunks: list) -> str:
    """
    Format document chunks into context string for the prompt.
    
    Args:
        chunks: List of chunk dictionaries with keys:
                - chunk_text: The text content
                - document_name: Name of the source document
                - store_name: Name of the store
                - page_number: Page number (optional)
    
    Returns:
        Formatted context string
    """
    if not chunks:
        return "No relevant context found."
    
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        doc_name = chunk.get('document_name', 'Unknown')
        store_name = chunk.get('store_name', 'Unknown')
        page_num = chunk.get('page_number')
        text = chunk.get('chunk_text', '')
        
        # Build source attribution
        source = f"[Store: {store_name} | Document: {doc_name}"
        if page_num:
            source += f" | Page: {page_num}"
        source += "]"
        
        # Format as numbered context block
        context_parts.append(f"{i}. {source}\n{text}")
    
    return "\n\n".join(context_parts)


def build_chat_messages(question: str, context: str, conversation_history: list = None) -> list:
    """
    Build the messages array for chat completion API.
    
    Args:
        question: User's current question
        context: Formatted context from retrieved chunks
        conversation_history: List of previous messages (optional)
                              Each message: {"role": "user|assistant", "content": "..."}
    
    Returns:
        List of message dictionaries for the chat API
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    
    # Add conversation history (limit to prevent token overflow)
    if conversation_history:
        for msg in conversation_history[-10:]:  # Last 10 messages
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Add current question with context
    user_message = USER_PROMPT_TEMPLATE.format(
        context=context,
        question=question
    )
    messages.append({"role": "user", "content": user_message})
    
    return messages


def extract_sources_from_chunks(chunks: list) -> list:
    """
    Extract source information from chunks for API response.
    
    Args:
        chunks: List of chunk dictionaries
    
    Returns:
        List of source dictionaries suitable for JSON response
    """
    sources = []
    for chunk in chunks:
        source = {
            "store_id": chunk.get('store_id'),
            "store_name": chunk.get('store_name'),
            "document_id": chunk.get('document_id'),
            "document_name": chunk.get('document_name'),
            "chunk_id": chunk.get('chunk_id'),
            "chunk_text": chunk.get('chunk_text', '')[:500],  # Truncate for response
            "page_number": chunk.get('page_number'),
            "similarity_score": round(chunk.get('similarity_score', 0.0), 3)
        }
        sources.append(source)
    return sources
