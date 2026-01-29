import pytest
from unittest.mock import patch, MagicMock

from ppio_sandbox.core import Template
from ppio_sandbox.core.exceptions import SandboxException


@pytest.mark.skip_debug()
def test_delete_success():
    """Test successful template deletion"""
    # This test requires a real template ID to test against
    # In a real environment, you would create a template first, then delete it
    # For now, we'll skip this test in debug mode
    
    # Example usage (commented out to prevent accidental deletions):
    template_id = "ztw2gap810df89k3khqx"
    Template.delete(template_id=template_id)
    pass


def test_delete_empty_template_id():
    """Test delete with empty template_id"""
    with pytest.raises(ValueError, match="template_id cannot be empty"):
        Template.delete(template_id="")


def test_delete_none_template_id():
    """Test delete with None template_id"""
    with pytest.raises(ValueError, match="template_id cannot be empty"):
        Template.delete(template_id=None)


@patch("ppio_sandbox.core.template_sync.main.ApiClient")
def test_delete_with_mock_success(mock_api_client_class):
    """Test delete with mocked API client - success case"""
    # Setup mock
    mock_client = MagicMock()
    mock_api_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
    mock_api_client_class.return_value.__exit__ = MagicMock(return_value=None)
    
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.parsed = None
    
    with patch("ppio_sandbox.core.template_sync.main.delete_templates_template_id.sync_detailed", return_value=mock_response):
        # Should not raise any exception
        Template.delete(template_id="test-template-id")


@patch("ppio_sandbox.core.template_sync.main.ApiClient")
def test_delete_with_mock_401_error(mock_api_client_class):
    """Test delete with mocked API client - 401 unauthorized"""
    # Setup mock
    mock_client = MagicMock()
    mock_api_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
    mock_api_client_class.return_value.__exit__ = MagicMock(return_value=None)
    
    # Mock error response
    mock_response = MagicMock()
    mock_response.status_code = 401
    
    with patch("ppio_sandbox.core.template_sync.main.delete_templates_template_id.sync_detailed", return_value=mock_response):
        with patch("ppio_sandbox.core.template_sync.main.handle_api_exception") as mock_handle:
            mock_handle.return_value = SandboxException("Unauthorized")
            
            with pytest.raises(SandboxException):
                Template.delete(template_id="test-template-id")


@patch("ppio_sandbox.core.template_sync.main.ApiClient")
def test_delete_with_mock_500_error(mock_api_client_class):
    """Test delete with mocked API client - 500 server error"""
    # Setup mock
    mock_client = MagicMock()
    mock_api_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
    mock_api_client_class.return_value.__exit__ = MagicMock(return_value=None)
    
    # Mock error response
    mock_response = MagicMock()
    mock_response.status_code = 500
    
    with patch("ppio_sandbox.core.template_sync.main.delete_templates_template_id.sync_detailed", return_value=mock_response):
        with patch("ppio_sandbox.core.template_sync.main.handle_api_exception") as mock_handle:
            mock_handle.return_value = SandboxException("Server error")
            
            with pytest.raises(SandboxException):
                Template.delete(template_id="test-template-id")


@patch("ppio_sandbox.core.template_sync.main.ApiClient")
def test_delete_with_custom_api_key(mock_api_client_class):
    """Test delete with custom API key"""
    # Setup mock
    mock_client = MagicMock()
    mock_api_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
    mock_api_client_class.return_value.__exit__ = MagicMock(return_value=None)
    
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.parsed = None
    
    with patch("ppio_sandbox.core.template_sync.main.delete_templates_template_id.sync_detailed", return_value=mock_response):
        # Should not raise any exception
        Template.delete(template_id="test-template-id", api_key="custom-api-key")

