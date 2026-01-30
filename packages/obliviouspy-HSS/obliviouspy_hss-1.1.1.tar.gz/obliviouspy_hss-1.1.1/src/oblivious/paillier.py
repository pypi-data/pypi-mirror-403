from dataclasses import dataclass
import secrets
import math

from .number import Number


@dataclass
class PaillierPublicKey:
    """
    Paillier public key.
    - n: RSA modulus (product of two large primes)
    Plaintext space:  Z_n
    Ciphertext space: Z*_n^2
    """
    n: int

    @property
    def n2(self) -> int:
        """Convenience: n^2."""
        return self.n * self.n


@dataclass
class PaillierPrivateKey:
    """
    Paillier private key.
    We follow your notation and use φ = (p-1)(q-1) as secret key
    (instead of λ = lcm(p-1, q-1)). Decryption uses φ^{-1} mod n.
    """
    phi: int
    public_key: PaillierPublicKey


class Paillier:
    """
    Standard Paillier cryptosystem, written in the same style as DamgardJurik.
    Mathematically è esattamente DJ con ζ = 1:

        Enc(m) = (1 + n)^m * r^n mod n^2
        Dec(c) = L(c^φ mod n^2) * φ^{-1} mod n,
        L(a)   = (a - 1) / n mod n

    con plaintext m ∈ Z_n.
    """

    # ------------------------------------------------------------------
    # Key generation
    # ------------------------------------------------------------------
    @staticmethod
    def keygen(bits: int = 2048) -> tuple[PaillierPublicKey, PaillierPrivateKey]:
        """
        Generate a Paillier keypair.
        - bits: bitlength of n (must be even so p,q have ~bits/2 each).
        """
        if bits % 2 != 0:
            raise ValueError("bits should be even")

        half = bits // 2
        p = Number.random_prime(half)
        q = Number.random_prime(half)
        while p == q:
            q = Number.random_prime(half)

        n = p * q
        # Your notation: φ = (p-1)(q-1)
        phi = (p - 1) * (q - 1)

        # Check φ invertible mod n (should hold for RSA modulus)
        _ = Number.modinv(phi % n, n)

        pk = PaillierPublicKey(n=n)
        sk = PaillierPrivateKey(phi=phi, public_key=pk)
        return pk, sk

    # ------------------------------------------------------------------
    # Internal L function
    # ------------------------------------------------------------------
    @staticmethod
    def _L(a: int, n: int) -> int:
        """
        Paillier L-function:
            L(a) = (a - 1) / n  mod n
        assuming a ≡ 1 (mod n).
        """
        return ((a - 1) // n) % n

    # ------------------------------------------------------------------
    # Encryption / Decryption
    # ------------------------------------------------------------------
    @staticmethod
    def encrypt(pk: PaillierPublicKey, m: int) -> int:
        """
        Encrypt m in Z_n:
            c = (1 + n)^m * r^n mod n^2
        """
        n = pk.n
        n2 = pk.n2

        if not (0 <= m < n):
            raise ValueError("Plaintext out of range Z_n")

        # r uniform in Z*_n
        while True:
            r = secrets.randbelow(n)
            if 1 <= r < n and math.gcd(r, n) == 1:
                break

        g = n + 1
        c1 = pow(g, m, n2)
        c2 = pow(r, n, n2)
        c = (c1 * c2) % n2
        return c

    @staticmethod
    def decrypt(sk: PaillierPrivateKey, c: int) -> int:
        """
        Decryption:
            u = c^φ mod n^2
            m = L(u) * φ^{-1} mod n
        """
        n = sk.public_key.n
        n2 = sk.public_key.n2

        u = pow(c, sk.phi, n2)
        L_u = Paillier._L(u, n)

        inv_phi = Number.modinv(sk.phi % n, n)
        m = (L_u * inv_phi) % n
        return m

    # ------------------------------------------------------------------
    # Homomorphic operations
    # ------------------------------------------------------------------
    @staticmethod
    def add(pk: PaillierPublicKey, c1: int, c2: int) -> int:
        """
        Homomorphic addition:
            Enc(m1 + m2) = c1 * c2 mod n^2
        """
        return (c1 * c2) % pk.n2

    @staticmethod
    def mul(pk: PaillierPublicKey, c: int, k: int) -> int:
        """
        Homomorphic multiplication by constant:
            Enc(k * m) = c^k mod n^2
        """
        return pow(c, k, pk.n2)

    @staticmethod
    def rerandomize(pk: PaillierPublicKey, c: int) -> int:
        """
        Re-randomize a ciphertext keeping the same plaintext:
            c' = c * Enc(0)
        """
        enc_zero = Paillier.encrypt(pk, 0)
        return (c * enc_zero) % pk.n2
