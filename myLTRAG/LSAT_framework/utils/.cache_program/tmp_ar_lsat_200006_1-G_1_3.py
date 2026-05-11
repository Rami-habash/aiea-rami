import traceback
from z3 import *

try:
    boys_sort, (Fred, Juan, Marc, Paul) = EnumSort('boys', ['Fred', 'Juan', 'Marc', 'Paul'])
    girls_sort, (Nita, Rachel, Trisha) = EnumSort('girls', ['Nita', 'Rachel', 'Trisha'])
    lockers_sort = IntSort()
    boys = [Fred, Juan, Marc, Paul]
    girls = [Nita, Rachel, Trisha]
    lockers = [1, 2, 3, 4, 5]
    assigned = Function('assigned', boys_sort, lockers_sort)
    assigned_girls = Function('assigned_girls', girls_sort, lockers_sort)
    shared = Function('shared', lockers_sort, BoolSort())

    pre_conditions = []
    pre_conditions.append(And([Sum([assigned(b) == l for b in boys]) <= 2 for l in lockers]))
    pre_conditions.append(And([Sum([assigned_girls(g) == l for g in girls]) <= 2 for l in lockers]))
    b = Const('b', boys_sort)
    g = Const('g', girls_sort)
    pre_conditions.append(ForAll([b], Exists([g], shared(assigned(b)) and shared(assigned_girls(g)))))
    pre_conditions.append(assigned(Juan) != assigned_girls(Rachel))
    pre_conditions.append(And([Not(And(assigned(Nita) == l, assigned(Trisha) == l)) for l in lockers]))
    pre_conditions.append(assigned(Fred) == 3)
    b = Const('b', boys_sort)
    pre_conditions.append(ForAll([b], Implies(And(b == Juan, assigned(b) == 5), Sum([assigned(b1) == 5 for b1 in boys]) == 1)))
    b0 = Const('b0', boys_sort)
    pre_conditions.append(ForAll([b0], And(1 <= assigned(b0), assigned(b0) <= 5)))
    g0 = Const('g0', girls_sort)
    pre_conditions.append(ForAll([g0], And(1 <= assigned_girls(g0), assigned_girls(g0) <= 5)))
    pre_conditions.append(And([Sum([assigned(b) == l for b in boys]) <= 2 for l in lockers]))
    pre_conditions.append(And([Sum([assigned_girls(g) == l for g in girls]) <= 2 for l in lockers]))
    b = Const('b', boys_sort)
    g = Const('g', girls_sort)
    pre_conditions.append(ForAll([b], Exists([g], shared(assigned(b)) and shared(assigned_girls(g)))))
    pre_conditions.append(assigned(Juan) != assigned_girls(Rachel))
    pre_conditions.append(And([Not(And(assigned(Nita) == l, assigned(Trisha) == l)) for l in lockers]))
    pre_conditions.append(assigned(Fred) == 3)
    b = Const('b', boys_sort)
    pre_conditions.append(ForAll([b], Implies(And(b == Juan, assigned(b) == 5), Sum([assigned(b1) == 5 for b1 in boys]) == 1)))

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


    if is_accurate_list([Not(shared(2)), Not(shared(4))]): print('(A)')
    if is_accurate_list([Not(shared(4))]): print('(B)')
    if is_accurate_list([Not(shared(1)), Not(shared(2))]): print('(C)')
    if is_accurate_list([Not(shared(1)), Not(shared(4))]): print('(D)')
    if is_accurate_list([Not(shared(2)), Not(shared(4))]): print('(E)')
except Exception as e:
    tb = traceback.extract_tb(e.__traceback__)
    last_trace = tb[-1]
    print(f"{type(e).__name__}: {e}. `Error in Line: {last_trace.line}`\n")