#!/usr/bin/env python3
"""Test simple del LLM para verificar que responde correctamente."""

import httpx


def test_llm():
    payload = {
        "from_number": "+598123456789",
        "body": "crear remito",
        "message_id": "test_001",
    }
    
    response = httpx.post(
        "http://localhost:8000/webhook/whatsapp?use_v2=true",
        json=payload,
        timeout=60.0
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"\nRespuesta del LLM:")
    print(data['reply'])
    print(f"\nMetadata: {data['metadata']}")


if __name__ == "__main__":
    test_llm()
