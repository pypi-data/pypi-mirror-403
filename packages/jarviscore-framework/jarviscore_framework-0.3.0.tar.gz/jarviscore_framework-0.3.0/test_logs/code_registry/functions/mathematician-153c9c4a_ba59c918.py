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
            if n == 2:
                return True
            if n % 2 == 0:
                return False
            for i in range(3, int(math.sqrt(n)) + 1, 2):
                if n % i == 0:
                    return False
            return True
        
        primes = []
        num = 2
        while len(primes) < 100:
            if is_prime(num):
                primes.append(num)
            num += 1
        
        sum_of_primes = sum(primes)
        calculations['sum_first_100_primes'] = sum_of_primes
        calculations['first_10_primes'] = primes[:10]
        calculations['100th_prime'] = primes[99]
        
        # 6. Calculate Fibonacci sequence (first 20 numbers)
        def fibonacci(n):
            fib = [0, 1]
            for i in range(2, n):
                fib.append(fib[i-1] + fib[i-2])
            return fib[:n]
        
        fib_sequence = fibonacci(20)
        calculations['fibonacci_20'] = fib_sequence
        
        # 7. Calculate the area of a circle with radius 5
        radius = 5
        circle_area = math.pi * radius ** 2
        calculations['circle_area_radius_5'] = circle_area
        
        # 8. Calculate hypotenuse of a 3-4-5 triangle
        hypotenuse = math.hypot(3, 4)
        calculations['hypotenuse_3_4'] = hypotenuse
        
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
            'error': str(e)
        }