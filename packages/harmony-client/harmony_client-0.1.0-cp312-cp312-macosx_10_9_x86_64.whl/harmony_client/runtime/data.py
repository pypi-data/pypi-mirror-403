import json
import types
from typing import Annotated, Literal, Self, Union, get_args, get_origin

from pydantic import BaseModel, Field


class InputConfig(BaseModel):
    def __init_subclass__(cls, **kwargs):
        # Add union_variant BEFORE calling super (before Pydantic processes it)
        if not hasattr(cls, "__annotations__"):
            cls.__annotations__ = {}
        if "union_variant" not in cls.__annotations__:
            cls.__annotations__["union_variant"] = Annotated[Literal[cls.__name__], Field(default=cls.__name__)]
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "__annotations__"):
            for field_name, field_type in cls.__annotations__.items():
                origin = get_origin(field_type)
                if origin is Union or origin is types.UnionType:
                    # Add discriminator to the union annotation
                    cls.__annotations__[field_name] = Annotated[field_type, Field(discriminator="union_variant")]

                    # Add union_variant field to each variant class
                    variant_types = get_args(field_type)
                    for variant_type in variant_types:
                        # Skip None (for Optional types)
                        if variant_type is type(None):
                            continue

                        # Add union_variant: Literal["ClassName"] to the variant
                        # if not already present
                        if (
                            hasattr(variant_type, "__annotations__")
                            and "union_variant" not in variant_type.__annotations__
                        ):
                            variant_type.__annotations__["union_variant"] = Literal[variant_type.__name__]
                            # Set default value
                            setattr(variant_type, "union_variant", variant_type.__name__)

    @classmethod
    def load_from_file(cls, json_file) -> Self:
        with open(json_file) as f:
            data = json.load(f)
        return cls.model_validate(data)


from .dto.AdaptiveDataset import AdaptiveDatasetKind
from .dto.AdaptiveGrader import (
    AdaptiveGrader as AdaptiveGrader,
)
from .dto.AdaptiveGrader import (
    Judge as CustomJudge,
)
from .dto.AdaptiveGrader import (
    JudgeExample as CustomJudgeExample,
)
from .dto.AdaptiveGrader import (
    Prebuilt as PrebuiltJudge,
)
from .dto.AdaptiveGrader import (
    PrebuiltConfigKey,
)
from .dto.AdaptiveGrader import (
    Remote as RemoteRewardEndpoint,
)

__all__ = [
    "InputConfig",
    "AdaptiveDatasetKind",
    "AdaptiveGrader",
    "CustomJudge",
    "CustomJudgeExample",
    "PrebuiltJudge",
    "PrebuiltConfigKey",
    "RemoteRewardEndpoint",
]
