# Spaces

Types:

```python
from memv.types import (
    Space,
    SpaceCreateResponse,
    SpaceRetrieveResponse,
    SpaceUpdateResponse,
    SpaceListResponse,
    SpaceDeleteResponse,
    SpaceGetStatsResponse,
)
```

Methods:

- <code title="post /spaces">client.spaces.<a href="./src/memv/resources/spaces.py">create</a>(\*\*<a href="src/memv/types/space_create_params.py">params</a>) -> <a href="./src/memv/types/space_create_response.py">SpaceCreateResponse</a></code>
- <code title="get /spaces/{spaceId}">client.spaces.<a href="./src/memv/resources/spaces.py">retrieve</a>(space_id) -> <a href="./src/memv/types/space_retrieve_response.py">SpaceRetrieveResponse</a></code>
- <code title="patch /spaces">client.spaces.<a href="./src/memv/resources/spaces.py">update</a>(\*\*<a href="src/memv/types/space_update_params.py">params</a>) -> <a href="./src/memv/types/space_update_response.py">SpaceUpdateResponse</a></code>
- <code title="get /spaces">client.spaces.<a href="./src/memv/resources/spaces.py">list</a>() -> <a href="./src/memv/types/space_list_response.py">SpaceListResponse</a></code>
- <code title="delete /spaces">client.spaces.<a href="./src/memv/resources/spaces.py">delete</a>(\*\*<a href="src/memv/types/space_delete_params.py">params</a>) -> <a href="./src/memv/types/space_delete_response.py">SpaceDeleteResponse</a></code>
- <code title="get /spaces/stats">client.spaces.<a href="./src/memv/resources/spaces.py">get_stats</a>() -> <a href="./src/memv/types/space_get_stats_response.py">SpaceGetStatsResponse</a></code>

# Memories

Types:

```python
from memv.types import MemoryAddResponse, MemorySearchResponse
```

Methods:

- <code title="post /memories">client.memories.<a href="./src/memv/resources/memories.py">add</a>(\*\*<a href="src/memv/types/memory_add_params.py">params</a>) -> <a href="./src/memv/types/memory_add_response.py">MemoryAddResponse</a></code>
- <code title="post /memories/search">client.memories.<a href="./src/memv/resources/memories.py">search</a>(\*\*<a href="src/memv/types/memory_search_params.py">params</a>) -> <a href="./src/memv/types/memory_search_response.py">MemorySearchResponse</a></code>

# Videos

Types:

```python
from memv.types import Pagination, VideoListResponse, VideoDeleteResponse, VideoDownloadResponse
```

Methods:

- <code title="get /videos">client.videos.<a href="./src/memv/resources/videos.py">list</a>(\*\*<a href="src/memv/types/video_list_params.py">params</a>) -> <a href="./src/memv/types/video_list_response.py">VideoListResponse</a></code>
- <code title="delete /videos">client.videos.<a href="./src/memv/resources/videos.py">delete</a>(\*\*<a href="src/memv/types/video_delete_params.py">params</a>) -> <a href="./src/memv/types/video_delete_response.py">VideoDeleteResponse</a></code>
- <code title="get /videos/{videoId}/download">client.videos.<a href="./src/memv/resources/videos.py">download</a>(video_id, \*\*<a href="src/memv/types/video_download_params.py">params</a>) -> <a href="./src/memv/types/video_download_response.py">VideoDownloadResponse</a></code>

# Files

Types:

```python
from memv.types import (
    File,
    FileRetrieveResponse,
    FileListResponse,
    FileDeleteResponse,
    FileDownloadResponse,
)
```

Methods:

- <code title="get /files/{fileId}">client.files.<a href="./src/memv/resources/files.py">retrieve</a>(file_id) -> <a href="./src/memv/types/file_retrieve_response.py">FileRetrieveResponse</a></code>
- <code title="get /files">client.files.<a href="./src/memv/resources/files.py">list</a>(\*\*<a href="src/memv/types/file_list_params.py">params</a>) -> <a href="./src/memv/types/file_list_response.py">FileListResponse</a></code>
- <code title="delete /files">client.files.<a href="./src/memv/resources/files.py">delete</a>(\*\*<a href="src/memv/types/file_delete_params.py">params</a>) -> <a href="./src/memv/types/file_delete_response.py">FileDeleteResponse</a></code>
- <code title="get /files/{fileId}/download">client.files.<a href="./src/memv/resources/files.py">download</a>(file_id, \*\*<a href="src/memv/types/file_download_params.py">params</a>) -> <a href="./src/memv/types/file_download_response.py">FileDownloadResponse</a></code>

# Upload

## Batch

Types:

```python
from memv.types.upload import (
    BatchCreateResponse,
    BatchCancelResponse,
    BatchGetStatusResponse,
    BatchMarkFileUploadedResponse,
    BatchProcessUploadedMemoriesResponse,
)
```

Methods:

- <code title="post /upload/batch">client.upload.batch.<a href="./src/memv/resources/upload/batch.py">create</a>(\*\*<a href="src/memv/types/upload/batch_create_params.py">params</a>) -> <a href="./src/memv/types/upload/batch_create_response.py">BatchCreateResponse</a></code>
- <code title="post /upload/batch/{batchId}/cancel">client.upload.batch.<a href="./src/memv/resources/upload/batch.py">cancel</a>(batch_id) -> <a href="./src/memv/types/upload/batch_cancel_response.py">BatchCancelResponse</a></code>
- <code title="get /upload/batch/{batchId}/status">client.upload.batch.<a href="./src/memv/resources/upload/batch.py">get_status</a>(batch_id) -> <a href="./src/memv/types/upload/batch_get_status_response.py">BatchGetStatusResponse</a></code>
- <code title="patch /upload/batch/{batchId}/file-uploaded">client.upload.batch.<a href="./src/memv/resources/upload/batch.py">mark_file_uploaded</a>(batch_id, \*\*<a href="src/memv/types/upload/batch_mark_file_uploaded_params.py">params</a>) -> <a href="./src/memv/types/upload/batch_mark_file_uploaded_response.py">BatchMarkFileUploadedResponse</a></code>
- <code title="post /upload/batch/{batchId}/process">client.upload.batch.<a href="./src/memv/resources/upload/batch.py">process_uploaded_memories</a>(batch_id) -> <a href="./src/memv/types/upload/batch_process_uploaded_memories_response.py">BatchProcessUploadedMemoriesResponse</a></code>

# Chat

Types:

```python
from memv.types import ChatQueryMemoriesResponse
```

Methods:

- <code title="post /chat">client.chat.<a href="./src/memv/resources/chat.py">query_memories</a>(\*\*<a href="src/memv/types/chat_query_memories_params.py">params</a>) -> <a href="./src/memv/types/chat_query_memories_response.py">ChatQueryMemoriesResponse</a></code>

# Graph

Methods:

- <code title="get /graph/{type}/{id}/triplets">client.graph.<a href="./src/memv/resources/graph.py">retrieve_triplets</a>(id, \*, type) -> object</code>
