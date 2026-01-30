from .damgardjurik import DamgardJurikPublicKey, DamgardJurik
from .number import Number

class DistanceFunction:
    """
    Distance Function Damgard-Jurik.    
    Dist(c) = log( c * (c mod N)^-1 )
    """
    @staticmethod
    def evaluate(pk: DamgardJurikPublicKey, c: int) -> int:
        mod_cipher = pk.N_pow_s_plus_1 
        
        # h = c mod N
        h = c % pk.n
        
        #u = c / h  (in Z_{N^{s+1}}^*)
        h_inv = Number.modinv(h, mod_cipher)
        u = (c * h_inv) % mod_cipher
        
        # (m * d), 
        # e d = 1 mod N^s -> m
        return DamgardJurik._log(pk, u)

    @staticmethod
    def generate_hss_key(sk, N_pow_s):
        """
        Compute a d such that:
        d = 0 mod phi   (to remove the random noise r)
        d = 1 mod N^s   (to keep the message m intact)
        """
        phi = sk.phi
        
        # x = 0 mod phi
        # x = 1 mod N_pow_s
        
        # phi e N^s are coprims (phi has factorization (p-1, q-1); N has factorization p, q)
        M = phi * N_pow_s
        M1 = N_pow_s
        M2 = phi
        
        y1 = Number.modinv(M1, phi)
        y2 = Number.modinv(M2, N_pow_s)
        
        # CRT: x = (a1*M1*y1 + a2*M2*y2) mod M
        # a1=0, a2=1
        d = (1 * M2 * y2) % M
        
        return d