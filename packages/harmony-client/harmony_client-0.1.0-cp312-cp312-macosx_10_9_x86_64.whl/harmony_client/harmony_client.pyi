# ruff: noqa: E501, F401
"""Harmony Client - Python bindings for the Adaptive Harmony ML orchestration platform.

This module provides the Python interface to interact with Harmony workers for model training
and inference operations. It includes thread management, model lifecycle operations, and
training/evaluation utilities.
"""

from enum import Enum
from typing import Any, MutableSequence, NamedTuple, Optional, Sequence, Type, TypeVar

from adaptive_harmony.runtime import RecipeContext
from pydantic import BaseModel
from typing_extensions import Literal, Required, TypedDict

T = TypeVar("T", bound=BaseModel)

# Constants
DEFAULT_MAX_DRAFT_STEPS: int
"""Default maximum number of draft steps for speculative decoding."""

class ImageFragment(TypedDict, total=False):
    """Fragment representing an image in a conversation turn.

    Attributes:
        type: Must be "image"
        url: URL or data URI of the image (supports data URLs, file paths, and HTTP URLs)
    """

    type: Required[Literal["image"]]
    url: Required[str]

class TextFragment(TypedDict, total=False):
    """Fragment representing text content in a conversation turn.

    Attributes:
        type: Must be "text"
        text: The text content
    """

    type: Required[Literal["text"]]
    text: Required[str]

Fragment = ImageFragment | TextFragment
"""Union type for content fragments that can appear in conversation turns."""

class EvalSample:
    """Represents a single evaluation sample with its interaction and grades.

    An evaluation sample captures a conversation thread along with grades assigned
    by one or more graders. Used for evaluation artifact creation and analysis.

    Attributes:
        interaction: The conversation interaction being evaluated
        grades: List of grades from different graders
        dataset_key: Key identifying the dataset this sample belongs to
        id: Unique identifier for this evaluation sample (auto-generated UUID)
    """

    interaction: EvalSampleInteraction
    grades: MutableSequence[Grade]
    dataset_key: str
    id: str

    def __new__(
        cls,
        interaction: EvalSampleInteraction,
        grades: MutableSequence[Grade],
        dataset_key: str,
    ) -> EvalSample: ...
    def __repr__(self) -> str: ...

class EvalSampleInteraction:
    """Represents a conversation interaction for evaluation.

    Encapsulates a conversation thread and optionally tracks which model
    or source generated the interaction.

    Attributes:
        thread: The conversation thread (messages between user and assistant)
        source: Optional identifier for the model or system that generated this interaction
    """

    thread: StringThread
    source: Optional[str]

    def __new__(cls, thread: StringThread, source: Optional[str] = None) -> EvalSampleInteraction: ...
    def __repr__(self) -> str: ...

class EvaluationArtifactBase:
    """Base class for evaluation artifacts that can be registered with jobs.

    Evaluation artifacts track the results of model evaluations, including
    the evaluated samples and their grades. Can be uploaded to object storage.

    Attributes:
        artifact: The underlying job artifact with metadata
        id: Unique identifier for this artifact
        name: Human-readable name for the evaluation
        kind: Type of artifact (always "eval" for evaluations)
        uri: Optional URI where evaluation results are stored
    """

    artifact: JobArtifact
    id: str
    name: str
    kind: str
    uri: Optional[str]

    def __new__(cls, name: str, uri: str, id: str, **py_kwargs) -> EvaluationArtifactBase: ...
    def samples_to_adaptive_json(self, samples: MutableSequence[EvalSample]) -> list[str]:
        """Convert evaluation samples to JSONL format for storage.

        Args:
            samples: List of evaluation samples to serialize

        Returns:
            List of JSON strings, one per sample, suitable for JSONL file format
        """
        ...
    def __repr__(self) -> str: ...

class Grade:
    """Represents a grade assigned to an evaluation sample by a grader.

    Grades can include numeric scores and optional reasoning explaining
    the score.

    Attributes:
        value: Numeric grade value (typically 0.0-1.0 range)
        grader_key: Identifier for the grader that assigned this grade
        reasoning: Optional explanation for why this grade was assigned
    """

    value: float
    grader_key: str
    reasoning: Optional[str]

    def __new__(cls, value: float, grader_key: str, reasoning: Optional[str] = None) -> Grade: ...
    def __repr__(self) -> str: ...

class JobArtifact:
    """Represents an artifact produced by a training or evaluation job.

    Job artifacts track outputs like trained models, evaluation results, datasets,
    or custom artifacts. They can be registered with jobs to appear in the UI.

    Attributes:
        id: Unique identifier for this artifact
        name: Human-readable name
        kind: Type of artifact - "model", "eval", "dataset", or "custom"
        metadata: Additional key-value metadata for the artifact
        uri: Optional URI where the artifact is stored

    Example:
        ```python
        artifact = JobArtifact(
            id="my-model-v1",
            name="Fine-tuned Model",
            kind="model",
            uri="s3://bucket/models/my-model",
            checkpoint_step=1000,
            loss=0.25
        )
        notifier.register_artifact(artifact)
        ```
    """

    id: str
    name: str
    kind: str
    metadata: dict[str, Any]
    uri: Optional[str]

    def __new__(
        cls,
        id: str,
        name: str,
        kind: str,
        uri: Optional[str] = None,
        **py_kwargs,
    ) -> JobArtifact: ...
    def __repr__(self) -> str: ...

class StringTurn(NamedTuple):
    """A single turn in a conversation thread with string content.

    Attributes:
        role: The role of the entity that is creating the content
        content: The text content of the turn
    """

    role: str
    content: str

class TokenizedTurn(NamedTuple):
    """A single turn in a conversation thread with tokenized content.

    Attributes:
        role: The role of the entity that is creating the content
        content: The tokenized content as a list of token IDs
    """

    role: str
    content: list[int]

class ModelConfigResponse:
    """Configuration metadata for a model retrieved from the control plane.

    Attributes:
        model_id: Unique identifier for the model
        model_key: Human-readable key for the model
        path: File system or registry path to the model
        tp: Optional tensor parallelism degree
        kv_cache_len: Optional KV cache length for inference
        max_seq_len: Optional maximum sequence length the model supports
    """

    model_id: str
    model_key: str
    path: str
    tp: int | None
    kv_cache_len: int | None
    max_seq_len: int | None

class DatasetConfigResponse:
    """Configuration metadata for a dataset retrieved from the control plane.

    Attributes:
        dataset_id: Unique identifier for the dataset
        dataset_key: Human-readable key for the dataset
        name: Display name of the dataset
        file_path: Path to the dataset file
        kind: Type of dataset (e.g., "jsonl", "parquet")
    """

    dataset_id: str
    dataset_key: str
    name: str
    file_path: str
    kind: str

class GraderConfigResponse:
    """Configuration metadata for a grader retrieved from the control plane.

    Attributes:
        grader_id: Unique identifier for the grader
        key: Human-readable key for the grader
        name: Display name of the grader
        harmony_url: URL of the harmony instance to use for grading
        grader_config_json: JSON configuration for the grader
    """

    grader_id: str
    key: str
    name: str
    harmony_url: str
    grader_config_json: str

class HarmonyClient:
    """Main client for interacting with Harmony workers.

    The HarmonyClient is the primary interface for creating models and accessing
    platform configuration. It manages the connection to Harmony workers and
    provides access to model builders for spawning inference and training models.

    Example:
        ```python
        from harmony_client import get_client

        client = await get_client(
            addr="ws://localhost:8080",
            num_gpus=1,
            api_key="my-key"
        )

        # Create a model builder
        model = client.model("model_registry://llama-3.1-8b")

        # Spawn an inference model
        inf_model = await model.spawn_inference("my-model")

        # Generate text
        thread = StringThread([("user", "Hello!")])
        result = await inf_model.generate(thread)
        print(result.last_content())
        ```
    """
    def model(self, path: str, kv_cache_len: int = 131072, tokens_to_generate: int = 2048) -> ModelBuilder:
        """Create a model builder for spawning inference or training models.

        Args:
            path: Path to the model. Can be:
                - Model registry key: "model_registry://llama-3.1-8b"
                - External provider: "openai://gpt-4", "anthropic://claude-3-5-sonnet"
                - URL with API key: "openai://gpt-4?api_key=sk-..."
            kv_cache_len: KV cache length for inference (default: 131072). Will be ignored for external models as we do not control it.
            tokens_to_generate: Maximum tokens to generate (default: 2048)

        Returns:
            ModelBuilder that can be configured and spawned
        """
        ...
    def session_id(self) -> str:
        """Get the unique session ID for this client connection.

        Returns:
            Session UUID as a string
        """
        ...
    async def get_grader_config(self, grader_key: str) -> GraderConfigResponse:
        """Fetch grader configuration from the control plane.

        Args:
            grader_key: Key identifying the grader

        Returns:
            GraderConfigResponse with grader metadata

        Raises:
            RecipeError: If control_plane_url was not provided to get_client()
        """
        ...
    async def get_dataset_config(self, dataset_key: str) -> DatasetConfigResponse:
        """Fetch dataset configuration from the control plane.

        Args:
            dataset_key: Key identifying the dataset

        Returns:
            DatasetConfigResponse with dataset metadata

        Raises:
            RecipeError: If control_plane_url was not provided to get_client()
        """
        ...
    async def get_model_config(self, model_key: str) -> ModelConfigResponse:
        """Fetch model configuration from the control plane.

        Args:
            model_key: Key identifying the model

        Returns:
            ModelConfigResponse with model metadata

        Raises:
            RecipeError: If control_plane_url was not provided to get_client()
        """
        ...
    def close(self):
        """Close the client connection and release resources."""
        ...
    def __enter__(self) -> HarmonyClient: ...
    def __exit__(self, exc_type, exc_value, traceback) -> None: ...

class InferenceModel:
    """Model instance for running inference operations.

    InferenceModel provides methods for text generation, tokenization, scoring,
    and computing log probabilities. It can be created from a ModelBuilder using
    spawn_inference().

    The model is automatically deallocated when the object is garbage collected,
    but you can explicitly call dealloc() to free GPU memory sooner.

    Example:
        ```python
        model = client.model("model_registry://llama-3.1-8b")
        inf_model = await model.spawn_inference("my-inf-model")

        # Generate text
        thread = StringThread([("user", "What is 2+2?")])
        result = await inf_model.generate(thread)
        print(result.last_content())  # "4"
        ```
    """
    def is_scalar(self) -> bool:
        """Check if this model has a scalar output head (for scoring/reward models).

        Returns:
            True if model outputs scalars instead of next-token probabilities
        """
        ...
    async def dealloc(self) -> None:
        """Deallocate the model from GPU memory.

        Explicitly frees GPU resources. The model cannot be used after this call.
        Models are automatically deallocated on garbage collection if not called.
        """
        ...
    async def load(self, path: str) -> None:
        """Load model weights from a checkpoint path.

        Args:
            path: Path to model weights
        """
        ...
    async def generate(self, thread: StringThread, return_timings: bool = False) -> StringThread:
        """Generate text completion for a conversation thread.

        Appends an assistant turn with the generated completion to the thread.

        Args:
            thread: Conversation thread to continue
            return_timings: If True, returns tuple of (thread, timings)

        Returns:
            Updated thread with assistant response, or (thread, timings) tuple

        Example:
            ```python
            thread = StringThread([("user", "Hello!")])
            result = await model.generate(thread)
            print(result.last_content())  # Generated response
            ```
        """
        ...
    async def generate_tokens(self, thread: StringThread) -> TokenizedThread:
        """Generate token IDs for a conversation thread.

        Similar to generate() but returns tokenized output instead of strings.

        Args:
            thread: Conversation thread to continue

        Returns:
            TokenizedThread with generated token IDs
        """
        ...
    async def generate_and_validate(
        self,
        thread: StringThread,
        pydantic_model: Type[T],
        max_parsing_retries: int = 1,
    ) -> tuple[str, T]:
        """Generate structured output validated against a Pydantic model.

        Generates JSON output and parses it into the specified Pydantic model,
        with automatic retries on parse failures.

        Args:
            thread: Conversation thread (should request JSON output)
            pydantic_model: Pydantic model class to validate against
            max_parsing_retries: Maximum retry attempts on parse failures

        Returns:
            Tuple of (raw_json_string, parsed_model_instance)

        Example:
            ```python
            from pydantic import BaseModel

            class Response(BaseModel):
                answer: str
                confidence: float

            thread = StringThread([(
                "user",
                "Return JSON with 'answer' and 'confidence' fields"
            )])
            json_str, parsed = await model.generate_and_validate(
                thread, Response
            )
            print(parsed.answer, parsed.confidence)
            ```
        """
        ...
    async def tokenize_thread(self, thread: StringThread) -> TokenizedThread:
        """Convert a StringThread to a TokenizedThread.

        Args:
            thread: String-based conversation thread

        Returns:
            Tokenized version of the thread
        """
        ...
    async def detokenize_thread(self, thread: TokenizedThread) -> StringThread:
        """Convert a TokenizedThread back to a StringThread.

        Args:
            thread: Tokenized conversation thread

        Returns:
            String version of the thread
        """
        ...

    # the outputs of serialize_* are a list of tokens for the whole thread
    # a list with the image tokens, and a list with each token's weight
    async def serialize_thread(
        self, thread: StringThread
    ) -> tuple[list[int], list[tuple[int, list[float]]], list[float]]:
        """Serialize a thread into tokens with weights for training.

        Returns:
            Tuple of (token_ids, image_tokens, weights) where:
            - token_ids: All tokens in the thread
            - image_tokens: List of (position, embedding) for images
            - weights: Per-token training weights (0.0 = skip, 1.0 = train)
        """
        ...
    async def serialize_tokenized_thread(
        self, thread: TokenizedThread
    ) -> tuple[list[int], list[tuple[int, list[float]]], list[float]]:
        """Serialize a tokenized thread with weights for training.

        Returns:
            Tuple of (token_ids, image_tokens, weights)
        """
        ...
    async def logprobs(self, thread: StringThread) -> float:
        """Compute the total log probability of a thread.

        Returns the sum of log probabilities of all weighted tokens.

        Args:
            thread: Conversation thread to score

        Returns:
            Total log probability (summed across weighted tokens)
        """
        ...
    async def logprobs_per_token(self, thread: TokenizedThread) -> list[float]:
        """Compute log probabilities for each weighted token in a thread.

        Args:
            thread: Tokenized conversation thread

        Returns:
            List of log probabilities for each weighted token
        """
        ...
    async def score(self, thread: TokenizedThread) -> list[float]:
        """Score each weighted token using a scalar head model.

        Only works with scoring models (where is_scalar() returns True).

        Args:
            thread: Tokenized thread to score

        Returns:
            List of scalar scores for each weighted token
        """
        ...
    async def score_last_token(self, thread: StringThread) -> float:
        """Score the last token using a scalar head model.

        Args:
            thread: Conversation thread

        Returns:
            Scalar score for the last token
        """
        ...
    async def raw_string_create(self, prompt: str) -> str:
        """Generate text from a raw string prompt (no conversation formatting).
        Should normally not be used unless you know exactly what you are doing.

        Args:
            prompt: Raw text prompt

        Returns:
            Generated completion
        """
        ...
    async def raw_token_create(self, prompt: Sequence[int]) -> list[int]:
        """Generate tokens from raw token IDs (no conversation formatting).
        Should normally not be used unless you know exactly what you are doing.

        Args:
            prompt: List of token IDs

        Returns:
            Generated token IDs
        """
        ...
    async def tokenize(self, data: str) -> list[int]:
        """Tokenize a string into token IDs.

        Args:
            data: Text to tokenize

        Returns:
            List of token IDs
        """
        ...
    async def detokenize(self, data: Sequence[int]) -> str:
        """Convert token IDs back to text.

        Args:
            data: List of token IDs

        Returns:
            Decoded text string
        """
        ...
    async def char_to_token_rewards(self, text: str, char_rewards: Sequence[float]) -> list[float]:
        """Map character-level rewards to token-level rewards.

        Useful for reward modeling when you have character-granular feedback.

        Args:
            text: The text string
            char_rewards: Reward value for each character

        Returns:
            Reward value for each token
        """
        ...
    async def raw_logprobs(self, tokens: Sequence[int]) -> list[float]:
        """Compute log probabilities for raw token IDs.
        Should normally not be used unless you know exactly what you are doing.

        Args:
            tokens: Sequence of token IDs

        Returns:
            Log probability for each token (first token gets 0.0)
        """
        ...
    async def thread_with_tools(self, thread: StringThread, tool_uris: Sequence[str]) -> StringThread:
        """Inject tool definitions into a conversation thread.
            DOCS_TODO: add an example here.

        Args:
            thread: Base conversation thread
            tool_uris: List of tool URIs to make available

        Returns:
            Thread with tool definitions injected
        """
        ...
    @staticmethod
    def render_schema(pydantic_model: type[BaseModel], with_field_descriptions: bool = True) -> str:
        """Render a Pydantic model as a JSON schema string.

        Args:
            pydantic_model: Pydantic model class
            with_field_descriptions: Include field descriptions in schema

        Returns:
            JSON schema as a string
        """
        ...
    @staticmethod
    def render_pydantic_model(pydantic_model: BaseModel) -> str:
        """Serialize a Pydantic model instance to JSON string.

        Args:
            pydantic_model: Pydantic model instance

        Returns:
            JSON representation
        """
        ...
    def get_builder_args(self) -> dict[str, Any]:
        """Get the configuration args used to build this model.

        Returns:
            Dictionary of model builder arguments
        """
        ...
    def top_p(self, top_p: float) -> InferenceModel:
        """Return a shallow copy with modified top_p sampling parameter.

        Args:
            top_p: Nucleus sampling probability (0.0-1.0)

        Returns:
            New InferenceModel instance with updated parameter
        """
        ...
    def temperature(self, temperature: float) -> InferenceModel:
        """Return a shallow copy with modified temperature sampling parameter.

        Args:
            temperature: Sampling temperature (>0, typically 0.1-2.0)

        Returns:
            New InferenceModel instance with updated parameter
        """
        ...
    def max_gen_len(self, max_num_tokens: int) -> InferenceModel:
        """Return a shallow copy with modified maximum generation length.

        Args:
            max_num_tokens: Maximum tokens to generate

        Returns:
            New InferenceModel instance with updated parameter
        """
        ...
    def min_gen_len(self, min_num_tokens: int) -> InferenceModel:
        """Return a shallow copy with modified minimum generation length.

        Args:
            min_num_tokens: Minimum tokens to generate

        Returns:
            New InferenceModel instance with updated parameter
        """
        ...

class InferenceSettings:
    """Configuration for inference model spawning.

    Attributes:
        kv_cache_len: Length of the KV cache
        tokens_to_generate: Maximum tokens to generate per request
    """
    def __new__(cls, kv_cache_len: int, tokens_to_generate: int) -> InferenceSettings: ...
    def to_python_dict(self) -> dict[str, Any]:
        """Convert settings to a dictionary.

        Returns:
            Dictionary representation of settings
        """
        ...

class ModelBuilder:
    """Builder for configuring and spawning model instances.

    ModelBuilder provides a fluent API for configuring model parameters
    before spawning inference or training instances. Create via HarmonyClient.model().

    Example:
        ```python
        # Basic inference model
        model = client.model("model_registry://llama-3.1-8b")
        inf = await model.spawn_inference("my-model")

        # With tensor parallelism and temperature
        model = (client.model("llama-3.1-70b")
            .tp(4)
            .temperature(0.7))
        inf = await model.spawn_inference("my-70b")

        # Training model with LoRA adapter
        model = (client.model("model_registry://llama-3.1-8b")
            .with_adapter())
        train = await model.spawn_train("my-train", max_batch_size=4)

        # With speculative decoding
        model = (client.model("llama-3.1-70b")
            .with_draft("llama-3.1-8b", num_draft_steps=4))
        inf = await model.spawn_inference("fast-70b")
        ```
    """
    async def spawn_train(self, name: str, max_batch_size: int) -> TrainingModel:
        """Spawn a training model instance.

        Args:
            name: Unique name for this model instance
            max_batch_size: Maximum batch size for training. Due to our automatic packing this is also the maximum sequence length of a single sample.

        Returns:
            TrainingModel instance for fine-tuning operations
        """
        ...
    async def spawn_inference(self, name: str) -> InferenceModel:
        """Spawn an inference model instance.

        Args:
            name: Unique name for this model instance

        Returns:
            InferenceModel instance for generation operations
        """
        ...
    def tp(self, tp: int) -> ModelBuilder:
        """Set tensor parallelism degree.

        Args:
            tp: Number of GPUs to split the model across

        Returns:
            Updated builder
        """
        ...
    def tools(self, tools: list[str]) -> ModelBuilder:
        """Add tool calling support.

        Args:
            tools: List of tool URIs to make available

        Returns:
            Updated builder
        """
        ...
    def api_key(self, api_key: str) -> ModelBuilder:
        """Set API key for external model providers.

        Args:
            api_key: API key for provider (OpenAI, Anthropic, etc.)

        Returns:
            Updated builder
        """
        ...
    def into_scoring_model(self) -> ModelBuilder:
        """Configure model to use scalar output head for scoring. Useful when creating a reward/value model from a base language model.

        Returns:
            Updated builder configured for reward/value modeling
        """
        ...
    def with_adapter(self, use_adapter: bool = True) -> ModelBuilder:
        """Configure adapter/LoRA mode for model spawning.

        Args:
            use_adapter: Controls adapter mode (default: True).
                - True: Enable adapter mode. For FW models, creates a new adapter.
                  For LoRA models, uses the existing adapter (no-op).
                - False: Disable adapter mode. For FW models, trains the full weights directly.
                  For LoRA models, this is an error (cannot fall back to FW from a LoRA).

        If with_adapter() is not called at all:
            - FW models default to training full weights (equivalent to with_adapter(False))
            - LoRA models default to using the adapter (equivalent to with_adapter(True))

        Returns:
            Updated builder with adapter mode configured
        """
        ...
    def with_draft(self, draft_model_path: str, num_draft_steps: int | None = None) -> ModelBuilder:
        """Enable speculative decoding with a draft model.

        Args:
            draft_model_path: Path to smaller/faster draft model. Must share the same tokenizer as the main model.
            num_draft_steps: Number of speculative tokens per step (default: DEFAULT_MAX_DRAFT_STEPS)

        Returns:
            Updated builder with speculative decoding enabled
        """
        ...
    def to_python_dict(self) -> dict[str, Any]:
        """Get builder configuration as a dictionary.

        Returns:
            Dictionary of builder parameters
        """
        ...
    def extra_params(self, **params) -> ModelBuilder:
        """Set additional provider-specific parameters.
        DOCS_TODO: add examples for OpenAI, Anthropic, etc.

        Args:
            **params: Arbitrary parameters passed to the model provider

        Returns:
            Updated builder
        """
        ...

class SerializedThread:
    """Opaque type representing a fully serialized conversation thread.

    Used internally for efficient communication between client and workers.
    """

    ...

class StatDuration:
    """Statistics about tokens processed over a time period.

    Tracks input, output, and training token counts and throughput rates.

    Attributes:
        duration_sec: Duration in seconds
        num_input_tokens: Total input tokens processed
        num_output_tokens: Total output tokens generated
        num_trained_tokens: Total tokens used for training
        num_input_tokens_per_s: Input token throughput
        num_output_tokens_per_s: Output token throughput
        num_trained_tokens_per_s: Training token throughput
    """

    duration_sec: float
    num_input_tokens: int
    num_output_tokens: int
    num_trained_tokens: int
    num_input_tokens_per_s: float
    num_output_tokens_per_s: float
    num_trained_tokens_per_s: float

    def combine(self, other: StatDuration) -> StatDuration:
        """Combine statistics from two time periods.

        Args:
            other: Another StatDuration to combine

        Returns:
            Combined statistics spanning both periods
        """
        ...

class StatInstant:
    """Snapshot of model statistics at a point in time.

    Used to compute statistics over time intervals via stats_since().
    """
    def stats_since(self, other: StatInstant) -> StatDuration:
        """Compute statistics since another snapshot.

        Args:
            other: Earlier StatInstant snapshot

        Returns:
            StatDuration covering the time between snapshots
        """
        ...

class StringThread:
    """Represents a conversation thread with string-based content.

    StringThread is the primary way to represent conversations in Harmony. It consists
    of a sequence of turns (user, assistant, system, tool) with text content. Each turn
    has an associated weight that controls whether it's used for training.

    Threads support multi-modal content via fragments (text and images).

    Attributes:
        metadata: Arbitrary Python object to attach to this thread

    Example:
        ```python
        # Create a simple conversation
        thread = StringThread([
            ("user", "What is the capital of France?"),
            ("assistant", "The capital of France is Paris.")
        ])

        # Add more turns
        thread = thread.user("Tell me more about it.")

        # Access turns
        for role, content in thread.get_turns():
            print(f"{role}: {content}")

        # Multi-modal with images
        thread = await StringThread.from_fragments([
            ("user", [
                {"type": "text", "text": "What's in this image?"},
                {"type": "image", "url": "data:image/png;base64,..."}
            ])
        ], metadata=None)
        ```
    """

    metadata: Any

    def __new__(
        cls,
        turns: Optional[Sequence[tuple[str, str]]] = None,
        metadata: Optional[Any] = None,
    ) -> StringThread: ...
    @staticmethod
    async def from_fragments(raw_turns: Sequence[tuple[str, Sequence[Fragment]]], metadata: Any) -> StringThread:
        """Create a thread from multi-modal fragments (text and images).

        Args:
            raw_turns: Sequence of (role, fragments) tuples
            metadata: Optional metadata to attach

        Returns:
            StringThread with multi-modal content
        """
        ...
    @staticmethod
    async def from_dataset(raw_turns: Sequence[tuple[str, str | Sequence[Fragment]]], metadata: Any) -> StringThread:
        """Create a thread from dataset format (strings or fragments).

        Flexible constructor that accepts either plain strings or fragment lists
        for each turn's content.

        Args:
            raw_turns: Sequence of (role, content) where content is string or fragments
            metadata: Optional metadata to attach

        Returns:
            StringThread from dataset
        """
        ...
    @classmethod
    def with_metadata(cls, turns: Sequence[tuple[str, str]], metadata: Any) -> StringThread: ...
    def user(self, content: str) -> StringThread:
        """Append a user turn to the thread.

        Args:
            content: User message text

        Returns:
            New thread with user turn appended
        """
        ...
    def system(self, content: str) -> StringThread:
        """Append a system turn to the thread.

        Args:
            content: System message text

        Returns:
            New thread with system turn appended
        """
        ...
    def assistant(self, content: str) -> StringThread:
        """Append an assistant turn to the thread.

        Args:
            content: Assistant message text

        Returns:
            New thread with assistant turn appended
        """
        ...
    def tool(self, content: str) -> StringThread:
        """Append a tool result turn to the thread.

        Args:
            content: Tool output text

        Returns:
            New thread with tool turn appended
        """
        ...
    def last_content(self) -> str:
        """Get the content of the last turn.

        Returns:
            Text content of the last turn

        Raises:
            RecipeError: If thread is empty
        """
        ...
    def messages(self) -> list[tuple[str, str]]:
        """Get all turns except the last assistant turn (if present).
        DOCS_TODO: show example.

        Useful for extracting the prompt portion of a thread.

        Returns:
            List of (role, content) tuples excluding final assistant turn
        """
        ...
    def completion(self) -> str | None:
        """Get the completion if the last turn is from the assistant.
        DOCS_TODO: show example.

        Returns:
            Assistant's response if last turn is assistant, None otherwise
        """
        ...
    def get_turns(self) -> list[StringTurn]:
        """Get all turns as StringTurn namedtuples.

        Returns:
            List of StringTurn(role, content) tuples
        """
        ...
    def get_fragments(self) -> list[tuple[str, list[Fragment]]]:
        """Get all turns as multi-modal fragments.

        Returns:
            List of (role, fragments) tuples
        """
        ...
    @staticmethod
    def from_json(json_str) -> StringThread:
        """Deserialize a thread from JSON string.

        Args:
            json_str: JSON representation of thread

        Returns:
            Deserialized StringThread
        """
        ...
    def to_json(self) -> str:
        """Serialize thread to JSON string.

        Returns:
            JSON representation of thread
        """
        ...
    def with_weight_all_assistant_turns(self) -> StringThread:
        """Mark all assistant turns for training, zero out others.

        Returns:
            New thread with weights adjusted
        """
        ...
    def with_weight_last_assistant_turn(self) -> StringThread:
        """Mark only the last assistant turn for training.

        Returns:
            New thread with weights adjusted
        """
        ...
    def with_weight_assistant_turns_from_index(self, start_index: int) -> StringThread:
        """Mark assistant turns starting from index for training.

        Args:
            start_index: Index of first assistant turn to weight (0-based)

        Returns:
            New thread with weights adjusted
        """
        ...
    def uuid(self) -> str | None:
        """Get the UUID associated with this thread (if any).

        Returns:
            UUID string or None
        """
        ...
    def __repr__(self) -> str: ...

class TokenizedThread:
    """Represents a conversation thread with tokenized content.

    Similar to StringThread but stores token IDs instead of strings.
    Useful for training operations and when you need direct token-level control.

    Attributes:
        metadata: Arbitrary Python object to attach to this thread
    """

    metadata: Any

    def user(self, content: Sequence[int]) -> TokenizedThread:
        """Append a user turn with token IDs.

        Args:
            content: List of token IDs for user message

        Returns:
            New thread with user turn appended
        """
        ...
    def assistant(self, content: Sequence[int]) -> TokenizedThread:
        """Append an assistant turn with token IDs.

        Args:
            content: List of token IDs for assistant message

        Returns:
            New thread with assistant turn appended
        """
        ...
    def last_content(self) -> Optional[list[int]]:
        """Get the token IDs of the last turn.

        Returns:
            List of token IDs, or None if thread is empty
        """
        ...
    def len_last_turn(self) -> int:
        """Get the number of tokens in the last turn.

        Returns:
            Token count of last turn
        """
        ...
    def get_turns(self) -> list[TokenizedTurn]:
        """Get all turns as TokenizedTurn namedtuples.

        Returns:
            List of TokenizedTurn(role, content) tuples
        """
        ...
    def with_weight_all_assistant_turns(self) -> TokenizedThread:
        """Mark all assistant turns for training, zero out others.

        Returns:
            New thread with weights adjusted
        """
        ...
    def with_weight_last_assistant_turn(self) -> TokenizedThread:
        """Mark only the last assistant turn for training.

        Returns:
            New thread with weights adjusted
        """
        ...
    def with_weight_assistant_turns_from_index(self, start_index: int) -> TokenizedThread:
        """Mark assistant turns starting from index for training.

        Args:
            start_index: Index of first assistant turn to weight (0-based)

        Returns:
            New thread with weights adjusted
        """
        ...
    def uuid(self) -> str | None:
        """Get the UUID associated with this thread (if any).

        Returns:
            UUID string or None
        """
        ...
    def __repr__(self) -> str: ...

class TrainingModel(InferenceModel):
    """Model instance for running training operations.

    TrainingModel extends InferenceModel with training capabilities. It supports
    various training algorithms including supervised fine-tuning, PPO, DPO, GRPO,
    and reward modeling.

    Inherits all inference methods from InferenceModel.

    Example:
        ```python
        # Spawn a training model
        model = client.model("model_registry://llama-3.1-8b").with_adapter()
        train_model = await model.spawn_train("my-train", max_batch_size=1024)

        # Supervised fine-tuning
        thread = StringThread([
            ("user", "What is 2+2?"),
            ("assistant", "4")
        ]).with_weight_last_assistant_turn()

        await train_model.train_language_modelling(thread)
        await train_model.optim_step(lr=1e-5, wd=0.01, max_grad_norm=1.0)

        # Save the fine-tuned model
        model_key = await train_model.save("my-fine-tuned-model")
        ```
    """
    async def clone_inf(self) -> InferenceModel:
        """Clone this model as an inference-only instance. Useful for all reinforcement learning algorithms that perform regularization with KL divergence to a reference model.

        Returns:
            New InferenceModel sharing weights with this training model
        """
        ...
    def get_builder_args(self) -> dict[str, Any]: ...
    async def save(self, model_name: str, inference_only: bool = True, ctx: RecipeContext | None = None) -> str:
        """Save the model weights to the model registry.

        Args:
            model_name: Name for the saved model
            inference_only: If True, save only inference weights (default). If False we save the entire optimizer state as well.
            ctx: Optional recipe context for tracking

        Returns:
            Model key that can be used to load the model
        """
        ...
    async def optim_step(
        self, lr: float, wd: float, max_grad_norm: float, skip_nan_gradients: bool = False
    ) -> dict[str, float]:
        """Perform an optimizer step (update model weights).

        Args:
            lr: Learning rate
            wd: Weight decay
            max_grad_norm: Maximum gradient norm for clipping
            skip_nan_gradients: If True, skip step on NaN gradients instead of erroring

        Returns:
            Dictionary of training metrics (loss, grad_norm, etc.)
        """
        ...
    def get_optim_step(self) -> int:
        """Get the current optimizer step counter.

        Returns:
            Current step number
        """
        ...
    def set_optim_step(self, step: int) -> None:
        """Set the optimizer step counter.

        Args:
            step: Step number to set
        """
        ...
    def inf(self) -> InferenceModel:
        """Get inference-only view of this model.

        Returns:
            InferenceModel view (no copy, shares weights)
        """
        ...
    async def train_language_modelling(self, thread: StringThread) -> None:
        """Train with standard language modeling objective (next-token prediction).

        Args:
            thread: Conversation thread with weighted assistant turns
        """
        ...
    async def train_ppo(
        self,
        thread: TokenizedThread,
        trajectory_logprobs: Sequence[float],
        advantages: Sequence[float],
        clip_range: float,
    ) -> None:
        """Train with Proximal Policy Optimization (PPO) objective.

        Args:
            thread: Tokenized conversation thread
            trajectory_logprobs: Log probabilities from trajectory policy
            advantages: Per-token advantage estimates
            clip_range: PPO clipping range (epsilon)
        """
        ...
    async def train_grpo(
        self,
        thread: TokenizedThread,
        trajectory_logprobs: Sequence[float],
        reference_logprobs: Sequence[float],
        advantages: Sequence[float],
        clip_range: float,
        kl_beta: float,
    ) -> None:
        """Train with Group Relative Policy Optimization (GRPO).

        Args:
            thread: Tokenized conversation thread
            trajectory_logprobs: Log probabilities from trajectory policy
            reference_logprobs: Log probabilities from reference policy
            advantages: Per-token advantage estimates
            clip_range: Clipping range
            kl_beta: KL divergence penalty coefficient
        """
        ...
    async def train_gspo(
        self,
        thread: TokenizedThread,
        trajectory_logprobs: Sequence[float],
        reference_logprobs: Sequence[float],
        advantage: Sequence[float],
        left_clip: float,
        right_clip: float,
        kl_beta: float,
    ) -> None:
        """Train with Group Sampling Policy Optimization (GSPO).

        Args:
            thread: Tokenized conversation thread
            trajectory_logprobs: Log probabilities from trajectory policy
            reference_logprobs: Log probabilities from reference policy
            advantage: Advantage estimates
            left_clip: Left clipping bound
            right_clip: Right clipping bound
            kl_beta: KL divergence penalty coefficient
        """
        ...
    async def train_trust_region_mse(
        self,
        thread: TokenizedThread,
        targets: Sequence[float],
        clip_center: Sequence[float],
        clip_range: float,
    ) -> None:
        """Train with trust-region constrained MSE loss (for value functions).

        Args:
            thread: Tokenized conversation thread
            targets: Target values
            clip_center: Center values for clipping
            clip_range: Clipping range
        """
        ...
    async def train_mse(self, thread: StringThread, target: float) -> None:
        """Train with MSE loss on the last token (for reward models).

        Args:
            thread: Conversation thread
            target: Target scalar value
        """
        ...
    async def train_mse_per_token(self, thread: TokenizedThread, targets: Sequence[float]) -> None:
        """Train with per-token MSE loss.

        Args:
            thread: Tokenized conversation thread
            targets: Target value for each weighted token
        """
        ...
    async def train_ranking(self, pos_thread: StringThread, neg_thread: StringThread) -> None:
        """Train with ranking loss (positive example should score higher).

        Args:
            pos_thread: Preferred/positive example
            neg_thread: Rejected/negative example
        """
        ...
    async def train_dpo(
        self,
        sample_pos: StringThread,
        sample_neg: StringThread,
        ref_logprobs_pos: float,
        ref_logprobs_neg: float,
        beta: float,
    ) -> None:
        """Train with Direct Preference Optimization (DPO).

        Args:
            sample_pos: Preferred completion thread
            sample_neg: Rejected completion thread
            ref_logprobs_pos: Reference model logprobs for positive
            ref_logprobs_neg: Reference model logprobs for negative
            beta: DPO temperature parameter
        """
        ...
    def top_p(self, top_p: float) -> TrainingModel: ...
    def temperature(self, temperature: float) -> TrainingModel: ...
    def max_gen_len(self, max_num_tokens: int) -> TrainingModel: ...
    def min_gen_len(self, min_num_tokens: int) -> TrainingModel: ...

class Thread(Enum):
    """Enum of thread types (internal use)."""

    StringThread = ...
    TokenizedThread = ...
    SerializedThread = ...

class JobNotifier:
    """Helper class to report job progress to stdout.

    By default logs progress to stdout. For integration with the Harmony platform,
    use HarmonyJobNotifier instead.

    Example:
        ```python
        notifier = JobNotifier()
        notifier.register_stages(["training", "evaluation"])

        stage = notifier.stage_notifier("training")
        stage.report_progress(tot_num_samples=1000, processed_num_samples=100)
        ```
    """

    def __new__(cls) -> JobNotifier: ...
    def set_monitoring_link(self, monitoring_link: str) -> None:
        """Set a monitoring link (e.g., Weights & Biases URL).

        Args:
            monitoring_link: URL to monitoring dashboard
        """
        ...
    def register_stages(self, stages: Sequence[str]) -> None:
        """Register the stages of this job.

        Args:
            stages: Ordered list of stage names
        """
        ...
    def register_artifact(self, artifact: JobArtifact) -> None:
        """Register an artifact produced by this job.

        Args:
            artifact: Artifact to register
        """
        ...
    def report_error(self, error: str) -> None:
        """Report an error that occurred during the job.

        Args:
            error: Error message
        """
        ...
    def report_progress(
        self,
        stage: str,
        tot_num_samples: Optional[int] = None,
        processed_num_samples: Optional[int] = None,
        monitoring_link: Optional[str] = None,
        checkpoints: Optional[Sequence[str]] = None,
    ) -> None:
        """Report progress for a stage.

        Args:
            stage: Stage name
            tot_num_samples: Total number of samples to process
            processed_num_samples: Number of samples processed so far
            monitoring_link: Optional monitoring dashboard URL
            checkpoints: Optional list of checkpoint identifiers
        """
        ...
    def stage_notifier(self, stage: str) -> StageNotifier:
        """Get a stage-specific notifier.

        Args:
            stage: Stage name

        Returns:
            StageNotifier for the given stage
        """
        ...
    def __repr__(self) -> str: ...

class HarmonyJobNotifier(JobNotifier):
    """Job notifier that reports progress to the Harmony platform.

    Use this instead of JobNotifier when running jobs through the Harmony API
    to integrate with the UI and tracking system.

    Example:
        ```python
        notifier = HarmonyJobNotifier(client, job_id)
        notifier.register_stages(["training", "evaluation"])

        # Register artifacts
        artifact = JobArtifact(
            id="model-v1",
            name="Fine-tuned Model",
            kind="model",
            uri="s3://bucket/models/model-v1"
        )
        notifier.register_artifact(artifact)

        # Report progress
        stage = notifier.stage_notifier("training")
        stage.report_progress(tot_num_samples=1000, processed_num_samples=500)
        ```
    """
    def __new__(cls, client: HarmonyClient, job_id: str) -> HarmonyJobNotifier: ...
    # DOCS_TODO: add example and explain it will show up in the UI
    def set_monitoring_link(self, monitoring_link: str) -> None: ...

class StageNotifier:
    """Helper class to report progress for a specific job stage.

    Get an instance via JobNotifier.stage_notifier() or HarmonyJobNotifier.stage_notifier().
    Provides convenience methods for reporting progress without repeating the stage name.
    """

    def set_monitoring_link(self, monitoring_link: str) -> None:
        """Set monitoring link for this stage.

        Args:
            monitoring_link: URL to monitoring dashboard
        """
        ...
    def report_progress(
        self,
        tot_num_samples: Optional[int] = None,
        processed_num_samples: Optional[int] = None,
        monitoring_link: Optional[str] = None,
        checkpoints: Optional[Sequence[str]] = None,
    ) -> None:
        """Report progress for this stage.

        Args:
            tot_num_samples: Total number of samples to process
            processed_num_samples: Number of samples processed so far
            monitoring_link: Optional monitoring dashboard URL
            checkpoints: Optional list of checkpoint identifiers
        """
        ...

async def get_client(
    addr: str,
    num_gpus: int | None = None,
    api_key: str | None = None,
    use_case: str | None = None,
    compute_pool: str | None = None,
    job_id: str | None = None,
    default_headers: dict[str, str] | None = None,
    ttl_after_disconnect_s: int | None = 30,
    control_plane_url: str | None = None,
    control_plane_api_token: str | None = None,
) -> HarmonyClient:
    """Create and connect a HarmonyClient to workers.

    This is the main entry point for connecting to the Harmony platform.
    The client manages the connection to GPU workers and provides access
    to model building and inference/training operations.

    Args:
        addr: WebSocket address of the deployment (e.g., "ws://localhost:8080")
        num_gpus: Number of GPUs to request (None = use all available)
        api_key: API key for authentication (or set ADAPTIVE_API_KEY env var)
        use_case: Use case identifier (or set ADAPTIVE_USE_CASE env var, default: "default")
        compute_pool: Compute pool to use (or set ADAPTIVE_COMPUTE_POOL env var, default: "default")
        job_id: Job ID for tracking (or set ADAPTIVE_JOB_ID env var)
        default_headers: Additional HTTP headers for the connection
        ttl_after_disconnect_s: Keep session alive for this many seconds after disconnect (default: 30)
        control_plane_url: URL of control plane for fetching model/dataset/grader configs
        control_plane_api_token: API token for authenticating with the control plane

    Returns:
        Connected HarmonyClient instance

    Example:
        ```python
        from harmony_client import get_client

        # Basic connection
        client = await get_client("ws://localhost:8080", num_gpus=1)

        # With authentication
        client = await get_client(
            "wss://api.adaptive.com",
            num_gpus=4,
            api_key="my-api-key",
            control_plane_url="https://api.adaptive.com"
        )

        # Use as context manager
        async with await get_client(...) as client:
            model = client.model("model_registry://llama-3.1-8b")
            # ... use model
        # Connection closed automatically
        ```
    """
    ...
