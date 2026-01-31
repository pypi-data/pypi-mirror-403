# Shared Types

```python
from agentlin_client.types import ToolData
```

# Tasks

Types:

```python
from agentlin_client.types import (
    AgentTaskEvent,
    AnnotationContainerFileCitation,
    AnnotationFileCitation,
    AnnotationFilePath,
    AnnotationURLCitation,
    AudioContentItem,
    FileContentItem,
    ImageContentItem,
    JsonrpcError,
    LogProb,
    MessageContent,
    MessageItem,
    ReasoningItem,
    TaskAudioDeltaEvent,
    TaskAudioDoneEvent,
    TaskCanceledEvent,
    TaskCompletedEvent,
    TaskContentPartAddedEvent,
    TaskContentPartDoneEvent,
    TaskContextCompressionCompletedEvent,
    TaskContextCompressionCreatedEvent,
    TaskContextCompressionInProgressEvent,
    TaskCreatedEvent,
    TaskExpiredEvent,
    TaskFailedEvent,
    TaskFileDeltaEvent,
    TaskFileDoneEvent,
    TaskImageDeltaEvent,
    TaskImageDoneEvent,
    TaskInputRequiredEvent,
    TaskObject,
    TaskOutputItemAddedEvent,
    TaskOutputItemDoneEvent,
    TaskPausedEvent,
    TaskQueuedEvent,
    TaskReasoningSummaryPartAddedEvent,
    TaskReasoningSummaryPartDoneEvent,
    TaskReasoningSummaryTextDeltaEvent,
    TaskReasoningSummaryTextDoneEvent,
    TaskReasoningTextDeltaEvent,
    TaskReasoningTextDoneEvent,
    TaskRolloutEvent,
    TaskTextDeltaEvent,
    TaskTextDoneEvent,
    TaskToolCallArgumentsDeltaEvent,
    TaskToolCallArgumentsDoneEvent,
    TaskToolResultDeltaEvent,
    TaskToolResultDoneEvent,
    TaskToolsUpdatedEvent,
    TaskWorkingEvent,
    TextContentItem,
    ToolCallItem,
    ToolResultItem,
    TopLogProb,
    TaskCreateResponse,
    TaskDeleteResponse,
    TaskInfoResponse,
)
```

Methods:

- <code title="post /tasks">client.tasks.<a href="./src/agentlin_client/resources/tasks.py">create</a>(\*\*<a href="src/agentlin_client/types/task_create_params.py">params</a>) -> <a href="./src/agentlin_client/types/task_create_response.py">TaskCreateResponse</a></code>
- <code title="get /tasks">client.tasks.<a href="./src/agentlin_client/resources/tasks.py">list</a>(\*\*<a href="src/agentlin_client/types/task_list_params.py">params</a>) -> <a href="./src/agentlin_client/types/task_object.py">SyncListTasks[TaskObject]</a></code>
- <code title="delete /tasks/{task_id}">client.tasks.<a href="./src/agentlin_client/resources/tasks.py">delete</a>(task_id) -> <a href="./src/agentlin_client/types/task_delete_response.py">TaskDeleteResponse</a></code>
- <code title="post /tasks/{task_id}/cancel">client.tasks.<a href="./src/agentlin_client/resources/tasks.py">cancel</a>(task_id) -> <a href="./src/agentlin_client/types/task_object.py">TaskObject</a></code>
- <code title="get /tasks/{task_id}">client.tasks.<a href="./src/agentlin_client/resources/tasks.py">info</a>(task_id) -> <a href="./src/agentlin_client/types/task_info_response.py">TaskInfoResponse</a></code>
- <code title="post /tasks/{task_id}/pause">client.tasks.<a href="./src/agentlin_client/resources/tasks.py">pause</a>(task_id) -> <a href="./src/agentlin_client/types/task_object.py">TaskObject</a></code>
- <code title="post /tasks/{task_id}/resume">client.tasks.<a href="./src/agentlin_client/resources/tasks.py">resume</a>(task_id) -> <a href="./src/agentlin_client/types/task_object.py">TaskObject</a></code>

# Env

Types:

```python
from agentlin_client.types import (
    EnvInfo,
    EnvCreateResponse,
    EnvCloseResponse,
    EnvInfoResponse,
    EnvObservationResponse,
    EnvResetResponse,
    EnvSessionResponse,
    EnvSessionsResponse,
)
```

Methods:

- <code title="post /env/create">client.env.<a href="./src/agentlin_client/resources/env.py">create</a>(\*\*<a href="src/agentlin_client/types/env_create_params.py">params</a>) -> <a href="./src/agentlin_client/types/env_create_response.py">EnvCreateResponse</a></code>
- <code title="get /env">client.env.<a href="./src/agentlin_client/resources/env.py">list</a>(\*\*<a href="src/agentlin_client/types/env_list_params.py">params</a>) -> <a href="./src/agentlin_client/types/env_info.py">SyncListEnvs[EnvInfo]</a></code>
- <code title="post /env/sessions/cleanup">client.env.<a href="./src/agentlin_client/resources/env.py">clean_session</a>(\*\*<a href="src/agentlin_client/types/env_clean_session_params.py">params</a>) -> object</code>
- <code title="post /env/close">client.env.<a href="./src/agentlin_client/resources/env.py">close</a>(\*\*<a href="src/agentlin_client/types/env_close_params.py">params</a>) -> <a href="./src/agentlin_client/types/env_close_response.py">EnvCloseResponse</a></code>
- <code title="delete /env/session/{session_id}">client.env.<a href="./src/agentlin_client/resources/env.py">delete_session</a>(session_id) -> object</code>
- <code title="get /env/{env_id}">client.env.<a href="./src/agentlin_client/resources/env.py">info</a>(env_id) -> <a href="./src/agentlin_client/types/env_info_response.py">EnvInfoResponse</a></code>
- <code title="post /env/observation">client.env.<a href="./src/agentlin_client/resources/env.py">observation</a>(\*\*<a href="src/agentlin_client/types/env_observation_params.py">params</a>) -> <a href="./src/agentlin_client/types/env_observation_response.py">EnvObservationResponse</a></code>
- <code title="post /env/reset">client.env.<a href="./src/agentlin_client/resources/env.py">reset</a>(\*\*<a href="src/agentlin_client/types/env_reset_params.py">params</a>) -> <a href="./src/agentlin_client/types/env_reset_response.py">EnvResetResponse</a></code>
- <code title="get /env/session/{session_id}">client.env.<a href="./src/agentlin_client/resources/env.py">session</a>(session_id) -> <a href="./src/agentlin_client/types/env_session_response.py">EnvSessionResponse</a></code>
- <code title="get /env/sessions">client.env.<a href="./src/agentlin_client/resources/env.py">sessions</a>(\*\*<a href="src/agentlin_client/types/env_sessions_params.py">params</a>) -> <a href="./src/agentlin_client/types/env_sessions_response.py">EnvSessionsResponse</a></code>
- <code title="post /env/step">client.env.<a href="./src/agentlin_client/resources/env.py">step</a>(\*\*<a href="src/agentlin_client/types/env_step_params.py">params</a>) -> object</code>
