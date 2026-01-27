from langgraph.graph import StateGraph
from typing import TypedDict
from backend.app.rag import get_cached_context
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class AgentState(TypedDict):
    title: str
    description: str
    code: str
    context: str
    review: str


# -------- Knowledge Agent (RAG with Valkey Cache) --------
def knowledge_agent(state: AgentState):
    query = state["description"]
    context = get_cached_context(query)
    state["context"] = context
    return state


# -------- Review Agent --------
def review_agent(state: AgentState):
    prompt = f"""
You are an expert DSA mentor.

Your job is NOT to explain theory.
Your job is to create a compact memory card ONLY IF the user made a mistake.

================= CRITICAL RULE =================
If the user's solution is already optimal, correct, and uses the right DSA pattern,
respond with exactly:

NO_MISTAKE

Do not write anything else in that case.
================================================

================= PATTERN RULE =================
You MUST choose the PATTERN strictly from the allowed list below.
Never invent new pattern names.
Never use algorithm names like Kadane, Boyer-Moore, etc.
Map them to their parent pattern.

ALLOWED PATTERNS:

HashMap Pattern
Stack Pattern
Queue Pattern
Two Pointer Pattern
Fast & Slow Pointer Pattern
Sliding Window Pattern
Prefix Sum Pattern
Binary Search Pattern
Cyclic Sort
In-place Array Reversal
Merge Intervals
Monotonic Stack
Monotonic Queue

Dynamic Programming (Memoization)
Dynamic Programming (Tabulation)
Greedy Pattern
Divide and Conquer
Meet-in-the-Middle
QuickSelect (Selection Algorithm)

Tree BFS (Level Order)
Tree DFS
Graph BFS
Graph DFS
Topological Sort
Union Find (Disjoint Set)
Morris Traversal
Trie (Prefix Tree)
Binary Lifting

Dijkstra’s Algorithm
Bellman-Ford Algorithm
Floyd-Warshall Algorithm
Prim's Algorithm (MST)
Kruskal's Algorithm (MST)

Heap / Priority Queue (Top K Elements)
K-way Merge
Two Heaps Pattern
Segment Tree / Fenwick Tree

Bit Manipulation
Math / Geometry
Reservoir Sampling
Matrix Manipulation
String Matching (KMP / Rabin-Karp)
================================================

Otherwise, use this STRICT format. Do not add anything else.

MISTAKE:
(one line mistake in user's approach)

PATTERN:
(one pattern name strictly from the allowed list)

COMPLEXITY:
(expected vs used complexity)

REMINDER:
(one line mental trigger to remember next time)

CORRECTED CODE:
(Return the corrected optimal solution strictly in the SAME programming language used by the user.
Do NOT change the language.
Provide only the corrected code.)

Problem:
{state['title']}

Description:
{state['description']}

User Code:
{state['code']}

Relevant DSA Concepts:
{state['context']}
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
