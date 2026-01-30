from dataclasses import dataclass
import secrets
import math
from .number import Number


@dataclass
class DamgardJurikPublicKey:
    n: int      # RSA modulus
    s: int      # "message size" exponent, plaintexts in Z_{N^s}

    @property
    def N_pow_s(self) -> int:
        return pow(self.n, self.s)

    @property
    def N_pow_s_plus_1(self) -> int:
        return pow(self.n, self.s + 1)


@dataclass
class DamgardJurikPrivateKey:
    phi: int                 # φ(N) = (p-1)(q-1)
    public_key: DamgardJurikPublicKey



class DamgardJurik:
    """
    Implementation of Damgård–Jurik encryption exactly as:

    - Plaintexts:    x in Z / N^s Z
    - Ciphertexts:   c in (Z / N^{s+1} Z)^×
    - KeyGen:        N = p*q, φ = (p-1)(q-1)
    - Enc:           c = r^{N^s} * exp(x)      mod N^{s+1}
    - Dec:           x = φ^{-1} * log(c^φ)    mod N^s
    """

    # ---------------------- key generation -----------------------------

    @staticmethod
    def keygen(bits: int = 2048, s: int = 1):
        """
        DJ.KeyGen(1^κ) from Def. 1:
        - choose RSA modulus N = p*q, p,q ~ 2^{bits/2}
        - private key φ(N) = (p-1)(q-1)
        """
        if bits % 2 != 0:
            raise ValueError("Key size must be even so p and q have equal length")

        half = bits // 2
        p = Number.random_prime(half)
        q = Number.random_prime(half)
        while p == q:
            q = Number.random_prime(half)

        n = p * q
        phi = (p - 1) * (q - 1)   # they use φ(N), NOT lcm

        pk = DamgardJurikPublicKey(n=n, s=s)
        sk = DamgardJurikPrivateKey(phi=phi, public_key=pk)
        return pk, sk

    # -------------------- internal helpers -----------------------------

    @staticmethod
    def _exp(pk: DamgardJurikPublicKey, x: int) -> int:
        """
        exp(x) = sum_{k=0}^s (N x)^k / k!   in Z / N^{s+1} Z

        Domain: x in Z / N^s Z.
        """
        N = pk.n
        s = pk.s
        mod = pk.N_pow_s_plus_1

        # reduce x modulo N^s as in the paper
        x %= pk.N_pow_s

        # Nx fits in Z/N^{s+1}Z
        Nx = (N * x) % mod

        # Horner-style evaluation of the Taylor series
        res = 1  # k = 0 term
        term = 1
        fact = 1

        for k in range(1, s + 1):
            term = (term * Nx) % mod          # (Nx)^k
            fact *= k                         # k!
            inv_fact = Number.modinv(fact, mod)
            res = (res + term * inv_fact) % mod

        return res

    @staticmethod
    def _log(pk: DamgardJurikPublicKey, u: int) -> int:
        """
        log(1 + N x) = sum_{k=1}^s (-N)^{k-1} x^k / k    in Z / N^s Z

        Input: u in 1 + N Z / N^{s+1} Z.
        Output: z in Z / N^s Z such that exp(z) = u.
        """
        N = pk.n
        s = pk.s
        mod = pk.N_pow_s       # range of log

        # u = 1 + N x  (mod N^{s+1})  ⇒  x = (u - 1) / N  (as integer) mod N^s
        # representatives are in [0, N^{s+1}-1], so this division is exact.
        x = ((u - 1) // N) % mod

        res = 0
        pow_x = x              # x^k
        pow_minusN = 1         # (-N)^{k-1}

        for k in range(1, s + 1):
            if k == 1:
                pow_minusN = 1
            else:
                pow_minusN = (pow_minusN * (-N)) % mod

            denom_inv = Number.modinv(k, mod)
            term = (pow_minusN * pow_x) % mod
            term = (term * denom_inv) % mod
            res = (res + term) % mod

            # prepare x^{k+1}
            pow_x = (pow_x * x) % mod

        return res

    # ---------------- encryption / decryption --------------------------

    @staticmethod
    def encrypt(pk: DamgardJurikPublicKey, m: int) -> int:
        """
        DJ.Enc_{N,s}(x):

            c = r^{N^s} * exp(x)   mod N^{s+1}

        where r is uniform in (Z / N^{s+1} Z)^× and x ∈ Z_{N^s}.
        """
        N = pk.n
        s = pk.s
        mod = pk.N_pow_s_plus_1
        N_pow_s = pk.N_pow_s

        if not (0 <= m < N_pow_s):
            raise ValueError(f"Plaintext m must be in [0, N^s), got m={m}")

        # sample r in (Z / N^{s+1} Z)^×  ⇒ gcd(r, N) = 1
        while True:
            r = secrets.randbelow(mod)
            if 1 <= r < mod and math.gcd(r, N) == 1:
                break

        exp_m = DamgardJurik._exp(pk, m)
        r_part = pow(r, N_pow_s, mod)

        return (r_part * exp_m) % mod

    @staticmethod
    def decrypt(sk: DamgardJurikPrivateKey, c: int) -> int:
        """
        DJ.Dec_{N,s,φ}(c):

            u = c^φ           mod N^{s+1}
            z = log(u)        in Z / N^s Z   (so z = φ * x)
            x = z * φ^{-1}    mod N^s
        """
        pk = sk.public_key
        N = pk.n
        s = pk.s
        mod_ns1 = pk.N_pow_s_plus_1
        mod_ns = pk.N_pow_s

        # c should be in (Z / N^{s+1} Z)^×, ma se non lo è
        # la pow mod fallirà comunque in modo pulito
        u = pow(c, sk.phi, mod_ns1)          # u ∈ 1 + N Z / N^{s+1} Z
        z = DamgardJurik._log(pk, u)         # z = φ * x   in Z / N^s Z

        phi_inv = Number.modinv(sk.phi, mod_ns)
        m = (z * phi_inv) % mod_ns
        return m


    # ----------------- homomorphic operations (optional) ----------------

    @staticmethod
    def add(pk: DamgardJurikPublicKey, c1: int, c2: int) -> int:
        """
        Homomorphic addition:
            Enc(x) * Enc(y) = Enc(x + y)
        """
        return (c1 * c2) % pk.N_pow_s_plus_1

    @staticmethod
    def mul(pk: DamgardJurikPublicKey, c: int, k: int) -> int:
        """
        Homomorphic multiplication by a constant:
            Enc(x)^k = Enc(k * x)
        """
        return pow(c, k, pk.N_pow_s_plus_1)

    
