from typing import Any

from a2a.server.apps import A2ARESTFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill
from fastapi import FastAPI

from .executors import RoutingExecutor
from .model import RouterConfig
from .registry import DynamoDbRegistryLookup, AgentRegistryLookup
from .server import CAPABILITIES, AGENT_CARD_TABLE


def load_router(router_dic: dict[str, Any]) -> FastAPI:
    router_config = RouterConfig.model_validate(router_dic)
    agent_card = AgentCard(
        name="Router",
        description="Agent to redirect to the best matching agent based on the agent card",
        url=router_config.router.card.url,
        version="1.0.0",
        default_input_modes=router_config.router.card.default_input_modes,
        default_output_modes=router_config.router.card.default_output_modes,
        skills=[AgentSkill(
            id='routing',
            name='Agent routing',
            description='Identifies the most suitable agent for the given task and returns the agent card',
            tags=['agent', 'routing']
        )],
        preferred_transport=router_config.router.card.preferred_transport_protocol,
        capabilities=CAPABILITIES
    )

    executor = RoutingExecutor(
        router_config=router_config,
        routing_tool=AgentRegistryLookup(router_config.router.registry.agent.url).as_tool()
    )

    return A2ARESTFastAPIApplication(
        agent_card=agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=executor,
            task_store=InMemoryTaskStore()  # TODO replace with dynamodb store

        )).build(title=agent_card.name,
                 root_path=f"/{router_config.router.card.name}")
