#from benes import Benes
from csclib_tfhe import _csclib_tfhe as tfhe
from csclib_tfhe import LWE_FALSE, LWE_TRUE

def blog(x):
  l = -1
  while x > 0:
    x >>= 1
    l += 1
  return l

def encrypt(x):
  return tfhe.PyLweShort(x)
def encrypt_int(x, bit):
  return tfhe.PyLweInt(x, bit)

###################################################################
### 平文の整数配列を暗号化
### 整数は bit ビットで表現される
### bit == 0 の場合はブール値の配列とみなす
###################################################################
def enc_array(arr, bit):
  if bit == 0:
    return [tfhe.PyLweShort(val) for val in arr]
  else:
    return [tfhe.PyLwePacked(val, bit) for val in arr]

#def ApplySwitch(c, x, y):
#  if type(x) == int:
#    x = encrypt(x)
#  elif type(y) == int:
#    y = encrypt(y)
#  xp, yp = c.cmux(x, y)
#  return xp, yp

#def ApplySwitch_int(c, x, y):
#  if type(x) == int:
#    x = encrypt_int(x, y.get_bit_size())
#  elif type(y) == int:
#    y = encrypt_int(y, x.get_bit_size())
#  xp, yp = c.cmux_int(x, y)
#  return xp, yp

def ApplySwitch(c, x, y):
  if type(x) == tfhe.PyLweShort:
    if type(y) == int:
      y = encrypt(y)
    xp, yp = c.cmux(x, y)
  elif type(y) == tfhe.PyLweShort:
    if type(x) == int:
      x = encrypt(x)
    xp, yp = c.cmux(x, y)
  elif type(x) == tfhe.PyLweInt:
    if type(y) == int:
      y = encrypt_int(y, x.get_bit_size())
    xp, yp = c.cmux_int(x, y)
  elif type(y) == tfhe.PyLweInt:
    if type(x) == int:
      x = encrypt_int(x, y.get_bit_size())
    xp, yp = c.cmux_int(x, y)
  elif type(x) == tfhe.PyLwePacked:
    if type(y) == int:
      y = tfhe.PyLwePacked(y, x.get_bit_size())
    xp, yp = c.cmux_packed(x, y)
  elif type(y) == tfhe.PyLwePacked:
    if type(x) == int:
      x = tfhe.PyLwePacked(x, y.get_bit_size())
    xp, yp = c.cmux_packed(x, y)
  else:
    print("ApplySwitch: unsupported type:", type(x), type(y))
    raise TypeError("ApplySwitch: unsupported type")

  return xp, yp

def butterfly(X):
  n = len(X)
  Y = [None] * n
  for i in range(0,n//2):
    Y[i] = X[2*i]
    Y[i+n//2] = X[2*i+1]
  return Y

def inv_butterfly(X):
  n = len(X)
  Y = [None] * n
  for i in range(0,n//2):
    Y[i*2] = X[i]
    Y[i*2+1] = X[i+n//2]
  return Y

def AllPrefixSumMod2(X):
  n = len(X)
  rank = [None] * n
  r0 = LWE_FALSE
  i = 0
  while i < n:
    r0 = r0 ^ (~X[i])
    rank[i] = r0
    i += 1
  return rank

def Benes_sub(X, half = False):
  n = len(X)
  print("Benes_sub n:", n)
  if n == 2:
    Y = [None] * n
#    Y = tfhe.PyLweShortArray([encrypt(0)] * n)
    c = X[0] & (~X[1])
    Y[0], Y[1] = ApplySwitch(c, X[0], X[1])
    return ([[c],[],[],[]], Y)

  rank = AllPrefixSumMod2(X)
  SL = [None] * (n//2)
#  SL = tfhe.PyLweShortArray([encrypt(0)] * (n//2))
  i = 0
  while i < n//2:
    SL[i] = ~rank[i*2]
    i += 1
  SR = ~rank[n-1]

  W = [None] * n
#  W = tfhe.PyLweShortArray([encrypt(0)] * n)
  i = 0
  while i < n//2:
    W[i*2], W[i*2+1] = ApplySwitch(SL[i], X[i*2], X[i*2+1])
    i += 1
  Wp = butterfly(W)

  XU = Wp[0:n//2]
  XL = Wp[n//2:n]

  netU, ZU = Benes_sub(XU, half)
  netL, ZL = Benes_sub(XL, half)
  Zp = ZU + ZL

  SR_new = []
  if half == False:
    Z = inv_butterfly(Zp)
    Y = [0] * n
#    Y = tfhe.PyLweShortArray([encrypt(0)] * n)
    i = 0
    while i < n//2:
      c = SR & Z[i*2]
      Y[i*2], Y[i*2+1] = ApplySwitch(c, Z[i*2], Z[i*2+1])
      SR_new.append(c)
      i += 1
#    SR_new = tfhe.PyLweShortArray(SR_new)
  else:
    Y = Zp
  return ([SL, netU, netL, SR_new], Y)

def Benes(X, half = False):
  """ビット列の安定ソートを表すBenesネットワークを返す

  Args:
      X (0,1列): ビット列
      half (bool, optional): True の場合は，ネットワークの前半だけ計算 (0,1 の数が等しい場合に使用)

  Returns:
      N (Benes): 安定ソートを表すBenesネットワーク
      Y (0,1列): ソート後のビット列
  """
  n = len(X)
  d = blog(n-1)+1
  m = 1 << d
  if n < m:
    X_ext = X + [encrypt(1)] * (m - n)
#    print("X type:", type(X), X)
#    X_ext = X @ ([encrypt(1)] * (m - n))
    N, Y_ext = Benes_sub(X_ext, half)
    Y = Y_ext[0:n]
  else:
    N, Y = Benes_sub(X, half)
  return N, Y

def Benes_apply_sub(x, network, inverse: bool):
  n = len(x)
  x_new = x.copy()
  sl_tmp, netU, netL, sr_tmp = network

#  print("Benes_apply_sub n:", n)
#  print("sl_tmp:", [v.dec() for v in sl_tmp])

  if n > 2:
    if inverse:
      sl = sr_tmp
      sr = sl_tmp
    else:
      sl = sl_tmp
      sr = sr_tmp
    i = 0
    if sl != []:
      while i < n:
        c = sl[i//2]
        x_new[i], x_new[i+1] = ApplySwitch(c, x_new[i], x_new[i+1])
        i += 2
      x_tmp = butterfly(x_new)
    else:
      x_tmp = x_new
    if netU != []:
      x_tmp1 = Benes_apply_sub(x_tmp[0:n//2], netU, inverse)
    else:
      x_tmp1 = x_tmp[0:n//2]
    if netL != []:
      x_tmp2 = Benes_apply_sub(x_tmp[n//2:n], netL, inverse)
    else:
      x_tmp2 = x_tmp[n//2:n]

    x_new = x_tmp1 + x_tmp2
    if sr != []:
      x_new = inv_butterfly(x_new)

      i = 0
      while i < n:
        c = sr[i//2]
        x_new[i], x_new[i+1] = ApplySwitch(c, x_new[i], x_new[i+1])
        i += 2

  else: # n == 2
    if sl_tmp != []:
      x_new[0], x_new[1] = ApplySwitch(sl_tmp[0], x[0], x[1])
    elif sr_tmp != []:
      x_new[0], x_new[1] = ApplySwitch(sr_tmp[0], x[0], x[1]) # Benesネットワークが正規化されていれば不要だが念のため入れておく
    else:
      x_new = x
  return x_new

###################################################################
### w-bit整数の配列 X にBenesネットワークを適用
### O(wn log n) time
###################################################################
def Benes_apply(X, network, inverse = False):
  """w-bit整数の配列 X にBenesネットワークを適用
     O(wn log n) time

  Args:
      X (整数配列): w-bit整数の配列 
      network ([Benes]): Benesネットワークの配列
      inverse (bool, optional): True の場合は逆置換を計算

  Returns:
      X_new (整数配列): w-bit整数の配列を network で置換した配列
  """
  n = len(X)
  d = blog(n-1)+1
  m = 1 << d
  if n < m:
    if type(X[0]) == tfhe.PyLweInt:
      #X = X @ ([encrypt_int(0, X[0].get_bit_size())] * (m - n))
      X = X + ([encrypt_int(0, X[0].get_bit_size())] * (m - n))
    elif type(X[0]) == tfhe.PyLweShort:
      X = X + [encrypt(0)] * (m - n)
    elif type(X[0]) == tfhe.PyLwePacked:
      #X = X @ ([tfhe.PyLwePacked(0, X[0].get_bit_size())] * (m - n))
      X = X + ([tfhe.PyLwePacked(0, X[0].get_bit_size())] * (m - n))

  X_new = Benes_apply_sub(X, network, inverse)
  X_new = X_new[0:n]
  return X_new

###################################################################
### ビットの配列で表された置換を 1 個のBenesネットワークに変換
###################################################################
def Bit_to_Benes(b):
  """ビットの配列で表された置換を 1 個のBenesネットワークに変換

  Args:
      b (0,1列): ビット列

  Returns:
      [Benes]: b の安定ソートを表す Benes ネットワークの配列(長さ 1)
  """
  net, _ = Benes(b)
  return [net]

###################################################################
### 整数の配列で表された置換を log n 個のBenesネットワークに変換
### O(n log^3 n) time
###################################################################
def Perm_to_Benes(perm):
  """整数の配列で表された置換を log n 個のBenesネットワークに変換
     O(n log^3 n) time

  Args:
      perm (整数配列): 置換の配列表現

  Returns:
      N ([Benes]): 置換のBenesネットワーク表現
  """
  n = len(perm)
  w = blog(n-1)+1
  N = [None] * w
  perm_new = perm.copy()
  for k in range(w):
    print("Perm to Benes step:", k)
    b = [None] * n
    for i in range(n):
      b[i] = perm_new[i][k] # k ビット目を取り出す
    net, _ = Benes(b)
    N[k] = net
    perm_new = Benes_apply(perm_new, net, False) # O(n log^2 n) time
  return N

###################################################################
### wビット整数の配列 X をソートする w 個のBenesネットワークを求める
### O(w^2n log n) time
###################################################################
def Benes_sort(X, w):
  """wビット整数の配列 X をソートする w 個のBenesネットワークを求める
     O(w^2n log n) time

  Args:
      X (整数配列): ソートする配列
      w (整数(平文)): X のビット数

  Returns:
      N ([Benes]): X をソートする w 個のBenesネットワークの配列
      X_new (整数配列): ソートされた配列
  """
  n = len(X)
  N = [None] * w
  X_new = X.copy()
  for k in range(w):
    #print("Benes_sort step:", k)
    b = [None] * n
    for i in range(n):
      b[i] = X_new[i][k]
    net, _ = Benes(b)
    N[k] = net
    X_new = Benes_apply(X_new, net, False) # O(wn log n) time
  return N, X_new

###################################################################
### k 個のBenesネットワークで表された置換をw-bit整数の配列 x に適用
### (置換の場合は k = log n)
### inverse == True の場合は逆置換を計算
### O(kwn log n) time
###################################################################
def AppPerm(x, N, inverse = False):
  """k 個のBenesネットワークで表された置換をw-bit整数の配列 x に適用
     (置換の場合は k = log n)
     O(kwn log n) time
  Args:
      x (整数配列): 置換を適用する配列
      N ([Benes]): k 個のBenesネットワークで表された置換
      inverse (bool, optional): True の場合は逆置換を計算

  Returns:
      整数配列: Nで表された置換を x に適用した配列
  """
  n = len(x)
  #k = blog(n-1)+1
  k = len(N)
  print("AppPerm: x =", type(x[0]))
  if type(x[0]) == tfhe.PyLweInt:
    t = 1
  elif type(x[0]) == tfhe.PyLweShort:
    t = 2
#    x = [v.to_packed() for v in x]
  else:
    print("AppPerm: unsupported type:", type(x[0]))
  #x = [v.to_packed() for v in x]
  if inverse:
    for i in reversed(range(k)):
      print("AppPerm step:", i)
      x = Benes_apply(x, N[i], inverse)
  else:
    for i in range(k):
      print("AppPerm step:", i)
      x = Benes_apply(x, N[i], inverse)
#  if t == 2:
#    x = [v.to_short() for v in x]
  #else:
  #  x = [v.to_short() for v in x]
  return x

###################################################################
### Benesネットワークで表された置換の逆置換を表すBenesネットワークを返す
###################################################################
def Benes_inverse(N):
  """Benesネットワークで表された置換の逆置換を表すBenesネットワークを返す

  Args:
      N (Benes): Benesネットワーク

  Returns:
      N_inv (Benes): 逆置換のBenesネットワーク
  """
  if N == []:
    return []
  sl, netU, netL, sr = N
  if netU == [] and netL == [] and sr == []:
    return [sl, [], [], []] # n == 2 の場合，SL のみで表される
  return [sr, Benes_inverse(netU), Benes_inverse(netL), sl]

###################################################################
### k 個のBenesネットワークで表された置換の逆置換を表すBenesネットワークの配列を返す
###################################################################
def Perm_inverse(N):
  """k 個のBenesネットワークで表された置換の逆置換を表すBenesネットワークの配列を返す

  Args:
      N ([Benes]): Benesネットワークの配列

  Returns:
      N_inv ([Benes]): 逆置換のBenesネットワークの配列
  """
  k = len(N)
  N_inv = [None] * k
  for i in range(k):
    N_inv[i] = Benes_inverse(N[k-1-i])
  return N_inv


###################################################################
### k 個のBenesネットワークで表された置換を整数の配列に変換 (k <= log n)
### inverse == True の場合は逆置換を計算
### O(kn log^2 n) time
###################################################################
def Benes_to_Perm(N, inverse = False):
  """k 個のBenesネットワークで表された置換を整数の配列に変換
     k <= log n

  Args:
      N ([Benes]): Benesネットワークの配列
      inverse (bool, optional): True の場合は逆置換を計算

  Returns:
      pi (整数配列): Nで表された置換の配列表現
  """
  n = len(N[0][0])*2
  w = blog(n-1)+1
  id = [encrypt_int(i, w) for i in range(n)]
  pi = AppPerm(id, N, inverse)
  return pi

###################################################################
### 配列で表された置換と (log n 個の) Benesネットワークで表された置換を合成した置換を表す配列を計算
### (Benesネットワークに変換するには Perm_to_Benes を使う)
### O(n log^3 n) time
###################################################################
def Compose(pi, N, inverse = False):
  sigma = AppPerm(pi, N, inverse)
  return sigma

###############################################################
### 各位置で，それより左の接頭辞での or を計算
### （先頭は必ず 0 になる）
###############################################################
#def AllPrefixOr(X, inclusive=False):
#  n = len(X)
#  O = [None] * n
#  r = LWE_FALSE
#  for i in range(n):
#    if inclusive:
#      r = r | X[i]
#    O[i] = r
#    if not inclusive:
#      r = r | X[i]
#  return O

###############################################################
### 各位置で，それより右の接尾辞での or を計算
### （先頭は必ず 0 になる）
###############################################################
#def AllSuffixOr(X, inclusive=False):
#  n = len(X)
#  O = [None] * n
#  r = LWE_FALSE
#  for i in range(n-1, -1, -1):
#    if inclusive:
#      r = r | X[i]
#    O[i] = r
#    if not inclusive:
#      r = r | X[i]
#  return O

################################################################
### w ビット整数 x の unit vector 表現を返す
### O(n) 時間
################################################################
#def unitv(x):
#    w = x.get_bit_size()
#    n = 1 << w
#
#    x_bits = x.to_bit()
#
#    F = [LWE_TRUE]
#    for d in range(w):
#        s = 1 << d
#        F_next = [None] * (s*2)
#        b = x_bits[w-1-d]
#        for i in range(s):
#            F_next[2*i] = F[i] & ~b
#            F_next[2*i+1] = F[i] & b
#        F = F_next
#    return F

################################################################
### w bit配列 V を整数 k だけ左回転
### O(wn log n) 時間
################################################################
#def rotate_left(V, k):
#    n = len(V)
#    u = unitv(k)
#    o = AllSuffixOr(u)
#    pi, _ = Benes(o)
#    V_rot = Benes_apply(V, pi, False)
#    return V_rot

################################################################
### w bit配列 V を整数 k だけ右回転
### O(wn log n) 時間
################################################################
#def rotate_right(V, k):
#    n = len(V)
#    u = unitv(k)
#    o = AllSuffixOr(u)
#    pi, _ = Benes(o)
#    V_rot = Benes_apply(V, pi, True)
#    return V_rot

def rlex(x, d):
  if d == 0:
    return x

  if (x >> d) & 1: # 下半分
    x = x ^ 1
  if x & 1 == 1:
    return rlex(x // 2, d - 1) + (1 << d)
  else:
    return rlex(x // 2, d - 1)

def inv_butterfly2(X, pos, length):
  Y = [None] * length
  for i in range(0,length//2):
    Y[i*2] = X[pos + i]
    Y[i*2+1] = X[pos + i+length//2]
  for i in range(length):
    X[pos + i] = Y[i]

#################################################################
### スイッチを再帰的な表現に変換
#################################################################
def Perm_to_Benes_1bit_sub(S):
  k = len(S)
  if k == 1:
    return [S[0], [], [], []]
  n = len(S[0])
  SL = S[0]
  U = [None] * (k-1)
  L = [None] * (k-1)
  SR = [encrypt(0)] * (n//2) + [encrypt(1)] * (n//2)
  for i in range(k-1):
    U[i] = S[i+1][0:n//2]
    L[i] = S[i+1][n//2:n]
  NU = Perm_to_Benes_1bit_sub(U)
  NL = Perm_to_Benes_1bit_sub(L)

  N = [SL, NU, NL, SR]
  return N

#################################################################
### 0,1 列の安定ソートを表す置換の配列表現から Benes ネットワークを求める
### 0 と 1 の数は同じとする
### 配列の長さは2冪とする
### 入力 X: 置換を表す配列
### 出力 N: 置換 X の Benes ネットワーク表現
### O(n log^2 n) 時間
#################################################################
def Perm_to_Benes_1bit(X):
  """0,1 列の安定ソートを表す置換の配列表現から Benes ネットワークを求める
     0 と 1 の数は同じとする
     配列の長さは2冪とする
     O(n log^2 n) 時間

  Args:
      X (整数配列): 置換を表す配列

  Raises:
      ValueError: X の長さが2冪でない場合

  Returns:
      N (Benes): 置換 X の Benes ネットワーク表現
  """
  n0 = len(X)
  k = blog(n0-1)+1
  m = 1 << k
  n = n0
  if n < m:
  #  raise ValueError("Perm_to_Benes_1bit: length of X must be a power of 2")
    tmp = []
    for i in range(m-n):
      tmp.append(encrypt_int(n+i, k))
    X = X + tmp
  Y = [None] * m
  for i in range(m):
    Y[rlex(i, k-1)] = X[i]
  #print("Y:", [yi.dec() for yi in Y])

  S = [None] * k

  for d in range(k-1, -1, -1):
    S[d] = []
    for i in range(m//2):
      y = Y[2*i]
      #c = (y >> d) & 1
      c = y[d]
      S[d].append(c)
      Y[2*i], Y[2*i+1] = ApplySwitch(c, Y[2*i], Y[2*i+1])
    if d == 0:
      break
    pos = 0
    for g in range(1<<d-1):
      inv_butterfly2(Y, pos, (1<<k-d+1))
      pos += (1 << k-d+1)

  N = Perm_to_Benes_1bit_sub(S)
  return Benes_inverse(N)
#  return N

def Perm_to_Str_1bit(P):
  """0,1 列 X の安定ソートを表す置換の配列表現 P から X を求める
     0 と 1 の数は同じとする
     配列の長さは2冪とする
     O(n log n) 時間

  Args:
      P (整数配列): 置換を表す配列

  Returns:
      X (0,1列): 置換 P に対応する 0,1 列
  >>> P = enc_array_int([0, 4, 1, 2, 5, 6, 3, 7], 3)
  >>> X = Perm_to_Str_1bit(P)
  >>> dec_array(X)
  [0, 1, 0, 0, 1, 1, 0, 1]
  >>> N, _ = Benes(X)
  >>> Q = Benes_to_Perm([N])
  >>> dec_array(Q)
  [0, 2, 3, 6, 1, 4, 5, 7]
  """ 
  n = len(P)
  k = blog(n-1)+1
  Q = [encrypt_int(i, k) for i in range(n)]
  X = [None] * n
  for i in range(n):
    if i < n//2:
      #lt = Q[i] < P[i]
      #c = lt
      c = Q[i] < P[i]
    else:
      #lt = Q[i] < P[i]
      #eq = Q[i] == P[i]
      #c = lt | eq
      c = Q[i] <= P[i]
    X[i] = c
  return X

####################################################################
def convert_vecbenes_to_Benes(N):
#  print("convert_vecbenes_to_Benes:")
#  print("N len:", N.get_len())
#  print("network:", [v.dec() for v in N.get_v()])
  network = N.get_v()
  nlen = N.get_len()

  sl_len = nlen[0]
  if sl_len == 1:
#    print("switch_c: ")
#    for l in network:
#        print("{} ", l.dec())
#    print("\n")
    return [network, [], [], []]
  sr_len = nlen[1]
  if sr_len == 1:
#    print("switch_c: ")
#    for l in network:
#        print("{} ", l.dec())
#    print("\n")
    return [network, [], [], []]

  n1_len = nlen[2]
  n2_len = nlen[3]
  n1_llen = nlen[4]
  n2_llen = nlen[5]
  sl_pos = 0
  sr_pos = sl_pos + sl_len
  n1_pos = sr_pos + sr_len
  n2_pos = n1_pos + n1_len

  sl = network[sl_pos : (sl_pos + sl_len)]
  sr = network[sr_pos : (sr_pos + sr_len)]
#  print("sl_len:", sl_len, " sr_len:", sr_len, " n1_len:", n1_len, " n2_len:", n2_len)
#  print("sl: ")
#  for l in sl:
#      print("{} ", l.dec())
#  print("\n")
#  print("sr: ")
#  for l in sr:
#      print("{} ", l.dec())
#  print("\n")
  network1 = []
  if n1_len > 0:
    #print("network1: ")
    network1 = tfhe.PyVecBenes()
    network1.set(network[n1_pos:(n1_pos + n1_len)], nlen[6 : 6+n1_llen])
    #network1.v = network[n1_pos:(n1_pos + n1_len)]
    #network1.len = nlen[4:(4+n1_len)]
    network1 = convert_vecbenes_to_Benes(network1)
    #print("\n")

  network2 = []
  if n2_len > 0:
    #print("network2: ")
    network2 = tfhe.PyVecBenes()
    network2.set(network[n2_pos:(n2_pos + n2_len)], nlen[6+n1_llen : 6+n1_llen+n2_llen])
    #network2.v = network[n2_pos:(n2_pos + n2_len)]
    #network2.len = nlen[4+n1_len:(4+n1_len+n2_len)]
    network2 = convert_vecbenes_to_Benes(network2)
    #print("\n")

  return [sl, network1, network2, sr]


####################################################################

flatten = lambda x: [z for y in x for z in (flatten(y) if hasattr(y, '__iter__') and not isinstance(y, str) else (y,))]
flatten_dec = lambda x: [z.dec() for y in x for z in (flatten(y) if hasattr(y, '__iter__') and not isinstance(y, str) else (y,))]


if __name__ == '__main__':
#  import doctest
#  from csclib_tfhe.pycsclib_tfhe import enc_array_int, enc_array, dec_array
#  doctest.testmod()

#  k = 3
#  X = [0, 2, 3, 6, 1, 4, 5, 7]
#  X_enc = [encrypt_int(x, k) for x in X]
#  print("X:", [xi.dec() for xi in X_enc])
#  N = Perm_to_Benes_1bit(X_enc)
#  Y = [0, 1, 2, 3, 4, 5, 6, 7]
#  Y_enc = [encrypt_int(x, k) for x in Y]
#  Y_new = Benes_apply(Y_enc, N)
#  print("Y_new:", [xi.dec() for xi in Y_new])

  from csclib_tfhe.pycsclib_tfhe import enc_array_int, enc_array, dec_array
  P = enc_array_int([0, 4, 1, 2, 5, 6, 3, 7], 3)
  X = Perm_to_Str_1bit(P)
  print(dec_array(X))
  N, _ = Benes(X)
  Q = Benes_to_Perm([N])
  print(dec_array(Q))
  Q2 = Benes_to_Perm([N], inverse=True)
  print(dec_array(Q2))
  