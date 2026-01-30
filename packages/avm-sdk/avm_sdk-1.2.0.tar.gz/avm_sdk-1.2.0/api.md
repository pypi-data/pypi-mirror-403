# Sandboxes

Types:

```python
from sandbox_sdk.types import (
    Pagination,
    Sandbox,
    SandboxCreateResponse,
    SandboxListResponse,
    SandboxDeleteResponse,
    SandboxDeleteAllResponse,
    SandboxExecuteResponse,
    SandboxUploadResponse,
)
```

Methods:

- <code title="post /v1/sandboxes/create">client.sandboxes.<a href="./src/sandbox_sdk/resources/sandboxes.py">create</a>(\*\*<a href="src/sandbox_sdk/types/sandbox_create_params.py">params</a>) -> <a href="./src/sandbox_sdk/types/sandbox_create_response.py">SandboxCreateResponse</a></code>
- <code title="get /v1/sandboxes/list">client.sandboxes.<a href="./src/sandbox_sdk/resources/sandboxes.py">list</a>(\*\*<a href="src/sandbox_sdk/types/sandbox_list_params.py">params</a>) -> <a href="./src/sandbox_sdk/types/sandbox_list_response.py">SandboxListResponse</a></code>
- <code title="delete /v1/sandboxes/{id}/delete">client.sandboxes.<a href="./src/sandbox_sdk/resources/sandboxes.py">delete</a>(id, \*\*<a href="src/sandbox_sdk/types/sandbox_delete_params.py">params</a>) -> <a href="./src/sandbox_sdk/types/sandbox_delete_response.py">SandboxDeleteResponse</a></code>
- <code title="delete /v1/sandboxes/delete-all">client.sandboxes.<a href="./src/sandbox_sdk/resources/sandboxes.py">delete_all</a>() -> <a href="./src/sandbox_sdk/types/sandbox_delete_all_response.py">SandboxDeleteAllResponse</a></code>
- <code title="get /v1/sandboxes/{id}/download">client.sandboxes.<a href="./src/sandbox_sdk/resources/sandboxes.py">download</a>(id, \*\*<a href="src/sandbox_sdk/types/sandbox_download_params.py">params</a>) -> BinaryAPIResponse</code>
- <code title="post /v1/sandboxes/{id}/execute">client.sandboxes.<a href="./src/sandbox_sdk/resources/sandboxes.py">execute</a>(id, \*\*<a href="src/sandbox_sdk/types/sandbox_execute_params.py">params</a>) -> <a href="./src/sandbox_sdk/types/sandbox_execute_response.py">SandboxExecuteResponse</a></code>
- <code title="post /v1/sandboxes/{id}/upload">client.sandboxes.<a href="./src/sandbox_sdk/resources/sandboxes.py">upload</a>(id, \*\*<a href="src/sandbox_sdk/types/sandbox_upload_params.py">params</a>) -> <a href="./src/sandbox_sdk/types/sandbox_upload_response.py">SandboxUploadResponse</a></code>
