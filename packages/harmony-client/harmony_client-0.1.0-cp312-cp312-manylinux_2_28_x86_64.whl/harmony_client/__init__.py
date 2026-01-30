# ruff: noqa: F403, F401
from typing import TYPE_CHECKING

from .harmony_client import (
    EvalSample as EvalSample,
)
from .harmony_client import (
    EvalSampleInteraction as EvalSampleInteraction,
)
from .harmony_client import (
    EvaluationArtifactBase as EvaluationArtifactBase,
)
from .harmony_client import (
    Grade as Grade,
)
from .harmony_client import (
    HarmonyClient as HarmonyClient,
)
from .harmony_client import (
    HarmonyJobNotifier as HarmonyJobNotifier,
)
from .harmony_client import (
    InferenceModel as InferenceModel,
)
from .harmony_client import (
    JobArtifact as JobArtifact,
)
from .harmony_client import (
    JobNotifier as JobNotifier,
)
from .harmony_client import (
    ModelBuilder as ModelBuilder,
)
from .harmony_client import (
    StageNotifier as StageNotifier,
)
from .harmony_client import (
    StringThread as StringThread,
)
from .harmony_client import (
    TokenizedThread as TokenizedThread,
)
from .harmony_client import (
    TrainingModel as TrainingModel,
)
from .harmony_client import (
    get_client as get_client,
)

if TYPE_CHECKING:
    from .harmony_client import StringTurn as StringTurn
else:
    from typing import NamedTuple

    class StringTurn(NamedTuple):
        role: str
        content: str


# Ensure key classes are available at module level
__all__ = [
    "StringThread",
    "StringTurn",
    "TokenizedThread",
    "InferenceModel",
    "ModelBuilder",
    "TrainingModel",
    "HarmonyClient",
    "get_client",
    "Grade",
    "EvalSample",
    "EvalSampleInteraction",
    "JobArtifact",
    "JobNotifier",
    "HarmonyJobNotifier",
    "StageNotifier",
    "EvaluationArtifactBase",
]
