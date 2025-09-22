# Copyright 2025 Emcie Co Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from typing import Any, Sequence, cast

import pytest
from lagom import Container

from parlant.core.journeys import Journey, JourneyNode, JourneyStore, JourneyVectorStore
from parlant.core.tools import ToolId


async def _create_journey_with_node(
    store: JourneyVectorStore,
) -> tuple[Journey, JourneyNode, Any]:
    journey = await store.create_journey(
        title="Journey",
        description="Description",
        conditions=[],
    )

    created_node = await store.create_node(
        journey_id=journey.id,
        action="Ask for details",
        tools=[],
    )

    return journey, created_node, store._node_association_collection  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "legacy_representation",
    [
        [ToolId(service_name="built-in", tool_name="legacy_tool")],
        [("built-in", "legacy_tool")],
        [{"service_name": "built-in", "tool_name": "legacy_tool"}],
        ["legacy_tool"],
    ],
)
async def test_read_node_handles_legacy_tool_representations(
    container: Container,
    legacy_representation: Sequence[Any],
) -> None:
    journey_store = cast(JourneyVectorStore, container[JourneyStore])

    _, node, collection = await _create_journey_with_node(journey_store)

    await collection.update_one(
        filters={"node_id": {"$eq": node.id}},
        params={"tools": legacy_representation},
    )

    loaded_node = await journey_store.read_node(node.id)

    assert loaded_node.tools == [
        ToolId(service_name="built-in", tool_name="legacy_tool")
    ]


async def test_update_node_persists_tools_as_serialized_strings(
    container: Container,
) -> None:
    journey_store = cast(JourneyVectorStore, container[JourneyStore])

    _, node, collection = await _create_journey_with_node(journey_store)

    updated_node = await journey_store.update_node(
        node_id=node.id,
        params={
            "tools": [ToolId(service_name="built-in", tool_name="fresh_tool")],
        },
    )

    assert updated_node.tools == [
        ToolId(service_name="built-in", tool_name="fresh_tool")
    ]

    stored = await collection.find_one({"node_id": {"$eq": node.id}})

    assert stored
    assert stored["tools"] == ["built-in:fresh_tool"]
