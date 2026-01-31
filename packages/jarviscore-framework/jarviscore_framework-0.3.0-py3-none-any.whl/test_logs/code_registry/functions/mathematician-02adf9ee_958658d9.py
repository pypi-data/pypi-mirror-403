async def main():
    try:
        import math
        
        n = 5
        factorial_result = math.factorial(n)
        
        result = {
            'result': factorial_result,
            'calculation': f'{n}! = {factorial_result}',
            'method': 'math.factorial'
        }
        
        return result
    except Exception as e:
        return {
            'result': None,
            'error': str(e)
        }