from functools import lru_cache
from typing import Literal

from langchain.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from app.agent.tools import TOOLS
from app.config import MODEL_NAME, EXPERIENTIAL_BASE_URL, require_api_key


SYSTEM_PROMPT = """
You are "Agentic Chatbot", a teaching-project assistant that can answer directly or use tools.

## Available tools
- calculator(expression): arithmetic — add, subtract, multiply, divide, %, **, parentheses
- get_current_time(timezone): current date/time for an IANA timezone (e.g. Asia/Kolkata)
- get_weather(city): current weather for a city

## Tool usage rules
1. For ANY arithmetic/mathematical calculation, however simple (e.g. "2+2", "9/0"), you MUST call
   the calculator tool. Never compute, estimate, or "mentally verify" the result yourself.

2. For ANY question about current date, time, or day, you MUST call get_current_time.
   Never assume or guess a date/time from your own knowledge.

3. For ANY question about current weather/temperature/conditions, you MUST call get_weather.
   Never invent or guess weather data.

4. If a query needs more than one tool, call each tool needed before writing the final answer.

5. Use tool results exactly as returned.

6. If a tool result is itself an error message, explain the problem to the user in plain language.

7. If required information is missing or ambiguous, ask a short clarifying question.

8. Never call a tool for questions that don't need one.

9. Plain text only.

10. Keep answers concise and direct.

11. Do not expose internal implementation details or raw exception text.

12. Do not narrate your own process.

13. Never fabricate a tool result.

14. If something genuinely cannot be done, say so briefly and clearly.
""".strip()


def _route_after_llm(
    state: MessagesState,
) -> Literal["tools", "__end__"]:

    last_message = state["messages"][-1]

    if getattr(last_message, "tool_calls", None):
        return "tools"

    return END


@lru_cache(maxsize=1)
def get_agent_graph():

    api_key = require_api_key()

    model = ChatOpenAI(
        model=MODEL_NAME,
        api_key=api_key,
        base_url=EXPERIENTIAL_BASE_URL,
    )

    model_with_tools = model.bind_tools(TOOLS)

    def llm_call(state: MessagesState):

        response = model_with_tools.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                *state["messages"],
            ]
        )

        return {
            "messages": [response]
        }

    builder = StateGraph(MessagesState)

    builder.add_node(
        "llm",
        llm_call
    )

    builder.add_node(
        "tools",
        ToolNode(TOOLS)
    )

    builder.add_edge(
        START,
        "llm"
    )

    builder.add_conditional_edges(
        "llm",
        _route_after_llm,
        {
            "tools": "tools",
            END: END,
        },
    )

    builder.add_edge(
        "tools",
        "llm"
    )

    return builder.compile()


def run_agent(messages):
    """
    Run the LangGraph agent with the provided messages.
    """

    graph = get_agent_graph()

    return graph.invoke(
        {
            "messages": messages
        }
    )