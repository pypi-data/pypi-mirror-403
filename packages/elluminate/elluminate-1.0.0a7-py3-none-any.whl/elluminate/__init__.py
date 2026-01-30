from .async_client import AsyncClient
from .client import (
    Client,
    CollectionDefaults,
    CriterionSetDefaults,
    LLMConfigDefaults,
)
from .evaluate import evaluate
from .exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    ConflictError,
    ElluminateError,
    ModelNotBoundError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ResponseInfo,
    RetryExhaustedError,
    ServerError,
    ValidationError,
)
from .schemas import GenerationMetadata, LLMConfig
from .streaming import (
    BatchProgress,
    BatchStatusEvent,
    ExperimentProgress,
    ExperimentStatusEvent,
    TaskStatus,
)
from .utils import RetryConfig

# Set the __version__ attribute of this package. Used also
# for dynamic versioning of the hatch build system.
__version__ = "1.0.0a7"

__all__ = [
    "__version__",
    # Clients
    "Client",
    "AsyncClient",
    "RetryConfig",
    # TypedDicts for get_or_create defaults
    "CollectionDefaults",
    "CriterionSetDefaults",
    "LLMConfigDefaults",
    # Schemas
    "GenerationMetadata",
    "LLMConfig",
    # Streaming
    "ExperimentStatusEvent",
    "ExperimentProgress",
    "BatchStatusEvent",
    "BatchProgress",
    "TaskStatus",
    # Functions
    "evaluate",
    # Exceptions
    "ElluminateError",
    "APIError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ServerError",
    "ValidationError",
    "ConfigurationError",
    "RetryExhaustedError",
    "ModelNotBoundError",
    "ResponseInfo",
]
