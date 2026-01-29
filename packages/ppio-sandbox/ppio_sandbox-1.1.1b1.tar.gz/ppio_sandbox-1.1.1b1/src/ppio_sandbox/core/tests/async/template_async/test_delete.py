import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from ppio_sandbox.core import AsyncTemplate
from ppio_sandbox.core.exceptions import SandboxException


@pytest.mark.skip_debug()
@pytest.mark.asyncio
async def test_async_delete_success():
    """Test successful async template deletion"""
    # This test requires a real template ID to test against
    # In a real environment, you would create a template first, then delete it
    # For now, we'll skip this test in debug mode
    
    # Example usage (commented out to prevent accidental deletions):
    # template_id = "test-template-id"
    # await AsyncTemplate.delete(template_id=template_id)
    pass


@pytest.mark.asyncio
async def test_async_delete_empty_template_id():
    """Test async delete with empty template_id"""
    with pytest.raises(ValueError, match="template_id cannot be empty"):
        await AsyncTemplate.delete(template_id="")


@pytest.mark.asyncio
async def test_async_delete_none_template_id():
    """Test async delete with None template_id"""
    with pytest.raises(ValueError, match="template_id cannot be empty"):
        await AsyncTemplate.delete(template_id=None)


@pytest.mark.asyncio
@patch("ppio_sandbox.core.template_async.main.AsyncApiClient")
async def test_async_delete_with_mock_success(mock_async_api_client_class):
    """Test async delete with mocked API client - success case"""
    # Setup mock
    mock_client = MagicMock()
    mock_async_api_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_async_api_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
    
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.parsed = None
    
    with patch("ppio_sandbox.core.template_async.main.delete_templates_template_id.asyncio_detailed", new_callable=AsyncMock, return_value=mock_response):
        # Should not raise any exception
        await AsyncTemplate.delete(template_id="test-template-id")


@pytest.mark.asyncio
@patch("ppio_sandbox.core.template_async.main.AsyncApiClient")
async def test_async_delete_with_mock_401_error(mock_async_api_client_class):
    """Test async delete with mocked API client - 401 unauthorized"""
    # Setup mock
    mock_client = MagicMock()
    mock_async_api_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_async_api_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
    
    # Mock error response
    mock_response = MagicMock()
    mock_response.status_code = 401
    
    with patch("ppio_sandbox.core.template_async.main.delete_templates_template_id.asyncio_detailed", new_callable=AsyncMock, return_value=mock_response):
        with patch("ppio_sandbox.core.template_async.main.handle_api_exception") as mock_handle:
            mock_handle.return_value = SandboxException("Unauthorized")
            
            with pytest.raises(SandboxException):
                await AsyncTemplate.delete(template_id="test-template-id")


@pytest.mark.asyncio
@patch("ppio_sandbox.core.template_async.main.AsyncApiClient")
async def test_async_delete_with_mock_500_error(mock_async_api_client_class):
    """Test async delete with mocked API client - 500 server error"""
    # Setup mock
    mock_client = MagicMock()
    mock_async_api_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_async_api_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
    
    # Mock error response
    mock_response = MagicMock()
    mock_response.status_code = 500
    
    with patch("ppio_sandbox.core.template_async.main.delete_templates_template_id.asyncio_detailed", new_callable=AsyncMock, return_value=mock_response):
        with patch("ppio_sandbox.core.template_async.main.handle_api_exception") as mock_handle:
            mock_handle.return_value = SandboxException("Server error")
            
            with pytest.raises(SandboxException):
                await AsyncTemplate.delete(template_id="test-template-id")


@pytest.mark.asyncio
@patch("ppio_sandbox.core.template_async.main.AsyncApiClient")
async def test_async_delete_with_custom_api_key(mock_async_api_client_class):
    """Test async delete with custom API key"""
    # Setup mock
    mock_client = MagicMock()
    mock_async_api_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_async_api_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
    
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.parsed = None
    
    with patch("ppio_sandbox.core.template_async.main.delete_templates_template_id.asyncio_detailed", new_callable=AsyncMock, return_value=mock_response):
        # Should not raise any exception
        await AsyncTemplate.delete(template_id="test-template-id", api_key="custom-api-key")

