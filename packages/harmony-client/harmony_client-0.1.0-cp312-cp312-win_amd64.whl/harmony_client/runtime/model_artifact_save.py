from collections.abc import Awaitable, Callable

from harmony_client import TrainingModel
from harmony_client.artifacts.model_artifact import ModelArtifact
from harmony_client.runtime import RecipeContext


async def save_with_artifact(
    model: TrainingModel,
    model_name: str,
    inference_only: bool = True,
    ctx: RecipeContext | None = None,
    original_save_method: Callable[[TrainingModel, str, bool], Awaitable[str]] | None = None,
) -> str:
    if original_save_method is None:
        raise ValueError("original_save_method must be provided")

    real_model_key = await original_save_method(model, model_name, inference_only)

    if ctx is not None:
        ModelArtifact(real_model_key, ctx)

    return real_model_key
