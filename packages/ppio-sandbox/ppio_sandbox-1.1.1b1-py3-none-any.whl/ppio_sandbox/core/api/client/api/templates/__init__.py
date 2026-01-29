"""Contains endpoint functions for accessing the API"""

from .get_v2_templates import (
    asyncio as get_v2_templates_asyncio,
    asyncio_detailed as get_v2_templates_asyncio_detailed,
    sync as get_v2_templates_sync,
    sync_detailed as get_v2_templates_sync_detailed,
)
from .delete_templates_template_id import (
    asyncio as delete_templates_template_id_asyncio,
    asyncio_detailed as delete_templates_template_id_asyncio_detailed,
    sync as delete_templates_template_id_sync,
    sync_detailed as delete_templates_template_id_sync_detailed,
)

