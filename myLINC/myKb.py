# myKb.py
# Knowledge base: converts a Prolog file to ProofWriter + FOLIO samples and caches them as JSON
# Run directly (make pw) to generate soccer_pw.json and soccer_folio.json

import os
import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

#--------------#
# Config
#--------------#

MODEL = "gpt-5"

#--------------#

# Replicating ProofWriter samples from the ProofWriter study referenced in linc
PL_TO_PW_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a logic expert. Your job is to convert prolog files into ProofWriter format. \n"
        "For each prolog file you are provided, You will output a corresponding ProofWriter file. \n"
        "The ProofWriter file must contain EXACTLY 50 UNIQUE ProofWriter examples. \n\n"

        "Each ProofWriter example must be VALID JSON data that looks like this: \n"
        "[\n"
        "{{\n"
        "\"premises\": [\"\", ...],\n"
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
        "Output ONLY the JSON array, no extra text. \n\n"

        "You MUST perform this task like a human: \n"
        "1. Generate examples one at a time. \n"
        "2. Keep a mental tally of the number of the current example you generated. \n"
        "3. For example: generate one exmple, then think ok I generated one example."
        "Once you generate example 2, check your mental tally. It should say 1, now add one to it."
        "Then think, I generated 2 examples."

    )),
    ("human", (
        "Here is the prolog file: \n"
        "{prolog_file}"
    ))
])

# Replicating FOLIO data from the FOLIO study referenced in linc: https://github.com/Yale-LILY/FOLIO/blob/main/data/v0.0/folio-train.jsonl
PL_TO_FOLIO_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a logic expert. Your job is to convert prolog files into FOLIO format. \n"
        "For each prolog file you are provided, you will output a corresponding FOLIO file. \n"
        "The FOLIO file must contain EXACTLY 50 UNIQUE FOLIO examples. \n\n"

        "Each FOLIO example must be VALID JSON data that looks like this: \n"
        "[\n"
        "{{\n"
        "\"premises\": [\"\", ...],\n"
        "\"premises_FOL\": [\"\", ...],\n"
        "\"conclusion\": \"\", \n"
        "\"label\": \"\"\n"
        "}},\n"
        "...\n"
        "]\n\n"

        "Definitions: \n"
        "premises: translate EVERY fact and rule to a one line natural language premise. \n"
        "premises-FOL: translate EVERY fact and rule to a one line FOL premise. \n"
        "conclusion: one line natural language statement that follows from the premises. \n"
        "label: 'True' if the conclusion follows, 'False' if it is contradicted, 'Uncertain' otherwise. \n\n"

        "Sample FOL notation: \n"
        "∀ : for all \n"
        "∃ : there exists \n"
        "→ : then \n"
        "¬ :  not \n"
        "∧ :  and \n"
        "∨ :  or \n"
        "⟷ : iff \n\n"

        "General rules: \n"
        "premises must contain ALL the facts in the prolog file. \n"
        "LABELS must be EVENLY DISTRIBUTED: True, False, and Uncertain across EXACTLY 50 UNIQUE examples. \n"
        "Do not use a '.' separator to end a line just end it. \n"
        "Output EXACTLY 50 examples. Please track of how many examples you generated. \n"
        "Output ONLY the JSON array, no extra text. \n"
        
        "You MUST perform this task like a human: \n"
        "1. Generate examples one at a time. \n"
        "2. Keep a mental tally of the number of the current example you generated. \n"
        "3. For example: generate one exmple, then think ok I generated one example."
        "Once you generate example 2, check your mental tally. It should say 1, now add one to it."
        "Then think, I generated 2 examples."

    )),
    ("human", (
        "Here is the prolog file: \n"
        "{prolog_file}"
    ))
])


def read_pl_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


def generate(pl_path: str, llm) -> tuple[list[dict], list[dict]]:
    dir_path = os.path.dirname(pl_path)
    pl_text = read_pl_file(pl_path)

    # 1: Generating 50 ProofWriter examples
    print("Generating 50 ProofWriter (PW) examples...")
    pw_chain = PL_TO_PW_PROMPT | llm | JsonOutputParser()
    pw_examples = pw_chain.invoke({"prolog_file": pl_text})

    pw_path = os.path.join(dir_path, "soccer_pw.json")
    with open(pw_path, "w") as f:
        json.dump(pw_examples, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(pw_examples)} PW examples to {pw_path}")

    # 2: Generating 50 FOLIO examples
    print("Generating 50 FOLIO examples...")
    folio_chain = PL_TO_FOLIO_PROMPT | llm | JsonOutputParser()
    folio_examples = folio_chain.invoke({"prolog_file": pl_text})

    folio_path = os.path.join(dir_path, "soccer_folio.json")
    with open(folio_path, "w") as f:
        json.dump(folio_examples, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(folio_examples)} FOLIO examples to {folio_path}")

    return pw_examples, folio_examples


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    from langchain_openai import ChatOpenAI

    pl_path = os.path.join(os.path.dirname(__file__), "soccer.pl")
    llm = ChatOpenAI(model=MODEL, temperature=0.7)
    generate(pl_path, llm)