import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import boto3
from a2a.server.apps import A2ARESTFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentSkill, \
    AgentCapabilities, AgentCard
from fastapi import FastAPI

from .executors import RoutingAgentExecutor
from .model import AgentConfig
from .registry import DynamoDbRegistryLookup, registry_heart_beat

CAPABILITIES = AgentCapabilities(streaming=False, push_notifications=False)

HEART_BEAT_INTERVAL_SEC = 5
MAX_HEART_BEAT_MISSES = 3

AGENT_CARD_TABLE = "agent-cards"

def get_expire_at() -> int:
    return int(time.time() + MAX_HEART_BEAT_MISSES * HEART_BEAT_INTERVAL_SEC)



async def heart_beat(name: str, agent_card_table: str, agent_card: AgentCard) -> None:
    table = boto3.resource("dynamodb", region_name="eu-central-1").Table(agent_card_table)
    table.put_item(Item={"id": name, "card": agent_card.model_dump_json(), "expireAt": get_expire_at()})
    while True:
        await asyncio.sleep(HEART_BEAT_INTERVAL_SEC)
        table.update_item(
            Key={"id": name},
            UpdateExpression="SET expireAt = :expire_at",
            ExpressionAttributeValues={":expire_at": get_expire_at()}
        )




def load_app(agent_config: Any) -> FastAPI:

    agent_config= AgentConfig.model_validate(obj=agent_config)

    skills = [AgentSkill(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        tags=skill.tags)
    for skill in agent_config.agent.card.skills]
    skills.append(AgentSkill(
        id='routing',
        name='Agent routing',
        description='Identifies the most suitable agent for the given task and returns the agent card',
        tags=['agent', 'routing']
    ))

    agent_card = AgentCard(
        name=agent_config.agent.card.name,
        description=agent_config.agent.card.description,
        url=agent_config.agent.card.url,
        version=agent_config.agent.card.version,
        default_input_modes=agent_config.agent.card.default_input_modes,
        default_output_modes=agent_config.agent.card.default_output_modes,
        skills=skills,
        preferred_transport=agent_config.agent.card.preferred_transport_protocol,
        capabilities=CAPABILITIES
    )


    executor = RoutingAgentExecutor(agent_config=agent_config,
                                    routing_tool=DynamoDbRegistryLookup(agent_card_tabel=AGENT_CARD_TABLE).as_tool())

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None, Any]:
        asyncio.create_task(heart_beat(name=agent_card.name, agent_card_table=AGENT_CARD_TABLE, agent_card=agent_card))
        import os
        registry_url = os.getenv("REGISTRY_URL")
        if registry_url:
            asyncio.create_task(registry_heart_beat(name=agent_card.name, registry_url=registry_url,
                                                   agent_card=agent_card, interval_sec=HEART_BEAT_INTERVAL_SEC,
                                                   get_expire_at=get_expire_at))
        yield


    return A2ARESTFastAPIApplication(
        agent_card=agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=executor,
            task_store=InMemoryTaskStore() #TODO replace with dynamodb store

        )).build(title=agent_card.name, lifespan=lifespan, root_path=f"/{agent_config.agent.card.name}") #TODO use extra parameter
