import traceback
from z3 import *

try:
    boys_sort, (Fred, Juan, Marc, Paul) = EnumSort('boys', ['Fred', 'Juan', 'Marc', 'Paul'])
    girls_sort, (Nita, Rachel, Trisha) = EnumSort('girls', ['Nita', 'Rachel', 'Trisha'])
    lockers_sort = IntSort()
    l1, l2, l3, l4, l5 = Ints('l1 l2 l3 l4 l5')
    lockers = [l1, l2, l3, l4, l5]
    boys = [Fred, Juan, Marc, Paul]
    girls = [Nita, Rachel, Trisha]
    assigned = Function('assigned', boys_sort, lockers_sort)
    assigned_girl = Function('assigned_girl', girls_sort, lockers_sort)

    pre_conditions = []
    pre_conditions.append(And([Sum([assigned(b) == l for b in boys]) <= 2 for l in lockers]))
    c = Const('c', boys_sort)
    pre_conditions.append(ForAll([c], Sum([assigned(c) == l for l in lockers]) == 1))
    g = Const('g', girls_sort)
    pre_conditions.append(Exists([g], assigned(Juan) == assigned_girl(g)))
    pre_conditions.append(And([assigned(Rachel) != l for l in lockers]))
    pre_conditions.append(Not(And(assigned(Nita) == assigned(Trisha), Abs(assigned(Nita) - assigned(Trisha)) == 1)))
    pre_conditions.append(assigned(Fred) == l3)
    pre_conditions.append(And([Sum([assigned(b) == l for b in boys]) <= 2 for l in lockers]))
    c = Const('c', boys_sort)
    pre_conditions.append(ForAll([c], Sum([assigned(c) == l for l in lockers]) == 1))
    g = Const('g', girls_sort)
    pre_conditions.append(Exists([g], assigned(Juan) == assigned_girl(g)))
    pre_conditions.append(And([assigned(Rachel) != l for l in lockers]))
    pre_conditions.append(Not(And(assigned(Nita) == assigned(Trisha), Abs(assigned(Nita) - assigned(Trisha)) == 1)))
    pre_conditions.append(assigned(Fred) == l3)

    def is_valid(option_constraints):
        solver = Solver()
        solver.add(pre_conditions)
        solver.add(Not(option_constraints))
        return solver.check() == unsat

    def is_unsat(option_constraints):
        solver = Solver()
        solver.add(pre_conditions)
        solver.add(option_constraints)
        return solver.check() == unsat

    def is_sat(option_constraints):
        solver = Solver()
        solver.add(pre_conditions)
        solver.add(option_constraints)
        return solver.check() == sat

    def is_accurate_list(option_constraints):
        return is_valid(Or(option_constraints)) and all([is_sat(c) for c in option_constraints])

    def is_exception(x):
        return not x


    if is_valid(assigned(Juan) == l1): print('(A)')
    if is_valid(assigned(Juan) == l2): print('(B)')
    if is_valid(assigned(Juan) == l3): print('(C)')
    if is_valid(assigned(Juan) == l4): print('(D)')
    if is_valid(assigned(Juan) == l5): print('(E)')
except Exception as e:
    tb = traceback.extract_tb(e.__traceback__)
    last_trace = tb[-1]
    print(f"{type(e).__name__}: {e}. `Error in Line: {last_trace.line}`\n")