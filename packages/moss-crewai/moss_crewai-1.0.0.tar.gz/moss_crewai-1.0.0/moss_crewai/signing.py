"""
MOSS CrewAI Integration - Explicit Signing Functions

Explicit signing functions for CrewAI task outputs and agent results.
"""

from typing import Any, Dict, Optional

from moss import sign, sign_async, verify, SignResult, VerifyResult


def _extract_task_payload(output: Any) -> Dict[str, Any]:
    """Extract payload from CrewAI task output."""
    if isinstance(output, dict):
        return {"type": "task_output", **output}
    
    if isinstance(output, str):
        return {"type": "task_output", "output": output}
    
    if hasattr(output, "raw"):
        return {
            "type": "task_output",
            "raw": output.raw,
            "pydantic": output.pydantic.dict() if hasattr(output, "pydantic") and output.pydantic else None,
            "json_dict": output.json_dict if hasattr(output, "json_dict") else None,
        }
    
    if hasattr(output, "dict"):
        return {"type": "task_output", **output.dict()}
    
    return {"type": "task_output", "output": str(output)}


def _extract_agent_payload(output: Any) -> Dict[str, Any]:
    """Extract payload from CrewAI agent output."""
    if isinstance(output, dict):
        return {"type": "agent_output", **output}
    
    if isinstance(output, str):
        return {"type": "agent_output", "output": output}
    
    if hasattr(output, "dict"):
        return {"type": "agent_output", **output.dict()}
    
    return {"type": "agent_output", "output": str(output)}


def _extract_crew_payload(result: Any) -> Dict[str, Any]:
    """Extract payload from CrewAI crew result."""
    if isinstance(result, dict):
        return {"type": "crew_result", **result}
    
    if isinstance(result, str):
        return {"type": "crew_result", "output": result}
    
    if hasattr(result, "raw"):
        return {
            "type": "crew_result",
            "raw": result.raw,
            "tasks_output": [
                _extract_task_payload(t) for t in result.tasks_output
            ] if hasattr(result, "tasks_output") else None,
        }
    
    return {"type": "crew_result", "output": str(result)}


def sign_task_output(
    output: Any,
    agent_id: str,
    *,
    task: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign a CrewAI task output.
    
    Args:
        output: Task output (TaskOutput object or string)
        agent_id: Identifier for the crew/agent
        task: Optional task name/description
        context: Optional context (user_id, session_id, etc.)
    
    Returns:
        SignResult with envelope and enterprise info
    
    Example:
        from moss_crewai import sign_task_output
        
        result = crew.kickoff()
        for task_output in result.tasks_output:
            signed = sign_task_output(task_output, agent_id="research-crew", task="research")
    """
    payload = _extract_task_payload(output)
    if task:
        payload["task"] = task
    
    action = f"task:{task}" if task else "task_output"
    
    return sign(
        output=payload,
        agent_id=agent_id,
        action=action,
        context=context,
    )


async def sign_task_output_async(
    output: Any,
    agent_id: str,
    *,
    task: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_task_output."""
    payload = _extract_task_payload(output)
    if task:
        payload["task"] = task
    
    action = f"task:{task}" if task else "task_output"
    
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action=action,
        context=context,
    )


def sign_agent_output(
    output: Any,
    agent_id: str,
    *,
    agent_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign a CrewAI agent output.
    
    Args:
        output: Agent output
        agent_id: Identifier for the crew
        agent_name: Name of the specific agent
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    """
    payload = _extract_agent_payload(output)
    if agent_name:
        payload["agent_name"] = agent_name
    
    action = f"agent:{agent_name}" if agent_name else "agent_output"
    
    return sign(
        output=payload,
        agent_id=agent_id,
        action=action,
        context=context,
    )


async def sign_agent_output_async(
    output: Any,
    agent_id: str,
    *,
    agent_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_agent_output."""
    payload = _extract_agent_payload(output)
    if agent_name:
        payload["agent_name"] = agent_name
    
    action = f"agent:{agent_name}" if agent_name else "agent_output"
    
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action=action,
        context=context,
    )


def sign_crew_result(
    result: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign a CrewAI crew result (full kickoff output).
    
    Args:
        result: CrewOutput from crew.kickoff()
        agent_id: Identifier for the crew
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    
    Example:
        from moss_crewai import sign_crew_result
        
        result = crew.kickoff()
        signed = sign_crew_result(result, agent_id="research-crew")
    """
    payload = _extract_crew_payload(result)
    
    return sign(
        output=payload,
        agent_id=agent_id,
        action="crew_result",
        context=context,
    )


async def sign_crew_result_async(
    result: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_crew_result."""
    payload = _extract_crew_payload(result)
    
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action="crew_result",
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
