import logging
import os
from llm.AgentBase import AgentBase
from utils.knowledge import retrieve, vectorstore
from config.Settings import config
class symbol(AgentBase):
    def __init__(self,datatype="",agent_config:dict={}):
        model_type = "symbol"
        super().__init__(model_type,datatype)
        if not agent_config:
            self.num = config["agent"][model_type]["num"]
            self.kb_id = config["agent"][model_type]["kb_id"]
            self.temperature = config["agent"][model_type]["temperature"]
        else:
            self.num = agent_config.get("num",config["agent"][model_type]["num"])
            self.kb_id = agent_config.get("kb_id",config["agent"][model_type]["kb_id"])
            self.temperature = agent_config.get("temperature",config["agent"][model_type]["temperature"])
        # Grammar rules, may be used in subsequent tasks
        self.rule_msg = """The grammar of the first-order logic formular is defined as follows:
1) logical conjunction of expr1 and expr2: expr1 ∧ expr2
2) logical disjunction of expr1 and expr2: expr1 ∨ expr2
3) logical exclusive disjunction of expr1 and expr2: expr1 ⊕ expr2
Things that can't happen at the same time are generally used as logical exclusive disjunction rather than logical disjunction.
4) logical negation of expr1: ¬expr1
5) expr1 implies expr2: expr1 → expr2
6) expr1 if and only if expr2: expr1 ↔ expr2
7) logical universal quantification: ∀x
8) logical existential quantification: ∃x
9) available logical variable: u,v,w,x,y,z
The invalid characters are:
∈,∉,=,≠,≤,≥,<,>,True,False
These characters will lead to errors.Because the solver can not recognize them.
And, don't output in latex.The solver can not recognize latex.
"""
        self.chat_msg = ""
        self.json_msg = """
The user will provide some thought process for translating natural language to first-order logic language. You need to get all the premise formulas and a final conclusion formula. Please parse the "premise", "conclusion" and output it in JSON format.
EXAMPLE INPUT:
Premises:
1.Text:No criminal is kind.
Predicates:
Kind(x),Criminal(x)
Fol:∀x (Criminal(x) → ¬Kind(x))
2.Text:All person who breaks the law is a criminals.
Predicates:
BreakLaw(x),Criminal(x)
Fol:∀x (BreakLaw(x) → Criminal(x))
3.Text:People are either kind or evil.
Predicates:
Kind(x),Evil(x)
Fol:∀x (Kind(x) ⊕ Evil(x))
4.Text:If someone is evil, then they are ugly.
Predicates:
Evil(x),Ugly(x)
Fol:∀x (Evil(x) → Ugly(x))
5.Text:If someone is evil, then they are cold-blood.
Predicates:
ColdBlood(x),Evil(x)
Fol:∀x (Evil(x) → ColdBlood(x))
6.Text:If Garry is either evil and ugly or neither evil nor ugly, then Garry is not evil.
Predicates:
Evil(x),Ugly(x)
Constants:
garry
Fol:((Evil(garry) ∧ Ugly(garry)) ⊕ (¬Evil(garry) ∧ ¬Ugly(garry))) → ¬Evil(garry)
Conclusion:
Text:If Garry is evil or breaks the law, then Garry is not both a criminal and breaking the law.
Predicates:
BreakLaw(x),Evil(x),Criminal(x)
Constants:
garry
Fol:(Evil(garry) ∨ BreakLaw(garry)) → ¬(Criminal(garry) ∧ BreakLaw(garry))

EXAMPLE JSON OUTPUT:
{
  "premises": [
    "∀x (Criminal(x) → ¬Kind(x))",
    "∀x (BreakLaw(x) → Criminal(x))",
    "∀x (Kind(x) ⊕ Evil(x))",
    "∀x (Evil(x) → Ugly(x))",
    "∀x (Evil(x) → ColdBlood(x))",
    "((Evil(garry) ∧ Ugly(garry)) ⊕ (¬Evil(garry) ∧ ¬Ugly(garry))) → ¬Evil(garry)"
  ],
  "conclusion": "(Evil(garry) ∨ BreakLaw(garry)) → ¬(Criminal(garry) ∧ BreakLaw(garry))"
}
"""

    def generate_prompt(self, prompt: str,examples:list=None)->str:
        if examples:
            example = "\n-----\n".join([f"Input:\n{item['Input']}\nOutput:\n{item['Output']}" for item in examples])
        else:
            example = self.example
        prompt = f"""{self.rule_msg}
{example}
Input:
Now translate the given premises and conclusion into First-Order Logic (FOL) expressions.
{prompt}
Let's think step by step.
Output:"""
        return prompt


    def chat(self, prompt: str) -> tuple:
        examples = retrieve(vectorstore, prompt, k=self.num) if self.num > 0 else ""
        self.prompt = self.generate_prompt(prompt,examples)
        return super().chat(self.prompt)

if __name__ == "__main__":
    pass