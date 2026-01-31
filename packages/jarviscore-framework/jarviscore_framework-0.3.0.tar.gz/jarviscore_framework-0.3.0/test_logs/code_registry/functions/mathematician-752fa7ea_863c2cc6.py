async def main():
    try:
        calculation_result = 2 + 2
        result = {
            'result': calculation_result,
            'expression': '2 + 2',
            'success': True
        }
        return result
    except Exception as e:
        result = {
            'result': None,
            'expression': '2 + 2',
            'success': False,
            'error': str(e)
        }
        return result