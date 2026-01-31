# %%
from datetime import datetime
from venv import logger
from pydantic import Field, create_model, BaseModel

from functools import cache, cached_property, update_wrapper
from inspect import isfunction, get_annotations, isawaitable, signature, Parameter
from typing import Annotated, Any, Callable, Optional
from textwrap import dedent

from types import MethodType


class ArgsModelBase(BaseModel):
    "Base class for tool arguments. All tools should inherit from this class."


class ToolDescriptor[*A, R]:
    # __slots__ = (
    #     # "__module__",
    #     "__name__",
    #     "__qualname__",
    #     "__doc__",
    #     "__annotations__",
    #     # "__type_params__",
    #     "__func__",
    #     "__owner__",
    # )

    def __init__(self, func: Callable[[*A], R]):
        self.__func__ = func
        # update_wrapper(self, func)

    def __set_name__(self, owner, name):
        assert (
            self.__func__.__name__ == name
        ), f"Tool name mismatch: {self.__name__} != {name}"
        self.__owner__ = owner

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return MethodType(self.__func__, instance)

    #def __call__(self, instance, *args, **kwargs): ...

    @cached_property
    def ArgsModel(self) -> type[BaseModel]:
        assert hasattr(self, "__owner__"), "ToolDescriptor must be set on a class"

        sign = signature(self.__func__)

        field_definitions = {
            f.name: (
                (f.annotation, f.default)
                if f.default is not Parameter.empty
                else f.annotation
            )
            for f in sign.parameters.values()
            if f.annotation is not Parameter.empty
        }

        arg_model = create_model(
            "ArgsModel",
            __base__=ArgsModelBase,
            __module__=self.__func__.__module__,
            __doc__=self.__func__.__doc__,
            **field_definitions,
        )

        setattr(
            arg_model,
            "__qualname__",
            f"{self.__owner__.__name__}.{self.__func__.__name__}.ArgsModel",
        )

        return arg_model

    # @cache
    def generate_schema(self, namespace: Optional[str] = None):
        return {
            "name": (
                f"{namespace}-{self.__func__.__name__}"
                if namespace
                else self.__func__.__name__
            ),
            "type": "function",
            "description": dedent(self.__func__.__doc__.strip()) if self.__func__.__doc__ else "",
            "parameters": self.ArgsModel.model_json_schema(),
        }


def tool(fn):
    """
    Decorator to mark a function as a tool in the Toolset.
    """
    if not isfunction(fn):
        raise TypeError("tool decorator can only be applied to functions")

    return ToolDescriptor(fn)


def _generate_tools_schema(toolsets: dict[str, type[Any]]):
    """
    Create tool descriptors for all tools in the toolsets.
    """
    for namespace, toolset in toolsets.items():
        for name, tool in vars(toolset).items():
            if not isinstance(tool, ToolDescriptor):
                continue
            yield tool.generate_schema(namespace=namespace)


def _generate_tools_schema(toolsets: dict[str, type[Any]]):
    """
    Create tool descriptors for all tools in the toolsets.
    """
    for namespace, toolset in toolsets.items():
        for name, tool in vars(toolset).items():
            if not isinstance(tool, ToolDescriptor):
                continue
            yield tool.generate_schema(namespace=namespace)


class ToolDispatcher:

    def __init__(self, toolsets: dict[str, Any]):
        """
        Initialize the ToolDispatcher with a dictionary of toolsets.
        Each toolset should be a class with methods decorated with @tool.
        """
        self._toolsets = toolsets

    @cached_property
    def tools_schema(self) -> list[dict]:
        return list(
            _generate_tools_schema({nm: type(v) for nm, v in self._toolsets.items()})
        )

    @cached_property
    def tool_mapping(self) -> dict[str, tuple[Any, ToolDescriptor]]:
        result = {}
        for item in self.tools_schema:
            fullname = item["name"]
            namespace, fn_name = fullname.split("-")
            toolset = self._toolsets.get(namespace, None)
            assert (
                toolset is not None
            ), f"Toolset '{namespace}' not found in {self._toolsets.keys()}"
            tool_descriptor = getattr(type(toolset), fn_name, None)
            assert (
                tool_descriptor is not None
            ), f"Function '{fn_name}' not found in toolset '{namespace}'"
            result[fullname] = toolset, tool_descriptor
        return result

    async def _dispatch_tool_call(self, name: str, raw_args: Any) -> str:

        try:
            toolset, tool = self.tool_mapping.get(name, None)
        except Exception as e:
            return f"ERROR: Tool '{name}' not found."

        args_model_class = tool.ArgsModel

        # validate the model
        try:
            if isinstance(raw_args, (str, bytes, bytearray)):
                args_model = args_model_class.model_validate_json(raw_args)
            else:
                args_model = args_model_class.model_validate(raw_args)
        except Exception as e:
            logger.debug(f"Error validating args for tool '{name}': {str(e)}")
            return f"Error: Invalid arguments for tool '{name}': {str(e)}"

        # convert model fields to function arguments
        args = {
            nm: getattr(args_model, nm) for nm in args_model_class.model_fields.keys()
        }

        try:
            result = tool.__func__(toolset, **args)

            if isawaitable(result):
                result = await result

        except Exception as e:
            logger.debug(f"Error executing tool '{name}': {str(e)}")
            return f"Error executing tool '{name}': {str(e)}"
        else:
            logger.debug(f"Tool '{name}' executed successfully: {result}")



        if isinstance(result, BaseModel):
            # Convert BaseModel to JSON string
            result = result.model_dump_json()

        return result


if __name__ == "__main__":

    class MyToolset:

        # class Response(BaseModel):
        #     message: str

        #TODO: custom responses
        @tool
        def query_weather(
            self,
            city: Annotated[str, Field(description="nombre de la ciudad")],
            time: Annotated[datetime, Field(description="hora de la consulta")],
        ) -> str:
            """
            Example tool that takes two arguments and returns a string.
            """

    #ts = td.tools_schema

    # ts = MyToolset()
    # ts("query_weather", '{"city": "Madrid", "time": "2023-03-15T12:00:00Z"}')
    # print(MyToolset.tool_schemas)
    # %%
    #f = await td.dispatch_tool_call('mytools-query_weather', '{"city": "Madrid", "time": "2023-03-15T12:00:00Z"}')

