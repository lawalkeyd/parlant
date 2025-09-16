#!/usr/bin/env python3
"""
Test script demonstrating agent-specific journey creation and transitions via API.
This shows how to replicate the SDK pattern using the REST API endpoints.
"""

import asyncio
import json
from typing import Optional, Sequence
from dataclasses import dataclass


@dataclass
class MockToolEntry:
    """Mock tool entry for demonstration"""
    tool: object

    def __init__(self, name: str):
        self.tool = type('Tool', (), {'name': name})()


async def create_agent_journey_with_transitions():
    """
    Demonstrates creating a journey for an agent with transitions using the API.
    This mimics the SDK approach: agent.create_journey(...) followed by transitions.
    """

    # Mock data
    agent_id = "agent_123"
    get_upcoming_slots = MockToolEntry("get_upcoming_slots")

    print("=" * 60)
    print("AGENT JOURNEY CREATION WITH TRANSITIONS VIA API")
    print("=" * 60)
    print()

    # 1. Create the journey for the agent
    print("Step 1: Create journey for agent")
    print("-" * 40)
    journey_data = {
        "title": "Schedule an Appointment",
        "description": "Helps the patient find a time for their appointment.",
        "conditions": ["The patient wants to schedule an appointment"],
        "tags": ["scheduling", "appointment"]  # Agent tag will be added automatically
    }
    print(f"POST /agents/{agent_id}/journeys")
    print(f"Body: {json.dumps(journey_data, indent=2)}")
    print()

    # Mock response
    journey_response = {
        "id": "journey_123",
        "title": "Schedule an Appointment",
        "description": "Helps the patient find a time for their appointment.",
        "conditions": ["guid_001"],  # Guideline IDs created from conditions
        "tags": ["agent:agent_123", "scheduling", "appointment"],
        "root_node_id": "node_root_123"
    }
    print("Response:")
    print(json.dumps(journey_response, indent=2))
    print()

    journey_id = journey_response["id"]
    root_node_id = journey_response["root_node_id"]

    # 2. Get the initial node to start creating transitions
    print("Step 2: Get initial node of the journey")
    print("-" * 40)
    print(f"GET /journeys/{journey_id}/initial-node")
    print()

    initial_node_response = {
        "id": root_node_id,
        "creation_utc": "2024-01-20T10:30:00Z",
        "action": "<<JOURNEY ROOT: start the journey at the appropriate step based on the context>>",
        "tools": [],
        "metadata": {"journey_node": {"kind": "initial"}}
    }
    print("Response:")
    print(json.dumps(initial_node_response, indent=2))
    print()

    # 3. Create first state - determine appointment reason
    print("Step 3: Create first state - determine reason for visit")
    print("-" * 40)
    node1_data = {
        "action": "Determine the reason for the visit",
        "tools": []
    }
    print(f"POST /journeys/{journey_id}/nodes")
    print(f"Body: {json.dumps(node1_data, indent=2)}")
    node1_id = "node_1"
    print(f"Response: {{ \"id\": \"{node1_id}\", ... }}")
    print()

    # 4. Create transition from initial to first state
    print("Step 4: Transition from initial state to first state")
    print("-" * 40)
    edge1_data = {
        "source": root_node_id,
        "target": node1_id,
        "condition": None  # No condition for initial transition
    }
    print(f"POST /journeys/{journey_id}/edges")
    print(f"Body: {json.dumps(edge1_data, indent=2)}")
    print()

    # 5. Create second state - load appointment slots (with tool)
    print("Step 5: Create second state - load appointment slots (tool)")
    print("-" * 40)
    node2_data = {
        "action": "Load upcoming appointment slots",
        "tools": ["get_upcoming_slots"]
    }
    print(f"POST /journeys/{journey_id}/nodes")
    print(f"Body: {json.dumps(node2_data, indent=2)}")
    node2_id = "node_2"
    print(f"Response: {{ \"id\": \"{node2_id}\", ... }}")
    print()

    # 6. Transition from first to second state
    edge2_data = {
        "source": node1_id,
        "target": node2_id,
        "condition": None
    }
    print(f"POST /journeys/{journey_id}/edges")
    print(f"Body: {json.dumps(edge2_data, indent=2)}")
    print()

    # 7. Create third state - ask which time works
    print("Step 6: Create third state - ask patient preference")
    print("-" * 40)
    node3_data = {
        "action": "List available times and ask which ones works for them",
        "tools": []
    }
    print(f"POST /journeys/{journey_id}/nodes")
    print(f"Body: {json.dumps(node3_data, indent=2)}")
    node3_id = "node_3"
    print(f"Response: {{ \"id\": \"{node3_id}\", ... }}")
    print()

    # 8. Transition from second to third state
    edge3_data = {
        "source": node2_id,
        "target": node3_id,
        "condition": None
    }
    print(f"POST /journeys/{journey_id}/edges")
    print(f"Body: {json.dumps(edge3_data, indent=2)}")
    print()

    # 9. Create fourth state - confirm details (conditional)
    print("Step 7: Create fourth state - confirm appointment")
    print("-" * 40)
    node4_data = {
        "action": "Confirm the details with the patient before scheduling",
        "tools": []
    }
    print(f"POST /journeys/{journey_id}/nodes")
    print(f"Body: {json.dumps(node4_data, indent=2)}")
    node4_id = "node_4"
    print(f"Response: {{ \"id\": \"{node4_id}\", ... }}")
    print()

    # 10. Create conditional transition
    print("Step 8: Create conditional transition")
    print("-" * 40)
    edge4_data = {
        "source": node3_id,
        "target": node4_id,
        "condition": "The patient picks a time"
    }
    print(f"POST /journeys/{journey_id}/edges")
    print(f"Body: {json.dumps(edge4_data, indent=2)}")
    print()

    # 11. Set metadata to mark node types
    print("Step 9: Set node metadata for type information")
    print("-" * 40)
    metadata_tool = {
        "key": "journey_node",
        "value": {"kind": "tool"}
    }
    print(f"POST /journeys/nodes/{node2_id}/metadata")
    print(f"Body: {json.dumps(metadata_tool, indent=2)}")
    print()

    metadata_chat = {
        "key": "journey_node",
        "value": {"kind": "chat"}
    }
    for node_id in [node1_id, node3_id, node4_id]:
        print(f"POST /journeys/nodes/{node_id}/metadata")
        print(f"Body: {json.dumps(metadata_chat, indent=2)}")
        print()

    print("=" * 60)
    print("JOURNEY STRUCTURE CREATED:")
    print("=" * 60)
    print()
    print("  [Initial State]")
    print("        |")
    print("        v")
    print("  [Determine reason for visit] (chat)")
    print("        |")
    print("        v")
    print("  [Load appointment slots] (tool: get_upcoming_slots)")
    print("        |")
    print("        v")
    print("  [Ask which time works] (chat)")
    print("        |")
    print("        | (condition: 'The patient picks a time')")
    print("        v")
    print("  [Confirm details] (chat)")
    print()

    print("=" * 60)
    print("USEFUL API ENDPOINTS:")
    print("=" * 60)
    print()
    print("Journey Management:")
    print(f"  GET /journeys/{journey_id}               - Get journey details")
    print(f"  GET /journeys/{journey_id}/nodes         - List all nodes")
    print(f"  GET /journeys/{journey_id}/edges         - List all transitions")
    print(f"  GET /journeys/{journey_id}/initial-node  - Get starting node")
    print(f"  GET /journeys/{journey_id}/mermaid       - Get visual diagram")
    print()
    print("Agent Journeys:")
    print(f"  POST /agents/{agent_id}/journeys         - Create journey for agent")
    print(f"  GET /journeys?tag_id=agent:{agent_id}    - List agent's journeys")
    print()

    print("=" * 60)
    print("SDK EQUIVALENT:")
    print("=" * 60)
    print("""
    # The API calls above replicate this SDK code:

    journey = await agent.create_journey(
        title="Schedule an Appointment",
        description="Helps the patient find a time for their appointment.",
        conditions=["The patient wants to schedule an appointment"],
    )

    # Determine the reason for the appointment
    t0 = await journey.initial_state.transition_to(
        chat_state="Determine the reason for the visit"
    )

    # Load upcoming appointment slots
    t1 = await t0.target.transition_to(
        tool_state=get_upcoming_slots
    )

    # Ask which time works
    t2 = await t1.target.transition_to(
        chat_state="List available times and ask which ones works for them"
    )

    # Conditional transition when patient picks a time
    t3 = await t2.target.transition_to(
        chat_state="Confirm the details with the patient before scheduling",
        condition="The patient picks a time",
    )
    """)


if __name__ == "__main__":
    asyncio.run(create_agent_journey_with_transitions())