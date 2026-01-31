import json
import asyncio
import boto3
import requests
from langchain_core.tools import StructuredTool
from a2a.types import AgentCard


async def registry_heart_beat(name: str, registry_url: str, agent_card: AgentCard, interval_sec: int,
                              get_expire_at: callable) -> None:
    registry = AgentRegistryLookup(registry_url=registry_url)
    while True:
        try:
            registry.put_agent_card(name=name, agent_card=agent_card.model_dump(), expire_at=get_expire_at())
        except Exception as e:
            print(f"Failed to send heart beat to registry: {e}")
        await asyncio.sleep(interval_sec)


class AgentRegistryLookup:
    def __init__(self, registry_url: str):
        self.registry_url = registry_url

    def get_agent_cards(self) -> list[dict]:
        response = requests.get(url=f"{self.registry_url}/agent-cards")
        response.raise_for_status()
        return response.json()

    def put_agent_card(self, name: str, agent_card: dict, expire_at: int) -> None:
        response = requests.put(
            url=f"{self.registry_url}/agent-card/{name}",
            params={"expire_at": str(expire_at)},
            json=agent_card,
            timeout=30
        )
        response.raise_for_status()

    def as_tool(self) -> StructuredTool:
        return StructuredTool.from_function(func=lambda: self.get_agent_cards(), name="agent_card_lookup",
                                            description="Gets all available agent cards")

class DynamoDbRegistryLookup:
    def __init__(self, agent_card_tabel: str):
        dynamo = boto3.resource("dynamodb", region_name="eu-central-1")
        self.table = dynamo.Table(agent_card_tabel)

    def get_agent_cards(self) -> list[dict]:

        items = self.table.scan().get("Items", [])
        cards: list[dict] = [json.loads(it["card"]) for it in items]
        return cards

    def as_tool(self) -> StructuredTool:
        return StructuredTool.from_function(func=lambda: self.get_agent_cards(), name="agent_card_lookup",
                                            description="Gets all available agent cards")
