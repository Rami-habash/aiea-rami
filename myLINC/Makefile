
# Makefile for task 8

# To make changes to the models you want to use 
# open myProg.py and myKB.py to change the config 

# then you can run stuff here:
# 1. To generate ProoWriter samples from a .pl file run "make pw"
# 2. To test out LINC+ vs. baseline run "make run_test"
# 3. To see a plot of it run "make plt"
# 4. To run random queries/conclusions run "make run_queries"

data:
	python myKb.py

run_test:
	python myProg.py

run_queries:
	python myProg.py --queries

plt:
	python myPlot.py

clean:
	rm -rf __pycache__/
	rm -f *.json
