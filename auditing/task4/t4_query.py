import janus_swi as janus

janus.consult('t4_facts.pl')

print('Type "exit" to quit')

while True:
    print('Enter your Prolog query (without ?- ):')
    query = input().strip()
    if query.lower() == 'exit':
        break
    try:
        found = False
        for solution in janus.query(query):
            print(solution)
            found = True
            
        if not found:
            print("No solutions found.")
            
    except Exception as e:
        print("Error executing query:", e)

    print()