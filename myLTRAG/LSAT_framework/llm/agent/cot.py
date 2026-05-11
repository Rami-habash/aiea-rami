from llm.AgentBase import AgentBase

class CoT(AgentBase):
    def __init__(self, needExample=False):
        super().__init__()
        self.temperature = 0.1
        self.example = ""
        if needExample:
           self.example = """
An example showed as following:
## Input
### Context:
Eight camp counselorsFran, George, Henry, Joan, Kathy, Lewis, Nathan, and Olgamust each be assigned to supervise exactly one of three activitiesswimming, tennis, and volleyball. The assignment of counselors must conform to the following conditions: Each activity is supervised by at least two, but not more than three, of the eight counselors. Henry supervises swimming. Neither Kathy nor Olga supervises tennis. Neither Kathy nor Nathan supervises the same activity as Joan. If George supervises swimming, both Nathan and Olga supervise volleyball.
### Question:
Which one of the following is a pair of counselors who could be two of three counselors assigned to supervise swimming?
### Options:
A) George and Nathan
B) George and Olga
C) Joan and Kathy
D) Joan and Nathan
E) Joan and Olga
## Output
Alright, I'm tackling this LSAT problem about assigning camp counselors to activities. Let's break it down step by step to understand which pair of counselors could be two of the three assigned to supervise swimming.

### Understanding the Problem

We have:
- **Counselors**: Fran, George, Henry, Joan, Kathy, Lewis, Nathan, and Olga.
- **Activities**: Swimming, Tennis, and Volleyball.
- **Constraints**:
  1. Each activity is supervised by at least two, but not more than three counselors.
  2. Henry supervises swimming.
  3. Neither Kathy nor Olga supervises tennis.
  4. Neither Kathy nor Nathan supervises the same activity as Joan.
  5. If George supervises swimming, both Nathan and Olga supervise volleyball.

**Question**: Which pair of counselors could be two of the three counselors assigned to supervise swimming?

**Options**:
A) George and Nathan  
B) George and Olga  
C) Joan and Kathy  
D) Joan and Nathan  
E) Joan and Olga

### Breaking Down the Constraints

1. **Henry supervises swimming**: So, Henry is definitely one of the swimming supervisors.
2. **Neither Kathy nor Olga supervises tennis**: So, Kathy and Olga are either supervising swimming or volleyball.
3. **Neither Kathy nor Nathan supervises the same activity as Joan**: This means if Joan supervises swimming, Kathy and Nathan cannot supervise swimming, and similarly for other activities.
4. **If George supervises swimming, both Nathan and Olga supervise volleyball**: This is a conditional statement linking George, Nathan, and Olga.

### Analyzing Each Option

We need to find a pair that, along with Henry, could form the three supervisors for swimming. Let's examine each option.

#### Option A: George and Nathan

- **George supervises swimming**: According to constraint 5, if George supervises swimming, then Nathan and Olga must supervise volleyball.
- **Nathan supervises swimming**: But if Nathan supervises swimming, he cannot supervise volleyball, which contradicts the condition that he must supervise volleyball if George supervises swimming.
  
**Conclusion**: This pair is invalid because it leads to a contradiction.

#### Option B: George and Olga

- **George supervises swimming**: Again, according to constraint 5, Nathan and Olga must supervise volleyball.
- **Olga supervises swimming**: But if Olga supervises swimming, she cannot supervise volleyball, which contradicts the condition.
  
**Conclusion**: This pair is invalid for the same reason as Option A.

#### Option C: Joan and Kathy

- **Joan supervises swimming**: According to constraint 4, Kathy cannot supervise the same activity as Joan, so Kathy cannot supervise swimming.
- **Kathy supervises swimming**: But this contradicts the previous point.
  
**Conclusion**: This pair is invalid because Kathy cannot supervise swimming if Joan does.

#### Option D: Joan and Nathan

- **Joan supervises swimming**: According to constraint 4, Nathan cannot supervise the same activity as Joan, so Nathan cannot supervise swimming.
- **Nathan supervises swimming**: This contradicts the previous point.
  
**Conclusion**: This pair is invalid because Nathan cannot supervise swimming if Joan does.

#### Option E: Joan and Olga

- **Joan supervises swimming**: According to constraint 4, Kathy and Nathan cannot supervise swimming.
- **Olga supervises swimming**: Constraint 3 states that Olga does not supervise tennis, so she can supervise swimming or volleyball. Since we're assigning her to swimming, this is acceptable.
  
Now, let's check for any contradictions:
- Henry is already supervising swimming.
- Joan and Olga are also supervising swimming, making three supervisors for swimming, which satisfies the constraint of at least two but not more than three.
- Kathy and Nathan cannot supervise swimming, so they must supervise either tennis or volleyball.
  
**Conclusion**: This pair is valid because it doesn't violate any constraints.

### Final Answer

**Answer: C) Grace, Tom**
"""
        self.json_msg = """
The user will provide some process of thinking and reasoning, and the answer can only be one of 'A', 'B', 'C', 'D', 'E'. Please parse the "answer" and output it in JSON format.

## EXAMPLE INPUT
To solve this problem, we need to carefully analyze the given conditions and determine which pair of counselors could both be assigned to supervise swimming, considering that swimming must be supervised by exactly three counselors (since each activity is supervised by at least two but not more than three counselors, and Henry is already assigned to swimming).

### Step-by-Step Analysis:

1. **Henry is already assigned to swimming.**  
   - This means we need to find two more counselors who can be assigned to swimming.

2. **Neither Kathy nor Olga supervises tennis.**  
   - This means Kathy and Olga must supervise either swimming or volleyball.

3. **Neither Kathy nor Nathan supervises the same activity as Joan.**  
   - If Joan supervises swimming, then Kathy and Nathan cannot supervise swimming.  
   - If Joan supervises tennis or volleyball, then Kathy and Nathan cannot supervise that same activity.

4. **If George supervises swimming, both Nathan and Olga supervise volleyball.**  
   - This is a conditional rule that affects the assignments if George is assigned to swimming.

### Evaluating the Options:

**Option A: George and Nathan**  
- If George supervises swimming, then according to the conditional rule, Nathan must supervise volleyball.  
- Therefore, George and Nathan cannot both supervise swimming.  
- **This option is invalid.**

**Option B: George and Olga**  
- If George supervises swimming, then Olga must supervise volleyball (from the conditional rule).  
- Therefore, George and Olga cannot both supervise swimming.  
- **This option is invalid.**

**Option C: Joan and Kathy**  
- If Joan supervises swimming, then Kathy cannot supervise swimming (from the third condition).  
- Therefore, Joan and Kathy cannot both supervise swimming.  
- **This option is invalid.**

**Option D: Joan and Nathan**  
- If Joan supervises swimming, then Nathan cannot supervise swimming (from the third condition).  
- Therefore, Joan and Nathan cannot both supervise swimming.  
- **This option is invalid.**

**Option E: Joan and Olga**  
- Joan can supervise swimming.  
- Olga can also supervise swimming because there is no rule preventing her from doing so (the only restriction on Olga is that she cannot supervise tennis).  
- This pair does not violate any of the given conditions.  
- **This option is valid.**

### Conclusion:
The only pair of counselors who could both be assigned to supervise swimming, along with Henry, is **Joan and Olga**.

**Answer: E) Joan and Olga**

EXAMPLE JSON OUTPUT:
{
    "answer": "E"
}
"""
    def chat(self, prompt: str) -> str:
        prompt = f"""
The following is a LSAT problem.
The task is to choose the correct option follows from the context and the question.
{self.example}
Handle the following issue:
{prompt}
Choose the answer from 'A', 'B', 'C', 'D' and 'E' given the context.
"""
# Let's think step by step.
        print(prompt)
        return super().chat(prompt)
    
