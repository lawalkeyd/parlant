from dataclasses import dataclass
from typing import Sequence, Optional, Mapping

from parlant.core.agents import AgentId
from parlant.core.common import JSONSerializable
from parlant.core.guidelines import Guideline, GuidelineId, GuidelineStore
from parlant.core.loggers import Logger
from parlant.core.journeys import (
    JourneyEdge,
    JourneyEdgeId,
    JourneyId,
    JourneyNode,
    JourneyNodeId,
    JourneyNodeUpdateParams,
    JourneyEdgeUpdateParams,
    JourneyStore,
    Journey,
    JourneyUpdateParams,
)
from parlant.core.relationships import (
    RelationshipEntity,
    RelationshipEntityKind,
    RelationshipKind,
    RelationshipStore,
)
from parlant.core.tags import Tag, TagId
from parlant.core.tools import ToolId


@dataclass(frozen=True)
class JourneyGraph:
    journey: Journey
    nodes: Sequence[JourneyNode]
    edges: Sequence[JourneyEdge]


@dataclass(frozen=True)
class JourneyConditionUpdateParams:
    add: Sequence[GuidelineId] | None
    remove: Sequence[GuidelineId] | None


@dataclass(frozen=True)
class JourneyTagUpdateParams:
    add: Sequence[TagId] | None = None
    remove: Sequence[TagId] | None = None


class JourneyModule:
    def __init__(
        self,
        logger: Logger,
        journey_store: JourneyStore,
        guideline_store: GuidelineStore,
        relationship_store: RelationshipStore,
    ):
        self._logger = logger
        self._journey_store = journey_store
        self._guideline_store = guideline_store
        self._relationship_store = relationship_store

    async def create(
        self,
        title: str,
        description: str,
        conditions: Sequence[str],
        tags: Sequence[TagId] | None,
    ) -> tuple[Journey, Sequence[Guideline]]:
        guidelines = [
            await self._guideline_store.create_guideline(
                condition=condition,
                action=None,
                tags=[],
            )
            for condition in conditions
        ]

        journey = await self._journey_store.create_journey(
            title=title,
            description=description,
            conditions=[g.id for g in guidelines],
            tags=tags,
        )

        for guideline in guidelines:
            await self._guideline_store.upsert_tag(
                guideline_id=guideline.id,
                tag_id=Tag.for_journey_id(journey.id),
            )

        return journey, guidelines

    async def create_for_agent(
        self,
        agent_id: AgentId,
        title: str,
        description: str,
        conditions: Sequence[str],
        tags: Sequence[TagId] | None = None,
    ) -> tuple[Journey, Sequence[Guideline]]:
        """Creates a journey specifically for an agent, automatically tagging it."""
        # Prepare tags including the agent tag
        all_tags = list(tags) if tags else []
        agent_tag = Tag.for_agent_id(agent_id)
        if agent_tag not in all_tags:
            all_tags.append(agent_tag)

        # Create the journey with agent tag
        journey, guidelines = await self.create(
            title=title,
            description=description,
            conditions=conditions,
            tags=all_tags,
        )

        return journey, guidelines

    async def read(self, journey_id: JourneyId) -> JourneyGraph:
        journey = await self._journey_store.read_journey(journey_id=journey_id)
        nodes = await self._journey_store.list_nodes(journey_id=journey.id)
        edges = await self._journey_store.list_edges(journey_id=journey.id)

        return JourneyGraph(journey=journey, nodes=nodes, edges=edges)

    async def find(self, tag_id: TagId | None) -> Sequence[Journey]:
        if tag_id:
            journeys = await self._journey_store.list_journeys(
                tags=[tag_id],
            )
        else:
            journeys = await self._journey_store.list_journeys()

        return journeys

    async def update(
        self,
        journey_id: JourneyId,
        title: str | None,
        description: str | None,
        conditions: JourneyConditionUpdateParams | None,
        tags: JourneyTagUpdateParams | None,
    ) -> Journey:
        journey = await self._journey_store.read_journey(journey_id=journey_id)

        update_params: JourneyUpdateParams = {}
        if title:
            update_params["title"] = title
        if description:
            update_params["description"] = description

        if update_params:
            journey = await self._journey_store.update_journey(
                journey_id=journey_id,
                params=update_params,
            )

        if conditions:
            if conditions.add:
                for condition in conditions.add:
                    await self._journey_store.add_condition(
                        journey_id=journey_id,
                        condition=condition,
                    )

                    guideline = await self._guideline_store.read_guideline(guideline_id=condition)

                    await self._guideline_store.upsert_tag(
                        guideline_id=condition,
                        tag_id=Tag.for_journey_id(journey_id),
                    )

            if conditions.remove:
                for condition in conditions.remove:
                    await self._journey_store.remove_condition(
                        journey_id=journey_id,
                        condition=condition,
                    )

                    guideline = await self._guideline_store.read_guideline(guideline_id=condition)

                    if guideline.tags == [Tag.for_journey_id(journey_id)]:
                        await self._guideline_store.delete_guideline(guideline_id=condition)
                    else:
                        await self._guideline_store.remove_tag(
                            guideline_id=condition,
                            tag_id=Tag.for_journey_id(journey_id),
                        )

        if tags:
            if tags.add:
                for tag in tags.add:
                    await self._journey_store.upsert_tag(journey_id=journey_id, tag_id=tag)

            if tags.remove:
                for tag in tags.remove:
                    await self._journey_store.remove_tag(journey_id=journey_id, tag_id=tag)

        journey = await self._journey_store.read_journey(journey_id=journey_id)

        return journey

    async def delete(self, journey_id: JourneyId) -> None:
        journey = await self._journey_store.read_journey(journey_id=journey_id)

        await self._journey_store.delete_journey(journey_id=journey_id)

        for condition in journey.conditions:
            if not await self._journey_store.list_journeys(condition=condition):
                await self._guideline_store.delete_guideline(guideline_id=condition)
            else:
                guideline = await self._guideline_store.read_guideline(guideline_id=condition)

                if guideline.tags == [Tag.for_journey_id(journey_id)]:
                    await self._guideline_store.delete_guideline(guideline_id=condition)
                else:
                    await self._guideline_store.remove_tag(
                        guideline_id=condition,
                        tag_id=Tag.for_journey_id(journey_id),
                    )

    async def create_node(
        self,
        journey_id: JourneyId,
        action: Optional[str],
        tools: Sequence[ToolId],
    ) -> JourneyNode:
        """Creates a new node in the journey."""
        # Auto-generate action text if we have a single tool and no action
        if len(tools) == 1 and not action:
            action = f"Use the tool {tools[0].tool_name}"

        node = await self._journey_store.create_node(
            journey_id=journey_id,
            action=action,
            tools=tools,
        )

        # Create relationships between node and tools
        if tools:
            for tool_id in tools:
                await self._relationship_store.create_relationship(
                    source=RelationshipEntity(
                        id=Tag.for_journey_node_id(node.id),
                        kind=RelationshipEntityKind.TAG,
                    ),
                    target=RelationshipEntity(
                        id=tool_id,
                        kind=RelationshipEntityKind.TOOL,
                    ),
                    kind=RelationshipKind.REEVALUATION,
                )

        return node

    async def read_node(
        self,
        node_id: JourneyNodeId,
    ) -> JourneyNode:
        """Reads a specific node by ID."""
        return await self._journey_store.read_node(node_id=node_id)

    async def update_node(
        self,
        node_id: JourneyNodeId,
        action: Optional[str] = None,
        tools: Optional[Sequence[ToolId]] = None,
    ) -> JourneyNode:
        """Updates a node's properties."""
        params: JourneyNodeUpdateParams = {}
        if action is not None:
            params["action"] = action
        if tools is not None:
            params["tools"] = tools

        return await self._journey_store.update_node(
            node_id=node_id,
            params=params,
        )

    async def delete_node(
        self,
        node_id: JourneyNodeId,
    ) -> None:
        """Deletes a node from the journey."""
        await self._journey_store.delete_node(node_id=node_id)

    async def set_node_metadata(
        self,
        node_id: JourneyNodeId,
        key: str,
        value: JSONSerializable,
    ) -> JourneyNode:
        """Sets metadata on a node."""
        return await self._journey_store.set_node_metadata(
            node_id=node_id,
            key=key,
            value=value,
        )

    async def create_edge(
        self,
        journey_id: JourneyId,
        source: JourneyNodeId,
        target: JourneyNodeId,
        condition: Optional[str],
    ) -> JourneyEdge:
        """Creates an edge (transition) between two nodes."""
        return await self._journey_store.create_edge(
            journey_id=journey_id,
            source=source,
            target=target,
            condition=condition,
        )

    async def read_edge(
        self,
        edge_id: JourneyEdgeId,
    ) -> JourneyEdge:
        """Reads a specific edge by ID."""
        return await self._journey_store.read_edge(edge_id=edge_id)

    async def update_edge(
        self,
        edge_id: JourneyEdgeId,
        condition: Optional[str] = None,
    ) -> JourneyEdge:
        """Updates an edge's condition."""
        params: JourneyEdgeUpdateParams = {}
        if condition is not None:
            params["condition"] = condition

        return await self._journey_store.update_edge(
            edge_id=edge_id,
            params=params,
        )

    async def delete_edge(
        self,
        edge_id: JourneyEdgeId,
    ) -> None:
        """Deletes an edge from the journey."""
        await self._journey_store.delete_edge(edge_id=edge_id)
