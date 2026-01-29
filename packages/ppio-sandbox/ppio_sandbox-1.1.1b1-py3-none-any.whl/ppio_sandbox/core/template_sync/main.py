from typing import Optional, List
from typing_extensions import Unpack

from httpx import Limits

from ppio_sandbox.core.connection_config import ConnectionConfig, ApiParams
from ppio_sandbox.core.api import ApiClient
from ppio_sandbox.core.api.client.models import (
    Error,
    PaginatedTemplatesResponse,
    Template as TemplateModel,
)
from ppio_sandbox.core.api.client.api.templates import (
    get_v2_templates,
    delete_templates_template_id,
)
from ppio_sandbox.core.exceptions import SandboxException
from ppio_sandbox.core.api import handle_api_exception


class TemplateInfo:
    """Template information wrapper"""
    
    def __init__(self, template_model: TemplateModel):
        self._model = template_model
    
    @property
    def template_id(self) -> str:
        """Template ID"""
        return self._model.template_id
    
    @property
    def build_id(self) -> str:
        """Build ID"""
        return self._model.build_id
    
    @property
    def cpu_count(self) -> int:
        """CPU count"""
        return self._model.cpu_count
    
    @property
    def memory_mb(self) -> int:
        """Memory in MB"""
        return self._model.memory_mb
    
    @property
    def disk_size_mb(self) -> int:
        """Disk size in MB"""
        return self._model.disk_size_mb
    
    @property
    def envd_version(self) -> str:
        """Envd version"""
        return self._model.envd_version
    
    @property
    def public(self) -> bool:
        """Whether the template is public"""
        return self._model.public
    
    @property
    def aliases(self) -> List[str]:
        """Template aliases"""
        from ppio_sandbox.core.api.client.types import UNSET, Unset
        if isinstance(self._model.aliases, Unset):
            return []
        return self._model.aliases or []
    
    @property
    def spawn_count(self) -> int:
        """Spawn count"""
        return self._model.spawn_count
    
    @property
    def build_count(self) -> int:
        """Build count"""
        return self._model.build_count
    
    def __repr__(self) -> str:
        return f"TemplateInfo(template_id={self.template_id!r}, aliases={self.aliases!r})"


class TemplateList:
    """Template list response wrapper"""
    
    def __init__(self, response: PaginatedTemplatesResponse):
        self._response = response
        self._templates = [TemplateInfo(t) for t in response.templates]
    
    @property
    def items(self) -> List[TemplateInfo]:
        """List of templates"""
        return self._templates
    
    @property
    def total(self) -> int:
        """Total number of templates"""
        return self._response.total
    
    @property
    def page(self) -> int:
        """Current page number (1-based)"""
        return self._response.page
    
    @property
    def limit(self) -> int:
        """Number of items per page"""
        return self._response.limit
    
    @property
    def total_pages(self) -> int:
        """Total number of pages"""
        return self._response.total_pages
    
    def __iter__(self):
        return iter(self._templates)
    
    def __len__(self) -> int:
        return len(self._templates)
    
    def __getitem__(self, index: int) -> TemplateInfo:
        return self._templates[index]
    
    def __repr__(self) -> str:
        return f"TemplateList(total={self.total}, page={self.page}/{self.total_pages}, items={len(self._templates)})"


class Template:
    """
    Template API for listing and managing sandbox templates.
    
    Example:
    ```python
    from ppio_sandbox.core import Template
    
    # List all templates
    templates = Template.list()
    for template in templates.items:
        print(f"Template: {template.template_id}, Aliases: {template.aliases}")
    
    # List snapshot templates with pagination
    templates = Template.list(template_type="snapshot_template", page=1, limit=10)
    print(f"Total: {templates.total}, Page: {templates.page}/{templates.total_pages}")
    
    # Delete a template
    Template.delete(template_id="my-template-id")
    ```
    """
    
    _limits = Limits(
        max_keepalive_connections=40,
        max_connections=40,
        keepalive_expiry=300,
    )
    
    @staticmethod
    def list(
        template_type: str = "template_build",
        page: int = 1,
        limit: int = 20,
        **opts: Unpack[ApiParams],
    ) -> TemplateList:
        """
        List templates with pagination support.
        
        :param template_type: Filter templates by type. Defaults to "template_build".
            - "template_build": Include only original templates built from Dockerfile
            - "snapshot_template": Include only templates generated from snapshots/commits
        :param page: Page number (1-based). Defaults to 1.
        :param limit: Number of items per page (1-100). Defaults to 20.
        :return: TemplateList containing templates and pagination info
        
        Example:
        ```python
        # List all build templates
        templates = Template.list()
        
        # List snapshot templates
        templates = Template.list(template_type="snapshot_template")
        
        # With pagination
        templates = Template.list(page=2, limit=50)
        ```
        """
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        
        if page < 1:
            raise ValueError("page must be >= 1")
        
        if template_type not in ["template_build", "snapshot_template"]:
            raise ValueError("template_type must be 'template_build' or 'snapshot_template'")
        
        config = ConnectionConfig(**opts)
        
        with ApiClient(config, limits=Template._limits) as api_client:
            res = get_v2_templates.sync_detailed(
                client=api_client,
                template_type=template_type,
                page=page,
                limit=limit,
            )
            
            # Handle error responses with server-provided messages when available
            if res.status_code >= 300:
                error_message = None
                
                # Try to get error message from parsed response
                if isinstance(res.parsed, Error):
                    error_message = res.parsed.message
                
                # Use server message or fallback to generic error handler
                if error_message:
                    raise SandboxException(error_message)
                else:
                    raise handle_api_exception(res)
            
            if res.parsed is None:
                raise SandboxException("Body of the request is None")
            
            return TemplateList(res.parsed)
    
    @staticmethod
    def delete(
        template_id: str,
        **opts: Unpack[ApiParams],
    ) -> None:
        """
        Delete a template by ID.
        
        :param template_id: Template ID to delete
        :raises SandboxException: If the deletion fails
        
        Example:
        ```python
        # Delete a template
        Template.delete(template_id="my-template-id")
        
        # With custom API key
        Template.delete(
            template_id="my-template-id",
            api_key="your-api-key"
        )
        ```
        """
        if not template_id:
            raise ValueError("template_id cannot be empty")
        
        config = ConnectionConfig(**opts)
        
        with ApiClient(config, limits=Template._limits) as api_client:
            res = delete_templates_template_id.sync_detailed(
                template_id=template_id,
                client=api_client,
            )
            
            # Handle error responses with server-provided messages when available
            if res.status_code >= 300:
                error_message = None
                
                # Try to get error message from parsed response
                if isinstance(res.parsed, Error):
                    error_message = res.parsed.message
                
                # Use server message or fallback to generic error handler
                if error_message:
                    raise SandboxException(error_message)
                else:
                    raise handle_api_exception(res)


