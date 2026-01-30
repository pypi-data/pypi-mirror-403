"""
MOSS CrewAI Integration - Cryptographic Signing for CrewAI

Sign task outputs, agent outputs, and crew results explicitly.

Quick Start:
    from crewai import Crew, Agent, Task
    from moss_crewai import sign_task_output, sign_crew_result
    
    crew = Crew(agents=[...], tasks=[...])
    result = crew.kickoff()
    
    # Sign the crew result
    signed = sign_crew_result(result, agent_id="research-crew")
    
    # Or sign individual task outputs
    for task_output in result.tasks_output:
        sign_task_output(task_output, agent_id="research-crew")

Enterprise Mode:
    Set MOSS_API_KEY for policy evaluation and evidence retention.
"""

__version__ = "0.2.0"

# Explicit signing (recommended)
from .signing import (
    sign_task_output,
    sign_task_output_async,
    sign_agent_output,
    sign_agent_output_async,
    sign_crew_result,
    sign_crew_result_async,
    verify_envelope,
)

# Core types
from moss import SignResult, VerifyResult, Envelope, enterprise_enabled

# Legacy (backwards compatibility)
from .wrapper import moss_wrap
from .interceptor import enable_moss, disable_moss, is_enabled

__all__ = [
    # Explicit signing
    "sign_task_output",
    "sign_task_output_async",
    "sign_agent_output",
    "sign_agent_output_async",
    "sign_crew_result",
    "sign_crew_result_async",
    "verify_envelope",
    
    # Core types
    "SignResult",
    "VerifyResult",
    "Envelope",
    "enterprise_enabled",
    
    # Legacy
    "moss_wrap",
    "enable_moss",
    "disable_moss",
    "is_enabled",
]
