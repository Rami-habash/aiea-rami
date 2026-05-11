# myProg.py
## Reimplementing LINC using RAG in LngChain
'''
PIPELINE:
LINC:  ProofWriter/Folio -> Semantic Parser (LLM) -> FOL -> Prover9
MINE:  prolog -> BASE LLM -> generated ProofWriter (cached) -> RAG few-shot -> Semantic Parser (variable LLMs) -> FOL -> Prover9
'''

import os
from collections import Counter

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate

from myBase import build_chain, run_example, build_vectorstore, retrieve
from myPlot import plot_results

import random

global err
err = 0 # for debugging
#----------------#
# CONFIG
#----------------#

MODELS_TEST = ['gpt-3.5-turbo', 'gpt-4o-mini']
MODES = ['baseline', 'neurosymbolic']
PW_FILE = "soccer_kb.json"
K_VOTES = 3 # number of votes for each example verdict
RAG_TOP_K = 3 # number of relevant rag items
PW_SAMPLES = 50  # number of random proofwriter examples to test from json file
embeddings = OpenAIEmbeddings()
N_QUERIES = 10 # for make run_queries
LLM_Q = "gpt-5-mini" # model for queries
#----------------#
# BENCHMARK RUNNER
# similar to LINC's eval/base.py metric() lines 300+
#----------------#

def run_benchmark(pw_examples, all_examples):
    # loads KB, builds RAG index, loops models/modes (mirrors LINC eval/base.py metric())
    vector_store = build_vectorstore(all_examples, embeddings)  # build RAG index over full KB (not test set)

    results = {}
    traces = {}

    for model_name in MODELS_TEST:
        llm = ChatOpenAI(model=model_name, temperature=0.7)
        results[model_name] = {}

        for mode in MODES:
            chain = build_chain(llm, mode)
            correct = 0

            for doc in pw_examples:
                # baseline is zero-shot (pure, like LINC); neurosymbolic uses RAG few-shot
                few_shot_docs = [] if mode == "baseline" else retrieve(vector_store, doc["conclusion"], k=RAG_TOP_K)
                # k-majority vote (same idea as LINC base.py metric())
                verdict_results = [run_example(chain, doc, few_shot_docs, mode) for _ in range(K_VOTES)]
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

            results[model_name][mode] = correct / len(pw_examples)
            print(f"{model_name} | {mode}: {results[model_name][mode]:.0%}")

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

def queries(all_examples, n = N_QUERIES):
    # running (LINC only) test queries.
    vector_store = build_vectorstore(all_examples, embeddings)
    llm = ChatOpenAI(model=LLM_Q, temperature=0.7)
    chain = build_chain(llm, "neurosymbolic")

    samples = random.sample(all_examples, min(n, len(all_examples)))
    for i, doc in enumerate(samples, 1):

        # RAG and run_example
        few_shot_docs = retrieve(vector_store, doc["conclusion"], k=RAG_TOP_K)
        predicted, trace = run_example(chain, doc, few_shot_docs, "neurosymbolic")

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
    with open(os.path.join(os.path.dirname(__file__), PW_FILE), "r") as f:
        all_examples = json.load(f)

    if "--queries" in sys.argv:
        # query + inference trace
        queries(all_examples)
    else:
        # full benchmark run
        pw_examples = random.sample(all_examples, min(PW_SAMPLES, len(all_examples)))
        results, traces = run_benchmark(pw_examples, all_examples)

        # save results so "make plt" can replot without rerunning
        with open(os.path.join(os.path.dirname(__file__), "performance.json"), "w") as f:
            json.dump(results, f, indent=2)

        # save results for traces to each conclusion
        with open(os.path.join(os.path.dirname(__file__), "trace.json"), "w") as f:
            json.dump(traces, f, indent=2)

        # debug
        print (f"err {err}")