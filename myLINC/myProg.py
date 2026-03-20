# myProg.py
## Reimplementing LINC using RAG in LngChain
"""
NEW PIPELINE
LINC:  ProofWriter (PW)/Folio -> Semantic Parser (LLM) -> FOL -> Prover9
MINE:  prolog -> BASE LLM -> generated PW/FOLIO -> run_graph (linc if FOLIO training is relevant else cot)
"""

import os
from collections import Counter

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate

from myBase import build_chain, run_example, build_vectorstore, retrieve
from myGraph import run_graph
from myPlot import plot_results

import random

global err
err = 0 # for debugging
#----------------#
# CONFIG
#----------------#

MODELS_TEST = ['gpt-3.5-turbo', 'gpt-4o-mini']
MODES = ['baseline', 'neurosymbolic']
PW_FILE = "soccer_pw.json" # ProofWriter test set (NL only)
FOLIO_FILE = "soccer_folio.json"  # FOLIO examples (NL + FOL) — split into train/test
P_SAMPLES = 1 # percentage of tested samples PW and FOLIO
P_FOLIO_TRAIN = 0.3  # % "training" pool, rest is test
K_VOTES = 3 # number of votes for each example verdict
RAG_TOP_K = 3 # number of relevant rag items
embeddings = OpenAIEmbeddings()

# -- QUERIES --
N_QUERIES = 10 # for make run_queries
LLM_Q = "gpt-5-mini" # model for queries

#----------------#
# BENCHMARK RUNNER
# similar to LINC's eval/base.py metric() lines 300+
#----------------#

def run_benchmark(test_examples, vector_store, task_name=""):
    # evaluates test_examples against RAG few-shot from vector_store
    # mirrors LINC eval/base.py metric() (called once per task (PW, FOLIO))
    results = {}
    traces = {}

    for model_name in MODELS_TEST:
        llm = ChatOpenAI(model=model_name, temperature=0.7)
        results[model_name] = {}

        for mode in MODES:
            correct = 0

            for doc in test_examples:
                # baseline is zero-shot (pure, like LINC). Neurosymbolic uses LangGraph (RAG + relevance judge + CoT fallback)
                if mode == "baseline":
                    chain = build_chain(llm, mode)
                    verdict_results = [run_example(chain, doc, [], mode) for _ in range(K_VOTES)]
                else:
                    verdict_results = [run_graph(doc, vector_store, llm, mode) for _ in range(K_VOTES)]
                votes = [v for v, t in verdict_results]
                predicted = Counter(votes).most_common(1)[0][0]
                if predicted == doc["label"]:
                    correct += 1

                #-- FIXME --
                # debug
                global err
                if predicted == "Error":
                    err += 1
                #-- --

                # grab the trace of the winning vote
                trace = next(t for v, t in verdict_results if v == predicted)
                if trace: traces[doc["conclusion"]] = {**trace, "label": doc["label"], "predicted": predicted}

            results[model_name][mode] = correct / len(test_examples)
            print(f"{task_name} - {model_name} | {mode}: {results[model_name][mode]:.0%}")

    return results, traces

"""
Query part of deliverable:
P9_EXPLANATION: explains Prover9 syntax in nl
def queries: queries random conclusions from our database
"""
P9_EXPLANATION = ChatPromptTemplate.from_messages([

    ("system", (
        "You are a logic expert."
        "Your Job is to make the Prover9 inference trace more readable"
        "Use simple natural language to explain its inference"
        "Please be concise and interpretable"
    )),

    ("human", "here is the trace: {trace}")

])

"""
Updated for graph impl
TODO:
1. call graph for each test_example
2. pass in the same train examples
"""
def queries(train_examples, test_examples, vector_store, n = N_QUERIES):
    # running (graph) test queries.
    llm = ChatOpenAI(model=LLM_Q, temperature=0.7)

    for i, doc in enumerate(test_examples[:n], 1):

        predicted, trace = run_graph(doc, vector_store, llm, "neurosymbolic")

        print(f"\n{'='*60}")
        print(f"Query {i}: {doc['conclusion']}")
        print(f"{'='*60}")
        print(f"Label : {doc['label']}")
        print(f"Predicted : {predicted}")

        if trace.get("fol_premises"):
            print(f"\n--- FOL Translation ---")
            for p in trace["fol_premises"]:
                print(f"  Premise: {p}")
            print(f"  Conclusion: {trace['fol_conclusion']}")

        if trace.get("proof"):
            trace["proof"] = "\n".join(trace["proof"])

            # print p9 trace
            print(f"\n--- Prover9 Inference Trace ---") 
            print(trace["proof"])
            print(f"--- Interpretting Prover9's Resolution Inference ---")

            # nl version
            chain_p9 = P9_EXPLANATION | llm
            explanation = chain_p9.invoke({"trace": trace["proof"]})
            print(explanation.content)

        else:
            if predicted == "Error":
                # errors likely indicate fol syntax issues
                print(f"\n(Error: {trace.get('error', 'error')})")
            else:
                print(f"\n(No proof found because verdict: Uncertain)")



if __name__ == "__main__":
    import json, sys
    dir_path = os.path.dirname(__file__)
    with open(os.path.join(dir_path, PW_FILE), "r") as f:
        pw_examples = json.load(f)
    with open(os.path.join(dir_path, FOLIO_FILE), "r") as f:
        folio_examples = json.load(f)

    # setting up tested (PW and FOL) and trained (FOL only) examples
    num_examples = int(min(len(pw_examples), len(folio_examples)) * P_SAMPLES) 
    pw_examples = random.sample(pw_examples, num_examples)
    folio_examples = random.sample(folio_examples, num_examples)

    # train/test split on FOLIO (like LINC: FOLIO train for few-shot, test for evaluation)
    folio_train = random.sample(folio_examples, min(len(folio_examples), int(len(folio_examples) * P_FOLIO_TRAIN)))
    folio_test = [i for i in folio_examples if i not in folio_train]

    # RAG index built from FOLIO train only (has FOL translations for few-shot)
    vector_store = build_vectorstore(folio_train, embeddings)

    if "--queries" in sys.argv:
        queries(folio_train, pw_examples, vector_store)

    else:
        # two separate benchmarks for FOLIO and PW
        print(f"\n{'='*50}")
        print(f"FOLIO benchmark ({len(folio_test)} examples)")
        print(f"{'='*50}")
        folio_results, folio_traces = run_benchmark(folio_test, vector_store, "FOLIO")

        print(f"\n{'='*50}")
        print(f"ProofWriter benchmark ({len(pw_examples)} examples)")
        print(f"{'='*50}")
        pw_results, pw_traces = run_benchmark(pw_examples, vector_store, "ProofWriter")

        # save results
        results = {"ProofWriter": pw_results, "FOLIO": folio_results}
        traces = {"ProofWriter": pw_traces, "FOLIO": folio_traces}

        with open(os.path.join(dir_path, "performance.json"), "w") as f:
            json.dump(results, f, indent=2)
        with open(os.path.join(dir_path, "trace.json"), "w") as f:
            json.dump(traces, f, indent=2)

        # debug
        print(f"\n {'-'*50}")
        print(f"err {err}")