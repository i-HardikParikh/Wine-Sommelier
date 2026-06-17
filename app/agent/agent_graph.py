from langgraph.graph import StateGraph, END
from app.agent.nodes import (
    AgentState,
    analyze_query,
    vector_search,
    vision_analysis,
    ocr_analysis,
    answer_synthesis,
    fallback,
)


def route_after_vector_search(state: AgentState) -> str:
    """
    After vector_search:
    - If text chunks found → answer_synthesis
    - Else if vision chunks found → vision_analysis
    - Else → ocr_analysis
    """
    results = state.get("vector_results", [])
    text_chunks = [r for r in results if r.get("chunk_type") == "text" and r.get("score", 0) > 0.5]
    vision_chunks = [r for r in results if r.get("chunk_type") == "vision"]

    if text_chunks:
        return "answer_synthesis"
    elif vision_chunks:
        return "vision_analysis"
    else:
        return "ocr_analysis"


def route_after_synthesis(state: AgentState) -> str:
    """
    After answer_synthesis:
    - If context was sufficient → END
    - Else → fallback (LLM-only answer)
    """
    if state.get("context_sufficient"):
        return END
    return "fallback"


def build_agent_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("analyze_query", analyze_query)
    graph.add_node("vector_search", vector_search)
    graph.add_node("vision_analysis", vision_analysis)
    graph.add_node("ocr_analysis", ocr_analysis)
    graph.add_node("answer_synthesis", answer_synthesis)
    graph.add_node("fallback", fallback)

    # Entry point
    graph.set_entry_point("analyze_query")

    # Edges
    graph.add_edge("analyze_query", "vector_search")
    graph.add_conditional_edges(
        "vector_search",
        route_after_vector_search,
        {
            "answer_synthesis": "answer_synthesis",
            "vision_analysis": "vision_analysis",
            "ocr_analysis": "ocr_analysis",
        },
    )
    graph.add_edge("vision_analysis", "answer_synthesis")
    graph.add_edge("ocr_analysis", "answer_synthesis")
    graph.add_conditional_edges(
        "answer_synthesis",
        route_after_synthesis,
        {
            END: END,
            "fallback": "fallback",
        },
    )
    graph.add_edge("fallback", END)

    return graph.compile()


# Singleton compiled graph
wine_agent = build_agent_graph()
