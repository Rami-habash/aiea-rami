
import json
import os
from configparser import ConfigParser
import re
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from openai import OpenAI
import hashlib
import pickle
from dotenv import load_dotenv

load_dotenv()

# Read configuration file
file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../config.ini").replace("\\", "/")
cf = ConfigParser()
cf.read(file_path, encoding="utf-8")
os.environ["OPENAI_API_BASE"] = cf.get("API", "BASE_URL")
os.environ["OPENAI_API_KEY"] = os.getenv(cf.get("API", "API_SECRET_KEY"), cf.get("API", "API_SECRET_KEY"))

max_retry = cf.getint("API", "MAX_RETRY")
MODEL = cf.get("API", "MODEL")
CHECKER_MODEL = cf.get("API", "CHECKER_MODEL")
CHECKER_TEMPATURE = cf.get("API", "CHECKER_TEMPATURE")
Temperature  = cf.get("API", "TEMPERATURE")
K_NUM = cf.get("API", "K_NUM")
STATIC_NUM = cf.get("API", "STATIC_NUM")
KB_ID = cf.get("API", "KB_ID")
DATATYPE = cf.get("API", "DATATYPE")
client = OpenAI(
    api_key="sk-",
    base_url="https://api.deepseek.com",
)
llm = ChatOpenAI(
    model=MODEL,
    temperature=Temperature,
    api_key = cf.get("API", "API_SECRET_KEY"),
    base_url= cf.get("API", "BASE_URL"),
)
# globalvariableswitch
ENABLE_EXTRACTION = cf.get("API", "ENABLE_EXTRACTION") == "True"
ENABLE_SELECTION = cf.get("API", "ENABLE_SELECTION") == "True"
ENABLE_KNOWLEDGE = cf.get("API", "ENABLE_KNOWLEDGE") == "True"
ENABLE_FIX = cf.get("API", "ENABLE_FIX") == "True"
# For vector caching
vector_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../vector").replace("\\", "/")
if not os.path.exists(vector_path):
    os.makedirs(vector_path)
embeddings = OpenAIEmbeddings(model=cf.get("API", "EMBEDDING_MODEL"), openai_api_base=cf.get("API", "EMBEDDING_URL"), openai_api_key=cf.get("API", "EMBEDDING_KEY"))
# For vectorization
async def vectorize(text: str) -> list:
    global embeddings
    # Calculate MD5 hash of text to prevent duplication
    text_hash = hashlib.md5(text.encode()).hexdigest()+ str(len(text))
    cache_path = f"{vector_path}/{text_hash}.pkl"

    # Check cache first
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            return pickle.load(f)

    res = await embeddings.aembed_query(text)

    # Save to cache
    with open(cache_path, 'wb') as f:
        pickle.dump(res, f)

    return list(res)

# For sending messages, normal conversation
async def chat(prompt:str, system_msg:str = "", temperature=0.7):
    global cf,max_retry,llm
    cur = 0
    while cur < max_retry:
        try:
            res = await llm.ainvoke(get_msg(prompt, system_msg))
            return res.content
        except Exception as e:
            print(f"chat error {cur + 1}attempts: {e}")
            cur += 1
    return ""
# For sending messages, json conversation
async def chat_json(prompt:str, system_msg:str = "", temperature=0.7):
    global cf,max_retry,client
    cur = 0
    messages = [{"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}]
    while cur < max_retry:
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                response_format={
                    'type': 'json_object'
                }
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"chat_json error {cur + 1}attempts: {e}")
            cur += 1
    return []
# Construct chat json from data
def get_msg(hmsg, smsg=""):
    if smsg == "":
        messages = [
            ("human", hmsg),
       ]
    else:
        messages = [
            (
                "system",
                smsg,
            ),
            ("human", hmsg),
       ]
    return messages

DESC_OF_NLTK = """
To describe First-Order Logic (FOL) formulas using NLTK's symbols, follow these guidelines:

1. Quantifiers:
   - Universal quantifier (`∀`) is represented as `all x1.`.
   - Existential quantifier (`∃`) is represented as `exists x2.`.

2. Implication (`→`):
   - Implication is represented as `->`.

3. Biconditional (`⟷` or `↔`):
   - Biconditional is represented as `<->`.

4. Conjunction (`∧`):
   - Conjunction is represented as `&`.

5. Disjunction (`∨`):
   - Disjunction is represented as `|`.

6. Negation (`¬`):
   - Negation is represented as `-`.

7. Exclusive Disjunction (XOR) (`⊕`):
   - XOR is represented as `^`.

Variables that take the form of a single lowercase character followed by one or more digits.
Such as `x1`, `x2`, `y1`, `y2`, etc.

Expressions should adhere to the format of the Python NLTK package logic module.
So that the expressions can be evaluated by a theorem solver to determine whether the conclusion follows from the premises.
Here's an example:
all x1.(all x2.(InteractsWith(x1, x2) -> Influences(x1)))
This formula can be read as: "For all x1 and for all x2, if x1 interacts with x2 then x1 influences something."

To break it down:
- `all x1.` is the first universal quantifier.
- `all x2.` is the second universal quantifier.
- `InteractsWith(x1, x2)` is a predicate `InteractsWith` that takes two parameters, `x1` and `x2`.
- `InteractsWith(x1, x2) -> Influences(x1)` represents the implication where if predicate `InteractsWith` holds for both `x1` and `x2`, then predicate `Influences` holds for `x1`.
"""

e = """

Here's an example of an FOL formula using more descriptive predicates:

```
all x1.(exists x2.(HasProperty(x1) ^ MeetsCondition(x2)) <-> SatisfiesRequirement(x1))
```

This formula can be read as: "For all x1, there exists an x2 such that x1 has a certain property XOR x2 meets a certain condition if and only if x1 satisfies a certain requirement."

To break it down:
- `all x1.` is the universal quantifier.
- `exists x2.` is the existential quantifier.
- `HasProperty(x1) ^ MeetsCondition(x2)` represents the XOR (exclusive disjunction) of predicates `HasProperty` and `MeetsCondition`.
- `<->` is the biconditional symbol.
- `SatisfiesRequirement(x1)` is a predicate `SatisfiesRequirement` applied to `x1`.

Here's another example:

```
all x1.(all x2.(InteractsWith(x1, x2) -> Influences(x1)))
```

This formula can be read as: "For all x1 and for all x2, if x1 interacts with x2 then x1 influences something."

To break it down:
- `all x1.` is the first universal quantifier.
- `all x2.` is the second universal quantifier.
- `InteractsWith(x1, x2)` is a predicate `InteractsWith` that takes two parameters, `x1` and `x2`.
- `InteractsWith(x1, x2) -> Influences(x1)` represents the implication where if predicate `InteractsWith` holds for both `x1` and `x2`, then predicate `Influences` holds for `x1`.

This format ensures that the formula is syntactically correct and can be parsed by NLTK's logic module."""