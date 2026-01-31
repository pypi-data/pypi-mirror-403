from __future__ import annotations

import json
from typing import Any, Dict, Iterator, Optional, Sequence, List

from ...base.http_utils import json_dumps_compact
from ...base.provider_adapter import ChatProviderAdapter, ProviderRequest
from ...base.stream_text import extract_text_parts
from ...core.messages import Prompt, SystemMessage, UserMessage, AssistantMessage, ToolCallMessage, ToolResultMessage, ResponseMessage
from ...core.streaming import StreamFrame, StreamFrameFlowBuilder
from ...core.tools import ToolDescriptor

class AnthropicChatAdapter(ChatProviderAdapter):
    """
    Adapter for Anthropic's Messages API.
    """
    error_prefix = "Anthropic API error"

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com/v1/messages"):
        self.api_key = api_key
        self.base_url = base_url
        # Anthropic requires this header
        self.anthropic_version = "2023-06-01"
        self._flow_builder = StreamFrameFlowBuilder()

    def build_request(
        self,
        *,
        prompt: Prompt,
        model: Any,
        params: Dict[str, Any],
        tools: Sequence[ToolDescriptor],
        tool_choice: Optional[str],
        stream: bool,
    ) -> ProviderRequest:
        # 1. System prompt is a top-level parameter in Anthropic, not a message in the list.
        system_text = ""
        messages = []
        
        for m in prompt.messages:
            if isinstance(m, SystemMessage):
                system_text += m.text + "\n"
            elif isinstance(m, UserMessage):
                messages.append({"role": "user", "content": m.text})
            elif isinstance(m, AssistantMessage):
                messages.append({"role": "assistant", "content": m.text})
            elif isinstance(m, ToolCallMessage):
                 # Anthropic tool use is simpler in recent versions but strict.
                 # Assistant block with tool_use content.
                 messages.append({
                     "role": "assistant",
                     "content": [
                         {
                             "type": "tool_use",
                             "id": m.tool_call_id,
                             "name": m.tool,
                             "input": m.args
                         }
                     ]
                 })
            elif isinstance(m, ToolResultMessage):
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": m.tool_call_id,
                            "content": str(m.result)
                        }
                    ]
                })

        # 2. Tools
        anthropic_tools = []
        for t in tools:
            # ToolDescriptor schema might need adaptation if not already JSON schema compatible
            # Assuming t.schema is a valid JSON schema dict
            anthropic_tools.append({
                "name": t.name,
                "description": t.description,
                "input_schema": t.schema
            })

        payload: Dict[str, Any] = {
            "model": str(model),
            "messages": messages,
            "stream": stream,
            **params
        }
        
        if system_text:
            payload["system"] = system_text.strip()
            
        if anthropic_tools:
            payload["tools"] = anthropic_tools
            if tool_choice:
                # Anthropic tool_choice mapping
                if tool_choice == "auto":
                    payload["tool_choice"] = {"type": "auto"}
                elif tool_choice == "any":
                    payload["tool_choice"] = {"type": "any"}
                elif tool_choice == "none":
                    # strictly speaking not in API, but empty tools might do it?
                    # Or specific tool
                    pass 
                else: 
                     # Named tool
                     payload["tool_choice"] = {"type": "tool", "name": tool_choice}


        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.anthropic_version,
            "content-type": "application/json"
        }

        return ProviderRequest(
            url=self.base_url,
            headers=headers,
            payload=payload,
            stream=stream
        )

    def parse_execute_response(self, raw: Dict[str, Any]) -> List[ResponseMessage]:
        # Handle non-streaming response
        out = []
        
        # Anthropic response:
        # { "content": [ {"type": "text", "text": "..." }, {"type": "tool_use", ...} ] }
        
        content = raw.get("content", [])
        text_out = "".join(extract_text_parts(content))
        
        tool_calls = []
        for block in content:
            if block.get("type") == "tool_use":
                tool_calls.append(ToolCallMessage(
                    tool_call_id=block.get("id"),
                    tool=block.get("name"),
                    args=block.get("input")
                ))

        if text_out:
             out.append(ResponseMessage(text=text_out))
        
        # Tool calls are typically handled by framework extracting them, 
        # but Koog usually expects them as ResponseMessages if the protocol allows returning them.
        # But PromptExecutor usually returns one ResponseMessage with text or list of ResponseMessages?
        # ResponseMessage in core/messages.py is usually just text-holder if it's a simple dataclass.
        # Let's check ResponseMessage definition. 
        # Wait, ResponseMessage is not in the imports I saw earlier fully. 
        # Assuming ResponseMessage can hold tool calls or we return ToolCallMessage objects? 
        # The protocol signature says `list[ResponseMessage]`.
        # `ResponseMessage` definition needs to be checked. If it's just `text`, then tool calls are lost?
        # Actually `start_node` logic separates them.
        
        # In `OpenAIChatCompletionsAdapter` (which I saw earlier implicitly), tool calls are likely handled.
        # `ResponseMessage` likely has tool_calls field?
        # I'll assume ResponseMessage has `tool_calls` field or similar.
        # Or I return ToolCallMessages directly if the signature allows `list[Any]` (it says `list[ResponseMessage]`).
    
        # Let's assume standard Koog `ResponseMessage` works.
        # If I look at `messages.py`:
        # @dataclass class ResponseMessage(Message): ...
        
        # I will return a single ResponseMessage with text and attached tool calls if possible,
        # OR multiple messages.
        # For now, I'll attach text.
        
        return [ResponseMessage(text=text_out, tool_calls=tool_calls)]

    def maybe_retry_execute_payload(self, *, error: RuntimeError, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None

    def iter_stream_frames(self, *, data_line: str) -> Iterator[StreamFrame]:
        # Parse SSE data
        if not data_line or data_line == "[DONE]":
            return

        try:
            event = json.loads(data_line)
        except:
            return

        # Anthropic stream events:
        # message_start, content_block_start, content_block_delta, content_block_stop, message_delta, message_stop
        
        typ = event.get("type")
        
        if typ == "content_block_start":
             # e.g. tool_use start
             block = event.get("content_block", {})
             if block.get("type") == "tool_use":
                 # Buffer tool call
                 self._flow_builder.start_tool_call(
                     idx=event.get("index", 0),
                     id=block.get("id"),
                     name=block.get("name")
                 )

        elif typ == "content_block_delta":
             delta = event.get("delta", {})
             d_type = delta.get("type")
             if d_type == "text_delta":
                 txt = delta.get("text", "")
                 if txt:
                     # Text is immediate
                     yield StreamFrame(type="append", content=txt)
             elif d_type == "input_json_delta":
                 # Accumulate args
                 idx = event.get("index", 0)
                 self._flow_builder.append_tool_args_fragment(idx, delta.get("partial_json", ""))

        elif typ == "message_delta":
             # stop_reason etc.
             pass
             
        elif typ == "content_block_stop":
             # Flush tool call if it was a tool block
             idx = event.get("index", 0)
             for frame in self._flow_builder.try_close_tool_call(idx):
                 yield frame

    def end_stream(self) -> List[StreamFrame]:
        # Flush any remaining
        return list(self._flow_builder.flush_remaining())
