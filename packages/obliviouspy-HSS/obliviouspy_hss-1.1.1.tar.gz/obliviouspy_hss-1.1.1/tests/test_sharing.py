import pytest
import random
import sys, os

sys.path.append(os.path.abspath("src"))

from oblivious.sharing import SecretSharing as SS

def test_sharing_over_integers():

    print("\n--- TEST SHARING OVER Z (integer) ---")
    
    # 1. Basic Sharing & Reconstruction
    x = 12345
    # bits=64
    sh_x = SS.share_Z(x, bits=64)
    
    print(f"Secret: {x}")
    print(f"Shares: s0={sh_x.s0}, s1={sh_x.s1}")
    
    rec_x = SS.reconstruct_Z(sh_x)
    print(f"Reconstructed: {rec_x}")
    
    assert rec_x == x, "Reconstruction over Z failed"
    
    # 2. Homomorphic Addition (x + y)
    y = 67890
    sh_y = SS.share_Z(y)
    
    sh_sum = SS.add(sh_x, sh_y)
    rec_sum = SS.reconstruct_Z(sh_sum)
    print(f"Add ({x} + {y}) -> {rec_sum}")
    
    assert rec_sum == (x + y), "Addition over Z failed"
    
    # 3. Homomorphic Subtraction (x - y)
    sh_sub = SS.sub(sh_x, sh_y)
    rec_sub = SS.reconstruct_Z(sh_sub)
    print(f"Sub ({x} - {y}) -> {rec_sub}")
    
    assert rec_sub == (x - y), "Subtraction over Z failed"
    
    # 4. Scalar Multiplication (x * k)
    k = 5
    sh_mul = SS.scalar_mul(sh_x, k)
    rec_mul = SS.reconstruct_Z(sh_mul)
    print(f"Scalar Mul ({x} * {k}) -> {rec_mul}")
    
    assert rec_mul == (x * k), "Scalar Mul over Z failed"
    
    print("SHARING Z: OK")


def test_sharing_over_modulo():
    """
    sharing over modulo Z_m. (s1 - s0) % m = x % m
    """
    
    M = 1000
    print(f"Modulus: {M}")
    
    # 1. Basic Sharing
    x = 12345 # x mod M = 345
    sh_x = SS.share_mod(x, M)
    
    print(f"Secret: {x} (mod M = {x%M})")
    print(f"Shares: s0={sh_x.s0}, s1={sh_x.s1}")
    
    rec_x = SS.reconstruct_mod(sh_x)
    print(f"Reconstructed: {rec_x}")
    
    assert rec_x == (x % M), "Reconstruction over Z_m failed"
    
    # 2. Homomorphic Addition
    y = 67890
    sh_y = SS.share_mod(y, M)
    
    sh_sum = SS.add(sh_x, sh_y)
    rec_sum = SS.reconstruct_mod(sh_sum)
    expected_sum = (x + y) % M
    print(f"Add ({x} + {y}) mod {M} -> {rec_sum}")
    
    assert rec_sum == expected_sum, "Addition over Z_m failed"
    
    # 3. Scalar Multiplication
    k = 3
    sh_mul = SS.scalar_mul(sh_x, k)
    rec_mul = SS.reconstruct_mod(sh_mul)
    expected_mul = (x * k) % M
    print(f"Scalar Mul ({x} * {k}) mod {M} -> {rec_mul}")
    
    assert rec_mul == expected_mul, "Scalar Mul over Z_m failed"

    print(">>> SHARING MODULO: OK")