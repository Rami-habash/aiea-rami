from llm.AgentBase import AgentBase
from config.Settings import config
class standard(AgentBase):
    def __init__(self,datatype="",agent_config:dict={}):
        model_type = "standard"
        super().__init__(model_type,datatype)
        if not agent_config:
            self.num = config["agent"][model_type]["num"]
            self.kb_id = config["agent"][model_type]["kb_id"]
            self.temperature = config["agent"][model_type]["temperature"]
        else:
            self.num = agent_config.get("num",config["agent"][model_type]["num"])
            self.kb_id = agent_config.get("kb_id",config["agent"][model_type]["kb_id"])
            self.temperature = agent_config.get("temperature",config["agent"][model_type]["temperature"])
        self.chat_msg = ""
        self.json_msg = """
The user will provide some process of thinking and reasoning, and the answer can only be one of True, False, Unknown. Please parse the "answer" and output it in JSON format.

EXAMPLE INPUT:
To determine the validity of the conclusion "Miroslav Venhoda loved music" based on the provided premises, we need to analyze the logical connections between the premises and the conclusion using first-order logic. Let's break down the premises and the conclusion step by step:

1. **Premise 1**: "Miroslav Venhoda was a Czech choral conductor who specialized in the performance of Renaissance and Baroque music."
   - This tells us that Miroslav Venhoda is a choral conductor.

2. **Premise 2**: "Any choral conductor is a musician."
   - From this, we can infer that Miroslav Venhoda is a musician because he is a choral conductor.

3. **Premise 3**: "Some musicians love music."
   - This statement tells us that there exists at least one musician who loves music. However, it does not specify whether Miroslav Venhoda is among those musicians who love music.

4. **Premise 4**: "Miroslav Venhoda published a book in 1946 called Method of Studying Gregorian Chant."
   - This information is about Miroslav Venhoda's publication but does not directly relate to whether he loved music.

**Conclusion**: "Miroslav Venhoda loved music."

Now, let's analyze the logical connections:
- From Premise 1 and Premise 2, we know that Miroslav Venhoda is a musician.
- Premise 3 tells us that some musicians love music, but it does not provide specific information about Miroslav Venhoda's feelings towards music.
- Premise 4 is irrelevant to the conclusion.

Given the information provided, we cannot definitively conclude that Miroslav Venhoda loved music based on the premises. Therefore, the answer is 'Unknown'.

EXAMPLE JSON OUTPUT:
{
    "answer": "Unknown"
}
"""

    def generate_prompt(self, prompt: str)->str:
        prompt = f"""The following is a first-order logic (FOL) problem.
The problem is to determine whether the conclusion follows from the premises.
Below are the one you need to solve:
Context:
{prompt}
The task is to evaluate the conclusion as 'True', 'False', or 'Unknown' given the premises.
The definition of the three options are:
True: A statement is "True" if it necessarily follows from the given premises using logical rules.
False: A statement is "False" if it is contradicted by the premises or its negation is logically inferred from them.
Unknown: A statement is "Unknown" if there is insufficient information in the premises to determine its truth value conclusively.
You need to emphasize which premises were used to obtain your results."""
        return prompt


    def chat(self, prompt: str) -> tuple:
        self.prompt = self.generate_prompt(prompt)
        return super().chat(self.prompt)

if __name__ == "__main__":
    pass