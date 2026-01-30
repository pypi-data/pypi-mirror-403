"""Tests for moss-crewai signing functions."""

import pytest
from unittest.mock import MagicMock

from moss_crewai import (
    sign_task_output,
    sign_agent_output,
    sign_crew_result,
    verify_envelope,
    SignResult,
)


class TestSignTaskOutput:
    """Test sign_task_output function."""
    
    def test_sign_task_output_dict(self):
        """Sign a task output from dict."""
        output = {
            "raw": "Task completed successfully",
            "description": "Research task",
        }
        
        result = sign_task_output(output, agent_id="research-crew")
        
        assert isinstance(result, SignResult)
        assert result.payload["type"] == "task_output"
        assert result.payload["raw"] == "Task completed successfully"
    
    def test_sign_task_output_string(self):
        """Sign a string task output."""
        result = sign_task_output(
            "Task complete",
            agent_id="research-crew",
        )
        
        assert result.payload["type"] == "task_output"
        assert result.payload["output"] == "Task complete"
    
    def test_sign_task_output_with_task_name(self):
        """Sign task output with task name."""
        result = sign_task_output(
            {"result": "done"},
            agent_id="research-crew",
            task="research_task",
        )
        
        assert result.payload["task"] == "research_task"
    
    def test_sign_task_output_object(self):
        """Sign a TaskOutput object."""
        task_output = MagicMock()
        task_output.raw = "Analysis complete"
        task_output.pydantic = None
        task_output.json_dict = {"score": 0.95}
        
        result = sign_task_output(task_output, agent_id="analysis-crew")
        
        assert result.payload["raw"] == "Analysis complete"
    
    def test_sign_task_output_with_context(self):
        """Sign task output with context."""
        result = sign_task_output(
            {"data": "test"},
            agent_id="research-crew",
            context={"user_id": "u123"},
        )
        
        assert result.payload.get("_context") == {"user_id": "u123"}


class TestSignAgentOutput:
    """Test sign_agent_output function."""
    
    def test_sign_agent_output_dict(self):
        """Sign an agent output from dict."""
        output = {"message": "I found the answer"}
        
        result = sign_agent_output(output, agent_id="research-crew")
        
        assert result.payload["type"] == "agent_output"
        assert result.payload["message"] == "I found the answer"
    
    def test_sign_agent_output_with_name(self):
        """Sign agent output with agent name."""
        result = sign_agent_output(
            {"action": "search"},
            agent_id="research-crew",
            agent_name="researcher",
        )
        
        assert result.payload["agent_name"] == "researcher"
    
    def test_sign_agent_output_string(self):
        """Sign a string agent output."""
        result = sign_agent_output(
            "Search complete",
            agent_id="research-crew",
        )
        
        assert result.payload["output"] == "Search complete"


class TestSignCrewResult:
    """Test sign_crew_result function."""
    
    def test_sign_crew_result_dict(self):
        """Sign a crew result from dict."""
        crew_result = {
            "raw": "Final report complete",
            "task_outputs": [{"task": "research"}, {"task": "write"}],
        }
        
        result = sign_crew_result(crew_result, agent_id="research-crew")
        
        assert result.payload["type"] == "crew_result"
        assert result.payload["raw"] == "Final report complete"
    
    def test_sign_crew_result_string(self):
        """Sign a string crew result."""
        result = sign_crew_result(
            "All tasks completed",
            agent_id="research-crew",
        )
        
        assert result.payload["type"] == "crew_result"
        assert result.payload["output"] == "All tasks completed"
    
    def test_sign_crew_result_object(self):
        """Sign a CrewOutput object."""
        task1 = MagicMock()
        task1.raw = "Task 1 done"
        task1.pydantic = None
        task1.json_dict = None
        
        crew_output = MagicMock()
        crew_output.raw = "Crew finished"
        crew_output.tasks_output = [task1]
        
        result = sign_crew_result(crew_output, agent_id="research-crew")
        
        assert result.payload["raw"] == "Crew finished"
    
    def test_sign_crew_result_with_context(self):
        """Sign crew result with context."""
        result = sign_crew_result(
            {"final": "report"},
            agent_id="research-crew",
            context={"project_id": "p123"},
        )
        
        assert result.payload.get("_context") == {"project_id": "p123"}


class TestVerifyEnvelope:
    """Test verify_envelope function."""
    
    def test_verify_signed_envelope(self):
        """Verify a signed envelope."""
        sign_result = sign_task_output("test output", agent_id="test-crew")
        
        verify_result = verify_envelope(sign_result.envelope)
        
        assert verify_result.valid is True
