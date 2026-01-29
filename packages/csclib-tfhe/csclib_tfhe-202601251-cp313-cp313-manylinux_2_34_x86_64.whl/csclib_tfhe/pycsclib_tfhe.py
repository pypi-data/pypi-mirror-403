from csclib_tfhe import _csclib_tfhe as tfhe


def pylwe_xor_int(self, other):
  if type(other) == int: other = tfhe.PyLweInt(other, self.get_bit_size())
  return self.xor(other)
def pylwe_mod_int(self, other):
  if type(other) == int: other = tfhe.PyLweInt(other, self.get_bit_size())
  return self._mod(other)
def pylwe_eq_int(self, other):
  if type(other) == int: other = tfhe.PyLweInt(other, self.get_bit_size())
  return self.eq(other)
def pylwe_neq_int(self, other):
  if type(other) == int: other = tfhe.PyLweInt(other, self.get_bit_size())
  return self.__neq__(other)
def pylwe_lt_int(self, other):
  if type(other) == int: other = tfhe.PyLweInt(other, self.get_bit_size())
  return self.lt(other)
def pylwe_gt_int(self, other):
  if type(other) == int: other = tfhe.PyLweInt(other, self.get_bit_size())
  return self.gt(other)
def pylwe_add_int(self, other):
  if type(other) == int:
    if other < 0: other += (1 << self.get_bit_size())
    other = tfhe.PyLweInt(other, self.get_bit_size())
  if type(self) == int:
    if self < 0: self += (1 << other.get_bit_size())
    self = tfhe.PyLweInt(self, other.get_bit_size())
  return self.add(other)
def pylwe_sub_int(self, other):
  if type(other) == int:
    if other < 0: other += (1 << self.get_bit_size())
    other = tfhe.PyLweInt(other, self.get_bit_size())
  return self.sub(other)
def pylwe_array_int(x, k):
  return [tfhe.PyLweInt(xi, k) for xi in x]

def pylwe_mul_int(self, other):
  #if type(other) == int:
  #  if other < 0: other += (1 << self.get_bit_size())
  #  other = tfhe.PyLweInt(other, self.get_bit_size())
  #if type(self) == int:
  #  if self < 0: self += (1 << other.get_bit_size())
  #  self = tfhe.PyLweInt(self, other.get_bit_size())
  return self.mul(other)


tfhe.PyLweInt.__xor__ = pylwe_xor_int
tfhe.PyLweInt.__rxor__ = pylwe_xor_int
tfhe.PyLweInt.__mod__ = pylwe_mod_int
tfhe.PyLweInt.__eq__ = pylwe_eq_int
tfhe.PyLweInt.__neq__ = pylwe_neq_int
tfhe.PyLweInt.__lt__ = pylwe_lt_int
tfhe.PyLweInt.__gt__ = pylwe_gt_int
tfhe.PyLweInt.__add__ = pylwe_add_int
tfhe.PyLweInt.__radd__ = pylwe_add_int
tfhe.PyLweInt.__sub__ = pylwe_sub_int
tfhe.PyLweInt.array = pylwe_array_int

def pylwe_xor_short(self, other):
  if type(other) == int: other = tfhe.PyLweShort(other)
  return self.xor(other)
def pylwe_mod_short(self, other):
  if type(other) == int: other = tfhe.PyLweShort(other)
  return self._mod(other)
def pylwe_eq_short(self, other):
  if type(other) == int: other = tfhe.PyLweShort(other)
  return self.eq(other)
def pylwe_neq_short(self, other):
  if type(other) == int: other = tfhe.PyLweShort(other)
  return self.__neq__(other)
def pylwe_lt_short(self, other):
  if type(other) == int: other = tfhe.PyLweShort(other)
  return self.lt(other)
def pylwe_gt_short(self, other):
  if type(other) == int: other = tfhe.PyLweShort(other)
  return self.gt(other)
def pylwe_add_short(self, other):
  if type(other) == int:
    if other < 0: other += (1 << 2) # 2 が埋め込まれているので注意
    other = tfhe.PyLweShort(other)
  if type(self) == int:
    if self < 0: self += (1 << 2)
    self = tfhe.PyLweShort(self, other)
  return self.add(other)
def pylwe_sub_short(self, other):
  if type(other) == int:
    if other < 0: other += (1 << 2)
    other = tfhe.PyLweShort(other)
  return self.sub(other)
def pylwe_array_short(x):
  return [tfhe.PyLweShort(xi) for xi in x]
tfhe.PyLweShort.__xor__ = pylwe_xor_short
tfhe.PyLweShort.__rxor__ = pylwe_xor_short
tfhe.PyLweShort.__mod__ = pylwe_mod_short
tfhe.PyLweShort.__eq__ = pylwe_eq_short
tfhe.PyLweShort.__neq__ = pylwe_neq_short
tfhe.PyLweShort.__lt__ = pylwe_lt_short
tfhe.PyLweShort.__gt__ = pylwe_gt_short
tfhe.PyLweShort.__add__ = pylwe_add_short
tfhe.PyLweShort.__radd__ = pylwe_add_short
tfhe.PyLweShort.__sub__ = pylwe_sub_short
tfhe.PyLweShort.array = pylwe_array_short

def pylwe_slice(self, range_obj):
  #print("slice:", type(range_obj))
  if type(range_obj) == slice:
    #print(range_obj.start, range_obj.stop, range_obj.step)
    start, stop, step = range_obj.start, range_obj.stop, range_obj.step
    if range_obj.start is None:
      start = 0
    if range_obj.stop is None:
      stop = self.get_bit_size()
    if range_obj.step is None:
      step = 1
    return self.slice(start, stop, step)
  else:
    return self.getitem(range_obj)
tfhe.PyLweShortArray.__getitem__ = pylwe_slice
tfhe.PyLweIntArray.__getitem__ = pylwe_slice
tfhe.PyLweInt.__getitem__ = pylwe_slice

def blog(x):
  l = -1
  while x > 0:
    x >>= 1
    l += 1
  return l

def enc(x):
  return tfhe.PyLweShort(x)

def enc_int(x, bit):
  return tfhe.PyLweInt(x, bit)

def enc_packed(x, bit):
  return tfhe.PyLwePacked(x, bit)

def enc_array(arr):
    return [enc(val) for val in arr]

def enc_array_int(arr, bit):
    return [enc_int(val, bit) for val in arr]

def enc_array_packed(arr, bit):
    return [enc_packed(val, bit) for val in arr]

def dec_array(arr):
    return [val.dec() for val in arr]

def pylargelut_lookup(self, x):
  if type(x) == tfhe.PyLweInt:
    x = self.calibrate(x)
  return self.lookup(x)
tfhe.PyLargeLUT.__getitem__ = pylargelut_lookup

tfhe.PyLweShortArray.__len__ = lambda self: self.len()
tfhe.PyLweIntArray.__len__ = lambda self: self.len()

def pylwe_array_iter(self):
  for i in range(self.len()):
    yield self.getitem(i)

tfhe.PyLweIntArray.__iter__ = pylwe_array_iter
tfhe.PyLweShortArray.__iter__ = pylwe_array_iter

def pylweintarray_concat(self, other):
  if type(self) == int:
    self = tfhe.PyLweIntArray([self], other.get_bit_size())
  elif type(self) == list:
    if type(self[0]) == tfhe.PyLweInt:
      self = tfhe.PyLweIntArray(self)
    elif type(self[0]) == int:
      self = tfhe.PyLweIntArray(self, other.get_bit_size())

  if type(other) == tfhe.PyLweIntArray:
    return self.concat(other)
  if type(other) == list:
    if type(other[0]) == tfhe.PyLweInt:
      other = tfhe.PyLweIntArray(other)
      return self.concat(other)
    elif type(other[0]) == int:
      r = tfhe.PyLweIntArray(other, self.get_bit_size())
      return self.concat(r)
  raise TypeError("Unsupported type for concat:", type(other))

tfhe.PyLweIntArray.__matmul__ = pylweintarray_concat
tfhe.PyLweIntArray.__rmatmul__ = pylweintarray_concat


def pylweshortarray_concat(self, other):
  if type(self) == int:
    self = tfhe.PyLweShortArray([self], other.get_bit_size())
  elif type(self) == list:
    if type(self[0]) == tfhe.PyLweShort:
      #self = tfhe.PyLweShortArray.from_list(self)
      self = tfhe.PyLweShortArray(self)
    elif type(self[0]) == int:
      self = tfhe.PyLweShortArray(self, other.get_bit_size())

  if type(other) == tfhe.PyLweShortArray:
    return self.concat(other)
  if type(other) == list:
    if type(other[0]) == tfhe.PyLweShort:
      other = tfhe.PyLweShortArray(other)
      return self.concat(other)
    elif type(other[0]) == int:
      r = tfhe.PyLweShortArray(other, self.get_bit_size())
      return self.concat(r)
  raise TypeError("Unsupported type for concat:", type(other))

def pylweshortarray_mul(self, other):
  if type(other) != int:
    raise TypeError("Unsupported type for mul:", type(other))
  l = []
  for _ in range(other):
    l += self.v
  return tfhe.PyLweShortArray(l)


tfhe.PyLweShortArray.__matmul__ = pylweshortarray_concat
tfhe.PyLweShortArray.__rmatmul__ = pylweshortarray_concat

#tfhe.PyLweShortArray.__mul__ = pylweshortarray_mul
