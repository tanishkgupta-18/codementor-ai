from langgraph.graph import StateGraph
from typing import TypedDict
from backend.app.rag import load_vectorstore
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
vectorstore = load_vectorstore()


class AgentState(TypedDict):
    title: str
    description: str
    code: str
    context: str
    review: str


# -------- Knowledge Agent --------
def knowledge_agent(state: AgentState):
    docs = vectorstore.similarity_search(state["description"], k=2)
    context = "\n".join([doc.page_content for doc in docs])
    state["context"] = context
    return state


# -------- Review Agent --------
def review_agent(state: AgentState):
    prompt = f"""
You are a DSA mentor.

Relevant DSA Concepts:
{state['context']}

Problem:
{state['title']}

Description:
{state['description']}

User Code:
{state['code']}

Give feedback on:
1. Correctness
2. Time & Space Complexity
3. Which DSA pattern applies here and why
4. How to improve
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    state["review"] = response.choices[0].message.content
    return state


# -------- Build Graph --------
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("knowledge", knowledge_agent)
    graph.add_node("review", review_agent)

    graph.set_entry_point("knowledge")
    graph.add_edge("knowledge", "review")

    return graph.compile()
