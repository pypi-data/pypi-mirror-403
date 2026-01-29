use core::slice;

use pyo3::{panic, prelude::*};
//use tfhe::shortint::parameters::{PARAM_MESSAGE_2_CARRY_2_KS_PBS};
//use tfhe::core_crypto::prelude::LweCiphertextOwned;

mod algorithms;
mod arith;
mod keyswitch;
mod print;
use crate::algorithms::{TFHE_PARAMS, cmux_packed, lwe_encrypt};
use crate::algorithms::{LweShort, LweInt, LwePacked};
use crate::algorithms::{cmux_short, cmux_int, cmux_Int};
use crate::arith::{lwe_eq_int};


//#[pyclass]
//pub struct PyCiphertext {
//    pub v: LweCiphertextOwned<u64>,
//}

//#[pyclass]
//pub struct PyCiphertextVec {
//    pub v: Vec<LweCiphertextOwned<u64>>,
//}

#[derive(Clone)]
#[pyclass]
pub struct PyLweShort {
    pub v: LweShort,
}

#[derive(Clone)]
#[pyclass]
pub struct PyLweInt {
    pub v: LweInt,
}

#[pyclass]
pub struct PyLwePacked {
    pub v: LwePacked,
}


//#[pyfunction]
//pub fn generate_keys() -> PyResult<PyTfheParam> {
//    let tfhe_params = TfheParam::new_params(PARAM_MESSAGE_2_CARRY_2_KS_PBS);
//    Ok(PyTfheParam { tfhe_params: tfhe_params })
//}
#[pymethods]
impl PyLweShort {
    #[new]
    pub fn enc(v: u32) -> Self {
        let lwe_int = LweShort::new(v);
        Self { v: lwe_int }
    }
    pub fn dec(&self) -> u32 {
        self.v.dec() as u32
    }
    pub fn __str__(&self) -> String {
        return format!("[{}]", self.dec());
    }
    pub fn clone(&self) -> Self {
        Self {v: self.v.clone()}
    }
    //pub fn to_packed(&self) -> PyLwePacked {
    //    let packed = self.v.to_packed();
    //    PyLwePacked { v: packed }
    //}
    pub fn add(&self, other: &Self) -> Self {
        let (high, low) = self.v.addc(&other.v);
        Self {v: low}
    }
    pub fn addc(&self, other: &Self) -> (Self, Self) {
        let (high, low) = self.v.addc(&other.v);
        (Self {v: high}, Self {v: low})
    }
    pub fn __add__(&self, other: &Self) -> Self { // + operator
        self.add(&other)
    }
    pub fn sub(&self, other: &Self) -> Self {
        let (high, low) = self.v.subc(&other.v);
        Self {v: low}
    }
    pub fn subc(&self, other: &Self) -> (Self, Self) {
        let (high, low) = self.v.subc(&other.v);
        (Self {v: high}, Self {v: low})
    }
    pub fn __sub__(&self, other: &Self) -> Self { // - operator
        self.sub(&other)
    }
    pub fn lt(&self, other: &Self) -> Self {
        let (c, _) = self.subc(&other);
        c
    }
    pub fn __lt__(&self, other: &Self) -> Self { // < operator
        self.lt(&other)
    }
    pub fn ge(&self, other: &Self) -> Self {
        let (c, _) = self.subc(&other);
        c._not()
    }
    pub fn __ge__(&self, other: &Self) -> Self { // >= operator
        self.ge(&other)
    }
    pub fn gt(&self, other: &Self) -> Self {
        let (c, _) = other.subc(&self);
        c
    }
    pub fn __gt__(&self, other: &Self) -> Self { // > operator
        self.gt(&other)
    }
    pub fn le(&self, other: &Self) -> Self {
        let (c, _) = other.subc(&self);
        c._not()
    }
    pub fn __le__(&self, other: &Self) -> Self { // <= operator
        self.le(&other)
    }
    pub fn mul(&self, other: &Self) -> PyLweShort {
        let (high, low) = self.v.mul(&other.v);
        PyLweShort {v: low}
    }
    pub fn mulc(&self, other: &Self) -> (PyLweShort, PyLweShort) {
        let (high, low) = self.v.mul(&other.v);
        (PyLweShort {v: high}, PyLweShort {v: low})
    }
    pub fn __mul__(&self, other: &Self) -> PyLweShort { // * operator
        self.mul(&other)
    }
    pub fn __mod__(&self, other: &Self) -> Self {
        let v = self.v.__mod__(&other.v);
        Self {v: v}
    }
    pub fn _not(&self) -> Self {
        let result = self.v.not();
        Self {v: result}
    }
    pub fn __invert__(&self) -> Self { // ~ operator
        let result = self.v.not();
        Self {v: result}
    }
    pub fn xor(&self, other: &Self) -> Self {
        let result = self.v.xor(&other.v);
        Self {v: result}
    }
    pub fn __xor__(&self, other: &Self) -> Self { // ^ operator
        self.xor(other)
    }
    pub fn and(&self, other: &Self) -> Self {
        let result = self.v.and(&other.v);
        Self {v: result}
    }
    pub fn __and__(&self, other: &Self) -> Self { // & operator
        self.and(other)
    }
    pub fn or(&self, other: &Self) -> Self {
        let result = self.v.or(&other.v);
        Self {v: result}
    }
    pub fn __or__(&self, other: &Self) -> Self {
        self.or(other)
    }
    pub fn cmux(&self, x: &Self, y: &Self) -> (Self, Self) {
        let (res_x, res_y) = cmux_short(&self.v, &x.v, &y.v);
        (Self { v: res_x }, Self { v: res_y })
    }
    pub fn cmux_int(&self, x: &PyLweInt, y: &PyLweInt) -> (PyLweInt, PyLweInt) {
        let (res_x, res_y) = cmux_Int(&self.v, &x.v, &y.v);
        (PyLweInt { v: res_x }, PyLweInt { v: res_y })
    }
    pub fn cmux_packed(&self, x: &PyLwePacked, y: &PyLwePacked) -> (PyLwePacked, PyLwePacked) {
        let (res_x, res_y) = cmux_packed(&self.v, &x.v, &y.v);
        (PyLwePacked { v: res_x }, PyLwePacked { v: res_y })
    }

}


use crate::algorithms::{lwe_decrypt};

#[pymethods]
impl PyLweInt {
    #[new]
    pub fn enc(v: u32, bit_size: usize) -> Self {
        let lwe_int = LweInt::new(v, bit_size);
        Self { v: lwe_int }
    }
    pub fn dec(&self) -> u32 {
        self.v.dec() as u32
    }
    pub fn get_bit_size(&self) -> usize {
        self.v.bit_size
    }
    pub fn __str__(&self) -> String {
        return format!("[{}]", self.dec());
    }
    pub fn clone(&self) -> Self {
        Self {v: self.v.clone()}
    }
    pub fn geti(&self, ith: usize) -> PyLweShort {
        let result = self.v.geti(ith);
        PyLweShort {v: result}
    }
    pub fn getitem(&self, ith: usize) -> PyLweShort { // 2進表現での i ビット目 x[i] を得る
        let result = self.v.geti(ith);
        PyLweShort {v: result}
    }
    pub fn slice(&self, start: usize, stop: usize, step: usize) -> PyLweInt {
        let result = self.v.slice(start, stop, step);
        PyLweInt {v: result}
    }
    pub fn to_bit(&self) -> PyLweShortArray {
        let bits = self.v.to_bit();
        PyLweShortArray { v: bits }
    }
    pub fn to_packed(&self) -> PyLwePacked {
        let packed = self.v.to_packed();
        PyLwePacked { v: packed }
    }
    pub fn add(&self, other: &Self) -> PyLweInt {
        let (_, sum) = self.v.addc(&other.v);
        PyLweInt {v: sum}
    }
    pub fn addc(&self, other: &Self) -> (PyLweShort, PyLweInt) {
        let (c, sum) = self.v.addc(&other.v);
        (PyLweShort {v: c}, PyLweInt {v: sum})
    }
    pub fn __add__(&self, other: &Self) -> PyLweInt { // + operator
        self.add(&other)
    }
    pub fn sub(&self, other: &Self) -> PyLweInt {
        let (_, sum) = self.v.subc(&other.v);
        PyLweInt {v: sum}
    }
    pub fn subc(&self, other: &Self) -> (PyLweShort, PyLweInt) {
        let (c, sum) = self.v.subc(&other.v);
        (PyLweShort {v: c}, PyLweInt {v: sum})
    }
    pub fn __sub__(&self, other: &Self) -> PyLweInt { // - operator
        self.sub(&other)
    }
    pub fn eq(&self, other: &Self) -> PyLweShort {
        let v = self.v.eq(&other.v);
        PyLweShort {v: v}
    }
    pub fn __eq__(&self, other: &Self) -> PyLweShort { // == operator
        self.eq(&other)
    }
    pub fn __neq__(&self, other: &Self) -> PyLweShort { // != operator
        self.eq(&other)._not()
    }
    pub fn lt(&self, other: &Self) -> PyLweShort {
        let (c, _) = self.subc(&other);
        c
    }
    pub fn __lt__(&self, other: &Self) -> PyLweShort { // < operator
        self.lt(&other)
    }
    pub fn ge(&self, other: &Self) -> PyLweShort {
        let (c, _) = self.subc(&other);
        c._not()
    }
    pub fn __ge__(&self, other: &Self) -> PyLweShort { // >= operator
        self.ge(&other)
    }
    pub fn gt(&self, other: &Self) -> PyLweShort {
        let (c, _) = other.subc(&self);
        c
    }
    pub fn __gt__(&self, other: &Self) -> PyLweShort { // > operator
        self.gt(&other)
    }
    pub fn le(&self, other: &Self) -> PyLweShort {
        let (c, _) = other.subc(&self);
        c._not()
    }
    pub fn __le__(&self, other: &Self) -> PyLweShort { // <= operator
        self.le(&other)
    }
    pub fn xor(&self, other: &Self) -> Self {
        let v = self.v.__xor__(&other.v);
        Self {v: v}
    }
    pub fn __xor__(&self, other: &Self) -> Self {
        self.xor(&other)
    }
    pub fn _mod(&self, other: &Self) -> Self {
        let v = self.v.__mod__(&other.v);
        Self {v: v}
    }
    pub fn __mod__(&self, other: &Self) -> Self {
        self._mod(&other)
    }
    pub fn lshift(&self, shift: usize) -> Self {
        let v = self.v.lshift(shift);
        Self {v: v}
    }
    pub fn __lshift__(&self, shift: usize) -> Self {
        self.lshift(shift)
    }
    pub fn rshift(&self, shift: usize) -> Self {
        let v = self.v.rshift(shift);
        Self {v: v}
    }
    pub fn __rshift__(&self, shift: usize) -> Self {
        self.rshift(shift)
    }
    pub fn mul(&self, other: &Self) -> Self {
        let v = self.v.mul(&other.v);
        Self {v: v}
    }
    pub fn __mul__(&self, other: &Self) -> Self {
        self.mul(other)
    }


}

#[pymethods]
impl PyLwePacked {
    #[new]
    pub fn enc(v: u32, bit_size: usize) -> Self {
        let lwe_int = LwePacked::new(v, bit_size);
        Self { v: lwe_int }
    }
    pub fn dec(&self) -> u32 {
        self.v.dec() as u32
    }
    pub fn __str__(&self) -> String {
        return format!("[{}]", self.dec());
    }
    pub fn clone(&self) -> Self {
        Self {v: self.v.clone()}
    }
    pub fn get_bit_size(&self) -> usize {
        self.v.bit_size
    }
    pub fn geti(&self, ith: usize) -> PyLweShort {
        let result = self.v.geti(ith);
        PyLweShort {v: result}
    }
    pub fn __getitem__(&self, ith: usize) -> PyLweShort { // 2進表現での i ビット目 x[i] を得る
        let result = self.v.geti(ith);
        PyLweShort {v: result}
    }
    pub fn to_bit(&self) -> Vec<PyLweShort> {
        let bits = self.v.to_bit();
        bits
            .into_iter()
            .map(|b| PyLweShort { v: b })
            .collect()
    }
    pub fn to_int(&self) -> PyLweInt {
        let v = self.v.to_int();
        PyLweInt { v: v }
    }
}



#[pyfunction]
pub fn bit_decomposition_int(x: &PyLweInt) -> PyResult<PyLweInt> {
    let v = algorithms::lwe_bit_decomposition_int(&x.v.x, x.v.bit_size);
    Ok(PyLweInt { v: LweInt{x: v, bit_size: x.v.bit_size} })
}

#[pyfunction]
pub fn bit_composition_int(x: &PyLweInt) -> PyResult<PyLweInt> {
    let v = algorithms::lwe_bit_composition_int(&x.v.x);
    Ok(PyLweInt { v: LweInt{x: v, bit_size: x.v.bit_size} })
}

#[pyfunction]
pub fn getparams() -> String {
        TFHE_PARAMS.with(|params| {
            let tfhe_params = params.borrow();
            let lwe_dimension = tfhe_params.lwe_dimension;
            let glwe_dimension = tfhe_params.glwe_dimension;
            let polynomial_size = tfhe_params.polynomial_size;
            let lwe_std_dev = tfhe_params.lwe_noise_distribution;
            let glwe_std_dev = tfhe_params.glwe_noise_distribution;
            return format!("LweShort params LWE degree: {}, GLWE degree: {}, GLWE poly degree: {}, LWE std dev: {}, GLWE std dev: {}", 
                lwe_dimension.0,
                glwe_dimension.0,
                polynomial_size.0,
                lwe_std_dev,
                glwe_std_dev
            );
        })
}

mod benes;
//use benes::*;

use crate::benes::{benes_construct, BenesNetworkEnum};

pub fn benes_to_vec(network: &BenesNetworkEnum) -> Vec<LweShort> {
    let mut result: Vec<LweShort> = Vec::new();
    match network {
        BenesNetworkEnum::Nested(network_nested) => {
            let switch_l: Vec<LweShort> = network_nested.switch_l.clone().into();
            let switch_r: Vec<LweShort> = network_nested.switch_r.clone().into();
            result.extend_from_slice(&switch_l);
            result.extend_from_slice(&switch_r);

            let network1 = &network_nested.network1;
            let network2 = &network_nested.network2;

            result.extend_from_slice(&benes_to_vec(&network1));
            result.extend_from_slice(&benes_to_vec(&network2));
        },
        BenesNetworkEnum::NoNest(network_nonest) => {
            let switch_l = network_nonest.switch_l.clone();
            if let Some(switch_l_vec) = switch_l {
                let sl = switch_l_vec[0].clone();
                result.push(sl);
            } else {
                panic!("switch_l is None");
            }
        },
    }
    return result;
}

#[pyclass]
pub struct PyVecBenes {
    pub v: Vec<LweShort>,
    pub len: Vec<usize>,
}

#[pymethods]
impl PyVecBenes {
    #[new]
    pub fn new() -> Self {
        Self { v: Vec::new(), len: Vec::new()  }
    }
/* 
    pub fn new(v: Vec<PyLweShort>, len: Vec<usize>) -> Self {
        Self{v: v
            .into_iter()
            .map(|b| b.v)
            .collect(),
            len: len}
    }
*/
    pub fn set(&mut self, v: Vec<PyLweShort>, len: Vec<usize>) {
        self.v = v
            .into_iter()
            .map(|b| b.v)
            .collect();
        self.len = len;
    }
    pub fn get_len(&self) -> Vec<usize> {
        self.len.clone()
    }
    pub fn get_v(&self) -> Vec<PyLweShort> {
        self.v.clone()
            .into_iter()
            .map(|b| PyLweShort { v: b })
            .collect()
    }
}

pub fn benes_to_vec2(network: &BenesNetworkEnum) -> PyVecBenes {
    let mut result = PyVecBenes::new();
    match network {
        BenesNetworkEnum::Nested(network_nested) => {
            let switch_l = network_nested.switch_l.clone();
            let switch_r = network_nested.switch_r.clone();
            result.v.extend_from_slice(&switch_l);
            result.v.extend_from_slice(&switch_r);
            result.len.push(switch_l.len());
            result.len.push(switch_r.len());

            let network1 = &network_nested.network1;
            let network2 = &network_nested.network2;

            let n1 = benes_to_vec2(&network1);
            let n2 = benes_to_vec2(&network2);

            result.len.push(n1.v.len());
            result.len.push(n2.v.len());
            result.len.push(n1.len.len());
            result.len.push(n2.len.len());
            result.len.extend_from_slice(&n1.len);
            result.len.extend_from_slice(&n2.len);
            result.v.extend_from_slice(&n1.v);
            result.v.extend_from_slice(&n2.v);

        },
        BenesNetworkEnum::NoNest(network_nonest) => {
            let switch_l = network_nonest.switch_l.clone();
            if let Some(switch_l_vec) = switch_l {
                let sl = switch_l_vec[0].clone();
                result.v.push(sl);
                result.len.push(1);
                //result.len.push(0);
                //result.len.push(0);
                //result.len.push(0);

            } else {
                panic!("switch_l is None");
            }
        },
    }
    return result;
}

pub fn vec2_print(network: &PyVecBenes) {
    if network.len.len() < 4 {
        print!("switch_c: ");
        for l in &network.v {
            print!("{} ", l.dec());
        }
        print!("\n");
        return;
    }
    let sl_len = network.len[0];
    let sr_len = network.len[1];
    let n1_len = network.len[2];
    let n2_len = network.len[3];
    let sl_pos = 0;
    let sr_pos = sl_pos + sl_len;
    let n1_pos = sr_pos + sr_len;
    let n2_pos = n1_pos + n1_len;

    print!("len: ");
    for l in &network.len {
        print!("{} ", l);
    }
    print!("\n");

    print!("switch: ");
    for l in &network.v {
        print!("{} ", l.dec());
    }
    print!("\n");

    print!("switch_l: ");
    for i in sl_pos..(sl_pos + sl_len) {
        print!("{} ", network.v[i].dec()); 
    }
    print!("\n");
    print!("switch_r: ");
    for i in sr_pos..(sr_pos + sr_len) {
        print!("{} ", network.v[i].dec()); 
    }
    print!("\n");
    if n1_len > 0 {
        print!("network1: ");
        vec2_print(&PyVecBenes { v: network.v[n1_pos..(n1_pos + n1_len)].to_vec(), len: network.len[4..(4+n1_len)].to_vec() });
        print!("\n");
    }
    if n2_len > 0 {
        print!("network2: ");
        vec2_print(&PyVecBenes { v: network.v[n2_pos..(n2_pos + n2_len)].to_vec(), len: network.len[4+n1_len..(4+n1_len + n2_len)].to_vec() });
        print!("\n");
    }
}

#[pyfunction]
pub fn Benes_rs(x: &PyLweShortArray) -> PyResult<(PyLweShortArray, PyLweShortArray)> {
    let x2 = &x.v;
    let (N, t) = benes_construct(&x2);
    let N2 = benes_to_vec(&N);
    Ok((PyLweShortArray { v: N2 }, PyLweShortArray { v: t }))
}

#[pyfunction]
pub fn Benes_rs2(x: &PyLweShortArray) -> PyResult<(PyVecBenes, PyLweShortArray)> {
    let x2 = &x.v;
    let (N, t) = benes_construct(&x2);
    let N2 = benes_to_vec2(&N);
    //vec2_print(&N2);
    Ok((N2, PyLweShortArray { v: t }))
}



//#[pyfunction]
//pub fn encrypt(x: u32) -> PyResult<PyCiphertext> {
//    let v = algorithms::lwe_encrypt(x);
//    Ok(PyCiphertext { v: v })
//}

//#[pyfunction]
//pub fn decrypt(x: &PyCiphertext) -> PyResult<u32> {
//    let x = algorithms::lwe_decrypt_big(&x.v) as u32;
//    //print!("decrypt: {}\n", x);
//    Ok( x )
//}

/////////////////////////////////////////////////////////////
/// bit_size ビットの整数をビット分解してから暗号化する
/////////////////////////////////////////////////////////////
//#[pyfunction]
//pub fn encrypt_int(x: u32, bit_size: usize) -> PyResult<PyCiphertextVec> {
//    let v = algorithms::lwe_encrypt_int(x, bit_size);
//    Ok(PyCiphertextVec { v: v })
//}

//#[pyfunction]
//pub fn decrypt_int(x: &PyCiphertextVec, bit_size: usize) -> PyResult<u32> {
//    let x = algorithms::lwe_decrypt_int(&x.v, bit_size) as u32;
//    Ok( x )
//}


//#[pyfunction]
//pub fn _add(x: &PyCiphertext, y: &PyCiphertext) -> PyResult<PyCiphertext> {
//    let v = arith::lwe_add(&x.v, &y.v);
//    Ok(PyCiphertext { v: v })
//}

//#[pyfunction]
//pub fn _sub(x: &PyCiphertext, y: &PyCiphertext) -> PyResult<PyCiphertext> {
//    let v = arith::lwe_sub(&x.v, &y.v);
//    Ok(PyCiphertext { v: v })
//}

//#[pyfunction]
//pub fn _and(x: &PyCiphertext, y: &PyCiphertext) -> PyResult<PyCiphertext> {
//    let v = arith::and2(&x.v, &y.v);
//    Ok(PyCiphertext { v: v })
//}

//#[pyfunction]
//pub fn _or(x: &PyCiphertext, y: &PyCiphertext) -> PyResult<PyCiphertext> {
//    let v = arith::or2(&x.v, &y.v);
//    Ok(PyCiphertext { v: v })
//}

//#[pyfunction]
//pub fn _xor(x: &PyCiphertext, y: &PyCiphertext) -> PyResult<PyCiphertext> {
//    let v = arith::xor2(&x.v, &y.v);
//    Ok(PyCiphertext { v: v })
//}

//#[pyfunction]
//pub fn _not(x: &PyCiphertext) -> PyResult<PyCiphertext> {
//    let v = arith::not2(&x.v);
//    Ok(PyCiphertext { v: v })
//}

/////////////////////////////////////////////////////////////
/// c == 0 のとき x,y を，c == 1 のとき y,x を返す
/////////////////////////////////////////////////////////////
//#[pyfunction]
//pub fn cmux(c: &PyCiphertext, x: &PyCiphertext, y: &PyCiphertext) -> PyResult<(PyCiphertext,PyCiphertext)> {
//    let (v, w) = algorithms::cmux(&c.v, &x.v, &y.v);
//    Ok((PyCiphertext { v: v }, PyCiphertext { v: w }))
//}

/////////////////////////////////////////////////////////////
/// c == 0 のとき x,y を，c == 1 のとき y,x を返す
/// x, y はビット分解された整数
/////////////////////////////////////////////////////////////
//#[pyfunction]
//pub fn cmux_int0(c: &PyCiphertext, x: &PyCiphertextVec, y: &PyCiphertextVec) -> PyResult<(PyCiphertextVec, PyCiphertextVec)> {
//    let (v, w) = algorithms::cmux_int(&c.v, &x.v, &y.v);
//    Ok((PyCiphertextVec { v: v }, PyCiphertextVec { v: w }))
//}

//#[pyfunction]
//pub fn bit_decomposition(x: &PyCiphertextVec, bit_size: usize) -> PyResult<PyCiphertextVec> {
//    let v = algorithms::lwe_bit_decomposition_int(&x.v, bit_size);
//    Ok(PyCiphertextVec { v: v })
//}


/////////////////////////////////////////////////////////////
/// ビット分解された整数の，下から ith ビット目を取得する
/////////////////////////////////////////////////////////////
//#[pyfunction]
//pub fn geti(x: &PyCiphertextVec, ith: usize) -> PyResult<PyCiphertext> {
//    let v = algorithms::lwe_geti_int(&x.v, ith);
//    Ok(PyCiphertext { v: v })
//}

//    // $name:ident は識別子（関数名）、$($arg:tt)* は任意の引数、 $body:block は任意のブロック
//    ($name:ident, ($($arg:tt)*), $body:block) => {
//        fn $name($($arg)*) $body
//    };

/* 
macro_rules! define_array_op2 {
    ($op:ident, $t:ty) => {
        pub fn $op(&self, other: &Self) -> Self {
            assert_eq!(self.v.len(), other.v.len());
            let mut result_v: Vec<$t> = Vec::new();
            for i in 0..self.v.len() {
                let x = self.v[i].$op(&other.v[i]);
                result_v.push(x);
            }
            Self { v: result_v }
        }    
    }
}

macro_rules! define_array_op1 {
    ($op:item, $t:ty) => {
        pub fn $op(&self) -> Self {
            let mut result_v: Vec<$t> = Vec::new();
            for i in 0..self.v.len() {
                let x = self.v[i].$op();
                result_v.push(x);
            }
            Self { v: result_v }
        }    
    }
}
*/

//fn apply_function<F>(x: i32, func: F) -> i32 
//where
//    F: Fn(i32) -> i32,
//{
//    func(x)
//}

fn map_short1<F>(array: &PyLweShortArray, func:F) -> PyLweShortArray
where
    F: Fn(&LweShort) -> LweShort,
{
    let mut result_v: Vec<LweShort> = Vec::new();
    for i in 0..array.v.len() {
        let x = func(&array.v[i]);
        result_v.push(x);
    }
    PyLweShortArray { v: result_v }
}

fn map_short2<F>(array1: &PyLweShortArray, array2: &PyLweShortArray, func:F) -> PyLweShortArray
where
    F: Fn(&LweShort, &LweShort) -> LweShort,
{
    let mut result_v: Vec<LweShort> = Vec::new();
    for i in 0..array1.v.len() {
        let x = func(&array1.v[i], &array2.v[i]);
        result_v.push(x);
    }
    PyLweShortArray { v: result_v }
}

#[pyclass]
pub struct PyLweShortArray {
    pub v: Vec<LweShort>,
}

/*  
impl From<Vec<PyLweShort>> for PyLweShortArray {
    fn from(value: Vec<PyLweShort>) -> Self {
        PyLweShortArray { v: value.iter().map(|x| x.v.clone()).collect() }
    }
}

impl From<Vec<u64>> for PyLweShortArray {
    fn from(value: Vec<u64>) -> Self {
        PyLweShortArray { v: value.iter().map(|x| lwe_encrypt(*x as u32)).collect() }
    }
}

impl From<PyLweShortArray> for Vec<PyLweShort> {
    fn from(value: PyLweShortArray) -> Self {
        value.v.iter().map(|x| PyLweShort { v: x.clone() }).collect()
    }
}
*/

/* 
impl TryFrom<Vec<PyLweShort>> for PyLweShortArray {
    type Error = ();
    fn try_from(value: Vec<PyLweShort>) -> Result<Self, Self::Error> {
        Ok(PyLweShortArray { v: value.iter().map(|x| x.v.clone()).collect() })
    }
}
*/

/* 
impl TryInto<PyLweShortArray> for Vec<PyLweShort> {
    type Error = ();
    fn try_into(self) -> Result<PyLweShortArray, Self::Error> {
        Ok(PyLweShortArray { v: self.iter().map(|x| x.v.clone()).collect() })
    }
}
*/
#[pymethods]
impl PyLweShortArray {
    #[new]
    //pub fn new(a: Vec<u32>) -> Self {
    //    let v: Vec<LweShort> = a.into_iter().map(|x| LweShort::new(x)).collect();
    //    Self { v: v }
    //}
    pub fn new(a: Vec<PyLweShort>) -> Self {
        let v: Vec<LweShort> = a.into_iter().map(|x| x.v).collect();
        Self { v: v }
    }
    pub fn dup(&self) -> Self {
        Self { v: self.v.clone() }
    }
    pub fn copy(&self) -> Self {
        Self { v: self.v.clone() }
    }
    pub fn len(&self) -> usize {
        self.v.len()
    }
    pub fn __len__(&self) -> usize {
        self.len()
    }
/*   
    pub fn new_from_lwe(a: &Vec<PyLweShort>) -> Self {
        let mut a2: Vec<PyLweShort> = Vec::new();
        for x in a.iter() {
            //a2.push(PyLweShort { v: x.v.clone() });
            a2.push(x.clone());
        }
        //PyLweShortArray::from(&a2)
        Self{v: a2.iter().map(|x| x.v.clone()).collect()}
    }
*/
    pub fn getitem(&self, i: usize) -> PyLweShort {
        PyLweShort { v: self.v[i].clone() }
    }
    pub fn __getitem__(&self, i: usize) -> PyLweShort {
        self.getitem(i)
    }
    pub fn setitem(&mut self, i: usize, x: &PyLweShort) {
        self.v[i] = x.v.clone();
    }
    pub fn __setitem__(&mut self, i: usize, x: &PyLweShort) {
        self.setitem(i, x)
    }
    pub fn concat(&self, other: &Self) -> Self {
        let mut new_v = self.v.clone();
        new_v.extend_from_slice(&other.v);
        Self { v: new_v }
    }
    pub fn __matmul__(&self, other: &Self) -> Self { // @ operator
        self.concat(&other)
    }
    pub fn slice(&self, mut start: i64, mut end: i64, step: i64) -> Self {
        if start < 0 {start += self.v.len() as i64;}
        if end < 0 {end += self.v.len() as i64;}
        let mut new_v: Vec<LweShort> = Vec::new();
        if step == 1 {
            new_v = self.v[start as usize..end as usize].to_vec();
        } else {
            let mut idx = start;
            while idx < end {
                new_v.push(self.v[idx as usize].clone());
                idx += step;
            }
        }
        Self { v: new_v }
    }
    pub fn mul(&self, other: usize) -> Self {
        let mut ans:Vec<LweShort> = Vec::new();
        for i in 0..other {
            ans.extend_from_slice(&self.v);
        }
        Self { v: ans}
    }
    pub fn __mul__(&self, other: usize) -> Self { // * operator
        self.mul(other)
    }
    pub fn add(&self, other: &Self) -> Self {
        map_short2(&self, other, |x, y| x.add(y))
    }
    pub fn __add__(&self, other: &Self) -> Self { // + operator
        self.add(&other)
    }
/*
    pub fn sub(&self, other: &Self) -> Self {
        assert_eq!(self.v.len(), other.v.len());
        let mut result_v: Vec<LweShort> = Vec::new();
        for i in 0..self.v.len() {
            let sum = self.v[i].sub(&other.v[i]);
            result_v.push(sum);
        }
        Self { v: result_v }
    }
*/
    pub fn sub(&self, other: &Self) -> Self {
        map_short2(&self, other, |x, y| x.sub(y))
    }
    pub fn __sub__(&self, other: &Self) -> Self { // - operator
        self.sub(&other)
    }
/* 
    pub fn lt(&self, other: &Self) -> Self {
        assert_eq!(self.v.len(), other.v.len());
        let mut result_v: Vec<LweShort> = Vec::new();
        for i in 0..self.v.len() {
            let x = self.v[i].lt(&other.v[i]);
            result_v.push(x);
        }
        Self { v: result_v }
    }
*/
    pub fn eq(&self, other: &Self) -> Self {
        map_short2(&self, other, |x, y| x.eq(y))
    }
    pub fn __eq__(&self, other: &Self) -> Self { // == operator
        self.eq(&other)
    }
    pub fn lt(&self, other: &Self) -> Self {
        map_short2(&self, other, |x, y| x.lt(y))
    }
    pub fn __lt__(&self, other: &Self) -> Self { // < operator
        self.lt(&other)
    }
    pub fn le(&self, other: &Self) -> Self {
        map_short2(&self, other, |x, y| x.le(y))
    }
    pub fn __le__(&self, other: &Self) -> Self { // <= operator
        self.le(&other)
    }
    pub fn gt(&self, other: &Self) -> Self {
        map_short2(&self, other, |x, y| x.gt(y))
    }
    pub fn __gt__(&self, other: &Self) -> Self { // > operator
        self.gt(&other)
    }
    pub fn ge(&self, other: &Self) -> Self {
        map_short2(&self, other, |x, y| x.ge(y))
    }
    pub fn __ge__(&self, other: &Self) -> Self { // >= operator
        self.ge(&other)
    }
/* 
    pub fn and(&self, other: &Self) -> Self {
        assert_eq!(self.v.len(), other.v.len());
        let mut result_v: Vec<LweShort> = Vec::new();
        for i in 0..self.v.len() {
            let x = self.v[i].and(&other.v[i]);
            result_v.push(x);
        }
        Self { v: result_v }
    }
*/
    pub fn and(&self, other: &Self) -> Self {
        map_short2(&self, other, |x, y| x.and(y))
    }
    pub fn __and__(&self, other: &Self) -> Self { // & operator
        self.and(&other)
    }
/* 
    pub fn or(&self, other: &Self) -> Self {
        assert_eq!(self.v.len(), other.v.len());
        let mut result_v: Vec<LweShort> = Vec::new();
        for i in 0..self.v.len() {
            let x = self.v[i].or(&other.v[i]);
            result_v.push(x);
        }
        Self { v: result_v }
    }
*/
    pub fn or(&self, other: &Self) -> Self {
        map_short2(&self, other, |x, y| x.or(y))
    }
    pub fn __or__(&self, other: &Self) -> Self { // | operator
        self.or(&other)
    }
/* 
    pub fn xor(&self, other: &Self) -> Self {
        assert_eq!(self.v.len(), other.v.len());
        let mut result_v: Vec<LweShort> = Vec::new();
        for i in 0..self.v.len() {
            let x = self.v[i].xor(&other.v[i]);
            result_v.push(x);
        }
        Self { v: result_v }
    }
*/
    pub fn xor(&self, other: &Self) -> Self {
        map_short2(&self, other, |x, y| x.xor(y))
    }
    pub fn __xor__(&self, other: &Self) -> Self { // ^ operator
        self.xor(&other)
    }
/* 
    pub fn not(&self) -> Self {
        let mut result_v: Vec<LweShort> = Vec::new();
        for i in 0..self.v.len() {
            let x = self.v[i].not();
            result_v.push(x);
        }
        Self { v: result_v }
    }
*/
    pub fn not(&self) -> Self {
        map_short1(&self, |x| x.not())
    }
    pub fn __invert__(&self) -> Self { // ~ operator
        self.not()
    }

}

//use crate::algorithms::lwe_onehot;
/* 
impl PyLweShortArray {
    pub fn onehot(index: &PyLweInt, width: usize) -> Self {
        let public_params = LargeLUTparams::new(width,ThreadCount(8));
        let onehot = lwe_onehot(&public_params, &index.v.x);
        let list: Vec<LweShort> = onehot
            .into_iter()
            .map(|b| LweShort{x: b })
            .collect();
        Self { v: list  }
    }
}
*/

fn map_int1<F>(array: &PyLweIntArray, func:F) -> PyLweIntArray
where
    F: Fn(&LweInt) -> LweInt,
{
    let mut result_v: Vec<LweInt> = Vec::new();
    for i in 0..array.v.len() {
        let x = func(&array.v[i]);
        result_v.push(x);
    }
    PyLweIntArray { v: result_v }
}

fn map_int2<F>(array1: &PyLweIntArray, array2: &PyLweIntArray, func:F) -> PyLweIntArray
where
    F: Fn(&LweInt, &LweInt) -> LweInt,
{
    let mut result_v: Vec<LweInt> = Vec::new();
    for i in 0..array1.v.len() {
        let x = func(&array1.v[i], &array2.v[i]);
        result_v.push(x);
    }
    PyLweIntArray { v: result_v }
}

fn map_intshort2<F>(array1: &PyLweIntArray, array2: &PyLweIntArray, func:F) -> PyLweShortArray
where
    F: Fn(&LweInt, &LweInt) -> LweShort,
{
    let mut result_v: Vec<LweShort> = Vec::new();
    for i in 0..array1.v.len() {
        let x = func(&array1.v[i], &array2.v[i]);
        result_v.push(x);
    }
    PyLweShortArray { v: result_v }
}

#[pyclass]
pub struct PyLweIntArray {
    pub v: Vec<LweInt>,
}

/* 
impl From<Vec<PyLweInt>> for PyLweIntArray {
    fn from(value: Vec<PyLweInt>) -> Self {
        PyLweIntArray { v: value.iter().map(|x| x.v.clone()).collect() }
    }
}

impl From<PyLweIntArray> for Vec<PyLweInt> {
    fn from(value: PyLweIntArray) -> Self {
        value.v.iter().map(|x| PyLweInt { v: x.clone() }).collect()
    }
}
*/

#[pymethods]
impl PyLweIntArray {
    #[new]
    //pub fn new(a: Vec<u32>, bit_length: usize) -> Self {
    //    let v: Vec<LweInt> = a.into_iter().map(|x| LweInt::new(x, bit_length)).collect();
    //    Self { v: v }
    //}
    pub fn new(a: Vec<PyLweInt>) -> Self {
        let v: Vec<LweInt> = a.into_iter().map(|x| x.v).collect();
        Self { v: v }
    }
    pub fn copy(&self) -> Self {
        Self { v: self.v.clone() }
    }
    pub fn dup(&self) -> Self {
        Self { v: self.v.clone() }
    }
    pub fn len(&self) -> usize {
        self.v.len()
    }
    pub fn __len__(&self) -> usize {
        self.len()
    }
    pub fn getitem(&self, i: usize) -> PyLweInt {
        PyLweInt { v: self.v[i].clone() }
    }
    pub fn __getitem__(&self, i: usize) -> PyLweInt {
        self.getitem(i)
    }
    pub fn setitem(&mut self, i: usize, x: &PyLweInt) {
        self.v[i] = x.v.clone();
    }
    pub fn __setitem__(&mut self, i: usize, x: &PyLweInt) {
        self.setitem(i, x)
    }
    pub fn concat(&self, other: &Self) -> Self {
        let mut new_v = self.v.clone();
        new_v.extend_from_slice(&other.v);
        Self { v: new_v }
    }
    pub fn __matmul__(&self, other: &Self) -> Self { // @ operator
        self.concat(&other)
    }
    pub fn slice(&self, mut start: i64, mut end: i64, step: i64) -> Self {
        if start < 0 {start += self.v.len() as i64;}
        if end < 0 {end += self.v.len() as i64;}
        let mut new_v: Vec<LweInt> = Vec::new();
        if step == 1 {
            new_v = self.v[start as usize..end as usize].to_vec();
        } else {
            let mut idx = start;
            while idx < end {
                new_v.push(self.v[idx as usize].clone());
                idx += step;
            }
        }
        Self { v: new_v }
    }
    pub fn add(&self, other: &Self) -> Self {
        map_int2(&self, other, |x, y| x.add(y))
    }
    pub fn __add__(&self, other: &Self) -> Self { // + operator
        self.add(&other)
    }
    pub fn sub(&self, other: &Self) -> Self {
        map_int2(&self, other, |x, y| x.sub(y))
    }
    pub fn __sub__(&self, other: &Self) -> Self { // - operator
        self.sub(&other)
    }
    pub fn eq(&self, other: &Self) -> PyLweShortArray {
        map_intshort2(&self, other, |x, y| x.eq(y))
   }
    pub fn __eq__(&self, other: &Self) -> PyLweShortArray { // == operator
        self.eq(&other)
    }
    pub fn lt(&self, other: &Self) -> PyLweShortArray {
        map_intshort2(&self, other, |x, y| x.lt(y))
    }
    pub fn __lt__(&self, other: &Self) -> PyLweShortArray { // < operator
        self.lt(&other)
    }
    pub fn le(&self, other: &Self) -> PyLweShortArray {
        map_intshort2(&self, other, |x, y| x.le(y))
    }
    pub fn __le__(&self, other: &Self) -> PyLweShortArray { // <= operator
        self.le(&other)
    }
    pub fn gt(&self, other: &Self) -> PyLweShortArray {
        map_intshort2(&self, other, |x, y| x.gt(y))
    }
    pub fn __gt__(&self, other: &Self) -> PyLweShortArray { // > operator
        self.gt(&other)
    }
    pub fn ge(&self, other: &Self) -> PyLweShortArray {
        map_intshort2(&self, other, |x, y| x.ge(y))
    }
    pub fn __ge__(&self, other: &Self) -> PyLweShortArray { // >= operator
        self.ge(&other)
    }
    //pub fn from_list(&self, x: &Vec<PyLweInt>) -> Self {
    //    let mut v: Vec<LweInt> = Vec::new();
    //    for item in x.iter() {
    //        v.push(item.v.clone());
    //    }
    //    PyLweIntArray { v: v }
    //}
}

#[pymodule]
fn _csclib_tfhe(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyLweShort>()?;
    m.add_class::<PyLweInt>()?;
    m.add_class::<PyLwePacked>()?;
    m.add_class::<PyLweShortArray>()?;
    m.add_class::<PyLweIntArray>()?;
    m.add_class::<PyVecBenes>()?;
    //m.add_function(wrap_pyfunction!(bit_decomposition_int, m)?)?;
    //m.add_function(wrap_pyfunction!(bit_composition_int, m)?)?;
    m.add_function(wrap_pyfunction!(Benes_rs, m)?)?;
    m.add_function(wrap_pyfunction!(Benes_rs2, m)?)?;
    m.add_function(wrap_pyfunction!(getparams, m)?)?;

    Ok(())
}

