import llm
from llm.default_plugins.openai_models import _Shared
from llm.default_plugins.openai_models import (
    remove_dict_none_values,
    combine_chunks,
)
import openai
from openai._streaming import SSEDecoder, ServerSentEvent
import json


GREENPT_API_BASE = "https://api.greenpt.ai/v1"


class ImpactCapturingSSEDecoder(SSEDecoder):
    """
    SSE Decoder that captures GreenPT impact data from streaming responses.
    
    GreenPT sends impact data in the final SSE data event (with empty choices).
    Unlike Neuralwatt which uses SSE comments, GreenPT follows the standard SSE
    data format, but includes an 'impact' field that the OpenAI SDK's Pydantic
    models would otherwise strip.
    
    We capture the raw JSON to preserve the impact data before Pydantic parsing.
    """
    
    def __init__(self):
        super().__init__()
        self.impact_data = None
    
    def decode(self, line: str) -> ServerSentEvent | None:
        # For data lines, check for impact before standard processing
        if line.startswith("data: ") and line != "data: [DONE]":
            data_str = line[6:]  # Skip "data: " prefix
            try:
                data = json.loads(data_str)
                # GreenPT sends impact in the final chunk (empty choices, has impact)
                if "impact" in data:
                    self.impact_data = data["impact"]
            except json.JSONDecodeError:
                pass
        
        # Fall back to standard SSE decoding
        return super().decode(line)


class GreenPTOpenAI(openai.OpenAI):
    """
    OpenAI client subclass that captures GreenPT impact data from streams.
    
    Overrides _make_sse_decoder() to use ImpactCapturingSSEDecoder, which
    captures the impact data that GreenPT sends in the final SSE event.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_decoder = None
    
    def _make_sse_decoder(self):
        self._last_decoder = ImpactCapturingSSEDecoder()
        return self._last_decoder
    
    def get_last_impact_data(self):
        """Get impact data captured from the last streaming request."""
        if self._last_decoder:
            return self._last_decoder.impact_data
        return None


class GreenPTAsyncOpenAI(openai.AsyncOpenAI):
    """
    AsyncOpenAI client subclass that captures GreenPT impact data from streams.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_decoder = None
    
    def _make_sse_decoder(self):
        self._last_decoder = ImpactCapturingSSEDecoder()
        return self._last_decoder
    
    def get_last_impact_data(self):
        """Get impact data captured from the last streaming request."""
        if self._last_decoder:
            return self._last_decoder.impact_data
        return None


@llm.hookimpl
def register_models(register):
    """Register GreenPT models with energy/impact tracking."""
    # GreenPT native models
    register(
        GreenPTChat(
            "greenpt/green-l",
            model_name="green-l",
            api_base=GREENPT_API_BASE,
        ),
        GreenPTAsyncChat(
            "greenpt/green-l",
            model_name="green-l",
            api_base=GREENPT_API_BASE,
        ),
        aliases=("greenpt-green-l", "greenpt-large"),
    )
    register(
        GreenPTChat(
            "greenpt/green-l-raw",
            model_name="green-l-raw",
            api_base=GREENPT_API_BASE,
        ),
        GreenPTAsyncChat(
            "greenpt/green-l-raw",
            model_name="green-l-raw",
            api_base=GREENPT_API_BASE,
        ),
        aliases=("greenpt-green-l-raw",),
    )
    register(
        GreenPTChat(
            "greenpt/green-r",
            model_name="green-r",
            api_base=GREENPT_API_BASE,
        ),
        GreenPTAsyncChat(
            "greenpt/green-r",
            model_name="green-r",
            api_base=GREENPT_API_BASE,
        ),
        aliases=("greenpt-green-r", "greenpt-reasoning"),
    )
    register(
        GreenPTChat(
            "greenpt/green-r-raw",
            model_name="green-r-raw",
            api_base=GREENPT_API_BASE,
        ),
        GreenPTAsyncChat(
            "greenpt/green-r-raw",
            model_name="green-r-raw",
            api_base=GREENPT_API_BASE,
        ),
        aliases=("greenpt-green-r-raw",),
    )
    # Third-party models available on GreenPT
    register(
        GreenPTChat(
            "greenpt/llama-3.3-70b-instruct",
            model_name="llama-3.3-70b-instruct",
            api_base=GREENPT_API_BASE,
        ),
        GreenPTAsyncChat(
            "greenpt/llama-3.3-70b-instruct",
            model_name="llama-3.3-70b-instruct",
            api_base=GREENPT_API_BASE,
        ),
        aliases=("greenpt-llama-70b",),
    )
    register(
        GreenPTChat(
            "greenpt/deepseek-r1-distill-llama-70b",
            model_name="deepseek-r1-distill-llama-70b",
            api_base=GREENPT_API_BASE,
        ),
        GreenPTAsyncChat(
            "greenpt/deepseek-r1-distill-llama-70b",
            model_name="deepseek-r1-distill-llama-70b",
            api_base=GREENPT_API_BASE,
        ),
        aliases=("greenpt-deepseek-r1",),
    )
    register(
        GreenPTChat(
            "greenpt/mistral-nemo-instruct-2407",
            model_name="mistral-nemo-instruct-2407",
            api_base=GREENPT_API_BASE,
        ),
        GreenPTAsyncChat(
            "greenpt/mistral-nemo-instruct-2407",
            model_name="mistral-nemo-instruct-2407",
            api_base=GREENPT_API_BASE,
        ),
        aliases=("greenpt-mistral-nemo",),
    )
    register(
        GreenPTChat(
            "greenpt/qwen3-235b-a22b-instruct-2507",
            model_name="qwen3-235b-a22b-instruct-2507",
            api_base=GREENPT_API_BASE,
        ),
        GreenPTAsyncChat(
            "greenpt/qwen3-235b-a22b-instruct-2507",
            model_name="qwen3-235b-a22b-instruct-2507",
            api_base=GREENPT_API_BASE,
        ),
        aliases=("greenpt-qwen3",),
    )


class GreenPTShared(_Shared):
    """Shared functionality for GreenPT models."""
    
    def __init__(self, *args, **kwargs):
        api_key_name = kwargs.pop("api_key_name", None)
        super().__init__(*args, **kwargs)
        if api_key_name:
            self.needs_key = api_key_name
        else:
            self.needs_key = "greenpt"
        self.key_env_var = "GREENPT_API_KEY"

    def __str__(self):
        return "GreenPT: {}".format(self.model_id)
    
    def get_client(self, key, *, async_=False):
        """
        Get an OpenAI client configured for GreenPT.
        
        Uses GreenPTOpenAI/GreenPTAsyncOpenAI subclasses that capture
        impact data from streaming responses.
        """
        import os
        from llm.utils import logging_client
        
        kwargs = {}
        if self.api_base:
            kwargs["base_url"] = self.api_base
        if self.needs_key:
            kwargs["api_key"] = self.get_key(key)
        else:
            kwargs["api_key"] = "DUMMY_KEY"
        if self.headers:
            kwargs["default_headers"] = self.headers
        if os.environ.get("LLM_OPENAI_SHOW_RESPONSES"):
            kwargs["http_client"] = logging_client()
        
        if async_:
            return GreenPTAsyncOpenAI(**kwargs)
        else:
            return GreenPTOpenAI(**kwargs)


class GreenPTChat(GreenPTShared, llm.KeyModel):
    """Synchronous GreenPT chat model with energy impact tracking."""
    
    default_max_tokens = None

    def execute(self, prompt, stream, response, conversation=None, key=None):
        """
        Execute a chat completion request to the GreenPT API,
        preserving returned impact/energy data in llm's local logs.db.
        
        GreenPT sends impact data:
        - Non-streaming: in the response body as 'impact' field
        - Streaming: in the final SSE data event with empty choices and 'impact' field
        """
        if prompt.system and not self.allows_system_prompt:
            raise NotImplementedError("Model does not support system prompts")
        
        messages = self.build_messages(prompt, conversation)
        kwargs = self.build_kwargs(prompt, stream)
        client = self.get_client(key)
        usage = None

        if stream:
            completion = client.chat.completions.create(
                model=self.model_name or self.model_id,
                messages=messages,
                stream=True,
                **kwargs,
            )
            chunks = []
            tool_calls = {}

            for chunk in completion:
                chunks.append(chunk)
                if chunk.usage:
                    usage = chunk.usage.model_dump()
                if chunk.choices and chunk.choices[0].delta:
                    for tool_call in chunk.choices[0].delta.tool_calls or []:
                        if tool_call.function.arguments is None:
                            tool_call.function.arguments = ""
                        index = tool_call.index
                        if index not in tool_calls:
                            tool_calls[index] = tool_call
                        else:
                            tool_calls[
                                index
                            ].function.arguments += tool_call.function.arguments
                try:
                    content = chunk.choices[0].delta.content
                except IndexError:
                    content = None
                if content is not None:
                    yield content
            
            # Combine chunks and add impact data
            response_json = remove_dict_none_values(combine_chunks(chunks))
            impact_data = client.get_last_impact_data()
            if impact_data:
                response_json["impact"] = impact_data
            response.response_json = response_json
            
            if tool_calls:
                for value in tool_calls.values():
                    response.add_tool_call(
                        llm.ToolCall(
                            tool_call_id=value.id,
                            name=value.function.name,
                            arguments=json.loads(value.function.arguments),
                        )
                    )
        else:
            completion = client.chat.completions.create(
                model=self.model_name or self.model_id,
                messages=messages,
                stream=False,
                **kwargs,
            )
            usage = completion.usage.model_dump() if completion.usage else None
            # Preserve ALL data including impact
            response_data = completion.model_dump()
            response.response_json = remove_dict_none_values(d=response_data)
            
            for tool_call in completion.choices[0].message.tool_calls or []:
                response.add_tool_call(
                    llm.ToolCall(
                        tool_call_id=tool_call.id,
                        name=tool_call.function.name,
                        arguments=json.loads(tool_call.function.arguments)
                        if isinstance(tool_call.function.arguments, str)
                        else tool_call.function.arguments,
                    )
                )
            if completion.choices[0].message.content is not None:
                yield completion.choices[0].message.content
        
        self.set_usage(response, usage)
        response._prompt_json = {"messages": messages}


class GreenPTAsyncChat(GreenPTShared, llm.AsyncKeyModel):
    """Asynchronous GreenPT chat model with energy impact tracking."""
    
    default_max_tokens = None

    async def execute(self, prompt, stream, response, conversation=None, key=None):
        """
        Execute an async chat completion request to the GreenPT API,
        preserving returned impact/energy data in llm's local logs.db.
        """
        if prompt.system and not self.allows_system_prompt:
            raise NotImplementedError("Model does not support system prompts")
        
        messages = self.build_messages(prompt, conversation)
        kwargs = self.build_kwargs(prompt, stream)
        client = self.get_client(key, async_=True)
        usage = None

        if stream:
            completion = await client.chat.completions.create(
                model=self.model_name or self.model_id,
                messages=messages,
                stream=True,
                **kwargs,
            )
            chunks = []
            tool_calls = {}

            async for chunk in completion:
                chunks.append(chunk)
                if chunk.usage:
                    usage = chunk.usage.model_dump()
                if chunk.choices and chunk.choices[0].delta:
                    for tool_call in chunk.choices[0].delta.tool_calls or []:
                        if tool_call.function.arguments is None:
                            tool_call.function.arguments = ""
                        index = tool_call.index
                        if index not in tool_calls:
                            tool_calls[index] = tool_call
                        else:
                            tool_calls[
                                index
                            ].function.arguments += tool_call.function.arguments
                try:
                    content = chunk.choices[0].delta.content
                except IndexError:
                    content = None
                if content is not None:
                    yield content

            # Combine chunks and add impact data
            response_json = remove_dict_none_values(combine_chunks(chunks))
            impact_data = client.get_last_impact_data()
            if impact_data:
                response_json["impact"] = impact_data
            response.response_json = response_json

            if tool_calls:
                for value in tool_calls.values():
                    response.add_tool_call(
                        llm.ToolCall(
                            tool_call_id=value.id,
                            name=value.function.name,
                            arguments=json.loads(value.function.arguments),
                        )
                    )
        else:
            completion = await client.chat.completions.create(
                model=self.model_name or self.model_id,
                messages=messages,
                stream=False,
                **kwargs,
            )
            usage = completion.usage.model_dump() if completion.usage else None
            # Preserve ALL data including impact
            response_data = completion.model_dump()
            response.response_json = remove_dict_none_values(response_data)

            for tool_call in completion.choices[0].message.tool_calls or []:
                response.add_tool_call(
                    llm.ToolCall(
                        tool_call_id=tool_call.id,
                        name=tool_call.function.name,
                        arguments=json.loads(tool_call.function.arguments)
                        if isinstance(tool_call.function.arguments, str)
                        else tool_call.function.arguments,
                    )
                )
            if completion.choices[0].message.content is not None:
                yield completion.choices[0].message.content
        
        self.set_usage(response, usage)
        response._prompt_json = {"messages": messages}
