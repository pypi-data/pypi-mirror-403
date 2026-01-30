"""
MOSS AutoGen Integration - Explicit Signing Functions

Explicit signing functions for AutoGen messages and function results.
"""

from typing import Any, Dict, List, Optional

from moss import sign, sign_async, verify, SignResult, VerifyResult


def _extract_message_payload(message: Any) -> Dict[str, Any]:
    """Extract payload from AutoGen message."""
    if isinstance(message, dict):
        return {"type": "message", **message}
    
    if isinstance(message, str):
        return {"type": "message", "content": message}
    
    if hasattr(message, "dict"):
        return {"type": "message", **message.dict()}
    
    return {"type": "message", "content": str(message)}


def _extract_function_result_payload(result: Any, function: str) -> Dict[str, Any]:
    """Extract payload from function result."""
    if isinstance(result, dict):
        return {"type": "function_result", "function": function, **result}
    
    if isinstance(result, str):
        return {"type": "function_result", "function": function, "output": result}
    
    return {"type": "function_result", "function": function, "output": str(result)}


def _extract_conversation_payload(messages: List[Any]) -> Dict[str, Any]:
    """Extract payload from conversation history."""
    return {
        "type": "conversation",
        "messages": [_extract_message_payload(m) for m in messages],
        "message_count": len(messages),
    }


def sign_message(
    message: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign an AutoGen message.
    
    Args:
        message: Message dict or string
        agent_id: Identifier for the agent
        context: Optional context (user_id, session_id, etc.)
    
    Returns:
        SignResult with envelope and enterprise info
    
    Example:
        from moss_autogen import sign_message
        
        response = agent.generate_reply(messages)
        result = sign_message(response, agent_id="assistant")
    """
    payload = _extract_message_payload(message)
    return sign(
        output=payload,
        agent_id=agent_id,
        action="message",
        context=context,
    )


async def sign_message_async(
    message: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_message."""
    payload = _extract_message_payload(message)
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action="message",
        context=context,
    )


def sign_function_result(
    result: Any,
    agent_id: str,
    *,
    function: str,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign a function/tool execution result.
    
    Args:
        result: Function return value
        agent_id: Identifier for the agent
        function: Name of the function that was called
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    
    Example:
        def my_function(args):
            result = execute(args)
            return sign_function_result(result, agent_id="assistant", function="my_function")
    """
    payload = _extract_function_result_payload(result, function)
    return sign(
        output=payload,
        agent_id=agent_id,
        action=f"function:{function}",
        context=context,
    )


async def sign_function_result_async(
    result: Any,
    agent_id: str,
    *,
    function: str,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_function_result."""
    payload = _extract_function_result_payload(result, function)
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action=f"function:{function}",
        context=context,
    )


def sign_conversation(
    messages: List[Any],
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign a full conversation history.
    
    Args:
        messages: List of messages in the conversation
        agent_id: Identifier for the agent
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    
    Example:
        from moss_autogen import sign_conversation
        
        # Sign the full conversation for audit
        result = sign_conversation(chat_history, agent_id="chat-agent")
    """
    payload = _extract_conversation_payload(messages)
    return sign(
        output=payload,
        agent_id=agent_id,
        action="conversation",
        context=context,
    )


async def sign_conversation_async(
    messages: List[Any],
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_conversation."""
    payload = _extract_conversation_payload(messages)
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action="conversation",
        context=context,
    )


def sign_reply(
    reply: Any,
    agent_id: str,
    *,
    agent_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign an agent's reply (generate_reply output).
    
    Args:
        reply: Agent reply (string or dict)
        agent_id: Identifier for the agent
        agent_name: Optional name of the specific agent
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    """
    payload = _extract_message_payload(reply)
    if agent_name:
        payload["agent_name"] = agent_name
    
    action = f"reply:{agent_name}" if agent_name else "reply"
    
    return sign(
        output=payload,
        agent_id=agent_id,
        action=action,
        context=context,
    )


async def sign_reply_async(
    reply: Any,
    agent_id: str,
    *,
    agent_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_reply."""
    payload = _extract_message_payload(reply)
    if agent_name:
        payload["agent_name"] = agent_name
    
    action = f"reply:{agent_name}" if agent_name else "reply"
    
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action=action,
        context=context,
    )


def verify_envelope(envelope: Any, payload: Any = None) -> VerifyResult:
    """
    Verify a signed envelope.
    
    Args:
        envelope: MOSS Envelope or dict
        payload: Original payload for hash verification (optional)
    
    Returns:
        VerifyResult with valid=True/False and details
    """
    return verify(envelope, payload)
