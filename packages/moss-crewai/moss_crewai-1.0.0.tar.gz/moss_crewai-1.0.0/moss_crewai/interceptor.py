"""
MOSS CrewAI Integration - Automatic Output Signing

Usage:
    from moss_crewai import enable_moss
    enable_moss()
    
    # All CrewAI task outputs and tool calls are now signed
"""

from functools import wraps
import os

from moss import Subject
from moss.errors import KeyNotFound


def _get_or_create_subject(subject_id: str) -> Subject:
    """Load existing subject or create new one."""
    try:
        return Subject.load(subject_id)
    except KeyNotFound:
        return Subject.create(subject_id)


_moss_enabled = False
_subject_prefix = "moss:crewai"


def enable_moss(subject_prefix: str = "moss:crewai"):
    """
    Enable MOSS signing for all CrewAI operations.

    Args:
        subject_prefix: Prefix for agent subjects (e.g., "moss:crewai:researcher")
    """
    global _moss_enabled, _subject_prefix

    if _moss_enabled:
        return

    _subject_prefix = subject_prefix

    try:
        from crewai import Agent, Crew
    except ImportError:
        raise ImportError("CrewAI not installed. Run: pip install crewai")

    # Patch Agent.execute_task
    if hasattr(Agent, 'execute_task'):
        original_execute = Agent.execute_task

        @wraps(original_execute)
        def signed_execute(self, task, context=None, tools=None):
            role_slug = getattr(self, 'role', 'agent').lower().replace(' ', '-')
            subject_id = f"{subject_prefix}:{role_slug}"
            subject = _get_or_create_subject(subject_id)

            # Sign task start
            subject.sign({
                "type": "task_start",
                "task_description": str(getattr(task, 'description', task)),
                "context": str(context) if context else None,
                "agent_role": getattr(self, 'role', 'unknown'),
            })

            try:
                result = original_execute(self, task, context, tools)
            except Exception as e:
                subject.sign({
                    "type": "task_error",
                    "error": str(e),
                    "task": str(getattr(task, 'description', task)),
                })
                raise

            # Sign task completion
            envelope = subject.sign({
                "type": "task_complete",
                "task_description": str(getattr(task, 'description', task)),
                "output": str(result),
            })

            # Store envelope on agent
            self._moss_envelope = envelope
            return result

        Agent.execute_task = signed_execute

    # Patch Crew.kickoff
    if hasattr(Crew, 'kickoff'):
        original_kickoff = Crew.kickoff

        @wraps(original_kickoff)
        def signed_kickoff(self, inputs=None):
            subject_id = f"{subject_prefix}:crew"
            subject = _get_or_create_subject(subject_id)

            # Sign crew start
            agents = getattr(self, 'agents', [])
            tasks = getattr(self, 'tasks', [])
            subject.sign({
                "type": "crew_start",
                "agents": [getattr(a, 'role', str(a)) for a in agents],
                "tasks": [str(getattr(t, 'description', t)) for t in tasks],
                "inputs": str(inputs) if inputs else None,
            })

            try:
                result = original_kickoff(self, inputs)
            except Exception as e:
                subject.sign({
                    "type": "crew_error",
                    "error": str(e),
                })
                raise

            # Sign crew completion
            envelope = subject.sign({
                "type": "crew_complete",
                "output": str(result),
            })

            # Store envelope on crew
            self._moss_envelope = envelope
            return result

        Crew.kickoff = signed_kickoff

    # Try to patch CrewAI tools
    try:
        from crewai.tools import BaseTool as CrewAIBaseTool

        if hasattr(CrewAIBaseTool, '_run'):
            original_tool_run = CrewAIBaseTool._run

            @wraps(original_tool_run)
            def signed_tool_run(self, *args, **kwargs):
                tool_name = getattr(self, 'name', 'unknown')
                subject_id = f"{subject_prefix}:tool-{tool_name}"
                subject = _get_or_create_subject(subject_id)

                subject.sign({
                    "type": "tool_input",
                    "tool": tool_name,
                    "args": str(args),
                    "kwargs": str(kwargs),
                })

                try:
                    result = original_tool_run(self, *args, **kwargs)
                except Exception as e:
                    subject.sign({
                        "type": "tool_error",
                        "tool": tool_name,
                        "error": str(e),
                    })
                    raise

                envelope = subject.sign({
                    "type": "tool_output",
                    "tool": tool_name,
                    "output": str(result),
                })

                self._moss_envelope = envelope
                return result

            CrewAIBaseTool._run = signed_tool_run
    except ImportError:
        pass  # CrewAI tools not available

    _moss_enabled = True
    print(f"MOSS: CrewAI signing enabled with prefix '{subject_prefix}'")


def disable_moss():
    """
    Disable MOSS auto-signing (for testing).
    Note: Already-patched classes remain patched.
    """
    global _moss_enabled
    _moss_enabled = False


def is_enabled() -> bool:
    """Check if MOSS auto-signing is enabled."""
    return _moss_enabled


# Auto-enable on import if MOSS_AUTO_ENABLE is set
if os.environ.get("MOSS_AUTO_ENABLE", "").lower() in ("1", "true", "yes"):
    enable_moss()
