# Authors

Types:

```python
from moderation_api.types import (
    AuthorCreateResponse,
    AuthorRetrieveResponse,
    AuthorUpdateResponse,
    AuthorListResponse,
    AuthorDeleteResponse,
)
```

Methods:

- <code title="post /authors">client.authors.<a href="./src/moderation_api/resources/authors.py">create</a>(\*\*<a href="src/moderation_api/types/author_create_params.py">params</a>) -> <a href="./src/moderation_api/types/author_create_response.py">AuthorCreateResponse</a></code>
- <code title="get /authors/{id}">client.authors.<a href="./src/moderation_api/resources/authors.py">retrieve</a>(id) -> <a href="./src/moderation_api/types/author_retrieve_response.py">AuthorRetrieveResponse</a></code>
- <code title="put /authors/{id}">client.authors.<a href="./src/moderation_api/resources/authors.py">update</a>(id, \*\*<a href="src/moderation_api/types/author_update_params.py">params</a>) -> <a href="./src/moderation_api/types/author_update_response.py">AuthorUpdateResponse</a></code>
- <code title="get /authors">client.authors.<a href="./src/moderation_api/resources/authors.py">list</a>(\*\*<a href="src/moderation_api/types/author_list_params.py">params</a>) -> <a href="./src/moderation_api/types/author_list_response.py">AuthorListResponse</a></code>
- <code title="delete /authors/{id}">client.authors.<a href="./src/moderation_api/resources/authors.py">delete</a>(id) -> <a href="./src/moderation_api/types/author_delete_response.py">AuthorDeleteResponse</a></code>

# Queue

Types:

```python
from moderation_api.types import QueueRetrieveResponse, QueueGetStatsResponse
```

Methods:

- <code title="get /queue/{id}">client.queue.<a href="./src/moderation_api/resources/queue/queue.py">retrieve</a>(id) -> <a href="./src/moderation_api/types/queue_retrieve_response.py">QueueRetrieveResponse</a></code>
- <code title="get /queue/{id}/stats">client.queue.<a href="./src/moderation_api/resources/queue/queue.py">get_stats</a>(id, \*\*<a href="src/moderation_api/types/queue_get_stats_params.py">params</a>) -> <a href="./src/moderation_api/types/queue_get_stats_response.py">QueueGetStatsResponse</a></code>

## Items

Types:

```python
from moderation_api.types.queue import ItemListResponse, ItemResolveResponse, ItemUnresolveResponse
```

Methods:

- <code title="get /queue/{id}/items">client.queue.items.<a href="./src/moderation_api/resources/queue/items.py">list</a>(id, \*\*<a href="src/moderation_api/types/queue/item_list_params.py">params</a>) -> <a href="./src/moderation_api/types/queue/item_list_response.py">ItemListResponse</a></code>
- <code title="post /queue/{id}/items/{itemId}/resolve">client.queue.items.<a href="./src/moderation_api/resources/queue/items.py">resolve</a>(item_id, \*, id, \*\*<a href="src/moderation_api/types/queue/item_resolve_params.py">params</a>) -> <a href="./src/moderation_api/types/queue/item_resolve_response.py">ItemResolveResponse</a></code>
- <code title="post /queue/{id}/items/{itemId}/unresolve">client.queue.items.<a href="./src/moderation_api/resources/queue/items.py">unresolve</a>(item_id, \*, id, \*\*<a href="src/moderation_api/types/queue/item_unresolve_params.py">params</a>) -> <a href="./src/moderation_api/types/queue/item_unresolve_response.py">ItemUnresolveResponse</a></code>

# Actions

Types:

```python
from moderation_api.types import (
    ActionCreateResponse,
    ActionRetrieveResponse,
    ActionUpdateResponse,
    ActionListResponse,
    ActionDeleteResponse,
)
```

Methods:

- <code title="post /actions">client.actions.<a href="./src/moderation_api/resources/actions/actions.py">create</a>(\*\*<a href="src/moderation_api/types/action_create_params.py">params</a>) -> <a href="./src/moderation_api/types/action_create_response.py">ActionCreateResponse</a></code>
- <code title="get /actions/{id}">client.actions.<a href="./src/moderation_api/resources/actions/actions.py">retrieve</a>(id) -> <a href="./src/moderation_api/types/action_retrieve_response.py">ActionRetrieveResponse</a></code>
- <code title="put /actions/{id}">client.actions.<a href="./src/moderation_api/resources/actions/actions.py">update</a>(id, \*\*<a href="src/moderation_api/types/action_update_params.py">params</a>) -> <a href="./src/moderation_api/types/action_update_response.py">ActionUpdateResponse</a></code>
- <code title="get /actions">client.actions.<a href="./src/moderation_api/resources/actions/actions.py">list</a>(\*\*<a href="src/moderation_api/types/action_list_params.py">params</a>) -> <a href="./src/moderation_api/types/action_list_response.py">ActionListResponse</a></code>
- <code title="delete /actions/{id}">client.actions.<a href="./src/moderation_api/resources/actions/actions.py">delete</a>(id) -> <a href="./src/moderation_api/types/action_delete_response.py">ActionDeleteResponse</a></code>

## Execute

Types:

```python
from moderation_api.types.actions import ExecuteExecuteResponse, ExecuteExecuteByIDResponse
```

Methods:

- <code title="post /actions/execute">client.actions.execute.<a href="./src/moderation_api/resources/actions/execute.py">execute</a>(\*\*<a href="src/moderation_api/types/actions/execute_execute_params.py">params</a>) -> <a href="./src/moderation_api/types/actions/execute_execute_response.py">ExecuteExecuteResponse</a></code>
- <code title="post /actions/{actionId}/execute">client.actions.execute.<a href="./src/moderation_api/resources/actions/execute.py">execute_by_id</a>(action_id, \*\*<a href="src/moderation_api/types/actions/execute_execute_by_id_params.py">params</a>) -> <a href="./src/moderation_api/types/actions/execute_execute_by_id_response.py">ExecuteExecuteByIDResponse</a></code>

# Content

Types:

```python
from moderation_api.types import ContentSubmitResponse
```

Methods:

- <code title="post /moderate">client.content.<a href="./src/moderation_api/resources/content.py">submit</a>(\*\*<a href="src/moderation_api/types/content_submit_params.py">params</a>) -> <a href="./src/moderation_api/types/content_submit_response.py">ContentSubmitResponse</a></code>

# Account

Types:

```python
from moderation_api.types import AccountListResponse
```

Methods:

- <code title="get /account">client.account.<a href="./src/moderation_api/resources/account.py">list</a>() -> <a href="./src/moderation_api/types/account_list_response.py">AccountListResponse</a></code>

# Auth

Types:

```python
from moderation_api.types import AuthCreateResponse, AuthRetrieveResponse
```

Methods:

- <code title="post /auth">client.auth.<a href="./src/moderation_api/resources/auth.py">create</a>() -> <a href="./src/moderation_api/types/auth_create_response.py">AuthCreateResponse</a></code>
- <code title="get /auth">client.auth.<a href="./src/moderation_api/resources/auth.py">retrieve</a>() -> <a href="./src/moderation_api/types/auth_retrieve_response.py">AuthRetrieveResponse</a></code>

# Wordlist

Types:

```python
from moderation_api.types import (
    WordlistRetrieveResponse,
    WordlistUpdateResponse,
    WordlistListResponse,
    WordlistGetEmbeddingStatusResponse,
)
```

Methods:

- <code title="get /wordlist/{id}">client.wordlist.<a href="./src/moderation_api/resources/wordlist/wordlist.py">retrieve</a>(id) -> <a href="./src/moderation_api/types/wordlist_retrieve_response.py">WordlistRetrieveResponse</a></code>
- <code title="put /wordlist/{id}">client.wordlist.<a href="./src/moderation_api/resources/wordlist/wordlist.py">update</a>(id, \*\*<a href="src/moderation_api/types/wordlist_update_params.py">params</a>) -> <a href="./src/moderation_api/types/wordlist_update_response.py">WordlistUpdateResponse</a></code>
- <code title="get /wordlist">client.wordlist.<a href="./src/moderation_api/resources/wordlist/wordlist.py">list</a>() -> <a href="./src/moderation_api/types/wordlist_list_response.py">WordlistListResponse</a></code>
- <code title="get /wordlist/{id}/embedding-status">client.wordlist.<a href="./src/moderation_api/resources/wordlist/wordlist.py">get_embedding_status</a>(id) -> <a href="./src/moderation_api/types/wordlist_get_embedding_status_response.py">WordlistGetEmbeddingStatusResponse</a></code>

## Words

Types:

```python
from moderation_api.types.wordlist import WordAddResponse, WordRemoveResponse
```

Methods:

- <code title="post /wordlist/{id}/words">client.wordlist.words.<a href="./src/moderation_api/resources/wordlist/words.py">add</a>(id, \*\*<a href="src/moderation_api/types/wordlist/word_add_params.py">params</a>) -> <a href="./src/moderation_api/types/wordlist/word_add_response.py">WordAddResponse</a></code>
- <code title="delete /wordlist/{id}/words">client.wordlist.words.<a href="./src/moderation_api/resources/wordlist/words.py">remove</a>(id, \*\*<a href="src/moderation_api/types/wordlist/word_remove_params.py">params</a>) -> <a href="./src/moderation_api/types/wordlist/word_remove_response.py">WordRemoveResponse</a></code>
