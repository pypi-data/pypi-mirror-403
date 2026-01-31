import math

async def main():
    try:
        # Calculate various mathematical results
        calculations = {}
        
        # 1. Calculate the golden ratio
        golden_ratio = (1 + math.sqrt(5)) / 2
        calculations['golden_ratio'] = golden_ratio
        
        # 2. Calculate e (Euler's number) using series expansion
        e_approximation = sum(1 / math.factorial(n) for n in range(20))
        calculations['e_approximation'] = e_approximation
        calculations['e_actual'] = math.e
        
        # 3. Calculate pi using Leibniz formula
        pi_approximation = 4 * sum((-1)**n / (2*n + 1) for n in range(10000))
        calculations['pi_approximation'] = pi_approximation
        calculations['pi_actual'] = math.pi
        
        # 4. Calculate factorial of 10
        factorial_10 = math.factorial(10)
        calculations['factorial_10'] = factorial_10
        
        # 5. Calculate the sum of first 100 prime numbers
        def is_prime(n):
            if n < 2:
                return False
            for i in range(2, int(math.sqrt(n)) + 1):
                if n % i == 0:
                    return False
            return True
        
        primes = []
        num = 2
        while len(primes) < 100:
            if is_prime(num):
                primes.append(num)
            num += 1
        
        calculations['sum_first_100_primes'] = sum(primes)
        calculations['first_10_primes'] = primes[:10]
        
        # 6. Calculate Fibonacci sequence (first 20 numbers)
        def fibonacci(n):
            fib = [0, 1]
            for i in range(2, n):
                fib.append(fib[i-1] + fib[i-2])
            return fib[:n]
        
        calculations['fibonacci_20'] = fibonacci(20)
        
        # 7. Calculate square root of 2 (irrational number approximation)
        calculations['sqrt_2'] = math.sqrt(2)
        
        # 8. Calculate the area of a circle with radius 5
        radius = 5
        calculations['circle_area_r5'] = math.pi * radius ** 2
        
        result = {
            'result': calculations,
            'status': 'success',
            'description': 'Various mathematical calculations completed successfully'
        }
        
        return result
        
    except Exception as e:
        return {
            'result': None,
            'status': 'error',
            'error_message': str(e)
        }