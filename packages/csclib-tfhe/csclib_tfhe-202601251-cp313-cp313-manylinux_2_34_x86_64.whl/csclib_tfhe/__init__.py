#from csclib_tfhe import _csclib_tfhe as tfhe
#from . import pycsclib_tfhe

# csclib_tfhe._csclib_tfhe.PyLweInt
import csclib_tfhe._csclib_tfhe as tfhe
from . import pycsclib_tfhe
#from . import benes
#from . import LOUDS

LWE_TRUE = tfhe.PyLweShort(1)
LWE_FALSE = tfhe.PyLweShort(0)

print("csclib_tfhe imported")

