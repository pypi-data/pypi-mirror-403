#python3 -m venv env
#source env/bin/activate
#maturin build --release
#pip install --force-reinstall ./rust/target/wheels/csclib_tfhe-*.whl 


from csclib_tfhe import * # ok
from csclib_tfhe.benes import Benes, Benes_apply


###############################################################
### 各位置で，それより左の接頭辞での or を計算
###############################################################
def AllPrefixOr(X):
  """各位置で，それより左の接尾辞での or を計算 (その場所を含む)

  Args:
      X (0,1列): bit列

  Returns:
      (0,1列): 各位置での接尾辞 or
  """
  n = len(X)
  O = [None] * n
  r0 = LWE_FALSE
  for i in range(n):
    r0 = r0 | X[i]
    O[i] = r0
  return O

###############################################################
### 各位置で，それより右の接尾辞での or を計算
### （先頭は必ず 0 になる）
###############################################################
def AllSuffixOr(X, inclusive=False):
  """各位置で，それより右の接尾辞での or を計算

  Args:
      X (0,1列): bit列
      inclusive (bool, optional): True の場合，その場所を含んだ or を計算.  

  Returns:
      (0,1列): 各位置での接尾辞 or
  """
  n = len(X)
  O = [None] * n
  r = LWE_FALSE
  for i in range(n-1, -1, -1):
    if inclusive:
      r = r | X[i]
    O[i] = r
    if not inclusive:
      r = r | X[i]
  return O


################################################################
### w ビット整数 x の unit vector 表現を返す
### O(n) 時間
################################################################
def unitv(x):
    """w ビット整数 x の unit vector 表現を返す
       O(n) 時間

    Args:
        x (整数): w ビット整数

    Returns:
        F (0,1列): x の unit vector 表現 (F[x] = 1, その他 0)
    >>> dec_array(unitv(tfhe.PyLweInt(3, 3)))
    [0, 0, 0, 1, 0, 0, 0, 0]
    >>> dec_array(unitv(tfhe.PyLweInt(5, 3)))
    [0, 0, 0, 0, 0, 1, 0, 0]
    """
    w = x.get_bit_size()
    n = 1 << w

    x_bits = x.to_bit()

    F = [LWE_TRUE]
    for d in range(w):
        print("d:", d)
        s = 1 << d
        F_next = [None] * (s*2)
        b = x_bits[w-1-d]
        for i in range(s):
            F_next[2*i] = F[i] & ~b
            F_next[2*i+1] = F[i] & b
        F = F_next
    return F

################################################################
### w bit配列 V を整数 k だけ左回転
### O(wn log n) 時間
################################################################
def rotate_left(V, k):
    """w bit配列 V を整数 k だけ左回転
       O(wn log n) 時間

    Args:
        V (整数配列): w bit整数の配列
        k (整数): 回転量

    Returns:
        V_rot (整数配列): 左回転後の配列
    >>> dec_array(rotate_left(tfhe.PyLweInt.array([0,1,2,3,4,5,6,7], 3), tfhe.PyLweInt(2,3)))
    [2, 3, 4, 5, 6, 7, 0, 1]
    >>> dec_array(rotate_left(tfhe.PyLweInt.array([0,1,2,3,4,5,6,7], 3), tfhe.PyLweInt(5,3)))
    [5, 6, 7, 0, 1, 2, 3, 4]
    """
    n = len(V)
    u = unitv(k)
    o = AllSuffixOr(u)
    pi, _ = Benes(o)
    V_rot = Benes_apply(V, pi, False)
    return V_rot

################################################################
### w bit配列 V を整数 k だけ右回転
### O(wn log n) 時間
################################################################
def rotate_right(V, k):
    """w bit配列 V を整数 k だけ右回転
       O(wn log n) 時間

    Args:
        V (整数配列): w bit整数の配列
        k (整数): 回転量

    Returns:
        V_rot (整数配列): 右回転後の配列
    """
    n = len(V)
    u = unitv(k)
    o = AllSuffixOr(u)
    pi, _ = Benes(o)
    V_rot = Benes_apply(V, pi, True)
    return V_rot

def dec_array(arr):
  return [val.dec() for val in arr]

if __name__ == '__main__':
#
#    w = 3
#
#    A = [tfhe.PyLweInt(i, w) for i in range(1<<w)]
#
#    for x in range(1<<w):
#        print("x:", x)
#        y = rotate_right(A, tfhe.PyLweInt(x, w))
#        print("rol:", [val.dec() for val in y])
    import doctest
    doctest.testmod()
