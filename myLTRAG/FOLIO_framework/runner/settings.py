"""Experiment choices and token pricing."""

#============ Config ============#
# folio samples and workers
# max follio is 182 samples
N_SAMPLES = 182
NUM_WORKERS = 182 # concurrent threads for model requests
# which pipeline to test
RUN_COT = True
RUN_STANDARD = True
RUN_LTRAG = True
LTRAG_COT = True # yes or no to cot in LTRAG
# models
MODELS = ['gpt-5.4-mini']
# for 4o
EFFORTS = ['low']
# (uncached_in, cached_in, out) prices
# gpt-5.4-nano: https://developers.openai.com/api/docs/models/compare ; gpt-4o: standard OpenAI pricing.
PRICE_TABLE = {'gpt-5.4-nano': [0.2, 0.02, 1.25], 'gpt-5.4-mini': [0.75, 0.08, 4.5], 'gpt-4o': [5, 0, 15.0], 'gpt-4o-mini': [0.15, 0.08, 0.6], 'gpt-3.5-turbo': [0.5, 0, 1.5], 'gpt-4.1-mini': [0.4, 0.1, 1.6]}
#================================#
