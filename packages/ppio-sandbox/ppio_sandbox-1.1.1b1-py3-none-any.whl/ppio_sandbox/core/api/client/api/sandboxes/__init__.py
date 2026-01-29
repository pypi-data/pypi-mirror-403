"""Contains endpoint functions for accessing the API"""

from .delete_sandboxes_sandbox_id import (
    asyncio as delete_sandboxes_sandbox_id_asyncio,
    asyncio_detailed as delete_sandboxes_sandbox_id_asyncio_detailed,
    sync as delete_sandboxes_sandbox_id_sync,
    sync_detailed as delete_sandboxes_sandbox_id_sync_detailed,
)
from .get_sandboxes import (
    asyncio as get_sandboxes_asyncio,
    asyncio_detailed as get_sandboxes_asyncio_detailed,
    sync as get_sandboxes_sync,
    sync_detailed as get_sandboxes_sync_detailed,
)
from .get_sandboxes_metrics import (
    asyncio as get_sandboxes_metrics_asyncio,
    asyncio_detailed as get_sandboxes_metrics_asyncio_detailed,
    sync as get_sandboxes_metrics_sync,
    sync_detailed as get_sandboxes_metrics_sync_detailed,
)
from .get_sandboxes_sandbox_id import (
    asyncio as get_sandboxes_sandbox_id_asyncio,
    asyncio_detailed as get_sandboxes_sandbox_id_asyncio_detailed,
    sync as get_sandboxes_sandbox_id_sync,
    sync_detailed as get_sandboxes_sandbox_id_sync_detailed,
)
from .get_sandboxes_sandbox_id_logs import (
    asyncio as get_sandboxes_sandbox_id_logs_asyncio,
    asyncio_detailed as get_sandboxes_sandbox_id_logs_asyncio_detailed,
    sync as get_sandboxes_sandbox_id_logs_sync,
    sync_detailed as get_sandboxes_sandbox_id_logs_sync_detailed,
)
from .get_sandboxes_sandbox_id_metrics import (
    asyncio as get_sandboxes_sandbox_id_metrics_asyncio,
    asyncio_detailed as get_sandboxes_sandbox_id_metrics_asyncio_detailed,
    sync as get_sandboxes_sandbox_id_metrics_sync,
    sync_detailed as get_sandboxes_sandbox_id_metrics_sync_detailed,
)
from .get_v2_sandboxes import (
    asyncio as get_v2_sandboxes_asyncio,
    asyncio_detailed as get_v2_sandboxes_asyncio_detailed,
    sync as get_v2_sandboxes_sync,
    sync_detailed as get_v2_sandboxes_sync_detailed,
)
from .post_sandboxes import (
    asyncio as post_sandboxes_asyncio,
    asyncio_detailed as post_sandboxes_asyncio_detailed,
    sync as post_sandboxes_sync,
    sync_detailed as post_sandboxes_sync_detailed,
)
from .post_sandboxes_sandbox_id_commit import (
    asyncio as post_sandboxes_sandbox_id_commit_asyncio,
    asyncio_detailed as post_sandboxes_sandbox_id_commit_asyncio_detailed,
    sync as post_sandboxes_sandbox_id_commit_sync,
    sync_detailed as post_sandboxes_sandbox_id_commit_sync_detailed,
)
from .post_sandboxes_sandbox_id_pause import (
    asyncio as post_sandboxes_sandbox_id_pause_asyncio,
    asyncio_detailed as post_sandboxes_sandbox_id_pause_asyncio_detailed,
    sync as post_sandboxes_sandbox_id_pause_sync,
    sync_detailed as post_sandboxes_sandbox_id_pause_sync_detailed,
)
from .post_sandboxes_sandbox_id_refreshes import (
    asyncio as post_sandboxes_sandbox_id_refreshes_asyncio,
    asyncio_detailed as post_sandboxes_sandbox_id_refreshes_asyncio_detailed,
    sync as post_sandboxes_sandbox_id_refreshes_sync,
    sync_detailed as post_sandboxes_sandbox_id_refreshes_sync_detailed,
)
from .post_sandboxes_sandbox_id_resume import (
    asyncio as post_sandboxes_sandbox_id_resume_asyncio,
    asyncio_detailed as post_sandboxes_sandbox_id_resume_asyncio_detailed,
    sync as post_sandboxes_sandbox_id_resume_sync,
    sync_detailed as post_sandboxes_sandbox_id_resume_sync_detailed,
)
from .post_sandboxes_sandbox_id_timeout import (
    asyncio as post_sandboxes_sandbox_id_timeout_asyncio,
    asyncio_detailed as post_sandboxes_sandbox_id_timeout_asyncio_detailed,
    sync as post_sandboxes_sandbox_id_timeout_sync,
    sync_detailed as post_sandboxes_sandbox_id_timeout_sync_detailed,
)