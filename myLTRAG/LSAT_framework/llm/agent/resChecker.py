from llm.AgentBase import AgentBase,cf
from langchain_openai import ChatOpenAI
class ResChecker(AgentBase):
    def chat(self, prompt: str,label: str = None) -> tuple:
        error_help = ""
        if label == "Error":
            error_help = self.error_help
        prompt = f"""You are a logic assistant to help a user evaluate and modify a set of premises and a conclusion in first-order logic (FOL).
The premises and conclusion are in first order logic(fol).
The task is to translate each of the premises and conclusions into FOL expressions, so that the expressions can be evaluated by a theorem solver to determine whether the conclusion follows from the premises.
The possible labels are:
True: The conclusion can be derived from the premises.
False: The negation of the conclusion can be derived from the premises.
Uncertain: Neither the conclusion nor its negation can be derived from the premises.
{error_help}
{prompt}
First, you need to evaluate the conclusion as a label ('True', 'False', or 'Uncertain') given the premises.
Then, compare this label with the label of the process of program reasoning.

If the labels are the same and the formulas are right, reply that the formulas are no problem.

Otherwise the formula group has missing or redundant information.
You can add a new formula to fill in the missing facts, or modify the wrong formula, such as deleting certain predicates in the formula that should not have appeared or adding missing predicates.
In general, if the label given by the solver is Uncertain and does not match yours, it may be necessary to add some facts so that the logic program can continue to execute and get the correct result.
In addition, not getting the correct label may also be due to the fact that'either or 'does not correctly distinguish between disjunction[expr1 | expr2] and exclusive disjunction[(expr1 & -expr2) | (-expr1 & expr2)].Things that can't happen at the same time are generally used as XOR.
Then, give all the final formulas and follow the NLTK rules into this format:
```python
    premises = []
    conclusion = ""
```
NLTK rules:
logical conjunction of expr1 and expr2: expr1 & expr2
logical disjunction of expr1 and expr2: expr1 | expr2
logic exclusive disjunction of expr1 and expr2:(expr1 & -expr2) | (-expr1 & expr2)
'either or ' can use disjunction[expr1 | expr2] or exclusive disjunction[(expr1 & -expr2) | (-expr1 & expr2)].
Things that can't happen at the same time are generally used as XOR.
logical negation of expr1: -expr1
expr1 implies expr2: expr1 -> expr2
expr1 if and only if expr2: expr1 <-> expr2
logical universal quantification: all x. expr
logical existential quantification: exists x. expr
multiple quantifiers: all x. all y. expr, exists x. all y. expr, etc. `all x,y ` is not allowed, use `all x. all y.`
Equality between terms: x = y, -(x = y) for inequality.
```"""
        return super().chat(prompt)
    def __init__(self,tempature=0.2):
        super().__init__()
        self.temperature = tempature
        self.llm = ChatOpenAI(
            model=cf.get("API", "CHECKER_MODEL"),
            temperature=tempature,
            api_key = cf.get("API", "CHECKER_KEY"),
            base_url= cf.get("API", "CHECKER_URL"),
        )
        # Grammar rules, may be used in subsequent tasks
        self.rule_msg = """To describe First-Order Logic (FOL) formulas using NLTK's symbols, follow these guidelines:
logical conjunction of expr1 and expr2: expr1 & expr2
logical disjunction of expr1 and expr2: expr1 | expr2
logic exclusive disjunction of expr1 and expr2:(expr1 & -expr2) | (-expr1 & expr2)
logical negation of expr1: -expr1
expr1 implies expr2: expr1 -> expr2
expr1 if and only if expr2: expr1 <-> expr2
logical universal quantification: all x. expr
logical existential quantification: exists x. expr
multiple quantifiers: all x. all y. expr, exists x. all y. expr, etc. `all x,y ` is not allowed, use `all x. all y.`
Equality between terms: x = y, -(x = y) for inequality
"""
         # errorhelp
        self.error_help = """If the first-order logic formula cannot be resolved by the solver, only the following label can be obtained:Error"""

        self.json_msg = """
The user will provide an explanation of whether to modify the existing first-order logic formula, and the modified premise formula, conclusion formula.
You need to get all the premise formulas and a final conclusion formula.
parse the "is_modify", "premise", "conclusion" and output it in JSON format.
If is_modify is false, premise and conclusion are empty.
"""+self.rule_msg+"""
EXAMPLE INPUT:
Reasoning in Natural Language:
Premises:

Robert Lewandowski is a striker.

Strikers are soccer players.

Robert Lewandowski left Bayern Munchen.

If a player leaves a team, they no longer play for that team.

Conclusion:

Robert Lewandowski is a star.

Analysis:
From the premises, we know that Robert Lewandowski is a striker, and strikers are soccer players. Therefore, Robert Lewandowski is a soccer player.

We also know that Robert Lewandowski left Bayern Munchen, which implies that he no longer plays for Bayern Munchen.

However, the conclusion that Robert Lewandowski is a star is not directly supported by the given premises. The premises only tell us about his role as a striker and his departure from Bayern Munchen, but they do not provide any information about him being a star.

Label:
Unknown (since the conclusion cannot be derived from the premises)

Comparison with Program Reasoning:
The program reasoning also results in Unknown, which matches our natural language reasoning. Therefore, there is no problem with the formulas.

Final Formulas:
Striker(robertLewandowski)
all x. (Striker(x) -> SoccerPlayer(x))
LeftTeam(robertLewandowski, bayernMunchen)
all x all y. (LeftTeam(x, y) -> -PlayFor(x, y))
Conclusion:
The formula is no problem.
EXAMPLE JSON OUTPUT:
{
  "is_modify": false,
  "premises": [],
  "conclusion": ""
}
EXAMPLE INPUT:
### Reasoning in Natural Language:

1. Premise 1: Books contain tons of knowledge.
2. Premise 2: When a person reads a book, that person gains knowledge.
3. Premise 3: If a person gains knowledge, they become smarter.
4. Premise 4: Harry read the book “Walden” by Henry Thoreau.

Conclusion: Harry is smarter than before.

### Step-by-Step Reasoning:

1. Premise 4 tells us that Harry read the book "Walden."
2. According to Premise 2, since Harry is a person and he read a book (specifically "Walden"), he gained knowledge.
3. Premise 3 states that if a person gains knowledge, they become smarter.
4. Therefore, since Harry gained knowledge by reading "Walden," he became smarter.

Label: True

### Comparison with Program Reasoning:

The program reasoning output is "Unknown," which indicates that the program could not derive the conclusion from the given premises. This suggests that there might be an issue with the formulas provided to the program.

### Analysis of the Formulas:

1. Premise 1: `all x. (Book(x) -> Contain(x, tonsOfKnowledge))`
   - This premise is correctly formulated.

2. Premise 2: `all x. all y. ((Person(x) & Book(y) & Read(x, y)) -> GainKnowledge(x))`
   - This premise is correctly formulated.

3. Premise 3: `all x. (GainKnowledge(x) -> BecomeSmarter(x))`
   - This premise is correctly formulated.

4. Premise 4: `Read(harry, walden)`
   - This premise is correctly formulated.

5. Conclusion: `SmarterThanBefore(harry)`
   - This conclusion is correctly formulated.

### Identifying the Issue:

The issue lies in the fact that the program does not have enough information to link Harry to the predicate `Person(x)`. The program knows that Harry read a book, but it does not know that Harry is a person. This missing information prevents the program from making the necessary logical connections.

### Solution:

To fix this, we need to add a new premise that explicitly states that Harry is a person.

### Final Formulas:

1. `all x. (Book(x) -> Contain(x, tonsOfKnowledge))`
2. `all x. all y. ((Person(x) & Book(y) & Read(x, y)) -> GainKnowledge(x))`
3. `all x. (GainKnowledge(x) -> BecomeSmarter(x))`
4. `Read(harry, walden)`
5. `Person(harry)` (New premise)

Conclusion: `SmarterThanBefore(harry)`

### Final Response:

The formula is now complete and should allow the program to correctly derive the conclusion that Harry is smarter than before.

EXAMPLE JSON OUTPUT:
{
  "is_modify": true,
  "premises": [
    "all x. (Book(x) -> Contain(x, tonsOfKnowledge))",
    "all x. all y. ((Person(x) & Book(y) & Read(x, y)) -> GainKnowledge(x))",
    "all x. (GainKnowledge(x) -> BecomeSmarter(x))",
    "Read(harry, walden)",
    "Person(harry)"
  ],
  "conclusion": "SmarterThanBefore(harry)"
}
"""
