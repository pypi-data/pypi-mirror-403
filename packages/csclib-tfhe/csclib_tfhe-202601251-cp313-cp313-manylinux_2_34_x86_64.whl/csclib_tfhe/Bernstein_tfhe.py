#  An implementation of the control bits computation for Benes networks
#  based on Daniel J. Bernstein's paper
#@misc{cryptoeprint:2020/1493,
#      author = {Daniel J.  Bernstein},
#      title = {Verified fast formulas for control bits for permutation networks},
#      howpublished = {Cryptology {ePrint} Archive, Paper 2020/1493},
#      year = {2020},
#      url = {https://eprint.iacr.org/2020/1493}
#}



#python3 -m venv env
#source env/bin/activate
#maturin build --release
#pip install --force-reinstall ./rust/target/wheels/csclib_tfhe-*.whl 

#from csclib_tfhe import _csclib_tfhe as tfhe
from csclib_tfhe import *
from csclib_tfhe.benes import Benes_sort, AppPerm
from csclib_tfhe.pycsclib_tfhe import enc, enc_int, enc_array_int, enc_array, dec_array, blog

flatten = lambda x: [z for y in x for z in (flatten(y) if hasattr(y, '__iter__') and not isinstance(y, str) else (y,))]
flatten_dec = lambda x: [z.dec() for y in x for z in (flatten(y) if hasattr(y, '__iter__') and not isinstance(y, str) else (y,))]

def permutation(c):
    m = 1
    while (2*m-1)<<(m-1) < len(c): m += 1
    assert (2*m-1)<<(m-1) == len(c)
    n = 1<<m
    pi = list(range(n))
    pi = enc_array_int(pi, m)
    for i in range(2*m-1):
        gap = 1<<min(i,2*m-2-i)
        for j in range(n//2):
            #print("c[{}]: {}".format(i*n//2+j, c[i*n//2+j].dec()))
            pos = (j%gap)+2*gap*(j//gap)
            #if c[i*n//2+j] == encrypt_int(1, m, 1):
            #    pi[pos],pi[pos+gap] = pi[pos+gap],pi[pos]
            d = (c[i*n//2+j] == 1)
            pi[pos],pi[pos+gap] = d.cmux_int(pi[pos], pi[pos+gap])
    return pi

def composeinv(c,pi):
    #return [y for x,y in sorted(zip(pi,c))]
    print("composeinv input c:", flatten_dec(c))
    print("composeinv input pi:", flatten_dec(pi))
    n = len(pi)
    w = blog(n-1)+1
    sigma1, c1 = Benes_sort(c, w)
    pi2 = AppPerm(pi, sigma1, True)
    sigma2, pi3 = Benes_sort(pi2, w)
    y = AppPerm(c1, sigma2, True)
    print("y:", flatten_dec(y))
    return y


def lwe_min(x, y):
    if type(x) == int:
        x = enc_int(x, y.get_bit_size())
    elif type(y) == int:
        y = enc_int(y, x.get_bit_size())
    c = x < y
    return c.cmux_int(x, y)[0]

#def controlbits(pi):
def Perm_to_Benes(pi):
    n = len(pi)
    m = 1
    while 1<<m < n: m += 1
    assert 1<<m == n
    if m == 1: return [[pi[0]]]

    p = [pi[x^1] for x in range(n)]
    q = [pi[x]^1 for x in range(n)]
    range_n = [enc_int(x, m) for x in range(n)]
    piinv = composeinv(range_n,pi)
    p,q = composeinv(p,q),composeinv(q,p)

    #c = [lwe_min(encrypt_int(x, m), p[x]) for x in range(n)]
    c = [lwe_min(p[x], x) for x in range(n)]
    p,q = composeinv(p,q),composeinv(q,p)
    for i in range(1,m-1):
        cp,p,q = composeinv(c,q),composeinv(p,q),composeinv(q,p)
        c = [lwe_min(c[x],cp[x]) for x in range(n)]

    print("c:", [x.dec() for x in flatten(c)])
    f = [c[2*j] % 2 for j in range(n//2)]
    #F = [encrypt_int(x, m)^f[x//2] for x in range(n)]
    F = [x ^ f[x//2] for x in range(n)]
    Fpi = composeinv(F,piinv)
    l = [Fpi[2*k] % 2 for k in range(n//2)]
    #L = [encrypt_int(y, m)^l[y//2] for y in range(n)]
    L = [y ^ l[y//2] for y in range(n)]
    M = composeinv(Fpi,L)
    subM = [[M[2*j+e]>>1 for j in range(n//2)] for e in range(2)]
    print("subM:", flatten_dec(subM))
    #subz = map(Perm_to_Benes,subM)
    subz = [Perm_to_Benes(x) for x in subM]
    sz = []
    for i in range(len(subz[0])):
        sz.append([subz[j][i] for j in range(len(subz))])
    #z = [s for s0s1 in zip(*subz) for s in s0s1]
    #for s0s1 in zip(*subz):
    z = []
    for s0s1 in sz:
        #print("s0s1:", flatten_dec(s0s1))
        for s in s0s1:
            #print("s:", flatten_dec(s))
            z.append(s)
    print("z:", flatten_dec(z))
    return [f,z,l]

if __name__ == '__main__':
    pi = [3,2,1,0]
    n = len(pi)
    m = blog(n-1)+1
    pi_enc = enc_array_int(pi, m)
    c = Perm_to_Benes(pi_enc)
    print("c:", [x.dec() for x in flatten(c)])
    c = flatten(c)
    pi2 = permutation(c)
    pi2 = dec_array(pi2)
    print(pi2)
    assert pi2 == pi
