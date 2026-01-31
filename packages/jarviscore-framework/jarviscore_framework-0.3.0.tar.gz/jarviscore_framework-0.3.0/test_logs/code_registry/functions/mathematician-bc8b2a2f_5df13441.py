async def main():
    try:
        # Calculate sum of numbers from 1 to 100
        # Using the formula: n * (n + 1) / 2
        n = 100
        sum_formula = n * (n + 1) // 2
        
        # Alternative: using sum with range
        sum_range = sum(range(1, 101))
        
        result = {
            'result': sum_formula,
            'verification': sum_range,
            'method': 'Gauss formula: n*(n+1)/2',
            'n': n
        }
        
        return result
    except Exception as e:
        return {
            'result': None,
            'error': str(e)
        }