# %%
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import json
import logging
from abc import abstractmethod
from dataclasses import Field, dataclass
from functools import cached_property
from inspect import isawaitable
from textwrap import dedent
from typing import Annotated, Awaitable, Optional, Any

from openai import AsyncOpenAI
from stackraise import model

from openai.types.responses import (
    ResponseInputFileParam,
    ResponseInputImageParam,
    ResponseInputParam,
    ResponseFunctionToolCall,
    ResponseOutputMessage, 
)

logger = logging.getLogger(__name__)


EMBEDDED_IMAGE_URL_CONTENT_TYPE = {
    "image/png",
    "image/jpeg",
}


# # mime types that can be embedded in the message body via URL encoding
# EMBEDDED_IMAGE_URL_CONTENT_TYPE = {
#     "image/png",
#     "image/jpeg",
# }

# CONTENT_TYPE_TO_TOOL_MAPPING = {
#     "image/jpeg": "code_interpreter",
#     "image/png": "code_interpreter",
#     "application/pdf": "file_search",
#     "text/plain": "file_search",
#     "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "file_search",
#     "application/msword": "file_search",
#     "application/vnd.ms-excel": "code_interpreter",
#     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "code_interpreter",
#     "application/vnd.openxmlformats-officedocument.spreadsheetml.presentation": "code_interpreter",
# }


class StopRPA[R](Exception):
    """Exception to signal that the RPA process should finish with a result."""

    def __init__(self, status: str, result: R):
        self._status = status
        self._result = result

    @property
    def result(self) -> R:
        return self._result

    @property
    def status(self) -> str:
        return self._status


class Rpa[C, R]:  # TODO: RpaBase
    """
    Assistant that processes emails using OpenAI's API to extract intentions and relevant data
    C: Context
    R: Result
    """

    class _ToolBase[R](model.Base):
        @abstractmethod
        def run(self, rpa: Rpa.Context) -> Awaitable[R] | R:
            raise NotImplementedError()

    class Query(_ToolBase[str]): ...

    class Action(_ToolBase[str]):
        def run(self, rpa: Rpa.Context) -> str:
            return "Successfully executed action: " + self.__class__.__name__

    class Result[R](_ToolBase[R]): ...

    class Context(model.Base):
        # rpa: Rpa
        performed_actions: Annotated[
            list[Rpa.Action], model.Field(default_factory=list)
        ]

        def make_prompt(self) -> str:
            raise NotImplementedError(
                "get_prompt() must be implemented in context subclasses"
            )

        def get_files(self) -> list[model.File]:
            """Return the list of files to be processed by the RPA."""
            return []

    def __init__(
        self,
        *,
        model: str,
        name: Optional[str] = None,
        instructions: Optional[str] = None,
        # toolsets: dict[str, Any] = {},
        queries: list[Query] = [],
        actions: list[Action] = [],
        results: list[Result[R]],
    ):
        """Initialize the RPA assistant with OpenAI credentials"""
        # super().__init__(toolsets=toolsets)
        self.model = model
        self.instructions = dedent(instructions or self.__doc__)
        self.client = AsyncOpenAI()
        self.queries = queries
        self.actions = actions
        self.results = results
        self.name = name or self.__class__.__name__
        # self.conversation = None

    @cached_property
    def _oai_tool_classes(self) -> list[type[_ToolBase]]:
        """Return all tools defined in the assistant"""
        return [
            *self.queries,
            *self.actions,
            *self.results,
        ]

    @cached_property
    def _oai_tool_by_name(self) -> dict[str, type[_ToolBase]]:
        return {tool.__name__: tool for tool in self._oai_tool_classes}

    async def _oai_create_file_content(
        self, file: model.File
    ) -> ResponseInputFileParam | ResponseInputImageParam:
        file_content = await file.content()
        
        uploaded_file = await self.client.files.create(
            file=(file.filename, file_content, file.content_type),
            purpose="user_data",
        )

        if file.content_type in EMBEDDED_IMAGE_URL_CONTENT_TYPE:
            return {
                "type": "input_image",
                "file_id": uploaded_file.id,
                "detail": "high",
            }
        else:
            return {
                "type": "input_file",
                "file_id": uploaded_file.id,
            }

    async def run(self, ctx: Context) -> R:
        """
        Process an email to determine its type and extract relevant information

        Args:
            email: The email message to process

        Returns:
            InferResult with the detected label and associated action
        """

        response = None

        tools = [
            # {"type": "file_search"},
            # {"type": "code_interpreter"},
            *[get_oai_tool_schema(tool) for tool in self._oai_tool_classes],
        ]

        user_input: list[ResponseInputParam] = [
            {
                "type": "text",
                "text": ctx.make_prompt(),
            }
        ] 

        for file in ctx.get_files():
            user_input.append(await self._oai_create_file_content(file))

        input: list[ResponseInputParam] = [
            {
                "role": "user",
                "content": user_input,
            },
        ]

        try:
            while True:
                response = await self.client.responses.create(
                    model=self.model,
                    instructions=self.instructions,
                    tools=tools,
                    input=input,
                )

                input.extend(response.output)

                match response.status:
                    # case 'completed':
                    #     input.append({
                    #         'role': "system",
                    #         'content': "IMPORTANT: You must complete the task by calling a Result tool.",
                    #     })
                    #     continue
                    case "failed" | "cancelled":
                        raise StopRPA(
                            response.status, response.output.content[0].text.value
                        )
                    case _:
                        pass

                for output_item in response.output:
                    match output_item:
                        case ResponseFunctionToolCall(
                            name=name, arguments=arguments, call_id=call_id
                        ):
                            logger.info("Dispatching tool call %s with arguments %s", name, arguments)

                            result = await self._dispatch_tool_call(
                                ctx,
                                name,
                                arguments,
                            )

                            input.append(
                                {
                                    "type": "function_call_output",
                                    "call_id": call_id,
                                    "output": str(result) if result is not None else "OK",
                                }
                            )
                        case ResponseOutputMessage(content=content):
                            print(f"RPA >>> {content}")
                        case _:
                            logger.info(f"Unhandled response output {type(output_item)}")
                            pass

        except StopRPA as e:
            if e.status == "completed":
                return e.result
            raise e

    async def _dispatch_tool_call(self, ctx: Context, function_name, arguments):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError as e:
            return f"Invalid JSON in function arguments: {e}"

        try:
            tool_cls = self._oai_tool_by_name.get(function_name)
        except KeyError:
            return f"Tool {function_name} not found"

        try:
            tool = tool_cls.model_validate(arguments)
        except ValueError as e:
            return str(e)

        logger.info("Running tool %s", tool)

        try:
            result = tool.run(ctx)

            if isawaitable(result):
                result = await result

            if issubclass(tool_cls, self.Action):
                ctx.performed_actions.append(tool)

            if issubclass(tool_cls, self.Result):
                raise StopRPA("completed", result)
        except StopRPA as e:
            raise e
        except Exception as e:
            logger.exception("Error running tool %s: %s", tool_cls.__name__, e)
            return f"Error running tool {tool_cls.__name__}: {e}"

        return result


def get_oai_tool_schema(model_class: type[model.Base], flatten_schema: bool = False):
    schema = model_class.model_json_schema()

    if flatten_schema:
        # Post-procesamiento para eliminar $ref:
        defs = schema.pop("$defs", {})  # Extraer definiciones

        def resolve_refs(obj: dict):
            """Función recursiva para reemplazar $ref por la definición correspondiente."""
            for key, value in list(obj.items()):
                if isinstance(value, dict):
                    if "$ref" in value:  # encontramos una referencia
                        ref_path: str = value.pop("$ref")
                        ref_name = ref_path.split("/")[
                            -1
                        ]  # nombre de la definición referenciada
                        if ref_name in defs:
                            # Tomar una copia de la definición e insertarla aquí
                            sub_schema = defs[ref_name]
                            # Antes de insertar, opcionalmente remover metadata no deseada
                            sub_schema.pop(
                                "title", None
                            )  # (ejemplo: quitar títulos automáticos)
                            value.update(sub_schema)  # insertar keys del sub-esquema
                    # Llamada recursiva para anidar más profundo
                    resolve_refs(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            resolve_refs(item)

        resolve_refs(schema)

    # return {
    #     "type": "function",
    #     "function": {
    #         "name": model_class.__name__,
    #         "description": dedent(model_class.__doc__),
    #         "parameters": schema,
    #         # {
    #         #     "type": "object",
    #         #     "properties": schema.get("properties"),
    #         #     "required": schema.get("required", []),
    #         # },
    #     },
    # }

    return {
        "type": "function",
        "name": model_class.__name__,
        "description": dedent(model_class.__doc__),
        "parameters": schema,
    }


if __name__ == "__main__":
    from asyncio import run

    class WeatherAgent(Rpa[str]):
        "You are a weather agent that provides current weather information."

        class QueryCurrentWeather(Rpa.Query):
            "get the current weather in a given city"

            city: str

            async def run(self, rpa: WeatherAgent):
                return (
                    f"current weather in {self.city} are sunny and 25 degrees Celsius"
                )

        class CurrentWeatherResult(Rpa.Result[str]):
            """
            Result of the current weather query

            You must call this tool when you have the current weather information to finalize the RPA process.
            """

            city: str
            temperature: float
            # condition: str

            async def run(self, rpa: WeatherAgent):
                return f"The current weather in {self.city} is {self.temperature}°C."

        def __init__(self):
            super().__init__(
                model="gpt-4o",
                queries=[self.QueryCurrentWeather],
                actions=[],
                results=[self.CurrentWeatherResult],
            )

    rpa = WeatherAgent()
    response = run(rpa.run("Get the current weather in New York City"))
    print(response)
