#python3 -m venv env
#source env/bin/activate
#maturin build --release
#pip install --force-reinstall ./rust/target/wheels/csclib_tfhe-*.whl 


from csclib_tfhe import *
from csclib_tfhe.benes import Benes, Benes_apply, Benes_to_Perm, Perm_to_Benes, Perm_to_Benes_1bit, AppPerm, ApplySwitch, encrypt, encrypt_int, blog

################################################################
### X の i 番目の 0 と i 番目の 1 を交換する置換を求める．
### 0 と 1 の数は同じとする．
### O(n log^2 n) 時間
################################################################
def zero_one_match(X):
  n = len(X)
  w = blog(n-1)+1
  N, Y = Benes(X, half=True)
  I = [tfhe.PyLweInt(i, w) for i in range(n)]
  I2 = Benes_apply(I, N, False)
  for i in range(n//2):
    tmp = I2[i]
    I2[i] = I2[n-1-i]
    I2[n-1-i] = tmp
  I3 = Benes_apply(I2, N, True)
  return I3

################################################################
### LOUDS 表現に関する演算
### 次数 d のノードは 1 0^d と表現される
### 先頭にダミーの 0 がついているとする (super root の次数)
### super root の 1 は省略されているとする
### 長さは 2n ビット (n はノード数)
################################################################



################################################################
### LOUDS表現された木構造 t とノードのラベル v から
### 各ノードの親ノードのラベルを返す
### t: LOUDS表現された木構造
### v: 各ノードのラベル（整数）
### z: 各ノードの親ノードのラベル
### 根ノードの id は 0 とする．全体で n ノード．t の長さは 2n ビット
### O(n log^2 n) 時間
################################################################
def LOUDS_parentlabel(t, v, r, sigma=None):
  """LOUDS表現された木構造 t とノードのラベル v から各ノードの親ノードのラベルを返す
     根ノードの id は 0 とする．全体で n ノード．t の長さは 2n ビット
     O(n log^2 n) 時間

  Args:
      t (0,1列): LOUDS表現
      v (整数配列): 各ノードの値
      r (整数): super rootの値
      sigma (整数配列, optional): t の配列表現

  Returns:
      z (整数配列): 各ノードの親の値
  >>> X = enc_array([0,1,0,0,0,1,0,0,0,1,1,0,1,1,0,0,1,1,1,1])
  >>> V = enc_array_int([0,1,2,3,4,5,6,7,8,9], 4)
  >>> P = LOUDS_parentlabel(X, V, enc_int(7, 4))
  >>> dec_array(P)
  [7, 0, 0, 0, 1, 1, 1, 3, 5, 5]
  """
  n = (len(t)+1)//2 # ノード数
  m = len(t)

  if sigma is None:
    N, _ = Benes(t)
    sigma = [N]

  k = v[0].get_bit_size()
  d = [encrypt_int(0, k)] * n + [v[0] - r] + [v[i+1] - v[i] for i in range(n-1)]
#  d = tfhe.PyLweIntArray(d)
  w = AppPerm(d, sigma, inverse=True)
  x = [None] * m
#  x = tfhe.PyLweIntArray([encrypt_int(0, k)] * m)
  x[0] = r
  for i in range(1, m):
    x[i] = x[i-1] + w[i]
  y = AppPerm(x, sigma)
  z = y[0:n]

  return z

################################################################
### O(n log^2 n) 時間
################################################################
def LOUDS_firstchildlabel(t, v, sigma=None):
  """LOUDS表現 t とノードの値 v から，各ノードの最初の子ノードの値を返す

  Args:
      t (0,1列): LOUDS表現
      v (整数配列): 各ノードの値
      sigma (整数配列, optional): t の配列表現

  Returns:
      z (整数配列): 各ノードの最初の子ノードの値
  >>> X = enc_array([0,1,0,0,0,1,0,0,0,1,1,0,1,1,0,0,1,1,1,1])
  >>> V = enc_array_int([0,1,2,3,4,5,6,7,8,9], 4)
  >>> P = LOUDS_firstchildlabel(X, V)
  >>> dec_array(P)
  [1, 4, 7, 7, 8, 8, 9, 9, 9, 9]
  """
  n = (len(t)+1)//2 # ノード数
  m = len(t)

  if sigma is None:
    N, _ = Benes(t)
    sigma = [N]

  k = v[0].get_bit_size()
  #d =  [v[i+1] - v[i] for i in range(n-1)] + [encrypt_int(0, k) - v[n-1]] + [encrypt_int(0, k)] * n
  d =  [v[i+1] - v[i] for i in range(n-1)] + [encrypt_int(0, k)] + [encrypt_int(0, k)] * n
#  d = tfhe.PyLweIntArray(d)
  w = AppPerm(d, sigma, inverse=True)
  x = [None] * m
#  x = tfhe.PyLweIntArray([encrypt_int(0, k)] * m)
  x[0] = v[0] + w[0]
  for i in range(1, m):
    x[i] = x[i-1] + w[i]
  y = AppPerm(x, sigma)
  z = [None] * n
#  z = tfhe.PyLweIntArray([encrypt_int(0, k)] * n)
  #for i in range(0, n):
  #  z[i] = y[i+n]
  z = y[n:m]

  return z



################################################################
### 親と最初の子ノードのインデックスを返す
### (unary表現をbinary表現に変換しているだけ)
### parent(0) = -1 とする
### O(n log^2 n) 時間
################################################################
def LOUDS_parent_firstchild(t, sigma=None):
  """親と最初の子ノードのインデックスを返す

  Args:
      t (0,1列): LOUDS表現
      sigma (整数配列, optional): t の配列表現
  Returns:
      p (整数配列): 各ノードの親の配列表現
      fc (整数配列): 各ノードの最初の子の配列表現
  >>> X = enc_array([0,1,0,0,0,1,0,0,0,1,1,0,1,1,0,0,1,1,1,1])
  >>> V = enc_array_int([0,1,2,3,4,5,6,7,8,9], 4)
  >>> p, q = LOUDS_parent_firstchild(X)
  >>> dec_array(p)
  [63, 0, 0, 0, 1, 1, 1, 3, 5, 5]
  >>> dec_array(q)
  [1, 4, 7, 7, 8, 8, 10, 10, 10, 10]
  """
  n = (len(t)+1)//2 # ノード数
  m = len(t)
  k = blog(m-1)+1

  if sigma is None:
    N, _ = Benes(t)
    sigma = [N]

#  id = [tfhe.PyLweInt(i, k) for i in range(m)]
#  sigma_inv = AppPerm(id, sigma)
  sigma_inv = Benes_to_Perm(sigma)

### firstchild(i) = rank0( select1(i+1) ) = select1(i+1) - i (i >= 0)
### parent(i) = rank1( select0(i+1) ) - 1 = select0(i+1) - i - 1 (i >= 0)
### sigma_inv = [select0(i+1)] + [select1(i+1)]
  p = [None] * n
#  p = tfhe.PyLweIntArray([encrypt_int(0, k)] * n)
  fc = [None] * n
#  fc = tfhe.PyLweIntArray([encrypt_int(0, k)] * n)
  for i in range(0, n):
    p[i] = sigma_inv[i] - (i + 1)
    fc[i] = sigma_inv[i+n] - i

  return p, fc


################################################################
### LOUDS表現 t から，縮約（親の親を新しい親にする）した木のLOUDS表現 t2 と
### その配列表現 rho を返す
### sigma は t の配列表現
### O(n log^2 n) 時間
################################################################
def LOUDS_contract(t, sigma=None):
  """LOUDS表現 t から縮約 (親の親を新しい親にする) した木のLOUDS表現 t2 とその配列表現 rho を返す
  Args:
      t (0,1列): LOUDS表現
      sigma (整数配列, optional): t の配列表現

  Returns:
      t2 (0,1列): LOUDS表現
      rho (整数配列): t2 の配列表現
  >>> X = enc_array([0,1,0,0,0,1,0,0,0,1,1,0,1,1,0,0,1,1,1,1])
  >>> t2, rho = LOUDS_contract(X)
  >>> dec_array(t2)
  [0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]
  >>> dec_array(rho)
  [0, 1, 2, 3, 5, 6, 7, 8, 10, 11, 4, 9, 12, 13, 14, 15, 16, 17, 18, 19]
  """
  if sigma is None:
    N, _ = Benes(t)
    sigma = [N]

  n = len(t)
  p, fc = LOUDS_parent_firstchild(t, sigma)
#  print("p:", [pi.dec() for pi in p])
#  print("fc:", [qi.dec() for qi in fc])

  #p2 = LOUDS_parentlabel(t, p, encrypt_int(0, p[0].get_bit_size()))
  p2 = LOUDS_parentlabel(t, p, p[0], sigma)
  fc2 = LOUDS_firstchildlabel(t, fc, sigma)
#  print("p2:", [pi.dec() for pi in p2])
#  print("fc2:", [qi.dec() for qi in fc2])
  rho = [None] * n
#  rho = tfhe.PyLweIntArray([tfhe.PyLweInt(0, p2[0].get_bit_size())] * n)
  for i in range(n//2):
    rho[i] = p2[i] + (i+1)
    rho[i + n//2] = fc2[i] + i
#  print("rho:", [ri.dec() for ri in rho])

#  tmp = [encrypt(0)] * (n//2) + [encrypt(1)] * (n//2)
#  t2 = AppPerm(tmp, Perm_to_Benes(rho))
#  return t2, rho

### rho を拡張して長さを2冪にする
  k = blog(n-1)+1
  m = 1 << k
  diff = (m - n)//2
  t2tmp = [encrypt(0)] * (m//2) + [encrypt(1)] * (m//2)
  if diff > 0:
    rhotmp = [encrypt_int(i, k) for i in range(0, diff)] + [x+diff for x in rho] + [encrypt_int(i, k) for i in range(n+diff, m)]
    t2 = AppPerm(t2tmp, [Perm_to_Benes_1bit(rhotmp)])
    t2 = t2[diff : diff + n]
  else:
    t2 = AppPerm(t2tmp, [Perm_to_Benes_1bit(rho)])

  return t2, rho

################################################################
### LOUDS表現 t とノードの値 v から，各ノードの子の値の和を返す
### sigma は t の配列表現
### O(n log^2 n) 時間
################################################################
def LOUDS_childlabelSum(t, v, sigma=None):
  """LOUDS表現 t とノードの値 v から，各ノードの子の値の和を返す

  Args:
      t (0,1列): LOUDS表現
      v (整数配列): 各ノードの値
      sigma (整数配列, optional): t の配列表現

  Returns:
      z (整数配列): 各ノードの子の値の和
  >>> X = enc_array([0,1,0,0,0,1,0,0,0,1,1,0,1,1,0,0,1,1,1,1])
  >>> v = enc_array_int([1,1,1,1,1,1,1,1,1,1], 4)
  >>> z = LOUDS_childlabelSum(X, v)
  >>> dec_array(z)
  [3, 3, 0, 1, 0, 2, 0, 0, 0, 0]
  """
  n = (len(t)+1)//2 # ノード数
  m = len(t)

  if sigma is None:
    N, _ = Benes(t)
    sigma = [N]

  k = v[0].get_bit_size()
  vp = v + [encrypt_int(0, k)] * n
  #vp = v @ ([encrypt_int(0, k)] * n)
  w = AppPerm(vp, sigma, inverse=True)
  x = [None] * m
#  x = tfhe.PyLweIntArray([encrypt_int(0, k)] * m)
  x[0] = w[0]
  for i in range(1, m):
    x[i] = x[i-1] + w[i]
  y = AppPerm(x, sigma)
  z = [None] * n
#  z = tfhe.PyLweIntArray([encrypt_int(0, k)] * n)
  for i in range(0, n-1):
    z[i] = y[i+1+n] - y[i+n]
  z[n-1] = v[0]
  for i in range(1, n):
    z[n-1] = z[n-1] + v[i]
  z[n-1] = z[n-1] - y[2*n-1]

  return z


flatten = lambda x: [z for y in x for z in (flatten(y) if hasattr(y, '__iter__') and not isinstance(y, str) else (y,))]
flatten_dec = lambda x: [z.dec() for y in x for z in (flatten(y) if hasattr(y, '__iter__') and not isinstance(y, str) else (y,))]

def LOUDS_contract_all(t):
  """LOUDS表現 t を繰り返し縮約していき，その過程で得られる LOUDS 表現と配列表現を返す
  Args:
      t (0,1列): LOUDS表現
  Returns:
      T (0,1列の配列): 縮約過程で得られる LOUDS 表現
      Sigma (整数配列の配列): 縮約過程で得られる配列表現
  >>> X = enc_array([0,1,0,0,0,1,0,0,0,1,1,0,1,1,0,0,1,1,1,1])
  >>> T_Sigma = LOUDS_contract_all(X)
  >>> z = LOUDS_PathSum(X_enc, v, T_Sigma)
  >>> dec_array(z)
  [1, 2, 2, 2, 3, 3, 3, 3, 4, 4]
  """
  n = len(t) // 2
  k = blog(n-1)+1

  T = [None] * k
  Sigma = [None] * k

  for r in range(0, k):
    N, _ = Benes(t)
    sigma = [N]
    T[r] = t
    Sigma[r] = sigma
    if r < k-1:    
      print("contract_all r:", r, flatten_dec(t))
      t, sigma_int = LOUDS_contract(t, sigma)
  return T, Sigma

################################################################
### LOUDS表現 t とノードの値 v から，根から各ノードへのパス上の値の和を返す
### sigma は t の配列表現
### O(n log^3 n) 時間
################################################################
def LOUDS_PathSum(t_, v, t_sigma=None):
  """LOUDS表現 t とノードの値 v から，根から各ノードへのパス上の値の和を返す
     O(n log^3 n) 時間

  Args:
      t (0,1列): LOUDS表現
      v (整数配列): 各ノードの値
      t_sigma (整数配列, 整数配列, optional): t と sigma を事前計算したもの

  Returns:
      z (整数配列): 各ノードの子の値の和
  >>> X = enc_array([0,1,0,0,0,1,0,0,0,1,1,0,1,1,0,0,1,1,1,1])
  >>> v = enc_array_int([1,1,1,1,1,1,1,1,1,1], 4)
  >>> z = LOUDS_PathSum(X, v)
  >>> dec_array(z)
  [1, 2, 2, 2, 3, 3, 3, 3, 4, 4]
  """
#  if sigma is None:
#    N, _ = Benes(t)
#    sigma = [N]
  t = t_.copy()

  n = len(t) // 2
  k = blog(n-1)+1
  z = v.copy()
  #z = v.dup()
  for r in range(0, k):
    #p = LOUDS_parentlabel(t, z, encrypt_int(0, v[0].get_bit_size()), sigma)
    if t_sigma is not None:
      t = t_sigma[0][r]
      sigma = t_sigma[1][r]
      print("PathSum r:", r, flatten_dec(t), flatten_dec(z))
      p = LOUDS_parentlabel(t, z, encrypt_int(0, v[0].get_bit_size()), sigma)
    else:
      N, _ = Benes(t)
      sigma = [N]
      print("PathSum r:", r, flatten_dec(t), flatten_dec(z))
      p = LOUDS_parentlabel(t, z, encrypt_int(0, v[0].get_bit_size()), sigma)
      t, sigma_int = LOUDS_contract(t, sigma)
    for i in range(n):
      z[i] = z[i] + p[i]
    #z = z + p
  return z

################################################################
### LOUDS表現 t とノードの値 v から，各ノードの子孫の値の和を返す
### sigma は t の配列表現
### O(n log^3 n) 時間
################################################################
def LOUDS_TreeSum(t_, v, t_sigma=None):
  """LOUDS表現 t とノードの値 v から，各ノードの子孫の値の和を返す
     sigma は t の配列表現
     O(n log^3 n) 時間
  Args:
      t (0,1列): LOUDS表現
      v (整数配列): 各ノードの値
      t_sigma (整数配列, 整数配列, optional): t と sigma を事前計算したもの

  Returns
      z (整数配列): 各ノードの子孫の値の和
  >>> X = enc_array([0,1,0,0,0,1,0,0,0,1,1,0,1,1,0,0,1,1,1,1])
  >>> v = enc_array_int([1,1,1,1,1,1,1,1,1,1], 4)
  >>> z = LOUDS_TreeSum(X, v)
  >>> dec_array(z)
  [10, 6, 1, 2, 1, 3, 1, 1, 1, 1]
  """
  t = t_.copy()

  n = len(t) // 2
  k = blog(n-1)+1
  z = v.copy()
  for r in range(0, k):
    #print("TreeSum r:", r, flatten_dec(t), flatten_dec(z))
    if t_sigma is not None:
      t = t_sigma[0][r]
      sigma = t_sigma[1][r]
      #print("TreeSum r:", r, flatten_dec(t), flatten_dec(z))
      s = LOUDS_childlabelSum(t, z, sigma)
    else:
      N, _ = Benes(t)
      sigma = [N]
      #print("TreeSum r:", r, flatten_dec(t), flatten_dec(z))
      s = LOUDS_childlabelSum(t, z, sigma)
      t, sigma_int = LOUDS_contract(t, sigma)
    for i in range(n):
      z[i] = z[i] + s[i]
    #z = z + s
  return z

################################################################
### LOUDS表現 t から，各ノードの深さを返す
### 根の深さは 1 とする
### sigma は t の配列表現
### O(n log^3 n) 時間
################################################################
def LOUDS_depth(t, t_sigma=None):
  """LOUDS表現 t から，各ノードの深さを返す
     根の深さは 1 とする
     sigma は t の配列表現
     O(n log^3 n) 時間
  >>> X = enc_array([0,1,0,0,0,1,0,0,0,1,1,0,1,1,0,0,1,1,1,1])
  >>> z = LOUDS_depth(X_enc)
  >>> dec_array(z)
  [1, 2, 2, 2, 3, 3, 3, 3, 4, 4]
  """
  n = (len(t)+1)//2 # ノード数
  k = blog(n+1-1)+1 # 値の範囲は [0,n]
  depth = [encrypt_int(1, k)] * n

  return LOUDS_PathSum(t, depth, t_sigma)

################################################################
def LOUDS_desc(t, t_sigma=None):
  """LOUDS表現 t とノードの値 v から，各ノードの子孫の数を返す
     sigma は t の配列表現
     O(n log^3 n) 時間
  >>> X = enc_array([0,1,0,0,0,1,0,0,0,1,1,0,1,1,0,0,1,1,1,1])
  >>> z = LOUDS_desc(X_enc)
  >>> dec_array(z)
  [10, 6, 1, 2, 1, 3, 1, 1, 1, 1]
  """
  n = (len(t)+1)//2 # ノード数
  k = blog(n+1-1)+1 # 値の範囲は [0,n]
  desc = [encrypt_int(1, k)] * n

  return LOUDS_TreeSum(t, desc, t_sigma)


if __name__ == '__main__':
  import doctest
  from csclib_tfhe.pycsclib_tfhe import enc_int, enc_array_int, enc_array, dec_array
  #doctest.testmod()

#  X = [0,1,0,0,0,1,0,0,0,1,1,0,1,1,0,0,1,1,1,1]
#  #X = [1,0,0,0,1,0,0,0,1,1,0,1,1,0,0,1,1,1,1]
  X = [0,1,0,0,1,0,1,1]
  n = len(X)
  k = blog(10)+1
  X_enc = [encrypt(x) for x in X]
#  X_enc = tfhe.PyLweShortArray([encrypt(x) for x in X])

#
#  V_enc = [tfhe.PyLweInt(i, k) for i in range((n+1)//2)]

#  P = LOUDS_parentlabel(X_enc, V_enc, encrypt_int(7, k))
#  print("P:", [pi.dec() for pi in P])

#  p, q = LOUDS_parent_firstchild(X_enc)
#  print("p:", [pi.dec() for pi in p])
#  print("q:", [qi.dec() for qi in q])

#  P = LOUDS_firstchildlabel(X_enc, V_enc)
#  print("P:", [pi.dec() for pi in P])

#  t2, rho = LOUDS_contract(X_enc)
#  print("rho:", [ri.dec() for ri in rho])
#  print("t2:", [ti.dec() for ti in t2])
#  print("X_enc:", [xi.dec() for xi in X_enc])

  v = [encrypt_int(1, k) for i in range(n//2)]
#  v = tfhe.PyLweIntArray(v)

  t_sigma = LOUDS_contract_all(X_enc)

  z = LOUDS_PathSum(X_enc, v, t_sigma)
  print("z:", [zi.dec() for zi in z])
#  print("X_enc:", [xi.dec() for xi in X_enc])
#  print("v:", [zi.dec() for zi in v])
#  z2 = LOUDS_childlabelSum(X_enc, v)
#  print("z2:", [zi.dec() for zi in z2])
#  z3 = LOUDS_TreeSum(X_enc, v)
#  print("z3:", [zi.dec() for zi in z3])
