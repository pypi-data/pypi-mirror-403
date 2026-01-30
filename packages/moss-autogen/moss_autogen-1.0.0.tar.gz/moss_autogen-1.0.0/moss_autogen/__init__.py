"""
MOSS AutoGen Integration - Cryptographic Signing for AutoGen

Sign messages, function results, and conversations explicitly.

Quick Start:
    from autogen import AssistantAgent
    from moss_autogen import sign_message, sign_function_result
    
    assistant = AssistantAgent(name="assistant", ...)
    reply = assistant.generate_reply(messages)
    
    # Sign the reply
    result = sign_message(reply, agent_id="assistant")

Enterprise Mode:
    Set MOSS_API_KEY for policy evaluation and evidence retention.
"""

__version__ = "0.2.0"

# Explicit signing (recommended)
from .signing import (
    sign_message,
    sign_message_async,
    sign_function_result,
    sign_function_result_async,
    sign_conversation,
    sign_conversation_async,
    sign_reply,
    sign_reply_async,
    verify_envelope,
)

# Core types
from moss import SignResult, VerifyResult, Envelope, enterprise_enabled

# Legacy (backwards compatibility)
from .wrapper import signed_agent

__all__ = [
    # Explicit signing
    "sign_message",
    "sign_message_async",
    "sign_function_result",
    "sign_function_result_async",
    "sign_conversation",
    "sign_conversation_async",
    "sign_reply",
    "sign_reply_async",
    "verify_envelope",
    
    # Core types
    "SignResult",
    "VerifyResult",
    "Envelope",
    "enterprise_enabled",
    
    # Legacy
    "signed_agent",
]
