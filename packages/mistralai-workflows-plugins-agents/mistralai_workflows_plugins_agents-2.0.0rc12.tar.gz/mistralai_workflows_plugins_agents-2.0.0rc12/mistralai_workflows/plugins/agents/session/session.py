import abc
from typing import Generic, TypeVar

import mistralai
from pydantic import BaseModel

from mistralai_workflows.plugins.agents.agent import Agent

T = TypeVar("T", bound=BaseModel)
Inputs = list[T | str | mistralai.ContentChunk]
Outputs = list[T]
FinalOutputs = list[mistralai.ContentChunk]


class Session(abc.ABC, Generic[T]):
    @abc.abstractmethod
    def is_conversation_active(self) -> bool: ...

    @abc.abstractmethod
    async def initialize_conversation(self, agent: Agent, inputs: Inputs[T]) -> Outputs[T]: ...

    @abc.abstractmethod
    async def close_conversation(self) -> None: ...

    @abc.abstractmethod
    async def append_messages(self, inputs: Inputs[T]) -> Outputs[T]: ...

    @abc.abstractmethod
    async def process_output(self, output: T) -> Outputs[T]: ...

    @abc.abstractmethod
    def format_final_outputs(self, outputs: Outputs[T]) -> FinalOutputs: ...
