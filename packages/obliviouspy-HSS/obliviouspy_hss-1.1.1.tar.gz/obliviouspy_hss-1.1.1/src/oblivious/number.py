import math
import random
import secrets

class Number:
    @staticmethod
    def gcd(a: int, b: int) -> int:
        """Compute the greatest common divisor of a and b."""
        return math.gcd(a, b)
    
    @staticmethod
    def lcm(a: int, b: int) -> int:
        """Compute the least common multiple of a and b."""
        return abs(a * b) // Number.gcd(a, b)
    
    @staticmethod
    def modinv(a: int, m: int) -> int:
        """Compute the modular inverse of a modulo m."""
        # Extended Euclidean Algorithm
        r0, r1 = a, m
        s0, s1 = 1, 0
        t0, t1 = 0, 1
        while r1 != 0:
            q = r0 // r1
            r0, r1 = r1, r0 - q * r1
            s0, s1 = s1, s0 - q * s1
            t0, t1 = t1, t0 - q * t1

        if r0 != 1:
            raise ValueError("modinv does not exist")
        return s0 % m
    
    @staticmethod
    def is_probable_prime(n: int, k: int = 40) -> bool:
        """Miller–Rabin probabilistic algorithm."""
        if n < 2:
            return False
        # because this is a proof of concept, we use a small set of bases, 
        # this check list improva performances for small scenarios
        small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        if n in small_primes:
            return True
        if any(n % p == 0 for p in small_primes):
            return False

        d = n - 1
        s = 0
        while d % 2 == 0:
            d //= 2
            s += 1

        for _ in range(k):
            a = secrets.randbelow(n - 3) + 2  # [2, n-2]
            x = pow(a, d, n)
            if x == 1 or x == n - 1:
                continue
            for _ in range(s - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False
        return True
    
    @staticmethod
    def random_prime(bits: int) -> int:
        """generate a prime of lenght 'bits' bit (probabilistic)."""
        assert bits >= 2
        while True:
            # MSB e LSB 
            candidate = secrets.randbits(bits) | 1 | (1 << (bits - 1))
            if Number.is_probable_prime(candidate):
                return candidate