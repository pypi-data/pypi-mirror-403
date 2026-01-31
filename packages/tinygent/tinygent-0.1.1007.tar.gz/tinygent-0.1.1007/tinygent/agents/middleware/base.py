from typing import Any
from typing import Generic
from typing import TypeVar

from pydantic import Field

from tinygent.core.datamodels.middleware import AbstractMiddleware
from tinygent.core.datamodels.middleware import AbstractMiddlewareConfig
from tinygent.core.datamodels.tool import AbstractTool
from tinygent.core.types.io.llm_io_input import TinyLLMInput

T = TypeVar('T', bound='TinyBaseMiddleware')


class TinyBaseMiddlewareConfig(AbstractMiddlewareConfig[T], Generic[T]):
    """Configuration for BaseMiddleware."""

    type: Any = Field(default='base')

    def build(self) -> T:
        """Build the BaseMiddleware from the configuration."""
        raise NotImplementedError('Subclasses must implement this method.')


class TinyBaseMiddleware(AbstractMiddleware):
    """Base class for agent middleware.

    Middleware can mutate the kwargs dict in-place to override/add parameters
    that will be visible to subsequent middleware and the agent.
    """

    async def before_llm_call(
        self, *, run_id: str, llm_input: TinyLLMInput, kwargs: dict[str, Any]
    ) -> None:
        pass

    async def after_llm_call(
        self,
        *,
        run_id: str,
        llm_input: TinyLLMInput,
        result: Any,
        kwargs: dict[str, Any],
    ) -> None:
        pass

    async def before_tool_call(
        self,
        *,
        run_id: str,
        tool: AbstractTool,
        args: dict[str, Any],
        kwargs: dict[str, Any],
    ) -> None:
        pass

    async def after_tool_call(
        self,
        *,
        run_id: str,
        tool: AbstractTool,
        args: dict[str, Any],
        result: Any,
        kwargs: dict[str, Any],
    ) -> None:
        pass

    async def on_plan(self, *, run_id: str, plan: str, kwargs: dict[str, Any]) -> None:
        pass

    async def on_reasoning(
        self, *, run_id: str, reasoning: str, kwargs: dict[str, Any]
    ) -> None:
        pass

    async def on_tool_reasoning(
        self, *, run_id: str, reasoning: str, kwargs: dict[str, Any]
    ) -> None:
        pass

    async def on_answer(
        self, *, run_id: str, answer: str, kwargs: dict[str, Any]
    ) -> None:
        pass

    async def on_answer_chunk(
        self, *, run_id: str, chunk: str, idx: str, kwargs: dict[str, Any]
    ) -> None:
        pass

    async def on_error(
        self, *, run_id: str, e: Exception, kwargs: dict[str, Any]
    ) -> None:
        pass


def register_middleware(name: str):
    def decorator(cls: type[T]) -> type[T]:
        from tinygent.core.runtime.middleware_catalog import GlobalMiddlewareCatalog

        GlobalMiddlewareCatalog().get_active_catalog().register(
            name,
            cls,
        )
        return cls

    return decorator
