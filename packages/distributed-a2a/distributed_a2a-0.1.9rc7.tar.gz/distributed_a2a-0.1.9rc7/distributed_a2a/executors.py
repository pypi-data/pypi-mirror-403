import json
import logging
import os

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import TaskStatusUpdateEvent, TaskStatus, TaskState, TaskArtifactUpdateEvent, Artifact
from a2a.utils import new_text_artifact
from langchain_core.tools import BaseTool

from .agent import StatusAgent, RoutingResponse, StringResponse
from .model import AgentConfig, RouterConfig

logger = logging.getLogger(__name__)

ROUTING_SYSTEM_PROMPT = """
You are a helpful routing assistant which routes user requests to specialized remote agents. Your main task is to:
1. look up available agents via their A2A agent cards
2. select the best matching agent for the user query
3. return the matching agent card for that agent."""


class RoutingAgentExecutor(AgentExecutor):

    def __init__(self, agent_config: AgentConfig, routing_tool: BaseTool, tools: list[BaseTool] | None = None):
        super().__init__()
        api_key = os.environ.get(agent_config.agent.llm.api_key_env)
        if api_key is None:
            raise ValueError("No API key found for LLM.")

        self.agent = StatusAgent[StringResponse](
            llm_config=agent_config.agent.llm,
            system_prompt=agent_config.agent.system_prompt,
            name=agent_config.agent.card.name,
            api_key=api_key,
            is_routing=False,
            tools=[] if tools is None else tools,
        )
        self.routing_agent = StatusAgent[RoutingResponse](
            llm_config=agent_config.agent.llm,
            system_prompt=ROUTING_SYSTEM_PROMPT,
            name="Router",
            api_key=api_key,
            is_routing=True,
            tools=[routing_tool]
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.context_id is None or context.task_id is None:
            raise ValueError("Context ID and Task ID must be provided.")

        # set status to processing
        await event_queue.enqueue_event(TaskStatusUpdateEvent(status=TaskStatus(state=TaskState.working),
                                                              final=False,
                                                              context_id=context.context_id,
                                                              task_id=context.task_id))
        agent_response: StringResponse = await self.agent(message=context.get_user_input(),
                                                          context_id=context.context_id)

        artifact: Artifact
        if agent_response.status == TaskState.rejected:
            routing_agent_response: RoutingResponse = await self.routing_agent(message=context.get_user_input(),
                                                                       context_id=context.context_id)
            agent_card = routing_agent_response.agent_card
            if isinstance(agent_card, str):
                try:
                    agent_card_dict = json.loads(agent_card)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse agent_card as JSON: {agent_card}")
                    raise
            else:
                agent_card_dict = agent_card

            agent_name: str = agent_card_dict["name"]
            logger.info(f"Request with id {context.context_id} got rejected and will be rerouted to a '{agent_name}'.",
                        extra={"card": routing_agent_response.agent_card})
            artifact = new_text_artifact(name='target_agent', description='New target agent for request.',
                                         text=json.dumps(agent_card_dict) if isinstance(agent_card_dict, dict) else str(agent_card))
        else:
            logger.info(f"Request with id {context.context_id} was successfully processed by agent.")
            artifact = new_text_artifact(name='current_result', description='Result of request to agent.',
                                         text=agent_response.response)

        # publish actual result
        await event_queue.enqueue_event(TaskArtifactUpdateEvent(append=False,
                                                                context_id=context.context_id,
                                                                task_id=context.task_id,
                                                                last_chunk=True,
                                                                artifact=artifact))
        # set and publish the final status
        await event_queue.enqueue_event(TaskStatusUpdateEvent(status=TaskStatus(
            state=TaskState(agent_response.status)),
            final=True,
            context_id=context.context_id,
            task_id=context.task_id))


class RoutingExecutor(AgentExecutor):
    def __init__(self, router_config: RouterConfig, routing_tool: BaseTool) -> None:
        super().__init__()
        api_key = os.environ.get(router_config.router.llm.api_key_env)
        if api_key is None:
            raise ValueError("No API key found for LLM.")

        self.routing_agent = StatusAgent[RoutingResponse](
            llm_config=router_config.router.llm,
            system_prompt=ROUTING_SYSTEM_PROMPT,
            name=router_config.router.card.name,
            api_key=api_key,
            is_routing=True,
            tools=[routing_tool]
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.context_id is None or context.task_id is None:
            raise ValueError("Context ID and Task ID must be provided.")

        await event_queue.enqueue_event(TaskStatusUpdateEvent(status=TaskStatus(state=TaskState.working),
                                                              final=False,
                                                              context_id=context.context_id,
                                                              task_id=context.task_id))

        agent_response: RoutingResponse = await self.routing_agent(message=context.get_user_input(),
                                                                   context_id=context.context_id)
        logger.info(f"Routing agent response for request with id {context.context_id}: {agent_response}")
        agent_card = agent_response.agent_card
        if isinstance(agent_card, str):
            try:
                agent_card_dict = json.loads(agent_card)
            except json.JSONDecodeError:
                # If it's not JSON, maybe it's already the name or something else?
                # But AgentCard expects a dict if we use model_validate
                logger.error(f"Failed to parse agent_card as JSON: {agent_card}")
                raise
        else:
            agent_card_dict = agent_card

        agent_name: str = agent_card_dict["name"]
        logger.info(f"Request with id {context.context_id} got rejected and will be rerouted to a '{agent_name}'.",
                    extra={"card": agent_card})
        artifact = new_text_artifact(name='target_agent', description='New target agent for request.',
                                     text=json.dumps(agent_card_dict) if isinstance(agent_card_dict, dict) else str(agent_card))

        # publish actual result
        await event_queue.enqueue_event(TaskArtifactUpdateEvent(append=False,
                                                                context_id=context.context_id,
                                                                task_id=context.task_id,
                                                                last_chunk=True,
                                                                artifact=artifact))
        # set and publish the final status
        await event_queue.enqueue_event(TaskStatusUpdateEvent(status=TaskStatus(
            state=TaskState(agent_response.status)),
            final=True,
            context_id=context.context_id,
            task_id=context.task_id))