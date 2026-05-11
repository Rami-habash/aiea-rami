from llm.AgentBase import AgentBase
from utils.knowledge import retrieve, translation_store
from llm.base import DATATYPE
class Symbol(AgentBase):
    def __init__(self,tempature=0.6,num=0, static_num=0):
        super().__init__()
        self.temperature = tempature
        self.num = int(num)
        self.example = ""
        self.static_num = static_num
        if self.num == 0:
            for i in range(0, static_num):
                self.example += f"{static_examples[i]}\n---\n"

        # syntax rule，possibleinsubsequenttaskinuse
        self.rule_msg = """
### Format of the Logical Program for SAT Problems:

# Declarations
Here, you need to declare some variables and functions.
- **EnumSort**: Used to define an enumeration type. The format for calling `EnumSort` is `type_name = EnumSort([value_list])`.
   - Example: `computers = EnumSort([P, Q, R, S, T, U])`
- **IntSort**: Used to define integer variables. The format is: `type_name = IntSort([value_list])`. Note that the `value_list` here cannot directly use numbers, such as `ranks = IntSort([1, 2, 3, 4, 5, 6, 7, 8])`(prohibited usage).
   - Example: `ranks = IntSort([r1, r2, r3, r4, r5, r6, r7, r8])`, then constraints can be added to indicate the size relationships of these variables (such as r1 < r2, or r1 == 1, r2 == 2, etc.).
- **Function**: Defines a function mapping from one set to another. The format is `function_name = Function([input_types] -> [output_type])`.
   - Example: `assigned = Function([assistants] -> [courses])`, `transmitted = Function([computers, computers] -> [bool])`
- To prevent parsing errors, please do not use single quotes, double quotes, or # signs to enclose a quantity in this section.
   - For example, the statement `computers = EnumSort([P, Q, R, S, T, U]) # Define a computers variable` is incorrect. There should be no comments in this part.

# Constraints
Here, you need to translate background information into constraint statements. The format is: `constraint_statement ::: corresponding original sentence`
- **ForAll**: This is a universal quantifier, indicating that a certain condition should be satisfied for all members. The format is `ForAll([variables], condition)`. The condition may involve complex logical expressions, including comparisons, logical AND (And), OR (Or), etc.
- **Exists**: This is an existential quantifier, indicating that at least one member satisfies a certain condition. The format is `Exists([variables], condition)`.
- **And**: Used to connect multiple conditions, requiring all conditions to be true simultaneously. The format is `And(condition1, condition2, ...)`.
- **Or**: At least one condition is true. The format is `Or(condition1, condition2, ...)`.
- **Not**: Logical NOT operation, used to negate a condition. The format is `Not(condition)`.
- **Count**: Counts the number of members that satisfy a specific condition. The format is `Count([variables], condition) == number`, used to specify a specific quantity.
- **Other simple statements**: Such as `assigned(Vogel) != assigned(Yi)`.
Each constraint statement should be followed by a ":::" comment, indicating which sentence the constraint statement is translated from.

# Options
Here, you need to translate each option into an SAT statement and wrap the translated statement with one of the four types of labels: "is_valid", "is_unsat", "is_sat", "is_accurate_list".
- **is_valid**: If the question is a conditional question, i.e., asking "Which of the following options is correct under certain conditions," use this label to wrap each option, for example, `is_valid(transmitted(S, T)) ::: (A)`.
- **is_unsat**: If the question asks which option is incorrect, use this label to wrap each option, for example, `is_unsat(Exists([s:songs], performed(s) == flute - 1)) ::: (C)`.
- **is_sat**: If the question asks which option is correct, use this label to wrap each option, for example, `is_sat(assigned(Juan) == 4) ::: (D)`.
- **is_accurate_list**: If the question asks which combination is correct, use this label to wrap each option, for example, `is_accurate_list([Exists([c:children], assigned(Juan) == assigned(c)), Exists([c:children], assigned(Paul) == assigned(c))]) ::: (B)`.
Each SAT statement for an option should be marked with its label, such as `::: (A)`, to identify different verification options, making it easier to distinguish the verification results of each option in the results.

Note:
1. A formula is written on a single line, without line breaks.
2. In the Constraints and Options sections, the following symbols are prohibited: ['->', '?', '|', '&']. If you need to use '|' or '&', use 'or' and 'and' respectively instead.
"""
        self.chat_msg = """"""
        self.json_msg = """
Users will provide some thought processes for converting natural language processing into SAT logic programs. You need to obtain all translated declarations, constraints, and option formulas. Please parse it as 'raw_logic_program'and output it in JSON format.
If you find some incomplete or incorrect formulas, you should fix them.
"""+self.rule_msg+"""
EXAMPLE INPUT:
# Declarations
children = EnumSort([Fred, Juan, Marc, Paul, Nita, Rachel, Trisha])
lockers = EnumSort([1, 2, 3, 4, 5])
assigned = Function([children] -> [lockers])
shared = Function([lockers] -> [bool])

# Constraints
ForAll([c:children], Exists([l:lockers], assigned(c) == l)) ::: Each child must be assigned to exactly one locker
ForAll([l:lockers], Or(Count([c:children], assigned(c) == l) == 1, And(Count([c:children], assigned(c) == l) == 2, shared(l)))) ::: Each locker must be assigned to either one or two children, and each shared locker must be assigned to one girl and one boy
ForAll([l:lockers], Implies(shared(l), Exists([b:boys], Exists([g:girls], And(assigned(b) == l, assigned(g) == l))))) ::: Each shared locker must be assigned to one girl and one boy
Exists([l:lockers], And(assigned(Juan) == l, shared(l))) ::: Juan must share a locker
ForAll([l:lockers], Not(And(assigned(Rachel) == l, shared(l)))) ::: Rachel cannot share a locker
ForAll([l1:lockers], ForAll([l2:lockers], Implies(And(assigned(Nita) == l1, assigned(Trisha) == l2, Abs(l1 - l2) == 1), False))) ::: Nita's locker cannot be adjacent to Trisha's locker
assigned(Fred) == 3 ::: Fred must be assigned to locker 3
ForAll([l:lockers], Implies(l <= 3, Exists([g:girls], assigned(g) == l))) ::: The first three lockers are assigned to girls

# Options
is_valid(assigned(Juan) == 1) ::: (A)
is_valid(assigned(Nita) == 3) ::: (B)
is_valid(assigned(Trisha) == 1) ::: (C)
is_valid(assigned(Juan) == assigned(Trisha)) ::: (D)
is_valid(assigned(Paul) == assigned(Trisha)) ::: (E)

EXAMPLE JSON OUTPUT:
{
   "raw_logic_programs: [
      "# Declarations\\nchildren = EnumSort([Fred, Juan, Marc, Paul, Nita, Rachel, Trisha])\\nlockers = EnumSort([1, 2, 3, 4, 5])\\nassigned = Function([children] -> [lockers])\\nshared = Function([lockers] -> [bool])\\n\\n# Constraints\\nForAll([c:children], Exists([l:lockers], assigned(c) == l)) ::: Each child must be assigned to exactly one locker\\nForAll([l:lockers], Or(Count([c:children], assigned(c) == l) == 1, And(Count([c:children], assigned(c) == l) == 2, shared(l)))) ::: Each locker must be assigned to either one or two children, and each shared locker must be assigned to one girl and one boy\\nForAll([l:lockers], Implies(shared(l), Exists([b:boys], Exists([g:girls], And(assigned(b) == l, assigned(g) == l))))) ::: Each shared locker must be assigned to one girl and one boy\\nExists([l:lockers], And(assigned(Juan) == l, shared(l))) ::: Juan must share a locker\\nForAll([l:lockers], Not(And(assigned(Rachel) == l, shared(l)))) ::: Rachel cannot share a locker\\nForAll([l1:lockers], ForAll([l2:lockers], Implies(And(assigned(Nita) == l1, assigned(Trisha) == l2, Abs(l1 - l2) == 1), False))) ::: Nita's locker cannot be adjacent to Trisha's locker\\nassigned(Fred) == 3 ::: Fred must be assigned to locker 3\\nForAll([l:lockers], Implies(l <= 3, Exists([g:girls], assigned(g) == l))) ::: The first three lockers are assigned to girls\\n\\n# Options\\nis_valid(assigned(Juan) == 1) ::: (A)\\nis_valid(assigned(Nita) == 3) ::: (B)\\nis_valid(assigned(Trisha) == 1) ::: (C)\\nis_valid(assigned(Juan) == assigned(Trisha)) ::: (D)\\nis_valid(assigned(Paul) == assigned(Trisha)) ::: (E)"
   ]
}
"""
    async def chat(self, prompt: str) -> str:
        examples = retrieve(translation_store, prompt, k=self.num) if self.num > 0 else ""
        if examples:
            example = "\n\n".join([f"Input:\n```plaintext\n{item['Input']}\n```\nOutput:\n```plaintext\n{item['Output']}\n```\n---" for item in examples])
            print(f"- Generate program examples:{self.num}\n- from {DATATYPE}\n- An example:\n```plaintext\n{examples[0]['Input']}\n```\nOutput:\n```plaintext\n{examples[0]['Output']}\n```\n\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        else:
            example = self.example
            print(f"Use {self.static_num} static examples, partial cases\n------------------------\n{self.example[:500]}\n\n\n")
        prompt = f"""
# Task Description: Given a problem description and a question. The task is to formulate the problem as a logic program, consisting three parts: Declarations, Constraints, and Options.
Declarations: Declare the variables and functions.
Constraints: Write the constraints in the problem description as logic formulas.
Options: Write the options in the question as logic formulas.

{self.rule_msg}
The formulas should follow the guidelines for describing SAT logic program. Don't use latex or any other symbols.

# There are some examples for leanring.
{example}

# The following is the new question that need to be addressed:
{prompt}
Output:
"""
        # print(f"# this timeGenerate programprompt\n```\n{prompt}\n```\n")
        return await super().chat(prompt)


static_examples = [
    """Input:
```plaintext
Context:
An economics department is assigning six teaching assistants—Ramos, Smith, Taj, Vogel, Yi, and Zane—to three courses—Labor, Markets, and Pricing. Each assistant will be assigned to exactly one course, and each course will have at least one assistant assigned to it. The assignment of assistants to courses is subject to the following conditions: Markets must have exactly two assistants assigned to it. Smith and Taj must be assigned to the same course as each other. Vogel and Yi cannot be assigned to the same course as each other. Yi and Zane must both be assigned to Pricing if either one of them is.

Question:
If no other assistant is assigned to the same course as Ramos, which one of the following must be true?

Options:
A) Taj is assigned to Labor.
B) Vogel is assigned to Labor.
C) Yi is assigned to Markets.
D) Zane is assigned to Markets.
E) Smith is assigned to Pricing
```
Output:
```plaintext
# Declarations
assistants = EnumSort([Ramos, Smith, Taj, Vogel, Yi, Zane])
courses = EnumSort([Labor, Markets, Pricing])
assigned = Function([assistants] -> [courses])

# Constraints
ForAll([c:courses], Exists([a:assistants], assigned(a) == c)) ::: each course will have at least one assistant assigned to it
Count([a:assistants], assigned(a) == Markets) == 2 ::: Markets must have exactly two assistants assigned to it
assigned(Smith) == assigned(Taj) ::: Smith and Taj must be assigned to the same course as each other
assigned(Vogel) != assigned(Yi) ::: Vogel and Yi cannot be assigned to the same course as each other
Implies(Or(assigned(Yi) == Pricing, assigned(Zane) == Pricing), And(assigned(Yi) == Pricing, assigned(Zane) == Pricing)) ::: Yi and Zane must both be assigned to Pricing if either one of them is
ForAll([a:assistants], Implies(a != Ramos, assigned(a) != assigned(Ramos))) ::: if no other assistant is assigned to the same course as Ramos

# Options
is_valid(assigned(Taj) == Labor) ::: (A)
is_valid(assigned(Vogel) == Labor) ::: (B)
is_valid(assigned(Yi) == Markets) ::: (C)
is_valid(assigned(Zane) == Markets) ::: (D)
is_valid(assigned(Smith) == Pricing) ::: (E)
```
""",
"""Input:
```plaintext
Context:
There are exactly six computers—P, Q, R, S, T, and U—on a small network. Exactly one of those computers was infected by a virus from outside the network, and that virus was then transmitted between computers on the network. Each computer received the virus exactly once. The following pieces of information concerning the spread of the virus have been established: No computer transmitted the virus to more than two other computers on the network. S transmitted the virus to exactly one other computer on the network. The computer that transmitted the virus to R also transmitted it to S. Either R or T transmitted the virus to Q. Either T or U transmitted the virus to P.

Question:
If P is the only computer that transmitted the virus to two other computers on the network, which one of the following must be true?

Options:
A) S transmitted the virus to T.
B) T transmitted the virus to P.
C) Q did not transmit the virus to any other computer on the network.
D) R did not transmit the virus to any other computer on the network.
E) U did not transmit the virus to any other computer on the network.
```
Output:
```plaintext
# Declarations
computers = EnumSort([P, Q, R, S, T, U])
transmitted = Function([computers, computers] -> [bool])

# Constraints
ForAll([c:computers], Exists([c1:computers], And(c1 != c, transmitted(c1, c)))) ::: Each computer received the virus exactly once
ForAll([c:computers], Count([c1:computers], transmitted(c, c1)) <= 2) ::: No computer transmitted the virus to more than two other computers on the network
Count([c:computers], transmitted(S, c)) == 1 ::: S transmitted the virus to exactly one other computer on the network
Exists([c:computers], And(transmitted(c, R), transmitted(c, S))) ::: The computer that transmitted the virus to R also transmitted it to S
Or(transmitted(R, Q), transmitted(T, Q)) ::: Either R or T transmitted the virus to Q
Or(transmitted(T, P), transmitted(U, P)) ::: Either T or U transmitted the virus to P
Count([c:computers], transmitted(P, c)) == 2 ::: P is the only computer that transmitted the virus to two other computers on the network

# Options
is_valid(transmitted(S, T)) ::: (A)
is_valid(transmitted(T, P)) ::: (B)
is_valid(ForAll([c:computers], Not(transmitted(Q, c)))) ::: (C)
is_valid(ForAll([c:computers], Not(transmitted(R, c)))) ::: (D)
is_valid(ForAll([c:computers], Not(transmitted(U, c)))) ::: (E)
```
""",
"""Input:
```plaintext
# Context:
For a behavioral study, a researcher will select exactly six individual animals from among three monkeys—F, G, and H—three pandas—K, L, and N—and three raccoons—T, V, and Z. The selection of animals for the study must meet the following conditions: F and H are not both selected. N and T are not both selected. If H is selected, K is also selected. If K is selected, N is also selected.

# Question:
If all three of the raccoons are selected, which one of the following must be true?

# Options:
A) K is selected.
B) L is selected.
C) Exactly one monkey is selected.
D) Exactly two pandas are selected.
E) All three of the monkeys are selected.
```
Output:
```plaintext
# Declarations
animals = EnumSort([F, G, H, K, L, N, T, V, Z])
selected = Function([animals] -> [bool])
# Constraints
Count([a:animals], selected(a)) == 6 ::: exactly six individual animals are selected
Not(And(selected(F), selected(H))) ::: F and H are not both selected
Not(And(selected(N), selected(T))) ::: N and T are not both selected
Implies(selected(H), selected(K)) ::: If H is selected, K is also selected
Implies(selected(K), selected(N)) ::: If K is selected, N is also selected
ForAll([a:animals], Implies(Or(a == T, a == V, a == Z), selected(a))) ::: all three of the raccoons are selected
# Options
is_valid(selected(K)) ::: (A)
is_valid(selected(L)) ::: (B)
is_valid(Count([a:animals], And(a == F, selected(a))) + Count([a:animals], And(a == G, selected(a))) + Count([a:animals], And(a == H, selected(a))) == 1) ::: (C)
is_valid(Count([a:animals], And(a == K, selected(a))) + Count([a:animals], And(a == L, selected(a))) + Count([a:animals], And(a == N, selected(a))) == 2) ::: (D)
is_valid(ForAll([a:animals], Implies(Or(a == F, a == G, a == H), selected(a)))) ::: (E)
```
""",
"""Input:
```plaintext
# Context:
Of the five Pohl children—Sara, Theo, Uma, Will, and Zoe—three are left-handed and two are right-handed. Each of the five children was born in a different one of seven calendar years, 1990 through 1996. The following conditions apply: No two left-handed children were born in consecutive years. No two right-handed children were born in consecutive years. Sara, who is left-handed, was born before Uma. Zoe was born before both Theo and Will. A left-handed child was born in 1991. Uma, who is right-handed, was born in 1993.

# Question:
Which one of the following must be false?

# Options:
A) None of the children was born in 1990, nor was a child born in 1992.
B) None of the children was born in 1992, nor was a child born in 1995.
C) None of the children was born in 1994, nor was a child born in 1996.
D) One of the children was born in 1990, and another in 1993.
E) One of the children was born in 1993, and another in 1995.
```
Output:
```plaintext
# Declarations
children = EnumSort([Sara, Theo, Uma, Will, Zoe])
hand_types = EnumSort([left_handed, right_handed])
years = EnumSort([1990, 1991, 1992, 1993, 1994, 1995, 1996])
handedness = Function([children] -> [hand_types])
birth_year = Function([children] -> [years])
# Constraints
Count([c:children], handedness(c) == left_handed) == 3 ::: three are left-handed
Count([c:children], handedness(c) == right_handed) == 2 ::: two are right-handed
ForAll([c1:children, c2:children], Implies(And(handedness(c1) == left_handed, handedness(c2) == left_handed, c1 != c2), Abs(birth_year(c1) - birth_year(c2)) != 1)) ::: No two left-handed children were born in consecutive years
ForAll([c1:children, c2:children], Implies(And(handedness(c1) == right_handed, handedness(c2) == right_handed, c1 != c2), Abs(birth_year(c1) - birth_year(c2)) != 1)) ::: No two right-handed children were born in consecutive years
birth_year(Sara) < birth_year(Uma) ::: Sara, who is left-handed, was born before Uma
birth_year(Zoe) < birth_year(Theo) ::: Zoe was born before both Theo and Will
birth_year(Zoe) < birth_year(Will) ::: Zoe was born before both Theo and Will
Exists([c:children], And(handedness(c) == left_handed, birth_year(c) == 1991)) ::: A left-handed child was born in 1991
birth_year(Uma) == 1993 ::: Uma, who is right-handed, was born in 1993
handedness(Uma) == right_handed ::: Uma, who is right-handed, was born in 1993
# Options
is_unsat(And(ForAll([c:children], birth_year(c) != 1990), ForAll([c:children], birth_year(c) != 1992))) ::: (A)
is_unsat(And(ForAll([c:children], birth_year(c) != 1992), ForAll([c:children], birth_year(c) != 1995))) ::: (B)
is_unsat(And(ForAll([c:children], birth_year(c) != 1994), ForAll([c:children], birth_year(c) != 1996))) ::: (C)
is_unsat(And(Exists([c:children], birth_year(c) == 1990), Exists([c:children], birth_year(c) == 1993))) ::: (D)
is_unsat(And(Exists([c:children], birth_year(c) == 1993), Exists([c:children], birth_year(c) == 1995))) ::: (E)
```
""",
"""Input:
```plaintext
# Context:
For a behavioral study, a researcher will select exactly six individual animals from among three monkeys—F, G, and H—three pandas—K, L, and N—and three raccoons—T, V, and Z. The selection of animals for the study must meet the following conditions: F and H are not both selected. N and T are not both selected. If H is selected, K is also selected. If K is selected, N is also selected.

# Question:
If all three of the raccoons are selected, which one of the following must be true?

# Options:
A) K is selected.
B) L is selected.
C) Exactly one monkey is selected.
D) Exactly two pandas are selected.
E) All three of the monkeys are selected.
```
Output:
```plaintext
# Declarations
animals = EnumSort([F, G, H, K, L, N, T, V, Z])
selected = Function([animals] -> [bool])
# Constraints
Count([a:animals], selected(a)) == 6 ::: exactly six individual animals are selected
Not(And(selected(F), selected(H))) ::: F and H are not both selected
Not(And(selected(N), selected(T))) ::: N and T are not both selected
Implies(selected(H), selected(K)) ::: If H is selected, K is also selected
Implies(selected(K), selected(N)) ::: If K is selected, N is also selected
ForAll([a:animals], Implies(Or(a == T, a == V, a == Z), selected(a))) ::: all three of the raccoons are selected
# Options
is_valid(selected(K)) ::: (A)
is_valid(selected(L)) ::: (B)
is_valid(Count([a:animals], And(a == F, selected(a))) + Count([a:animals], And(a == G, selected(a))) + Count([a:animals], And(a == H, selected(a))) == 1) ::: (C)
is_valid(Count([a:animals], And(a == K, selected(a))) + Count([a:animals], And(a == L, selected(a))) + Count([a:animals], And(a == N, selected(a))) == 2) ::: (D)
is_valid(ForAll([a:animals], Implies(Or(a == F, a == G, a == H), selected(a)))) ::: (E)
```
"""
]
