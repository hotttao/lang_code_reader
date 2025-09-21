from langgraph.graph import StateGraph
from langgraph.graph import START, END
from lang_code_reader.agent.graph.node import entry_file
from lang_code_reader.agent.graph.types import State, Basic


def build_graph() -> StateGraph:
    graph = StateGraph(State)
    graph.add_node(entry_file)
    graph.add_edge(START, "entry_file")
    graph.add_edge("entry_file", END)
    return graph


if __name__ == "__main__":
    builder = build_graph()
    graph = builder.compile()
    
    graph.invoke({"basic": Basic(repo_name="test", main_goal="test", files=[])})
