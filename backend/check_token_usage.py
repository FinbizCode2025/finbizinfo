from financial_analyzer import FinancialAnalyzer

fa = FinancialAnalyzer()
print('Initial token_stats:', fa.token_stats)
print('Initial last_request:', fa.last_request)
# simulate setting last request
fa.set_last_request_tokens(12, 34, prompt_text='Test prompt', completion_text='Test completion', usage={'prompt_tokens':12,'completion_tokens':34})
print('After set: token_stats (unchanged):', fa.token_stats)
print('After set: last_request:', fa.last_request)
# simulate accumulation as analyze would do
fa.token_stats['input_tokens'] += fa.last_request['prompt_tokens']
fa.token_stats['output_tokens'] += fa.last_request['completion_tokens']
fa.token_stats['total_tokens'] = fa.token_stats['input_tokens'] + fa.token_stats['output_tokens']
print('After accumulate: token_stats:', fa.token_stats)
