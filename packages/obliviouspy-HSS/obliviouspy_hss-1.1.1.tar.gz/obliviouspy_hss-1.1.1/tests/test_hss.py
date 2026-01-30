import pytest
import random
import sys, os

sys.path.append(os.path.abspath("src"))

from oblivious.damgardjurik import DamgardJurik as DJ
from oblivious.distance import DistanceFunction
from oblivious.sharing import SecretSharing as SS

@pytest.fixture(scope="module")
def dj_setup():
    bits = 64
    s = 2
    pk, sk = DJ.keygen(bits, s)
    mod_plain = pk.N_pow_s
    mod_cipher = pk.N_pow_s_plus_1
    
    hss_key_d = DistanceFunction.generate_hss_key(sk, mod_plain)
    
    return {
        "pk": pk,
        "sk": sk,
        "d": hss_key_d,
        "mod_plain": mod_plain,
        "mod_cipher": mod_cipher,
        "s": s,
        "bits": bits
    }

def test_hss_key_properties(dj_setup):
    d = dj_setup["d"]
    phi = dj_setup["sk"].phi
    mod_plain = dj_setup["mod_plain"]
    
    assert d % phi == 0, "The key d must be 0 modulo φ(N)"
    assert d % mod_plain == 1, "the key d must be 1 modulo N^s"

def test_vole_correctness_deterministic(dj_setup):
    pk = dj_setup["pk"]
    d = dj_setup["d"]
    mod_cipher = dj_setup["mod_cipher"]
    mod_plain = dj_setup["mod_plain"]
    
    x = 123
    y = 456
    expected = (x * y) % mod_plain
    
    C_x = DJ.encrypt(pk, x)
    
    y_scaled = y * d
    y1 = y_scaled + 123456789 
    y0 = 123456789
    
    assert (y1 - y0) == y_scaled, "logic error in simulation of additive sharing"
    
    # 3. Valutazione Omomorfica
    C1 = pow(C_x, y1, mod_cipher)
    C0 = pow(C_x, y0, mod_cipher)
    
    # 4. Distance Function
    dist1 = DistanceFunction.evaluate(pk, C1)
    dist0 = DistanceFunction.evaluate(pk, C0)
    
    # 5. Verifica risultato
    result = (dist1 - dist0) % mod_plain
    
    assert result == expected, f"V-OLE faild: result: {result}, expected: {expected}"

@pytest.mark.parametrize("iteration", range(5))
def test_vole_randomized(dj_setup, iteration):
    pk = dj_setup["pk"]
    d = dj_setup["d"]
    mod_cipher = dj_setup["mod_cipher"]
    mod_plain = dj_setup["mod_plain"]
    bits = dj_setup["bits"]
    s = dj_setup["s"]
    

    limit = (pk.n.bit_length() * s) // 2 - 10
    x = random.getrandbits(limit)
    y = random.getrandbits(limit)
    
    expected = (x * y) % mod_plain
    
    # 1. Encrypt x
    C_x = DJ.encrypt(pk, x)
    
    # 2. Share y * d
    y_scaled = y * d
    
    r = random.getrandbits(bits * s + 50)
    y1 = r
    y0 = r - y_scaled
    
    # 3. Eval
    C1 = pow(C_x, y1, mod_cipher)
    C0 = pow(C_x, y0, mod_cipher)
    
    # 4. Dist
    dist1 = DistanceFunction.evaluate(pk, C1)
    dist0 = DistanceFunction.evaluate(pk, C0)
    
    # 5. Check
    result = (dist1 - dist0) % mod_plain
    
    assert result == expected, f"iteration {iteration}: V-OLE random faild with param x={x}, y={y}"

def test_homomorphic_properties_with_distance(dj_setup):
    pk = dj_setup["pk"]
    d = dj_setup["d"]
    mod_cipher = dj_setup["mod_cipher"]
    mod_plain = dj_setup["mod_plain"]
    
    x1 = 50
    x2 = 60
    y = 2
    
    c1 = DJ.encrypt(pk, x1)
    c2 = DJ.encrypt(pk, x2)
    
    #Enc(x1 + x2)
    c_sum = (c1 * c2) % mod_cipher
    
    # Mul with y
    y_scaled = y * d
    y1_share = random.getrandbits(100)
    y0_share = y1_share - y_scaled
    
    # Eval
    res_c1 = pow(c_sum, y1_share, mod_cipher)
    res_c0 = pow(c_sum, y0_share, mod_cipher)
    
    # Dist
    d1 = DistanceFunction.evaluate(pk, res_c1)
    d0 = DistanceFunction.evaluate(pk, res_c0)
    
    result = (d1 - d0) % mod_plain
    expected = ((x1 + x2) * y) % mod_plain
    
    assert result == expected, "Error in additive + V-OLE homomorphic property"