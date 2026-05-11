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
    assigned_girls = Function('assigned_girls', girls_sort, lockers_sort)

    pre_conditions = []
    b = Const('b', boys_sort)
    g = Const('g', girls_sort)
    pre_conditions.append(And([Or(Exists([b], assigned(b) == l), Exists([g], assigned_girls(g) == l)) for l in lockers]))
    c = Const('c', boys_sort)
    pre_conditions.append(ForAll([c], Sum([assigned(c) == l for l in lockers]) == 1))
    c = Const('c', girls_sort)
    pre_conditions.append(ForAll([c], Sum([assigned_girls(c) == l for l in lockers]) == 1))
    b = Const('b', boys_sort)
    g = Const('g', girls_sort)
    pre_conditions.append(And([Implies(And(Exists([b], assigned(b) == l), Exists([g], assigned_girls(g) == l)), And(Sum([assigned(b) == l for b in boys]) <= 1, Sum([assigned_girls(g) == l for g in girls]) <= 1)) for l in lockers]))
    pre_conditions.append(Or([assigned(Juan) == l for l in lockers]))
    pre_conditions.append(Not(Or([assigned_girls(Rachel) == l for l in lockers])))
    pre_conditions.append(And([And([Implies(And(assigned_girls(Nita) == l1, assigned_girls(Trisha) == l2, Abs(l1 - l2) == 1), False) for l2 in lockers]) for l1 in lockers]))
    pre_conditions.append(assigned(Fred) == 3)
    pre_conditions.append(assigned_girls(Trisha) == 3)
    pre_conditions.append(assigned(Marc) == 1)
    b = Const('b', boys_sort)
    g = Const('g', girls_sort)
    pre_conditions.append(And([Or(Exists([b], assigned(b) == l), Exists([g], assigned_girls(g) == l)) for l in lockers]))
    c = Const('c', boys_sort)
    pre_conditions.append(ForAll([c], Sum([assigned(c) == l for l in lockers]) == 1))
    c = Const('c', girls_sort)
    pre_conditions.append(ForAll([c], Sum([assigned_girls(c) == l for l in lockers]) == 1))
    b = Const('b', boys_sort)
    g = Const('g', girls_sort)
    pre_conditions.append(And([Implies(And(Exists([b], assigned(b) == l), Exists([g], assigned_girls(g) == l)), And(Sum([assigned(b) == l for b in boys]) <= 1, Sum([assigned_girls(g) == l for g in girls]) <= 1)) for l in lockers]))
    pre_conditions.append(Or([assigned(Juan) == l for l in lockers]))
    pre_conditions.append(Not(Or([assigned_girls(Rachel) == l for l in lockers])))
    pre_conditions.append(And([And([Implies(And(assigned_girls(Nita) == l1, assigned_girls(Trisha) == l2, Abs(l1 - l2) == 1), False) for l2 in lockers]) for l1 in lockers]))
    pre_conditions.append(assigned(Fred) == 3)
    pre_conditions.append(assigned_girls(Trisha) == 3)
    pre_conditions.append(assigned(Marc) == 1)

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


    if is_valid(assigned(Juan) == 4): print('(A)')
    if is_valid(assigned(Juan) == 5): print('(B)')
    if is_valid(assigned(Paul) == 2): print('(C)')
    if is_valid(assigned_girls(Rachel) == 2): print('(D)')
    if is_valid(assigned_girls(Rachel) == 5): print('(E)')
except Exception as e:
    tb = traceback.extract_tb(e.__traceback__)
    last_trace = tb[-1]
    print(f"{type(e).__name__}: {e}. `Error in Line: {last_trace.line}`\n")