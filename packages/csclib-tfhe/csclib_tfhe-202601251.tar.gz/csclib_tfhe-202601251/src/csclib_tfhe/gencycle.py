#python3 -m venv env
#source env/bin/activate
#maturin build --release
#pip install --force-reinstall ./rust/target/wheels/csclib_tfhe-*.whl 


from csclib_tfhe import * # ok
from csclib_tfhe.benes import ApplySwitch, butterfly, inv_butterfly, Benes_apply, AppPerm
from csclib_tfhe.pycsclib_tfhe import enc, enc_int, enc_array_int, enc_array, dec_array, blog
#import random

#def encrypt(x):
#  return tfhe.PyLweShort(x)

#def encrypt_int(x, bit):
#  return tfhe.PyLweInt(x, bit)

#def enc_array(arr, bit):
#  if bit == 0:
#    return [tfhe.PyLweShort(val) for val in arr]
#  else:
#    return [tfhe.PyLweInt(val, bit) for val in arr]

#def dec_array(arr):
#  return [val.dec() for val in arr]

#def blog(x):
#  l = -1
#  while x > 0:
#    x >>= 1
#    l += 1
#  return l

###################################################################
### GenCycleを表すBenesネットワークを構成
### 1 を右ローテイト（左ローテイトは作ったネットワークの inverse を使う）
### 0 - 0       0 - 0
### 0 - 0       0 - 0
###
### 1 - 1       1   1
###               x
### 1 - 1       1   1
###
### 0   1       0   1
###   x           x
### 1   0       1   0
###
### 1 - 1       1 - 1
### 0 - 0       0 - 0
###################################################################
def GenCycle_Benes_sub(X):
  n = len(X)
  if n == 2:
    Y = [None] * n
    c = X[0] & X[1]
    #print("X:", X)
    #print("c:", c)
    Y[0], Y[1] = ApplySwitch(c, X[0], X[1])
    #print("Y:", Y)
    return ([[c],[],[],[]], Y)

  SL = [None] * (n//2)
  SR = [None] * (n//2)
  i = 0
  while i < n//2:
    SL[i] = (~X[i*2]) & X[i*2+1] # pythonの ~ はビット反転なので注意
    SR[i] = X[i*2+1]
    i += 1

  W = [0] * n
  i = 0
  while i < n//2:
    W[i*2], W[i*2+1] = ApplySwitch(SL[i], X[i*2], X[i*2+1])
    i += 1
  Wp = butterfly(W)

  XU = Wp[0:n//2]
  XL = Wp[n//2:n]

  netU, ZU = GenCycle_Benes_sub(XU)
  netL = []
  ZL = XL

  Zp = ZU + ZL
  Z = inv_butterfly(Zp)

  Y = [None] * n
  i = 0
  while i < n//2:
    c = SR[i]
    Y[i*2], Y[i*2+1] = ApplySwitch(c, Z[i*2], Z[i*2+1])
    i += 1
  return ([SL, netU, netL, SR], Y)

def GenCycle_Benes(X):
  """X の GenCycle を表す Benes ネットワークを返す

  Args:
      X (0,1列): ビット列

  Returns:
      N (Benes): X の GenCycle を表す Benes ネットワーク
      Y (0,1列): ビット列 (不要?)
  """
  n = len(X)
  d = blog(n-1)+1
  m = 1 << d
  if n < m:
    X_ext = X + [enc(1)] * (m - n)
    N, Y_ext = GenCycle_Benes_sub(X_ext)
    Y = Y_ext[0:n]
  else:
    N, Y = GenCycle_Benes_sub(X)
  return N, Y


def PrefixSum(v):
  """整数配列の接頭辞和を計算 (その場所を含む)

  Args:
      v (整数配列): 整数の配列

  Returns:
      z (整数配列): 接頭辞和配列 (その場所を含む)
  """
  n = len(v)
  z = [None] * n
  s = enc_int(0, v[0].get_bit_size())
  for i in range(n):
    s = s + v[i]
    z[i] = s
  return z

###################################################################
### Propagate
###################################################################
def Propagate(g, v):
  """各グループの先頭の要素をコピーする

  Args:
      g (0,1列): グループベクトル
      v (整数配列): 整数配列

  Returns:
      v (整数配列): 整数配列
  """
  bit = v[0].get_bit_size()
  pi, _ = GenCycle_Benes(g)
  #print("v:", dec_array(v, bit))
  x = AppPerm(v, [pi], True)
  #print("x:", x)
  #x[0] = encrypt_int(0, bit)
  x[0] = enc_int(0, bit)
  #print("v:", dec_array(v, bit))
  #print("x:", dec_array(x, bit))
  v2 = [v[i] - x[i] for i in range(len(v))]
  z = PrefixSum(v2)
  return z


if __name__ == '__main__':

    X = [1, 0, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1]
    #X = [1, 0]
    #X = [random.randint(0, 1) for _ in range(16)]
    print("X:", X)
    X_enc = enc_array(X)
    net, Y_enc = GenCycle_Benes(X_enc)

    n = len(X)
    w = blog(n-1)+1

    A = [i for i in range(n)]
    A_enc = enc_array_int(A, w)
    print("A_enc", dec_array(A_enc))

    B = Benes_apply(A_enc, net)
    B_dec = dec_array(B)
    #print(B_dec)
    C = Benes_apply(A_enc, net, inverse=True)
    C_dec = dec_array(C)
    #print(C_dec)

    #print("Original X:", X)
    #print("Original A:", A)
    print("After Benes B:", B_dec)
    print("After Benes C:", C_dec)

    p = Propagate(X_enc, A_enc)
    p_dec = dec_array(p)
    print("After Propagate p:", p_dec)
