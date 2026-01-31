async def main():
    try:
        fibonacci_numbers = []
        a, b = 0, 1
        
        for _ in range(10):
            fibonacci_numbers.append(a)
            a, b = b, a + b
        
        result = {
            'result': fibonacci_numbers
        }
        return result
    except Exception as e:
        return {
            'result': None,
            'error': str(e)
        }