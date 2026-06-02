from llm.AgentBase import AgentBase
from config.Settings import config

class cot(AgentBase):
    def __init__(self, datatype="", agent_config: dict = {}):
        model_type = "cot"
        self.datatype = datatype
        super().__init__(model_type, datatype)
        if not agent_config:
            self.num = config["agent"][model_type]["num"]
            self.kb_id = config["agent"][model_type]["kb_id"]
            self.temperature = config["agent"][model_type]["temperature"]
        else:
            self.num = agent_config.get(
                "num", config["agent"][model_type]["num"])
            self.kb_id = agent_config.get(
                "kb_id", config["agent"][model_type]["kb_id"])
            self.temperature = agent_config.get(
                "temperature", config["agent"][model_type]["temperature"])
        self.reasoning_effort = (agent_config or {}).get("reasoning_effort", self.reasoning_effort)
        self.chat_msg = ""
        self.json_msg = ""
        if datatype == "folio":
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
        elif datatype == "AR-LSAT":

            self.json_msg = """
Users will choose what they think is correct from a bunch of options, and you need to find the option they finally choose.
EXAMPLE INPUT:
Let's analyze the conditions and options step by step:

Condition 1: "Tuesday is the only day on which George can give a report."
This means that George must give his report on Tuesday, or not at all.

Condition 2: "Neither Olivia nor Robert can give an afternoon report."
Olivia and Robert cannot give reports in the afternoon.

Condition 3: "If Nina gives a report, then on the next day Helen and Irving must both give reports, unless Nina's report is given on Wednesday."
If Nina reports on Monday or Tuesday, Helen and Irving must both give reports the next day, unless Nina reports on Wednesday.

Now, let's evaluate the options:

Option A:
Monday: morning: Helen; afternoon: Robert
Tuesday: morning: Olivia; afternoon: Irving
Wednesday: morning: Lenore; afternoon: Kyle
In this option, Robert is scheduled for the afternoon, which violates Condition 2.

Option B:
Monday: morning: Irving; afternoon: Olivia
Tuesday: morning: Helen; afternoon: Kyle
Wednesday: morning: Nina; afternoon: Lenore
In this option, Olivia is scheduled for the afternoon, which violates Condition 2.

Option C:
Monday: morning: Lenore; afternoon: Helen
Tuesday: morning: George; afternoon: Kyle
Wednesday: morning: Robert; afternoon: Irving
In this option:

George is scheduled for Tuesday (satisfies Condition 1);
Robert is scheduled for Wednesday morning (satisfies Condition 2);
Nina does not give a report, so Condition 3 does not apply.
Thus, Option C satisfies all conditions.
Option D:
Monday: morning: Nina; afternoon: Helen
Tuesday: morning: Robert; afternoon: Irving
Wednesday: morning: Olivia; afternoon: Lenore
In this option, Nina reports on Monday, which means Helen and Irving must report on Tuesday. However, Robert is scheduled on Tuesday morning instead of Helen, which violates Condition 3.

Option E:
Monday: morning: Olivia; afternoon: Nina
Tuesday: morning: Irving; afternoon: Helen
Wednesday: morning: Kyle; afternoon: George
In this option, George is scheduled on Wednesday, but he can only report on Tuesday (violating Condition 1).

Therefore, the correct option that satisfies all the conditions is Option C.

EXAMPLE JSON OUTPUT:
{
    "answer": "C"
}
    """

    def generate_prompt(self, prompt: str) -> str:
        if self.datatype == "folio":
            prompt = f"""The following is a first-order logic (FOL) problem.
{prompt}
The task is to evaluate the conclusion as 'True', 'False', or 'Unknown' given the premises.
The definition of the three options are:
True: A statement is "True" if it necessarily follows from the given premises using logical rules.
False: A statement is "False" if it is contradicted by the premises or its negation is logically inferred from them.
Unknown: A statement is "Unknown" if there is insufficient information in the premises to determine its truth value conclusively."""
        elif self.datatype == "AR-LSAT":
            prompt = f"""Task Description: Given a problem statement as contexts , the task is to answer a logical reasoning question.
{prompt}\nChoose the right option"""

        return prompt

    def chat(self, prompt: str) -> tuple:
        self.prompt = self.generate_prompt(prompt)
        return super().chat(self.prompt)


if __name__ == "__main__":
    pass
