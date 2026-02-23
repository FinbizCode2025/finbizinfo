from financial_analyzer import FinancialAnalyzer

fa = FinancialAnalyzer()
print('estimate for "hello world" ->', fa._estimate_tokens('hello world'))
print('estimate for longer sample ->', fa._estimate_tokens('This is a longer sample text to test tokenization. It includes punctuation, numbers 12345, and symbols.'))
