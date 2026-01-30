import pytest
import random
import sys, os

sys.path.append(os.path.abspath("src"))

from oblivious.paillier import Paillier
from oblivious.damgardjurik import DamgardJurik

def test_paillier_basics():
    """
    1. KeyGen
    2. Encrypt -> Decrypt
    3. Homomorphic Add
    4. Homomorphic Scalar Mul
    """
    
    # 1. SETUP
    bits = 128
    pk, sk = Paillier.keygen(bits=bits)
    print(f"Paillier KeyGen ({bits} bits): N={pk.n}")

    # 2. ENC / DEC
    m = 42
    c = Paillier.encrypt(pk, m)
    dec = Paillier.decrypt(sk, c)
    print(f"Enc({m}) -> Dec -> {dec}")
    assert m == dec, "Paillier Decryption Failed"

    # 3. ADDITION (c1 * c2)
    m1, m2 = 100, 50
    c1 = Paillier.encrypt(pk, m1)
    c2 = Paillier.encrypt(pk, m2)
    
    c_sum = Paillier.add(pk, c1, c2)
    dec_sum = Paillier.decrypt(sk, c_sum)
    print(f"Add({m1}, {m2}) -> {dec_sum}")
    assert dec_sum == (m1 + m2), "Paillier Addition Failed"

    # 4. SCALAR MULTIPLICATION (c^k)
    k = 5
    c_mul = Paillier.mul(pk, c1, k) # c1 era 100
    dec_mul = Paillier.decrypt(sk, c_mul)
    print(f"Mul({m1}, {k}) -> {dec_mul}")
    assert dec_mul == (m1 * k), "Paillier Scalar Mul Failed"
    
    print("PAILLIER: OK")


def test_damgard_jurik_basics():
    """
    1. KeyGen con s=2
    2. Encrypt -> Decrypt (anche con messaggi > N, grazie a s > 1)
    3. Homomorphic Add
    4. Homomorphic Scalar Mul
    """
    print("\n--- TEST DAMGARD-JURIK BASE (s=2) ---")
    
    # 1. SETUP
    bits = 128
    s = 2
    pk, sk = DamgardJurik.keygen(bits=bits, s=s)
    
    mod_plain = pk.N_pow_s
    print(f"DJ KeyGen ({bits} bits, s={s}): N={pk.n}")
    print(f"Spazio Messaggi (N^s): {mod_plain}")

    # 2. ENC / DEC
    m = pk.n + 12345 
    c = DamgardJurik.encrypt(pk, m)
    dec = DamgardJurik.decrypt(sk, c)
    print(f"Enc({m}) [>N] -> Dec -> {dec}")
    assert m == dec, "DJ Decryption Failed"

    # 3. ADDITION
    m1 = 123
    m2 = 456
    c1 = DamgardJurik.encrypt(pk, m1)
    c2 = DamgardJurik.encrypt(pk, m2)
    
    c_sum = DamgardJurik.add(pk, c1, c2)
    dec_sum = DamgardJurik.decrypt(sk, c_sum)
    print(f"Add({m1}, {m2}) -> {dec_sum}")
    assert dec_sum == (m1 + m2), "DJ Addition Failed"

    # 4. SCALAR MULTIPLICATION
    k = 10
    c_mul = DamgardJurik.mul(pk, c1, k) # c1 era 123
    dec_mul = DamgardJurik.decrypt(sk, c_mul)
    print(f"Mul({m1}, {k}) -> {dec_mul}")
    assert dec_mul == (m1 * k), "DJ Scalar Mul Failed"

    print("DAMGARD-JURIK: OK")
