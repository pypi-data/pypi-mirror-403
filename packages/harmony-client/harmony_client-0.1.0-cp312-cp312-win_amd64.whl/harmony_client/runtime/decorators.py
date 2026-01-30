from typing import Any, Callable, TypeVar, overload

from harmony_client.runtime.context import RecipeContext
from harmony_client.runtime.data import InputConfig

IN = TypeVar("IN", bound=InputConfig)


@overload
def recipe_main[IN: InputConfig](func: Callable[[IN, RecipeContext], Any]): ...


@overload
def recipe_main(func: Callable[[RecipeContext], Any]): ...


def recipe_main(func):
    func.is_recipe_main = True
    return func
