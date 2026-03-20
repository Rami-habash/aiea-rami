# myBase.py
# Semantic parser: prompt formatting, LLM chain, example runner, and RAG retrieval
# Some functions similar to LINC's eval/base.py

import json
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS

from myUtils import evaluate_fol, convert_to_nltk_rep


PROMPT = ChatPromptTemplate.from_messages([
    ("system", "{instructions}{few_shot}"),
    ("human", "{problem}")
])


#----------------#
# RAG RETRIEVAL
#----------------#

# works similar to knn
# build_vectorstore indexes and retrieval finds knn 

def build_vectorstore(folio_examples: list[dict], embeddings) -> FAISS:
    # indexes ONLY FOLIO examples (which have FOL translations) for RAG retrieval
    texts = [ex["conclusion"] for ex in folio_examples]
    metadatas = [{"example": json.dumps(ex)} for ex in folio_examples]
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
    # added instructions imrpove parsing to nltk FOL
    instructions = ""
    instructions += "The following is a first-order logic (FOL) problem.\n"
    instructions += "The problem is to determine whether the conclusion follows from the premises.\n"
    instructions += "The premises are given in the form of a set of first-order logic sentences.\n"
    instructions += "The conclusion is given in the form of a single first-order logic sentence.\n"
    if mode == "baseline":
        instructions += "The task is to evaluate the conclusion as 'True', 'False', or 'Uncertain' given the premises. Respond with only one word: True, False, or Uncertain."
    elif mode == "neurosymbolic":
        instructions += "The task is to translate each of the natural language premises and the conclusion into FOL expressions, "
        instructions += "so that the expressions can be evaluated by a theorem solver to determine whether the conclusion follows from the premises.\n"
        instructions += "Output ONLY the FOL translations, one per line. Prefix EVERY line with 'FOL: '.\n"
        instructions += "The LAST FOL line must be the conclusion. All lines before it are premises. \n"
        instructions += "Use this notation for reference: \n" 
        instructions += "Sample FOL notation: \n" "∀ : for all \n" "∃ : there exists \n" "→ : then \n" "¬ :  not \n" "∧ :  and \n" "∨ :  or \n" "⟷ : iff \n" "⊕ : xor" "\n"
        instructions += "Here are a few example of some translations: \n"
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
    # neurosymbolic mode shows TEXT/FOL pairs so the LLM learns NL->FOL translation
    if not docs:
        return ""
    out = ""
    for doc in docs:
        if mode == "baseline":
            out += format_test(doc)
            out += f"{doc['label'].strip()}\n"
            out += "</EVALUATE>\n\n"
        elif mode == "neurosymbolic":
            # FOLIO example: show TEXT/FOL pairs (like LINC base.py line 220-222)
            out += "<PREMISES>\n"
            premises_fol = doc.get("premises_FOL", doc.get("premises-FOL", []))
            for premise, fol in zip(doc["premises"], premises_fol):
                out += f"TEXT:\t{premise.strip()}\nFOL:\t{fol.strip()}\n"
            out += "</PREMISES>\n"
            out += f"<CONCLUSION>\nTEXT:\t{doc['conclusion'].strip()}\n</CONCLUSION>\n"
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
        problem = "Full ProofWriter Example: translate each sentence into FOL: \n" + problem
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
        # convert unicode FOL (from FOLIO-style output) to NLTK syntax before Prover9
        premises = [convert_to_nltk_rep(p) for p in parses[:-1]]
        conclusion = convert_to_nltk_rep(parses[-1])
        result = evaluate_fol(premises, conclusion)

        # access the trace in every example 
        # makes sure we get trace and verdict
        trace = {"fol_premises": premises, "fol_conclusion": conclusion, "proof": result.get("proof", "").splitlines()}
        if "error" in result: trace["error"] = result["error"]
        return (result["verdict"], trace)