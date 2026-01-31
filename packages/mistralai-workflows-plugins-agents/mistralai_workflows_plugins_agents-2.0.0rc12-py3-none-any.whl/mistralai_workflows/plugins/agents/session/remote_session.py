import asyncio
import json
from typing import cast

import mistralai
from mistralai_workflows.plugins.mistralai import (
    AgentUpdateRequest,
    ConversationAppendRequest,
    mistralai_append_conversation,
    mistralai_append_conversation_stream,
    mistralai_create_agent,
    mistralai_start_conversation,
    mistralai_start_conversation_stream,
    mistralai_update_agent,
)

from mistralai_workflows.plugins.agents.agent import Agent
from mistralai_workflows.plugins.agents.mcp import (
    CollectMCPToolsParams,
    ExecuteMCPToolParams,
    MCPConfig,
    collect_mcp_tools,
    execute_mcp_tool,
)
from mistralai_workflows.plugins.agents.session.session import FinalOutputs, Inputs, Outputs, Session
from mistralai_workflows.plugins.agents.tool import convert_tool_to_mistral_tool, execute_activity_tool

AgentMapping = dict[Agent, mistralai.Agent]
Message = mistralai.InputEntries
RemoteSessionInputs = Inputs[Message]
RemoteSessionOutputs = Outputs[Message]


class RemoteSession(Session[Message]):
    def __init__(self, raise_on_tool_fail: bool = True, stream: bool = False) -> None:
        """Initialize remote session state and MCP tool registries.

        Prepares conversation tracking, the internal agent mapping
        (local `Agent` -> remote `mistralai.Agent`), and the MCP tool
        registry used to dispatch function calls to MCP clients.
        """
        self._raise_on_tool_fail = raise_on_tool_fail
        self._conversation_id: str | None = None
        self._agent_mapping: AgentMapping | None = None
        # Maps tool_name -> (list of all configs, config_index within that list)
        # This allows looking up: configs, idx = self._mcp_tool_registry[tool_name]
        self._all_mcp_configs: list[MCPConfig] = []
        self._mcp_tool_registry: dict[str, int] = {}  # tool_name -> index in _all_mcp_configs
        self._stream = stream

    def is_conversation_active(self) -> bool:
        """Return whether a remote conversation is active for this session."""
        return self._conversation_id is not None

    async def initialize_conversation(self, agent: Agent, inputs: RemoteSessionInputs) -> RemoteSessionOutputs:
        """Create the remote agent graph, start a conversation, and return first outputs.

        - agent: Root `Agent` to create remotely (including handoffs).
        - inputs: Initial user/system/tool inputs to seed the conversation.

        Returns the assistant's first batch of output entries.
        Raises `ValueError` if a conversation is already active.
        """
        if self._conversation_id:
            raise ValueError("Session already started")
        # Prepare remote agents deeply (create or update) and mutate ids
        self._agent_mapping = await self._prepare_agent_mapping(agent)
        await self._create_all_agent_handoffs(self._agent_mapping)

        mistral_agent = self._agent_mapping[agent]
        messages = self._convert_inputs_to_messages(inputs)
        if self._stream:
            response = await mistralai_start_conversation_stream(
                mistralai.ConversationRequest(agent_id=mistral_agent.id, inputs=messages)
            )
        else:
            response = await mistralai_start_conversation(
                mistralai.ConversationRequest(agent_id=mistral_agent.id, inputs=messages)
            )
        self._conversation_id = response.conversation_id
        return cast(RemoteSessionOutputs, response.outputs)

    async def close_conversation(self) -> None:
        """Close the active remote conversation and clear session state.
        Raises `ValueError` if no conversation is active.
        """
        if not self._conversation_id:
            raise ValueError("Session not started")
        self._conversation_id = None
        self._agent_mapping = None
        self._all_mcp_configs = []
        self._mcp_tool_registry = {}

    async def append_messages(self, inputs: RemoteSessionInputs) -> RemoteSessionOutputs:
        """Append inputs to the active remote conversation and return model outputs.

        - inputs: User/system/tool inputs to append to the conversation.

        Returns the assistant output entries produced for these inputs.
        Raises `ValueError` if no conversation is active.
        """
        if not self._conversation_id:
            raise ValueError("Session not started")
        messages = self._convert_inputs_to_messages(inputs)

        if self._stream:
            response = await mistralai_append_conversation_stream(
                ConversationAppendRequest(conversation_id=self._conversation_id, inputs=messages)
            )
            return cast(RemoteSessionOutputs, response.outputs)
        else:
            response = await mistralai_append_conversation(
                ConversationAppendRequest(conversation_id=self._conversation_id, inputs=messages)
            )
            return cast(RemoteSessionOutputs, response.outputs)

    async def process_output(self, output: Message) -> RemoteSessionOutputs:
        """Process a single model output and produce follow-up inputs.

        Executes function calls by dispatching to:
        - MCP tools, when the tool name exists in the MCP registry.
        - Activity tools, otherwise.

        Returns a single `FunctionResultEntry` to feed back into the agent,
        or an empty list for non-function outputs.
        """
        if output.type == "function.call":
            tool_name = output.name
            if tool_name in self._mcp_tool_registry:
                tool_args = output.arguments if isinstance(output.arguments, dict) else json.loads(output.arguments)

                mcp_result = await execute_mcp_tool(
                    ExecuteMCPToolParams(
                        configs=self._all_mcp_configs,
                        tool_name=tool_name,
                        tool_arguments=tool_args,
                        config_index=self._mcp_tool_registry[tool_name],
                    )
                )
                tool_response = mcp_result.result
            else:
                tool_response = await execute_activity_tool(tool_name, output.arguments, self._raise_on_tool_fail)

            next_input_entries = [mistralai.FunctionResultEntry(tool_call_id=output.tool_call_id, result=tool_response)]
        else:
            next_input_entries = []

        return cast(RemoteSessionOutputs, next_input_entries)

    def format_final_outputs(self, outputs: RemoteSessionOutputs) -> FinalOutputs:
        """Normalize raw agent outputs into displayable `ContentChunk`s.

        Flattens `MessageOutputEntry` content, forwarding known chunks and
        skipping unsupported types (marked TODOs) until mapped.
        """
        final_outputs: FinalOutputs = []
        for output in outputs:
            if not isinstance(output, mistralai.MessageOutputEntry):
                continue
            if isinstance(output.content, str):
                final_outputs.append(mistralai.TextChunk(text=output.content))
            elif isinstance(output.content, list):
                for content in output.content:
                    if isinstance(content, mistralai.ToolFileChunk) or isinstance(
                        content, mistralai.ToolReferenceChunk
                    ):
                        # TODO: implement mapping
                        pass
                    else:
                        final_outputs.append(content)
        return final_outputs

    async def _prepare_agent_mapping(self, agent: Agent) -> AgentMapping:
        """Create or update agents deeply and return mapping.

        For each agent in the handoff graph:
        - If `agent.id` is set, update the remote agent to reflect local fields.
        - Otherwise, create it remotely and mutate `agent.id` with the created id.
        Tools include both local tools and collected MCP tools.
        Handoffs are created separately once all agents exist remotely.
        """
        agents = list(Agent.iterate_agents_deeply_in_handoffs(agent))
        mistral_agents = await asyncio.gather(*[self._create_or_update_agent(a) for a in agents])
        return dict(zip(agents, mistral_agents, strict=True))

    async def _create_or_update_agent(self, agent: Agent) -> mistralai.Agent:
        local_tools = [convert_tool_to_mistral_tool(tool) for tool in agent.tools] if agent.tools else None

        # Enrich with MCP tools and update registry if provided
        all_tools = local_tools
        if agent.mcp_clients:
            mcp_result = await collect_mcp_tools(CollectMCPToolsParams(configs=agent.mcp_clients))

            # Add configs to global list and update registry
            config_offset = len(self._all_mcp_configs)
            self._all_mcp_configs.extend(agent.mcp_clients)
            for tool_name, local_index in mcp_result.tool_to_config_map.items():
                self._mcp_tool_registry[tool_name] = config_offset + local_index

            if mcp_result.tools:
                all_tools = (all_tools or []) + cast(list, mcp_result.tools)

        if agent.id:
            # Update existing remote agent
            update_payload = agent.model_dump(
                by_alias=True,
                exclude_unset=True,
                exclude={"handoffs", "tools", "mcp_clients", "_mistral_agent", "_conversation_id", "id"},
            )
            if all_tools is not None:
                update_payload["tools"] = all_tools
            mistral_agent = await mistralai_update_agent(AgentUpdateRequest(agent_id=agent.id, **update_payload))
        else:
            # Create new remote agent, ensure id is not sent in creation request
            agent_creation_request = mistralai.AgentCreationRequest.model_validate(
                agent.model_copy(update={"tools": local_tools}).model_dump(exclude={"handoffs", "mcp_clients", "id"})
            )
            mistral_agent = await mistralai_create_agent(agent_creation_request)
            # Mutate local agent with created id
            agent.id = mistral_agent.id

            # If MCP tools were collected, update tools post-creation
            if all_tools is not None and all_tools != local_tools:
                mistral_agent = await mistralai_update_agent(
                    AgentUpdateRequest.model_validate({"agent_id": mistral_agent.id, "tools": all_tools})
                )
        return mistral_agent

    async def _create_all_agent_handoffs(self, agent_mapping: AgentMapping) -> None:
        await asyncio.gather(
            *[
                mistralai_update_agent(
                    AgentUpdateRequest(
                        agent_id=mistral_agent.id,
                        handoffs=[agent_mapping[agent].id for agent in agent.handoffs],
                    )
                )
                for agent, mistral_agent in agent_mapping.items()
                if agent.handoffs
            ]
        )

    def _convert_inputs_to_messages(self, inputs: RemoteSessionInputs) -> RemoteSessionOutputs:
        messages: RemoteSessionOutputs = []
        for inp in inputs:
            if isinstance(inp, str):
                messages.append(mistralai.MessageInputEntry(role="user", content=inp))
            elif isinstance(
                inp,
                (mistralai.ImageURLChunk, mistralai.DocumentURLChunk, mistralai.TextChunk, mistralai.ToolFileChunk),
            ):
                messages.append(mistralai.MessageInputEntry(role="user", content=[inp]))
            elif isinstance(inp, (mistralai.MessageInputEntry, mistralai.FunctionResultEntry)):
                messages.append(inp)
            else:
                raise ValueError(
                    f"RemoteSession does not support input of type {type(inp)}, only str or mistralai.InputEntries"
                )
        return messages

    async def cleanup(self) -> None:
        """No-op cleanup for remote sessions.

        Remote conversations and SSE clients are managed by the worker and
        are expected to live for the worker lifetime.
        """
        pass
