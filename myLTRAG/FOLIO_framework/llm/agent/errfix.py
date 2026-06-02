import logging
import os
from llm.AgentBase import AgentBase
from utils.knowledge import retrieve, vectorstore
from config.Settings import config
class errfix(AgentBase):
    def __init__(self,datatype="",agent_config:dict={}):
        model_type = "errfix"
        super().__init__(model_type,datatype)
        if not agent_config:
            self.num = config["agent"][model_type]["num"]
            self.kb_id = config["agent"][model_type]["kb_id"]
            self.temperature = config["agent"][model_type]["temperature"]
        else:
            self.num = agent_config.get("num",config["agent"][model_type]["num"])
            self.kb_id = agent_config.get("kb_id",config["agent"][model_type]["kb_id"])
            self.temperature = agent_config.get("temperature",config["agent"][model_type]["temperature"])
        self.reasoning_effort = (agent_config or {}).get("reasoning_effort", self.reasoning_effort)
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
You can use predicate to represent the relation.Don't use these characters.
"""
        self.chat_msg = ""
        self.json_msg = """
The user will provide some first-order logic language modification procedures.
You need to get all the premise formulas and a final conclusion formula. Please parse the "premise", "conclusion" and output it in JSON format.
EXAMPLE INPUT:
PPremises:

1. Original:
   ParticipatedInWinterOlympics(guam)
   Explanation: There is no need to change.

2. Original:
   HeldIn(1988, calgary)
   Explanation: The predicate HeldIn has two arguments, which is valid. However, we need to ensure that the year is represented correctly. We replace it with a predicate indicating that the Winter Olympics were held in Calgary in 1988.
   Corrected:
   Year(y1988) → BeHeld(winterolympics, calgary)

3. Original:
   SentAthleteTo(guam, calgary)
   Explanation: The predicate SentAthleteTo has two arguments, which is valid. However, we need to ensure that it aligns with the corrected predicate from Premise 2.
   Corrected:
   BeHeld(winterolympics, calgary) → SendAthletes(guam)

4. Original:
   SentAthleteTo(guam, calgary) → ParticipatedInWinterOlympics(guam)
   Explanation: The predicate SentAthleteTo has two arguments, which is valid. However, we need to ensure that it aligns with the corrected predicate from Premise 3.
   Corrected:
   SendAthletes(guam) → ParticipatedIn(guam, winterolympics)

5. Original:
   ∀a (CompetedInWinterOlympics(a) → (a = juddbankert))
   Explanation: The use of a = juddbankert is invalid. We replace it with a predicate indicating that Judd Bankert is the only athlete from Guam who has ever competed in the Winter Olympics.
   Corrected:
   BeFrom(bankert, guam) ∧ ParticipatedIn(bankert, winterolympics)

Conclusion:

Original:
ParticipatedInSummerOlympics(guam)
Explanation: There is no need to change.

Final Corrected Formulas:

Premises:
1. ParticipatedInWinterOlympics(guam)
2. Year(y1988) → BeHeld(winterolympics, calgary)
3. BeHeld(winterolympics, calgary) → SendAthletes(guam)
4. SendAthletes(guam) → ParticipatedIn(guam, winterolympics)
5. BeFrom(bankert, guam) ∧ ParticipatedIn(bankert, winterolympics)

Conclusion:
ParticipatedInSummerOlympics(guam)
EXAMPLE JSON OUTPUT:
{
  "premises": [
    "ParticipatedInWinterOlympics(guam)",
    "Year(y1988) → BeHeld(winterolympics, calgary)",
    "BeHeld(winterolympics, calgary) → SendAthletes(guam)",
    "SendAthletes(guam) → ParticipatedIn(guam, winterolympics)",
    "BeFrom(bankert, guam) ∧ ParticipatedIn(bankert, winterolympics)"
  ],
  "conclusion": "ParticipatedInSummerOlympics(guam)"
}
"""

    def generate_prompt(self, prompt: str,examples:list=None)->str:
        if examples:
            example = "\n-----".join([f"Input:\n{item['Input']}\nOutput:\n{item['Output']}" for item in examples])
        else:
            example = self.example
        prompt = f"""Your task is to fix grammatical errors in the premises and conclusions of a problem according to the first-order logical grammar rules I have provided.
{self.rule_msg}
{example}
Input:
{prompt}
Now follow the grammar to fix the logic formulas.
Output:"""
        return prompt


    def chat(self, prompt: str) -> tuple:
        examples = retrieve(vectorstore, prompt, k=self.num) if self.num > 0 else ""
        self.prompt = self.generate_prompt(prompt,examples)
        return super().chat(self.prompt)

if __name__ == "__main__":
    pass