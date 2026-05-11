import traceback
from z3 import *

try:
    children_sort, (Fred, Juan, Marc, Paul, Nita, Rachel, Trisha) = EnumSort('children', ['Fred', 'Juan', 'Marc', 'Paul', 'Nita', 'Rachel', 'Trisha'])
    lockers_sort = IntSort()
    l1, l2, l3, l4, l5 = Ints('l1 l2 l3 l4 l5')
    lockers = [l1, l2, l3, l4, l5]
    children = [Fred, Juan, Marc, Paul, Nita, Rachel, Trisha]
    assigned = Function('assigned', children_sort, lockers_sort)
    shared = Function('shared', lockers_sort, BoolSort())

    pre_conditions = []
    c = Const('c', children_sort)
    pre_conditions.append(ForAll([c], Or([assigned(c) == l for l in lockers])))
    pre_conditions.append(And([Sum([assigned(c) == l for c in children]) <= 2 for l in lockers]))
    pre_conditions.append(And([And(shared(l), Sum([assigned(c) == l for c in children]) == 2) for l in lockers]))
    pre_conditions.append(Or([And(assigned(Juan) == l, Sum([assigned(c) == l for c in children]) == 2) for l in lockers]))
    pre_conditions.append(And([And(assigned(Rachel) == l, Sum([assigned(c) == l for c in children]) == 1) for l in lockers]))
    pre_conditions.append(Not(Or(And(assigned(Nita) == l1, assigned(Trisha) == l2), And(assigned(Nita) == l2, assigned(Trisha) == l1), And(assigned(Nita) == l2, assigned(Trisha) == l3), And(assigned(Nita) == l3, assigned(Trisha) == l2), And(assigned(Nita) == l3, assigned(Trisha) == l4), And(assigned(Nita) == l4, assigned(Trisha) == l3), And(assigned(Nita) == l4, assigned(Trisha) == l5), And(assigned(Nita) == l5, assigned(Trisha) == l4))))
    pre_conditions.append(assigned(Fred) == l3)
    c = Const('c', children_sort)
    pre_conditions.append(ForAll([c], Or([assigned(c) == l for l in lockers])))
    pre_conditions.append(And([Sum([assigned(c) == l for c in children]) <= 2 for l in lockers]))
    pre_conditions.append(And([And(shared(l), Sum([assigned(c) == l for c in children]) == 2) for l in lockers]))
    pre_conditions.append(Or([And(assigned(Juan) == l, Sum([assigned(c) == l for c in children]) == 2) for l in lockers]))
    pre_conditions.append(And([And(assigned(Rachel) == l, Sum([assigned(c) == l for c in children]) == 1) for l in lockers]))
    pre_conditions.append(Not(Or(And(assigned(Nita) == l1, assigned(Trisha) == l2), And(assigned(Nita) == l2, assigned(Trisha) == l1), And(assigned(Nita) == l2, assigned(Trisha) == l3), And(assigned(Nita) == l3, assigned(Trisha) == l2), And(assigned(Nita) == l3, assigned(Trisha) == l4), And(assigned(Nita) == l4, assigned(Trisha) == l3), And(assigned(Nita) == l4, assigned(Trisha) == l5), And(assigned(Nita) == l5, assigned(Trisha) == l4))))
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


    if is_accurate_list([assigned(Juan) == l1, assigned(Marc) == l1, assigned(Paul) == l1]): print('(A)')
    if is_accurate_list([assigned(Juan) == l1, assigned(Marc) == l1, assigned(Trisha) == l1]): print('(B)')
    if is_accurate_list([assigned(Juan) == l1, assigned(Nita) == l1, assigned(Trisha) == l1]): print('(C)')
except Exception as e:
    tb = traceback.extract_tb(e.__traceback__)
    last_trace = tb[-1]
    print(f"{type(e).__name__}: {e}. `Error in Line: {last_trace.line}`\n")