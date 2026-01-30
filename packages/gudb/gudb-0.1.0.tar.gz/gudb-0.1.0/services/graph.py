from langgraph.graph import StateGraph, END
from services.nodes import (
    SentinelState,
    detective_node,
    architect_node,
    validator_node,
)


def build_sentinel_graph():
    workflow = StateGraph(SentinelState)

    # Add nodes
    workflow.add_node("detective", detective_node)
    workflow.add_node("architect", architect_node)
    workflow.add_node("validator", validator_node)

    # Define the path
    workflow.set_entry_point("detective")
    workflow.add_edge("detective", "architect")
    workflow.add_edge("architect", "validator")
    workflow.add_edge("validator", END)

    return workflow.compile()