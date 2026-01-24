"""
Test LLM endpoint connection.
"""
import pytest
from langchain_openai import ChatOpenAI
from config import settings


def test_settings_loaded():
    """Test that settings are loaded from environment."""
    assert settings.openai_api_base is not None, "OPENAI_API_BASE not set"
    assert settings.openai_api_key is not None, "OPENAI_API_KEY not set"
    assert settings.model_name is not None, "MODEL_NAME not set"

    print(f"\n  API Base: {settings.openai_api_base}")
    print(f"  Model: {settings.model_name}")
    print(f"  API Key: {settings.openai_api_key[:10]}...")


def test_llm_connection():
    """Test that we can connect to the LLM endpoint."""
    llm = ChatOpenAI(
        model=settings.model_name,
        openai_api_base=settings.openai_api_base,
        openai_api_key=settings.openai_api_key,
        temperature=0.1,
        max_tokens=50,
    )

    # Simple test message
    response = llm.invoke("Say 'hello' in one word.")

    assert response is not None
    assert response.content is not None
    assert len(response.content) > 0

    print(f"\n  LLM Response: {response.content}")


def test_llm_with_system_prompt():
    """Test LLM with a system prompt (similar to agent usage)."""
    from langchain.prompts import ChatPromptTemplate

    llm = ChatOpenAI(
        model=settings.model_name,
        openai_api_base=settings.openai_api_base,
        openai_api_key=settings.openai_api_key,
        temperature=0.1,
        max_tokens=100,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Always respond in JSON format."),
        ("human", "{input}"),
    ])

    chain = prompt | llm
    response = chain.invoke({"input": "Return a JSON object with a 'status' key set to 'ok'"})

    assert response is not None
    assert "ok" in response.content.lower() or "status" in response.content.lower()

    print(f"\n  LLM Response: {response.content}")
