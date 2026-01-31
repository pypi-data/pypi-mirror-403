import math

async def main():
    try:
        number = 144
        square_root = math.sqrt(number)
        result = {
            'result': square_root,
            'input': number,
            'operation': 'square_root'
        }
        return result
    except Exception as e:
        return {
            'result': None,
            'error': str(e)
        }