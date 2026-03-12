# myKb.py
# Knowledge base: converts a Prolog file to ProofWriter samples and caches them as JSON
# Run directly (make pw) to generate soccer_kb.json without running the full benchmark

import os
import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

#--------------#
# Config
#--------------#

MODEL = "gpt-5"

#--------------#

"""
TODO: 2nd go around
introduce FOLIO type examples as well
remember PW: nl only FOL: nl and FOL translations
we will try RAG on FOLIO next time instead of PW
"""

PL_TO_PW_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a logic expert. Your job is to convert prolog files into ProofWriter format. \n"
        "You are also a counting expert and can keep track of how many examples you generate. \n"
        "For each prolog file you are provided, You will output a corresponding ProofWriter file. \n"
        "The ProofWriter file must contain EXACTLY 50 UNIQUE ProofWriter examples. \n\n"

        "Each ProofWriter example must be VALID JSON data that looks like this: \n"
        "[\n"
        "{{\n"
        "\"premises\": [],\n"
        "\"conclusion\": \"\",\n"
        "\"label\": \"\"\n"
        "}},\n"
        "...\n"
        "]\n"

        "Definitions: \n"
        "premises: directly map every fact and rule to a one line natural language premise. \n"
        "conclusion: one line natural language statement that follows from the premises. \n"
        "label: 'True' if the conclusion follows, 'False' if it is contradicted, 'Uncertain' otherwise. \n"

        "General rules: \n"
        "premises must contain ALL the facts in the prolog file. \n"
        "LABELS must be EVENLY DISTRIBUTED: True, False, and Uncertain across EXACTLY 50 UNIQUE examples. \n"
        "Output ONLY the JSON array, no extra text. \n"
    )),
    ("human", (
        "Here is the prolog file: \n"
        "{prolog_file}"
    ))
])


def read_pl_file(path: str) -> str:
    # reads the pl file and returns its contents as a string
    with open(path, "r") as f:
        return f.read()


def _kb_json_path(pl_path: str) -> str:
    # returns the path to the cached _kb.json file next to the .pl file
    base = os.path.splitext(pl_path)[0]
    return base + "_kb.json"


def generate(pl_path: str, llm) -> list[dict]:

    # generates new pw sample
    json_path = _kb_json_path(pl_path)

    print("Generating ProofWriter (PW) examples from .pl file...")
    pl_text = read_pl_file(pl_path)
    chain = PL_TO_PW_PROMPT | llm | JsonOutputParser()
    pw_examples = chain.invoke({"prolog_file": pl_text})

    with open(json_path, "w") as f:
        json.dump(pw_examples, f, indent=2)
    print(f"Saved {len(pw_examples)} examples to {json_path}")
    return pw_examples


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    from langchain_openai import ChatOpenAI

    pl_path = os.path.join(os.path.dirname(__file__), "soccer.pl")
    llm = ChatOpenAI(model=MODEL, temperature=0.7)
    generate(pl_path, llm)
