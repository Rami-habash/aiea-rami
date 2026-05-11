import re

def remove_markdown(text):
    text = text.replace("**", "").replace("`", "")
    # remove heading markers
    text = re.sub(r'#+\s?', '', text)

    # remove bold and italic markers
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    # remove ---
    text = re.sub(r'---', '', text)
    # remove consecutive 2 or more newline characters
    text = re.sub(r'\n{2,}', '\n\n', text)
    return text

if __name__ == "__main__":
    # example text
    text = """
Let's analyze the premises and the conclusion step by step to determine if the conclusion logically follows.

---

### Premises:
1. **All eels are fish.**
   - Eels belong to the category of fish.

2. **No fish are plants.**
   - Fish and plants are mutually exclusive; a fish cannot be a plant.

3. **A thing is either a plant or an animal.**
   - Everything falls into one of these two categories: it is either a plant or an animal.

4. **Nothing that breathes is paper.**
   - If something breathes, it cannot be paper.

5. **All animals breathe.**
   - All animals have the property of breathing.

6. **If a sea eel is either an eel or a plant, then a sea eel is an eel or an animal.**
   - This statement provides a condition: if a sea eel is either an eel or a plant, it must be an eel (from Premise 1) or an animal (from Premise 3).

---

### Conclusion:
**Sea eel breathes or is a paper.**

---

### Step-by-Step Evaluation:

1. From Premise 1 (**All eels are fish**), a **sea eel** is an eel, which means it is a fish.
   Therefore, a sea eel **is not a plant** (Premise 2: no fish are plants).

2. From Premise 3 (**A thing is either a plant or an animal**), since a sea eel is not a plant, it must be an **animal**.

3. From Premise 5 (**All animals breathe**), if a sea eel is an animal, then it **breathes**.

4. From Premise 4 (**Nothing that breathes is paper**), if a sea eel breathes, it **cannot be paper**.

---

### Conclusion Analysis:
The conclusion states: **"Sea eel breathes or is a paper."**
- From our logical deductions, a sea eel **breathes** (it is an animal and all animals breathe).
- Since the first part of the conclusion ("Sea eel breathes") is true, the entire statement "Sea eel breathes or is a paper" is **true** based on the logical rule of disjunction (A or B is true if A is true).

---

### Final Answer:
**True**
The conclusion logically follows from the premises because a sea eel breathes, satisfying the first part of the "or" statement."""
    # remove Markdown markers
    text = remove_markdown(text)
    # print processed text
    print(text)
