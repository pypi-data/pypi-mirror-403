from dataclasses import dataclass
import secrets
from typing import Optional


@dataclass
class AdditiveShare:
    """
    Two-party additive secret sharing of a value x.

    Semantica:  s1 - s0 = x   (in Z oppure in Z/modZ)

    - s0: share held by party 0
    - s1: share held by party 1
    - modulus:
        * None  -> shares live in Z, reconstruct as s1 - s0
        * m>0   -> shares live in Z/mZ, reconstruct as (s1 - s0) mod m
    """
    s0: int
    s1: int
    modulus: Optional[int] = None

    def value(self) -> int:
        """Reconstruct the secret from the two shares (single-process view)."""
        if self.modulus is None:
            return self.s1 - self.s0
        else:
            return (self.s1 - self.s0) % self.modulus

class SecretSharing:
    """
    Basic 2-party additive secret sharing.

    Notazione coerente con il paper:
      - useremo s1 - s0 = x  per scrivere ⟨x⟩σ   
      - in Z       -> REG/MUL over Z
      - in Z/N^s Z -> REG/MUL over Z/N^s Z
    """

    # --------------------------------------------------------------
    #   Sharing over Z   (no modulus)
    # --------------------------------------------------------------
    @staticmethod
    def share_Z(x: int, bits: int = 256) -> AdditiveShare:
        """
        Split x ∈ Z into shares (s0, s1) with s1 - s0 = x in Z.

        - s0 is chosen random in ~[-2^{bits-1}, 2^{bits-1})
        - s1 = s0 + x
        """
        if bits < 2:
            raise ValueError("bits must be >= 2")

        r = secrets.randbits(bits)
        r -= 1 << (bits - 1)
        s0 = r
        s1 = r + x
        return AdditiveShare(s0=s0, s1=s1, modulus=None)

    @staticmethod
    def reconstruct_Z(share: AdditiveShare) -> int:
        if share.modulus is not None:
            raise ValueError("Share has a modulus, use reconstruct_mod instead")
        return share.s1 - share.s0

    # --------------------------------------------------------------
    #   Sharing over Z_m   (modular)
    # --------------------------------------------------------------
    @staticmethod
    def share_mod(x: int, modulus: int) -> AdditiveShare:
        """
        Split x into shares modulo 'modulus':
            s1 - s0 ≡ x (mod modulus)
        """
        if modulus <= 0:
            raise ValueError("modulus must be positive")

        x_mod = x % modulus
        s0 = secrets.randbelow(modulus)
        s1 = (s0 + x_mod) % modulus
        return AdditiveShare(s0=s0, s1=s1, modulus=modulus)

    @staticmethod
    def reconstruct_mod(share: AdditiveShare) -> int:
        if share.modulus is None:
            raise ValueError("Share has no modulus, use reconstruct_Z instead")
        return (share.s1 - share.s0) % share.modulus

    # --------------------------------------------------------------
    #   Linear operations on shares
    # --------------------------------------------------------------
    @staticmethod
    def add(a: AdditiveShare, b: AdditiveShare) -> AdditiveShare:
        """
        Component-wise addition of two sharings of x, y:
          result shares x + y  (in the same ring).
        """
        if a.modulus != b.modulus:
            raise ValueError("Cannot add shares with different modulus")

        mod = a.modulus
        s0 = a.s0 + b.s0
        s1 = a.s1 + b.s1
        if mod is not None:
            s0 %= mod
            s1 %= mod
        return AdditiveShare(s0=s0, s1=s1, modulus=mod)

    @staticmethod
    def neg(a: AdditiveShare) -> AdditiveShare:
        """
        Negation of a sharing of x: yields sharing of −x.
        """
        mod = a.modulus
        if mod is None:
            return AdditiveShare(s0=-a.s0, s1=-a.s1, modulus=None)
        else:
            return AdditiveShare(s0=(-a.s0) % mod, s1=(-a.s1) % mod, modulus=mod)

    @staticmethod
    def sub(a: AdditiveShare, b: AdditiveShare) -> AdditiveShare:
        """
        Sharing of x - y, given sharings of x and y.
        """
        return SecretSharing.add(a, SecretSharing.neg(b))

    @staticmethod
    def scalar_mul(a: AdditiveShare, k: int) -> AdditiveShare:
        """
        Sharing of k * x, given sharing of x.
        """
        mod = a.modulus
        s0 = a.s0 * k
        s1 = a.s1 * k
        if mod is not None:
            s0 %= mod
            s1 %= mod
        return AdditiveShare(s0=s0, s1=s1, modulus=mod)
