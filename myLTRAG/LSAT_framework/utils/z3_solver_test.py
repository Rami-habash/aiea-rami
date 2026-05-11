from solver_copy import LSAT_Z3_Program

if __name__=="__main__":
    logic_program = """
# Declarations
contestants = EnumSort([Harry, Iris, Kate, Nancy, Victor])
days = IntSort([Monday, Tuesday, Wednesday, Thursday, Friday])
scheduled = Function([contestants] -> [days])

# Constraints
And(Monday == 1, Tuesday == 2, Wednesday == 3, Thursday == 4, Friday == 5) ::: Define size/order
ForAll([c:contestants], Count([d:days], scheduled(c) == d) == 1) ::: Each contestant is scheduled for exactly one day
ForAll([d:days], Count([c:contestants], scheduled(c) == d) == 1) ::: Each day has exactly one contestant scheduled
Not(scheduled(Nancy) == Monday) ::: Nancy is not scheduled for Monday
Implies(scheduled(Harry) == Monday, scheduled(Nancy) == Friday) ::: If Harry is scheduled for Monday, Nancy is scheduled for Friday
Implies(scheduled(Nancy) == Tuesday, scheduled(Iris) == Monday) ::: If Nancy is scheduled for Tuesday, Iris is scheduled for Monday
ForAll([d:days], Implies(scheduled(Victor) == d, scheduled(Kate) == d + 1)) ::: Kate is scheduled for the next day after the day for which Victor is scheduled
Exists([d:days], Implies(scheduled(Harry) == d, scheduled(Iris) == (d + 1)) )::: Iris is scheduled for the next day after Harry

# Options
is_accurate_list([scheduled(Harry) == Monday, scheduled(Harry) == Tuesday]) ::: (A)
is_accurate_list([scheduled(Harry) == Monday, scheduled(Harry) == Wednesday]) ::: (B)
is_accurate_list([scheduled(Harry) == Monday, scheduled(Harry) == Thursday]) ::: (C)
is_accurate_list([scheduled(Harry) == Monday, scheduled(Harry) == Tuesday, scheduled(Harry) == Wednesday]) ::: (D)
is_accurate_list([scheduled(Harry) == Monday, scheduled(Harry) == Wednesday, scheduled(Harry) == Thursday]) ::: (E)
"""
    # region
    z3_program = LSAT_Z3_Program(logic_program, 'AR-LSAT', 'TEST')
    # print(z3_program.standard_code)

    output, error_message = z3_program.execute_program()
    print(output)
    print(type(output))
    print(error_message)

    print(z3_program.answer_mapping(output))
    # endregion


"""

"""