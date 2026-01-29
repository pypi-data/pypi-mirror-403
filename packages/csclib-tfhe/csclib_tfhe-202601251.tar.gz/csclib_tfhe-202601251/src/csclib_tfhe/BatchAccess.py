from csclib_tfhe import *
from csclib_tfhe.benes import Benes, Benes_apply, AppPerm
from csclib_tfhe.gencycle import Propagate
#from csclib_tfhe.pycsclib_tfhe import blog
from csclib_tfhe import LWE_TRUE, LWE_FALSE

def vneg(idx):
  N = len(idx)
  idx_neg = [None] * N
  for i in range(N):
    idx_neg[i] = LWE_TRUE - idx[i]
  return idx_neg

##########################################################################
### 配列の要素をまとめて取り出す． 
# v はアクセスしたい配列．長さ U
# idx は v のアクセスしたい要素の添え字の配列を 1 進数表現にしたもの（添え字は単調増加）．
# idx の値の最大値は len(v) 未満 
# idx 中の 0 の数は v の値域の大きさと等しい
# idx 中の 1 の数はアクセス回数
# 1進数表現とは，0^k 1 で整数 k を表す方法
##########################################################################
def BatchAccessUnary(v, idx):
  """配列の要素をまとめて取り出す

  Args:
      v (整数配列): アクセスしたい配列．長さ U
      idx (0,1列): v のアクセスしたい要素の添え字の配列を 1 進数表現にしたもの（添え字は単調増加）．
                    idx の値の最大値は len(v) 未満
                    idx 中の 0 の数は v の値域の大きさと等しい
                    idx 中の 1 の数はアクセス回数
                    1進数表現とは 0^k 1 で整数 k を表す方法

  Returns:
      W (整数配列): 取り出した要素の配列. 長さ |idx|-|v|
  >>> dec_array(BatchAccessUnary(enc_array_int([0,1,2,3,4,5,6,7], 3), enc_array([0,0,1,0,0,1,1,1,0,0,0,1,0])))
  [1, 3, 3, 3, 6]
  """
  U = len(v)
  N = len(idx)
  sigma, _ = Benes(idx)
  X = v + ([tfhe.PyLweInt(0, v[0].get_bit_size())] * (N-U))
  Y = AppPerm(X, [sigma], inverse=True)
  Z = Propagate(vneg(idx), Y)
  W = AppPerm(Z, [sigma], inverse=False)
  return W[U:]

if __name__ == '__main__':
#
#  X = [0,0,1,0,0,1,1,1,0,0,1,0,1,0,1,1]
#  n = len(X)
#  k = blog(n-1)+1
#  X_enc = [encrypt(x) for x in X]
#
#  V = [tfhe.PyLweInt(i, k) for i in range(8)]
#
#  W = BatchAccessUnary(V, X_enc)
#  print("W:", [wi.dec() for wi in W])
  import doctest
  from csclib_tfhe.pycsclib_tfhe import enc_array_int, enc_array, dec_array
  doctest.testmod()
