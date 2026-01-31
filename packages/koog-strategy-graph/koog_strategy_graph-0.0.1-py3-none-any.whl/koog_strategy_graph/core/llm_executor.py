from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, TypeVar, Union

from ..base.prompt_executor import PromptExecutor, PromptExecutorResult
from .response_processor import ResponseProcessor
from .streaming import StreamFrame
from .tools import ToolDescriptor

from .messages import Prompt, ResponseMessage, ToolResultMessage, UserMessage
from .structured import JsonSchema, StructureFixingParser, StructuredResult, execute_structured

T = TypeVar("T")


class ToolChoice:
    """
    Koog-like tool choice modes.
    """

    AUTO = "auto"
    REQUIRED = "required"
    NONE = "none"

    @staticmethod
    def named(tool_name: str) -> str:
        return str(tool_name)


@dataclass(frozen=True)
class LLMResponse:
    """
    Parsed response from an LLM call.
    """

    responses: List[ResponseMessage]
    raw: Any


@dataclass
class LLMExecutor:
    """
    Koog-parity LLM executor wrapper.

    Kotlin reference: `AIAgentLLMSession` calls a `PromptExecutor` with:
    - prompt (message history)
    - model
    - params
    - tools
    - optional response processor

    This wrapper is intentionally provider-neutral and does NOT depend on LangChain.
    """

    executor: PromptExecutor
    default_model: Any = None
    default_params: Dict[str, Any] = field(default_factory=dict)
    response_processor: Optional[ResponseProcessor] = None

    def with_overrides(
        self,
        *,
        model: Any = None,
        params: Optional[Dict[str, Any]] = None,
        response_processor: Optional[ResponseProcessor] = None,
    ) -> "LLMExecutor":
        merged = dict(self.default_params)
        if params:
            merged.update(dict(params))
        return LLMExecutor(
            executor=self.executor,
            default_model=(model if model is not None else self.default_model),
            default_params=merged,
            response_processor=(response_processor if response_processor is not None else self.response_processor),
        )

    def invoke(
        self,
        prompt: Prompt,
        *,
        tools: Optional[Sequence[ToolDescriptor]] = None,
        tool_choice: Optional[str] = None,
        model: Any = None,
        params: Optional[Dict[str, Any]] = None,
        response_processor: Optional[ResponseProcessor] = None,
    ) -> LLMResponse:
        effective_model = model if model is not None else self.default_model
        effective_params: Dict[str, Any] = dict(self.default_params)
        if params:
            effective_params.update(dict(params))

        effective_tools: List[ToolDescriptor] = []
        if tool_choice != ToolChoice.NONE:
            effective_tools = list(tools or [])

        result: PromptExecutorResult = self.executor.execute(
            prompt=prompt,
            model=effective_model,
            params=effective_params,
            tools=effective_tools,
            tool_choice=tool_choice,
        )

        responses = list(result.responses)
        rp = response_processor if response_processor is not None else self.response_processor
        if rp is not None:
            responses = list(
                rp.process(
                    executor=self,
                    prompt=prompt,
                    model=effective_model,
                    tools=list(effective_tools),
                    responses=responses,
                )
            )
        return LLMResponse(responses=responses, raw=result.raw)

    def invoke_streaming(
        self,
        prompt: Prompt,
        *,
        tools: Optional[Sequence[ToolDescriptor]] = None,
        tool_choice: Optional[str] = None,
        model: Any = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        """
        Stream an LLM response as `StreamFrame`s.

        Provider-agnostic contract:
        - Executors should yield `StreamFrame(type="append", ...)` for incremental text.
        - If the provider supports tool calling in streaming mode, it may also yield
          `StreamFrame(type="tool_call", tool_call_id, tool_name, tool_args, ...)` for *completed* tool calls.
        - The stream should end with `StreamFrame(type="end", finish_reason=..., ...)`.
        """
        effective_model = model if model is not None else self.default_model
        effective_params: Dict[str, Any] = dict(self.default_params)
        if params:
            effective_params.update(dict(params))
        effective_tools: List[ToolDescriptor] = []
        if tool_choice != ToolChoice.NONE:
            effective_tools = list(tools or [])
        return self.executor.stream(
            prompt=prompt,
            model=effective_model,
            params=effective_params,
            tools=effective_tools,
            tool_choice=tool_choice,
        )

    def invoke_structured(
        self,
        prompt: Prompt,
        *,
        schema: Union[JsonSchema, Dict[str, Any]],
        examples: Optional[Sequence[Any]] = None,
        fixing_parser: Optional[StructureFixingParser] = None,
        decode: Optional[Callable[[Any], T]] = None,
        model: Any = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> StructuredResult[T]:
        """
        Koog-parity structured output entrypoint at the LLM/session layer.
        """
        return execute_structured(
            llm=self,
            prompt=prompt,
            schema=schema,
            examples=examples,
            fixing_parser=fixing_parser,
            decode=decode,
            model=model,
            params=params,
        )

    def moderate_message(self, message: str, *, model: Any = None) -> Dict[str, Any]:
        """
        Optional moderation API.

        For Koog parity, this is executor-dependent. If the configured PromptExecutor supports
        moderation, it can expose a `moderate_message(...)` method.
        """
        fn = getattr(self.executor, "moderate_message", None)
        if fn is None:
            raise RuntimeError("PromptExecutor does not support moderation.")
        return fn(message=message, model=model)


@dataclass
class AgentSession:
    """
    Koog-like mutable session: prompt history + tool choice.
    """

    prompt: Prompt = field(default_factory=Prompt)
    tool_choice: Optional[str] = None
    llm_tools: List[ToolDescriptor] = field(default_factory=list)

    def append(self, *msgs: Any) -> None:
        self.prompt.append(*msgs)

    def append_user(self, text: str) -> None:
        self.prompt.append(UserMessage(text=text))

    def append_tool_result(self, *, tool: str, tool_call_id: Optional[str], result: Any) -> None:
        self.prompt.append(ToolResultMessage(tool=tool, tool_call_id=tool_call_id, result=result))

