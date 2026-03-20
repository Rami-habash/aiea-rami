# myGraph.py
## Reimplementing LINC pipeline as a LangGraph
'''
- This will be the graph of LINC ++ (agentic solver)
- agent decides wether to persue linc route or cot
- Every time the LLM is tasked to predict:

retrieve FOL -> judge_relevance -> if relevant -> linc -> reuslt
                                        |
                                      else -> cot -> result

TODO: 
0. ALL IMPORTS
1. Create a LangGraph state
2. Create a node for each step
3. Routing function
4. invoke the graph for a few queries
5. Look at it in LangSmith
'''

import os, json, sys, random
from collections import Counter
from typing import TypedDict

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END

from myBase import (
    build_chain, run_example, build_vectorstore, retrieve,
    format_test, format_train, get_instructions,
)

#----------------#
# CONFIG
#----------------#

MODELS_TEST = ['gpt-4o-mini', 'gpt-3.5-turbo']
MODES = ['baseline', 'neurosymbolic']
PW_FILE = "soccer_pw.json"
FOLIO_FILE = "soccer_folio.json"
P_SAMPLES = 0.1
P_FOLIO_TRAIN = 0.3
K_VOTES = 3
RAG_TOP_K = 3
embeddings = OpenAIEmbeddings()

JUDGE_MODEL = "gpt-4o-mini" # fast model for relevance judge

N_QUERIES = 10
LLM_Q = "gpt-5-mini"

#----------------#
# LANGGRAPH STATE
#----------------#

class LINCState(TypedDict):
    doc: dict # test example {premises, conclusion, label}
    vector_store: object # FAISS index
    rag_k: int
    llm: object # main LLM for parsing/cot
    mode: str # like neurosymbolic/baseline
    few_shot_docs: list # retrieved FOLIO examples
    relevant: bool # judge decision
    verdict: str
    trace: dict

#----------------#
# GRAPH NODES
#----------------#

# 1. RAG retrieval node
def retrieve_node(state: LINCState) -> dict:
    # RAG retrieval from FOLIO vectorstore
    docs = retrieve(state["vector_store"], state["doc"]["conclusion"], k=state["rag_k"])
    return {"few_shot_docs": docs}

# 2. judge node
def judge_node(state: LINCState) -> dict:

    few_shot_docs = state["few_shot_docs"]

    if not few_shot_docs:
        return {"relevant": False}

    # strings for LLM 
    example_text = str(state["doc"])
    sample_text = str(few_shot_docs)

    judge_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a relevance judge. Looking at sample translations, decide "
         "if they are relevant enough to help translate the human's example "
         "into first order logic (FOL).\n"
         "Respond with ONLY 'Relevant' or 'Not Relevant'."),
        ("human",
         "Example: {example}. \nSample translations:\n{sample}"),
    ])

    chain = judge_prompt | state["llm"] | StrOutputParser()
    response = chain.invoke({
        "example": example_text, "sample": sample_text,
    })

    relevant = "not" not in response.strip().lower()
    return {"relevant": relevant}

# 3. route 1
def linc_node(state: LINCState) -> dict:
    # neurosymbolic: RAG few-shot -> FOL translation -> Prover9
    chain = build_chain(state["llm"], state["mode"])
    verdict, trace = run_example(chain, state["doc"], state["few_shot_docs"], state["mode"])
    return {"verdict": verdict, "trace": trace}

# 4. route 2
# CoT prompt from LINC's eval/base.py (scratchpad mode)
COT_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "The following is a first-order logic (FOL) problem.\n"
     "The problem is to determine whether the conclusion follows from the premises.\n"
     "Think step by step, then state your final answer.\n"
     "End your response with 'ANSWER: True', 'ANSWER: False', or 'ANSWER: Uncertain'."),
    ("human", "{problem}"),
])

def cot_node(state: LINCState) -> dict:
    chain = COT_PROMPT | state["llm"] | StrOutputParser()
    problem = format_test(state["doc"])
    response = chain.invoke({"problem": problem})

    # extract verdict after ANSWER: flag (like LINC base.py line 292-294)
    verdict = "Uncertain"
    if "ANSWER:" in response:
        verdict = response.split("ANSWER:")[-1].strip()
    trace = {"COT": response, "path": "cot"}
    return {"verdict": verdict, "trace": trace}

#----------------#
# ROUTING
#----------------#

# routing based on relevance
def route_relevance(state: LINCState) -> str:
    return "linc" if state["relevant"] else "cot"

#----------------#
# BUILDING GRAPH
#----------------#

def build_graph():

    # build graph
    g = StateGraph(LINCState)
    g.add_node("retrieve", retrieve_node)
    g.add_node("judge", judge_node)
    g.add_node("linc", linc_node)
    g.add_node("cot", cot_node)

    # direct graph
    g.set_entry_point("retrieve")
    g.add_edge("retrieve", "judge")
    g.add_conditional_edges("judge", route_relevance, {
        "linc": "linc",
        "cot": "cot",
    })
    g.add_edge("linc", END)
    g.add_edge("cot", END)
    return g.compile()

graph = build_graph()

#----------------#
# Running examples through graph
#----------------#

def run_graph(doc, vector_store, llm, mode="neurosymbolic", rag_k=RAG_TOP_K):
    # drop-in replacement for run_example but goes through the langgraph
    result = graph.invoke({
        "doc": doc,
        "vector_store": vector_store,
        "rag_k": rag_k,
        "llm": llm,
        "mode": mode,
        "few_shot_docs": [],
        "relevant": False,
        "verdict": "Error",
        "trace": {},
    })
    return result["verdict"], result["trace"]
