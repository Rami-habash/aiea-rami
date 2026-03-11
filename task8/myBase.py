# myBase.py
# Semantic parser: prompt formatting, LLM chain, example runner, and RAG retrieval
# Some functions similar to LINC's eval/base.py

import json
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS

from myUtils import evaluate_fol


PROMPT = ChatPromptTemplate.from_messages([
    ("system", "{instructions}{few_shot}"),
    ("human", "{problem}")
])


#----------------#
# RAG RETRIEVAL
#----------------#

# works similar to knn
# build_vectorstore indexes and retrieval finds knn 

def build_vectorstore(pw_examples: list[dict], embeddings) -> FAISS:
    texts = [ex["conclusion"] for ex in pw_examples]
    metadatas = [{"example": json.dumps(ex)} for ex in pw_examples]
    return FAISS.from_texts(texts, embeddings, metadatas=metadatas)

def retrieve(vector_store: FAISS, conclusion: str, k: int = 3) -> list[dict]:
    # filter out the same conclusion from the database
    results = vector_store.similarity_search(conclusion, k=k+3) #k+3 for safety
    retrieved = [json.loads(result.metadata["example"]) for result in results]
    filtered = [ex for ex in retrieved if ex["conclusion"] != conclusion]
    return filtered[:k]

#----------------#
# SEMANTIC PARSER
# Adapted from LINC eval/base.py
#----------------#

def get_instructions(mode: str) -> str:
    # adapted from LINC eval/base.py get_instructions()
    # to get similar instructions as linc for the models
    # added instructions imrpove parsing to nltk 
    instructions = ""
    instructions += "The following is a first-order logic (FOL) problem.\n"
    instructions += "The problem is to determine whether the conclusion follows from the premises.\n"
    instructions += "The premises are given in the form of a set of first-order logic sentences.\n"
    instructions += "The conclusion is given in the form of a single first-order logic sentence.\n"
    if mode == "baseline":
        instructions += "The task is to evaluate the conclusion as 'True', 'False', or 'Uncertain' given the premises. Respond with only one word: True, False, or Uncertain."
    elif mode == "neurosymbolic":
        instructions += "The task is to translate each of the premises and the conclusion into FOL expressions, "
        instructions += "so that the expressions can be evaluated by a theorem solver to determine whether the conclusion follows from the premises.\n"
        instructions += "Expressions should adhere to the format of the Python NLTK package logic module.\n"
        instructions += "Output ONLY the FOL translations, one per line. Prefix EVERY line with 'FOL: '.\n"
        instructions += "NOTATION: Use LOWERCASE for predicsted, CAPITALIZED names for constants (e.g. Kylian_mbappe), and standard NLTK connectives: &, |, ->, -, all x., exists x.\n"
        instructions += "Example output format:\n"
        instructions += "FOL: male(Kylian_mbappe)\n"
        instructions += "FOL: all x.(male(x) & plays_in(x, England) -> premier_league(x))\n"
        instructions += "FOL: premier_league(Kylian_mbappe)\n"
        instructions += "The LAST FOL line must be the conclusion. All lines before it are premises.\n"
    return instructions + "\n\n"


def format_test(doc: dict) -> str:
    # similar to LINC's eval/base.py format_test_example()
    out = "<PREMISES>\n"
    for premise in doc["premises"]:
        out += f"{premise.strip()}\n"
    out += "</PREMISES>\n"
    out += f"<CONCLUSION>\n{doc['conclusion'].strip()}\n</CONCLUSION>\n"
    out += "<EVALUATE>\n"
    return out


def format_train(docs: list[dict], mode: str) -> str:
    # similar to LINC's eval/base.py format_train_example()
    if not docs:
        return ""
    out = "RAG ProofWriter Examples (domain context):\n" if mode == "neurosymbolic" else ""
    for doc in docs:
        out += format_test(doc)
        if mode == "baseline":
            out += f"{doc['label'].strip()}\n"
        elif mode == "neurosymbolic":
            out += f"{doc['label'].strip()}\n"  # show complete PW example (label included) as domain context for FOL generation
        out += "</EVALUATE>\n\n"
    return out


def build_chain(llm, mode: str):
    # a chain version of LINC's get_prompt() in eval/base.py
    return PROMPT | llm | StrOutputParser()

def run_example(chain, doc: dict, few_shot_docs: list[dict], mode: str) -> tuple:
    # similar to LINC's eval/base.py postprocess_generation() but
    # fot only baseline and neurosymbolic only
    problem = format_test(doc)
    if mode == "neurosymbolic":
        problem = "Full ProofWriter Example - translate each sentence into FOL:\n" + problem
    response = chain.invoke({
        "instructions": get_instructions(mode),
        "few_shot": format_train(few_shot_docs, mode),
        "problem": problem
    })
    if mode == "baseline":
        return (response.strip(),{})
    elif mode == "neurosymbolic":
        flag = "FOL:"
        parses = [
            line.replace(flag, "").strip()
            for line in response.split("\n")
            if flag in line
        ]
        if len(parses) < 2:
            return ("Error", {})
        premises, conclusion = parses[:-1], parses[-1]
        result = evaluate_fol(premises, conclusion)

        # access the trace in every example 
        # makes sure we get trace and verdict
        trace = {"fol_premises": premises, "fol_conclusion": conclusion, "proof": result.get("proof", "").splitlines()}
        if "error" in result: trace["error"] = result["error"]
        return (result["verdict"], trace)