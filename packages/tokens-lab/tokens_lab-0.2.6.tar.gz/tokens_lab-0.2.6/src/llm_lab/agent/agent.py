from typing import Dict, Any, Optional, Callable

try:
    # LangGraph is the initial backend; kept isolated for future swaps
    from langgraph.graph import StateGraph
except Exception as exc:  # pragma: no cover
    raise ImportError(
        "langgraph is required for strategy-digital-agent at the moment."
    ) from exc


class Agent:
    """Generic agent wrapper around a graph-based workflow engine.

    Public API is stable and independent of the underlying engine.
    Currently implemented using LangGraph's StateGraph.
    """

    def __init__(self, state_type: Optional[type] = None) -> None:
        self._state_type = state_type or dict
        self._sg = StateGraph(self._state_type)
        self._compiled = None

    def reset(self, state_type: Optional[type] = None) -> "Agent":
        self._state_type = state_type or self._state_type
        self._sg = StateGraph(self._state_type)
        self._compiled = None
        return self

    def add_node(self, name: str, func: Callable[[Dict[str, Any]], Dict[str, Any]]) -> "Agent":
        self._sg.add_node(name, func)
        return self

    def set_entry_point(self, name: str) -> "Agent":
        self._sg.set_entry_point(name)
        return self

    def add_edge(self, start: str, end: str) -> "Agent":
        self._sg.add_edge(start, end)
        return self

    def add_conditional_edges(
        self,
        current: str,
        condition: Callable[[Dict[str, Any]], str],
        mapping: Dict[str, str],
    ) -> "Agent":
        self._sg.add_conditional_edges(current, condition, mapping)
        return self

    def compile(self) -> "Agent":
        self._compiled = self._sg.compile()
        return self

    def invoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        if not self._compiled:
            raise RuntimeError("Graph is not compiled. Call compile() first.")
        return self._compiled.invoke(initial_state)
