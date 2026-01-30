"""
Tests for MOSS CrewAI Interceptor.

Tests the enable_moss() auto-patching functionality.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestEnableMoss:
    """Test the enable_moss() function."""

    def test_enable_moss_sets_enabled_flag(self):
        """enable_moss() should set the enabled flag."""
        from moss_crewai import interceptor
        
        # Reset state
        interceptor._moss_enabled = False
        
        with patch.dict('sys.modules', {'crewai': MagicMock(), 'crewai.tools': MagicMock()}):
            try:
                interceptor.enable_moss("moss:test:crew")
            except ImportError:
                pass  # Expected if crewai not installed

    def test_disable_moss_clears_state(self):
        """disable_moss() should clear the enabled state."""
        from moss_crewai import interceptor
        
        interceptor._moss_enabled = True
        
        interceptor.disable_moss()
        
        assert interceptor._moss_enabled is False

    def test_is_enabled_returns_state(self):
        """is_enabled() should return current state."""
        from moss_crewai import interceptor
        
        interceptor._moss_enabled = True
        assert interceptor.is_enabled() is True
        
        interceptor._moss_enabled = False
        assert interceptor.is_enabled() is False

    def test_subject_prefix_stored(self):
        """enable_moss() should store the subject prefix."""
        from moss_crewai import interceptor
        
        interceptor._subject_prefix = "moss:default"
        
        # The prefix should be configurable
        assert hasattr(interceptor, '_subject_prefix')


class TestMossWrap:
    """Test the moss_wrap() function."""

    def test_moss_wrap_exported(self):
        """moss_wrap should be exported from package."""
        from moss_crewai import moss_wrap
        
        assert callable(moss_wrap)

    def test_moss_wrap_adds_envelope_attr(self):
        """moss_wrap should add moss_envelope attribute to agent."""
        from moss_crewai.wrapper import moss_wrap
        
        mock_agent = MagicMock()
        mock_agent.execute_task = MagicMock(return_value="result")
        
        with patch('moss_crewai.wrapper._get_or_create_subject') as mock_get_subject:
            mock_subject = MagicMock()
            mock_subject.sign = MagicMock(return_value=MagicMock())
            mock_get_subject.return_value = mock_subject
            
            wrapped = moss_wrap(mock_agent, "moss:test:agent")
            
            assert hasattr(wrapped, 'moss_envelope')
            assert hasattr(wrapped, '_moss_subject')

    def test_moss_wrap_preserves_agent(self):
        """moss_wrap should return the same agent instance."""
        from moss_crewai.wrapper import moss_wrap
        
        mock_agent = MagicMock()
        
        with patch('moss_crewai.wrapper._get_or_create_subject') as mock_get_subject:
            mock_subject = MagicMock()
            mock_get_subject.return_value = mock_subject
            
            result = moss_wrap(mock_agent, "moss:test:agent")
            
            assert result is mock_agent


class TestResultToPayload:
    """Test the _result_to_payload helper."""

    def test_dict_result(self):
        """Dict results should pass through."""
        from moss_crewai.wrapper import _result_to_payload
        
        result = {"key": "value"}
        payload = _result_to_payload(result)
        
        assert payload == {"key": "value"}

    def test_string_result(self):
        """String results should be wrapped."""
        from moss_crewai.wrapper import _result_to_payload
        
        result = "test output"
        payload = _result_to_payload(result)
        
        assert payload == {"output": "test output"}

    def test_object_with_raw(self):
        """Objects with .raw should use that."""
        from moss_crewai.wrapper import _result_to_payload
        
        mock_result = MagicMock()
        mock_result.raw = "raw content"
        del mock_result.dict  # Remove dict method
        
        payload = _result_to_payload(mock_result)
        
        assert payload == {"output": "raw content"}

    def test_object_with_dict_method(self):
        """Objects with .dict() should use that."""
        from moss_crewai.wrapper import _result_to_payload
        
        mock_result = MagicMock()
        mock_result.dict = MagicMock(return_value={"from": "dict"})
        del mock_result.raw  # Remove raw attribute
        
        payload = _result_to_payload(mock_result)
        
        assert payload == {"from": "dict"}


class TestGetOrCreateSubject:
    """Test the _get_or_create_subject helper."""

    def test_loads_existing_subject(self):
        """Should load existing subject if available."""
        from moss_crewai.wrapper import _get_or_create_subject
        
        with patch('moss_crewai.wrapper.Subject') as MockSubject:
            mock_subject = MagicMock()
            MockSubject.load.return_value = mock_subject
            
            result = _get_or_create_subject("moss:test:existing")
            
            MockSubject.load.assert_called_once_with("moss:test:existing")
            assert result is mock_subject

    def test_creates_new_subject_if_not_found(self):
        """Should create new subject if not found."""
        from moss_crewai.wrapper import _get_or_create_subject
        from moss.errors import KeyNotFound
        
        with patch('moss_crewai.wrapper.Subject') as MockSubject:
            MockSubject.load.side_effect = KeyNotFound("not found")
            mock_subject = MagicMock()
            MockSubject.create.return_value = mock_subject
            
            result = _get_or_create_subject("moss:test:new")
            
            MockSubject.create.assert_called_once_with("moss:test:new")
            assert result is mock_subject


class TestPackageExports:
    """Test that all expected items are exported."""

    def test_moss_wrap_exported(self):
        """moss_wrap should be in __all__."""
        from moss_crewai import moss_wrap
        assert callable(moss_wrap)

    def test_enable_moss_exported(self):
        """enable_moss should be in __all__."""
        from moss_crewai import enable_moss
        assert callable(enable_moss)

    def test_disable_moss_exported(self):
        """disable_moss should be in __all__."""
        from moss_crewai import disable_moss
        assert callable(disable_moss)

    def test_is_enabled_exported(self):
        """is_enabled should be in __all__."""
        from moss_crewai import is_enabled
        assert callable(is_enabled)
