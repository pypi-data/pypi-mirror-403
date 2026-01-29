# V1

## Memories

Types:

```python
from eos.types.v1 import (
    MemoryType,
    Metadata,
    MemoryCreateResponse,
    MemoryListResponse,
    MemoryDeleteResponse,
    MemorySearchResponse,
)
```

Methods:

- <code title="post /api/v1/memories">client.v1.memories.<a href="./src/eos/resources/v1/memories/memories.py">create</a>(\*\*<a href="src/eos/types/v1/memory_create_params.py">params</a>) -> <a href="./src/eos/types/v1/memory_create_response.py">MemoryCreateResponse</a></code>
- <code title="get /api/v1/memories">client.v1.memories.<a href="./src/eos/resources/v1/memories/memories.py">list</a>() -> <a href="./src/eos/types/v1/memory_list_response.py">MemoryListResponse</a></code>
- <code title="delete /api/v1/memories">client.v1.memories.<a href="./src/eos/resources/v1/memories/memories.py">delete</a>(\*\*<a href="src/eos/types/v1/memory_delete_params.py">params</a>) -> <a href="./src/eos/types/v1/memory_delete_response.py">MemoryDeleteResponse</a></code>
- <code title="get /api/v1/memories/search">client.v1.memories.<a href="./src/eos/resources/v1/memories/memories.py">search</a>() -> <a href="./src/eos/types/v1/memory_search_response.py">MemorySearchResponse</a></code>

### ConversationMeta

Types:

```python
from eos.types.v1.memories import ConversationMetaCreateResponse, ConversationMetaUpdateResponse
```

Methods:

- <code title="post /api/v1/memories/conversation-meta">client.v1.memories.conversation_meta.<a href="./src/eos/resources/v1/memories/conversation_meta.py">create</a>(\*\*<a href="src/eos/types/v1/memories/conversation_meta_create_params.py">params</a>) -> <a href="./src/eos/types/v1/memories/conversation_meta_create_response.py">ConversationMetaCreateResponse</a></code>
- <code title="patch /api/v1/memories/conversation-meta">client.v1.memories.conversation_meta.<a href="./src/eos/resources/v1/memories/conversation_meta.py">update</a>(\*\*<a href="src/eos/types/v1/memories/conversation_meta_update_params.py">params</a>) -> <a href="./src/eos/types/v1/memories/conversation_meta_update_response.py">ConversationMetaUpdateResponse</a></code>
