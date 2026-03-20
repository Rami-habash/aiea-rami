This deliverable acieves the main goals of understanding LangChain and RAG.

Future development: Make better use of RAG and try to compare it to LINC

- This is LINC’s original pipeline: ProofWriter → Semantic Parser (LLM) → FOL → Prover9 → results (label vs. prediction).
- This is my pipeline (LINC+): Prolog → LLM → ProofWriter → RAG → Semantic Parser (LLM) → Prover9 → Prover9 trace and results.

please look at LINC's: https://arxiv.org/abs/2310.15164

#================================================================#
Files:
#================================================================#
Files with config: *

*Makefile: shows all the makes you can use to run this program

myBase.py: essential functions for training and instructing the semantic parser LLM
myUtils.py: deals more with translations and ensuring proper syntax for our theorem prover and extracts the semantic parser's verdict

soccer.pl: input knowledge base
*myKb.py: translates my pl kb to ProofWriter samples
soccer_kb.json: translated ProofWriter examples

*myProg.py: runs either test for accuracy or --queries

query_results.txt: results for a sample query I ran

all json files:
save data to be used later

myPlot.py: graph (make plt) the accuracy of models tested


#================================================================#
Notes:
#================================================================#
- This md is not refined yet. Needs more expansion later










