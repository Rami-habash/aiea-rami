from llm.AgentBase import AgentBase
from utils.knowledge import retrieve, fix_store
from llm.base import DATATYPE

if DATATYPE == "lsat":
   KB_IDs = {
      "symbolic expressions": "674003c4c04426f7337e4dae",
      "if() missing": "6740034ec04426f7337e4cb7",
      "not defined": "6740023dc04426f7337e4aef",
      "not supported": "674001e6c04426f7337e4a0c",
      "unsupported operand": "673ffce2c04426f7337e4475",
      "sort mismatch": "673ffc2fc04426f7337e4341",
      "choice question": "673f1a60c04426f7337e2ed7",
      "syntaxerror: invalid syntax": "67442452155ca7fd24b7e8b6",
   }
elif DATATYPE == "logiqa":
   KB_IDs = {
      "unsupported operand": "6756ee1a155ca7fd24bc54d7",
      "sort mismatch. `error in line: raise z3exception(msg)`": "6756e549155ca7fd24bc4a09",
      "not supported": "67565c79155ca7fd24bc2172",
      "choice question": "67565ac1155ca7fd24bc1d02",
      "invalid decimal literal": "67563a7f155ca7fd24bbe8a3",
      "not defined": "67563548155ca7fd24bbdb34",
      "syntaxerror: invalid syntax": "675634a3155ca7fd24bbd925",
      "symbolic expressions": "6756333a155ca7fd24bbd42b"
   }
# ERROR_NUM = 1

# Fix single sentence error
class ErrorFixer(AgentBase):
   # Get error examples
   async def get_error_example(self, prmpt, type):
      examples = retrieve(fix_store, prmpt, k=self.ERROR_NUM) if (self.ERROR_NUM > 0 and type in KB_IDs) else ""
      if examples:
         example_text = "\n\n".join([f"{item['Input']}\n{item['Output']}\n---" for item in examples])
         print(f"- **Use`{type}`libraryerrorexample**")
         example_text_print = f"\n```plaintext\n{examples[0]['Input']}\n```\nOutput:\n```plaintext\n{examples[0]['Output']}\n```\n"
         example_text_print = example_text_print.replace('```', '`\\``').replace('\n', '\\n')
         print(f"- An example:\n> {example_text_print}\n\n")
      else:
         example_text = self.error_examples
         print(f"\n-----------------------\nUsing static error examples, partial cases:\n{example_text[:500]}\n-----------------------\n")

      return example_text

   async def chat(self, prompt: str, error_types: list) -> str:
      # Reduce errors to currently existing types
      error_types = [item for item in error_types if item.lower() in KB_IDs]
      if not error_types:
         error_types = ["static"]

      examples_text = ""
      for i in range(len(error_types)):
         example_text = await self.get_error_example(prompt, error_types[i].lower())
         examples_text += f"## Case {i+1}\n{example_text}\n"
      
      prompt = f"""You are an expert in checking the syntax of SAT format logic program.
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

# Issues that need to be strictly checked
1. Matching parentheses strictly.
2. Please carefully check whether each formula conforms to the syntax of the SAT program.
3. Please check if it is divided into three parts: "Declaration", "Constraint", and "Options". The format of each line also needs to comply with the above requirements.
4. Error Symbol Issue: The following symbols are prohibited in constraint statements and option statements: ['->', '|', '&', '?']. For statements containing these symbols, you need to rewrite them equivalently.
5. Avoid using quotes in logical programs. For example, `works = EnumSort(['FrenchNovel1', 'FrenchNovel2'])` should be modified to `works = EnumSort([FrenchNovel1, FrenchNovel2])`.
6. No matter how long a statement is, it can only be placed on one line. Please strictly check this issue. An example of this type of problem is given in "Some error cases".
7. Finally, you must provide the complete modified logic program, including the three parts of "# Declarations", "# Constraints", and "# Options".
8. And/and are different. The two symbolic expressions A and B cannot be connected using `A and B` as a Boolean value; instead, they should be used in the form `And(A, B)`. The same applies to Or/or.
9. The entire logic program can only contain 3 `#` symbols (i.e., three from "# Declarations", "# Constraints", and "# Options").

# Sample Learning
{examples_text}
These examples do not fully demonstrate the fragments of the logical program, but your response must include them at the end.

## Examples of erroneous statements and their analysis
### Case 1
`ForAll([c:courses], Implies(offered(mathematics), Or(offered(literature), offered(sociology)) And Not(And(offered(literature), offered(sociology))))) ::: If mathematics is offered, then either literature or sociology (but not both) is offered.`
- Analysis: The statement between `Or` and `Not` is incorrect; it should be `And(Or, Not)`. That is, change it to `ForAll([c:courses], Implies(offered(mathematics), And(Or(offered(literature), offered(sociology)), Not(And(offered(literature), offered(sociology)))))) ::: If mathematics is offered, then either literature or sociology (but not both) is offered.`
### Case 2
`circuit_load(switches) == Count([s:switches], is_on(s) == on) ::: The circuit load of the panel is the total number of its switches that are on.`
- Analysis: `circuit_load` is a function, and `switches` is a variable of a certain type, so it cannot be used as a parameter for this function.
### Case 3
`times = EnumSort([1PM, 2PM, 3PM, 4PM, 5PM, 6PM])`
- Analysis: Variables should not start with a number; they can be changed to `PM1`, etc.
### Case 4
`assign = Function([apples] -> [1, 2, 3, 4, 5])`
- Analysis: The domain and range of the function should both be type names, not `[1, 2, 3, 4, 5]`.
### Case 5
`ForAll([p1, p2], Implies(And(p1 == mike, p2 == john))) ::: This is an example sentence.`
- Analysis: It is not specified what p1 and p2 are variables for, so they should be supplemented according to the specific situation. For example, `ForAll([p1:person, p2:person], Implies(And(p1 == mike, p2 == john))) ::: This is an example sentence.`
### Case 6
`ranks = IntSort([1, 2, 3])`
- Analysis: All quantities should conform to the identifier writing method, such as not starting with a number, here it should be handled as `ranks = IntSort([r1, r2, r3])` (depending on the specific situation).
### Case 7
`Implies(scheduled(Harry) == d, scheduled(Iris) == (d + 1)) ::: Iris is scheduled for the next day after Harry`
- The `d` in the sentence is undefined; it needs to be changed to `Exists([d:days], Implies(scheduled(Harry) == d, scheduled(Iris) == (d + 1))) ::: Iris is scheduled for the next day after Harry`. (Whether to use `Exists`, `ForAll`, or another quantifier depends on the specific situation).

# Please help me check And modify the following program:
{prompt}
The error message comes from the solver program, and its syntax format is not our original logic program. Therefore, the error message is only for your analysis reference, and you must maintain the SAT logic program format when making modifications.
Let's think step by step.
"""
      # print(f"# this timerepairprompt：\n{prompt}\n")
      return await super().chat(prompt)
   def __init__(self,error_num=1, tempature=0.1):
      super().__init__()
      self.ERROR_NUM = error_num
      self.temperature = tempature
      # syntax rule，possibleinsubsequenttaskinuse
      self.rule_msg = """### Format of the Logical Program for SAT Problems:

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
         # errorhelp
      self.error_examples = \
"""### Context:
Four apprenticesLouis, Madelyn, Nora, and Oliverare initially assigned to projects Q, R, S, and T, respectively. During the year in which they are apprentices, two reassignments of apprentices to projects will be made, each time according to a different one of the following plans, which can be used in any order: Plan 1. The apprentice assigned to project Q switches projects with the apprentice assigned to project S and the apprentice assigned to project R switches projects with the apprentice assigned to project T. Plan 2. The apprentice assigned to project S switches projects with the apprentice assigned to project T. Plan 3. Louis and Madelyn switch projects with each other.
### Question:
Which one of the following could be true after only one reassignment during the year?
### Options:
A) Louis is assigned to project T.
B) Nora is assigned to project R.
C) Oliver is assigned to project Q.
D) Louis and Nora each remain assigned to the same projects as before.
E) Nora and Oliver each remain assigned to the same projects as before.
### Logic program
```plaintext
# Declarations
apprentices = EnumSort([Louis, Madelyn, Nora, Oliver])
projects = EnumSort([Q, R, S, T])
assigned = Function([apprentices] -> [projects])

# Constraints
assigned(Louis) == Q ::: Louis is initially assigned to project Q
assigned(Madelyn) == R ::: Madelyn is initially assigned to project R
assigned(Nora) == S ::: Nora is initially assigned to project S
assigned(Oliver) == T ::: Oliver is initially assigned to project T
Or(
    And(assigned(Louis) == S, assigned(Nora) == Q, assigned(Madelyn) == T, assigned(Oliver) == R),
    And(assigned(Louis) == Q, assigned(Nora) == S, assigned(Madelyn) == R, assigned(Oliver) == T)
) ::: Plan 1: The apprentice assigned to project Q switches projects with the apprentice assigned to project S and the apprentice assigned to project R switches projects with the apprentice assigned to project T
Or(
    And(assigned(Louis) == Q, assigned(Madelyn) == R, assigned(Nora) == T, assigned(Oliver) == S),
    And(assigned(Louis) == Q, assigned(Madelyn) == R, assigned(Nora) == S, assigned(Oliver) == T)
) ::: Plan 2: The apprentice assigned to project S switches projects with the apprentice assigned to project T
Or(
    And(assigned(Louis) == R, assigned(Madelyn) == Q, assigned(Nora) == S, assigned(Oliver) == T),
    And(assigned(Louis) == Q, assigned(Madelyn) == R, assigned(Nora) == S, assigned(Oliver) == T)
) ::: Plan 3: Louis and Madelyn switch projects with each other

# Options
is_valid(assigned(Louis) == T) ::: (A)
is_valid(assigned(Nora) == R) ::: (B)
is_valid(assigned(Oliver) == Q) ::: (C)
is_valid(And(assigned(Louis) == Q, assigned(Nora) == S)) ::: (D)
is_valid(And(assigned(Nora) == S, assigned(Oliver) == T)) ::: (E)
```
### Error
1. The Constraints part seems to have the issue of formulas not being written on a single line.

2. `SyntaxError: invalid syntax`. There might be some syntax errors.
### Analysis
1. Some constraint statements are not written on a single line; minor adjustments can be made. The obtained constraint part is as follows:：
```plaintext
# Constraints
assigned(Louis) == Q ::: Louis is initially assigned to project Q
assigned(Madelyn) == R ::: Madelyn is initially assigned to project R
assigned(Nora) == S ::: Nora is initially assigned to project S
assigned(Oliver) == T ::: Oliver is initially assigned to project T
Or(And(assigned(Louis) == S, assigned(Nora) == Q, assigned(Madelyn) == T, assigned(Oliver) == R),And(assigned(Louis) == Q, assigned(Nora) == S, assigned(Madelyn) == R, assigned(Oliver) == T)) ::: Plan 1: The apprentice assigned to project Q switches projects with the apprentice assigned to project S and the apprentice assigned to project R switches projects with the apprentice assigned to project T
Or(And(assigned(Louis) == Q, assigned(Madelyn) == R, assigned(Nora) == T, assigned(Oliver) == S),And(assigned(Louis) == Q, assigned(Madelyn) == R, assigned(Nora) == S, assigned(Oliver) == T)) ::: Plan 2: The apprentice assigned to project S switches projects with the apprentice assigned to project T
Or(And(assigned(Louis) == R, assigned(Madelyn) == Q, assigned(Nora) == S, assigned(Oliver) == T),And(assigned(Louis) == Q, assigned(Madelyn) == R, assigned(Nora) == S, assigned(Oliver) == T)) ::: Plan 3: Louis and Madelyn switch projects with each other
```
---
"""



      self.json_msg = """
The user will provide instructions for modifying the existing SAT logic program, and you need to find the modified final program.
parse the "formula" and output it in JSON format.
"""+self.rule_msg+"""
EXAMPLE INPUT:
- Program: "# Declarations\nchildren = EnumSort([Fred, Juan, Marc, Paul, Nita, Rachel, Trisha])\nlockers = EnumSort[1, 2, 3, 4, 5]\nassigned = Function([children] -> [lockers])\nshared = Function([lockers] -> [bool])\n\n# Constraints\nForAll([c:children], Exists([l:lockers], assigned(c) == l)) ::: Each child must be assigned to exactly one locker\nForAll([l:lockers], Or(Count([c:children], assigned(c) == l) == 1, And(Count([c:children], assigned(c) == l) == 2, shared(l)))) ::: Each locker must be assigned to either one or two children, and each shared locker must be assigned to one girl and one boy\nForAll([l:lockers], Implies(shared(l), Exists([b:boys], Exists([g:girls], And(assigned(b) == l, assigned(g) == l))))) ::: Each shared locker must be assigned to one girl and one boy\nExists([l:lockers], And(assigned(Juan) == l, shared(l))) ::: Juan must share a locker\nForAll([l:lockers], Not(And(assigned(Rachel) == l, shared(l)))) ::: Rachel cannot share a locker\nForAll([l1:lockers], ForAll([l2:lockers], Implies(And(assigned(Nita) == l1, assigned(Trisha) == l2, Abs(l1 - l2) == 1), False))) ::: Nita's locker cannot be adjacent to Trisha's locker\nassigned(Fred) == 3 ::: Fred must be assigned to locker 3\nForAll([l:lockers], Implies(l <= 3, Exists([g:girls], assigned(g) == l))) ::: The first three lockers are assigned to girls\n\n# Options\nis_valid(assigned(Juan) == 1) ::: (A)\nis_valid(assigned(Nita) == 3) ::: (B)\nis_valid(assigned(Trisha) == 1) ::: (C)\nis_valid(assigned(Juan) == assigned(Trisha)) ::: (D)\nis_valid(assigned(Paul) == assigned(Trisha)) ::: (E)"
- Analysis: The formula "lockers = EnumSort[1, 2, 3, 4, 5]" is not in accordance with SAT syntax requirements, a pair of parentheses should be added outside the variable value.
- Modification："# Declarations\nchildren = EnumSort([Fred, Juan, Marc, Paul, Nita, Rachel, Trisha])\nlockers = EnumSort([1, 2, 3, 4, 5])\nassigned = Function([children] -> [lockers])\nshared = Function([lockers] -> [bool])\n\n# Constraints\nForAll([c:children], Exists([l:lockers], assigned(c) == l)) ::: Each child must be assigned to exactly one locker\nForAll([l:lockers], Or(Count([c:children], assigned(c) == l) == 1, And(Count([c:children], assigned(c) == l) == 2, shared(l)))) ::: Each locker must be assigned to either one or two children, and each shared locker must be assigned to one girl and one boy\nForAll([l:lockers], Implies(shared(l), Exists([b:boys], Exists([g:girls], And(assigned(b) == l, assigned(g) == l))))) ::: Each shared locker must be assigned to one girl and one boy\nExists([l:lockers], And(assigned(Juan) == l, shared(l))) ::: Juan must share a locker\nForAll([l:lockers], Not(And(assigned(Rachel) == l, shared(l)))) ::: Rachel cannot share a locker\nForAll([l1:lockers], ForAll([l2:lockers], Implies(And(assigned(Nita) == l1, assigned(Trisha) == l2, Abs(l1 - l2) == 1), False))) ::: Nita's locker cannot be adjacent to Trisha's locker\nassigned(Fred) == 3 ::: Fred must be assigned to locker 3\nForAll([l:lockers], Implies(l <= 3, Exists([g:girls], assigned(g) == l))) ::: The first three lockers are assigned to girls\n\n# Options\nis_valid(assigned(Juan) == 1) ::: (A)\nis_valid(assigned(Nita) == 3) ::: (B)\nis_valid(assigned(Trisha) == 1) ::: (C)\nis_valid(assigned(Juan) == assigned(Trisha)) ::: (D)\nis_valid(assigned(Paul) == assigned(Trisha)) ::: (E)"
```

This correction ensures that the formula is syntactically correct and adheres to the SAT format rules.
EXAMPLE JSON OUTPUT:
{
   "raw_logic_programs: [
      "# Declarations\\nchildren = EnumSort([Fred, Juan, Marc, Paul, Nita, Rachel, Trisha])\\nlockers = EnumSort([1, 2, 3, 4, 5])\\nassigned = Function([children] -> [lockers])\\nshared = Function([lockers] -> [bool])\\n\\n# Constraints\\nForAll([c:children], Exists([l:lockers], assigned(c) == l)) ::: Each child must be assigned to exactly one locker\\nForAll([l:lockers], Or(Count([c:children], assigned(c) == l) == 1, And(Count([c:children], assigned(c) == l) == 2, shared(l)))) ::: Each locker must be assigned to either one or two children, and each shared locker must be assigned to one girl and one boy\\nForAll([l:lockers], Implies(shared(l), Exists([b:boys], Exists([g:girls], And(assigned(b) == l, assigned(g) == l))))) ::: Each shared locker must be assigned to one girl and one boy\\nExists([l:lockers], And(assigned(Juan) == l, shared(l))) ::: Juan must share a locker\\nForAll([l:lockers], Not(And(assigned(Rachel) == l, shared(l)))) ::: Rachel cannot share a locker\\nForAll([l1:lockers], ForAll([l2:lockers], Implies(And(assigned(Nita) == l1, assigned(Trisha) == l2, Abs(l1 - l2) == 1), False))) ::: Nita's locker cannot be adjacent to Trisha's locker\\nassigned(Fred) == 3 ::: Fred must be assigned to locker 3\\nForAll([l:lockers], Implies(l <= 3, Exists([g:girls], assigned(g) == l))) ::: The first three lockers are assigned to girls\\n\\n# Options\\nis_valid(assigned(Juan) == 1) ::: (A)\\nis_valid(assigned(Nita) == 3) ::: (B)\\nis_valid(assigned(Trisha) == 1) ::: (C)\\nis_valid(assigned(Juan) == assigned(Trisha)) ::: (D)\\nis_valid(assigned(Paul) == assigned(Trisha)) ::: (E)"
   ]
}
"""
