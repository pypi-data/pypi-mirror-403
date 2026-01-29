use tfhe::core_crypto::prelude::*;
use crate::algorithms::generate_lut_plain;
use crate::algorithms::lwe_lookup_glwe;
use crate::algorithms::lwe_lookup;
use crate::print;
use lwe_ciphertext_add;
use lwe_ciphertext_sub;
use crate::algorithms::trivial_const;
use crate::algorithms::TFHE_PARAMS;
use crate::algorithms::*;

/* 
pub fn lwe_add0(x: &LweCiphertextOwned<u64>, y: &LweCiphertextOwned<u64>, _tfhe_params: &TfheParam) -> LweCiphertextOwned<u64> {
    let mut x_plus_y = x.clone();
    lwe_ciphertext_add(&mut x_plus_y, &x, &y);
    return x_plus_y;
}
*/
pub fn lwe_add(x: &LweCiphertextOwned<u64>, y: &LweCiphertextOwned<u64>) -> LweCiphertextOwned<u64> {
    let mut x_plus_y = x.clone();
    lwe_ciphertext_add(&mut x_plus_y, &x, &y);
    return x_plus_y;
}

//use crate::algorithms::TFHE_PARAMS2;

pub fn lwe_decompose(x: &LweCiphertextOwned<u64>) -> (LweCiphertextOwned<u64>, LweCiphertextOwned<u64>) {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let message_modulus = tfhe_params.message_modulus;
        let carry_modulus = tfhe_params.carry_modulus;
        let modulus = message_modulus * carry_modulus;
        let w = blog(modulus -1) as u32 +1;

        let table_q: Vec<u64> = (0..(1 << w)).map(|j| (j / message_modulus) & 1 as u64).collect();
        let table_r: Vec<u64> = (0..(1 << w)).map(|j| (j % message_modulus) & 1 as u64).collect();

        let table_q_glwe = generate_lut_plain(&table_q);
        let table_r_glwe = generate_lut_plain(&table_r);

        let q = lwe_lookup_glwe(&x, &table_q_glwe);
        let r = lwe_lookup_glwe(&x, &table_r_glwe);

        (q, r)
    })
}

pub fn lwe_getqr(x: &LweCiphertextOwned<u64>) -> (LweCiphertextOwned<u64>, LweCiphertextOwned<u64>) {
    let (modulus_int, modulus_packed) = TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        (tfhe_params.message_modulus, tfhe_params.message_modulus * tfhe_params.carry_modulus)
    });
    let table_q: Vec<u64> = (0..modulus_packed).map(|j| (j / modulus_int) as u64).collect();
    let table_r: Vec<u64> = (0..modulus_packed).map(|j| (j % modulus_int) as u64).collect();
    let r = lwe_lookup_plain(&x, &table_r);
    let q = lwe_lookup_plain(&x, &table_q);
    (q, r)
}


/* 
pub fn lwe_sub0(x: &LweCiphertextOwned<u64>, y: &LweCiphertextOwned<u64>, _tfhe_params: &TfheParam) -> LweCiphertextOwned<u64> {
    let mut x_minus_y = x.clone();
    lwe_ciphertext_sub(&mut x_minus_y, &x, &y);
    return x_minus_y;
}
*/
pub fn lwe_sub(x: &LweCiphertextOwned<u64>, y: &LweCiphertextOwned<u64>) -> LweCiphertextOwned<u64> {
    let mut x_minus_y = x.clone();
    lwe_ciphertext_sub(&mut x_minus_y, &x, &y);
    return x_minus_y;
}

pub fn lwe_mul_const(x: &LweCiphertextOwned<u64>, mul_cleartext: u64) -> LweCiphertextOwned<u64> {
    let mut lwe = x.clone();
    lwe_ciphertext_cleartext_mul_assign(&mut lwe, Cleartext(mul_cleartext));
    return lwe;
}

pub fn lwe_add3(x: &LweCiphertextOwned<u64>, y: &LweCiphertextOwned<u64>, z: &LweCiphertextOwned<u64>) -> (LweCiphertextOwned<u64>, LweCiphertextOwned<u64>) {
    let xy = lwe_add(&x, &y);
    let xyz = lwe_add(&xy, &z);
    let (high, low) = lwe_getqr(&xyz);
    return (high, low);
}


//////////////////////////////////////////////////////////////////////////////////////////
/// 引き算．z は下の桁からの繰り下がり（1 or 0）
//////////////////////////////////////////////////////////////////////////////////////////
pub fn lwe_sub3(x: &LweCiphertextOwned<u64>, y: &LweCiphertextOwned<u64>, z: &LweCiphertextOwned<u64>) -> (LweCiphertextOwned<u64>, LweCiphertextOwned<u64>) {
    let xx = lwe_add(&x, &trivial_const(4));
    let xy = lwe_sub(&xx, &y);
    let xyz = lwe_sub(&xy, &z);
    let (high, low) = lwe_getqr(&xyz);
    let high2 = lwe_sub(&trivial_const(1), &high);
    return (high2, low);
}

fn mul_sub_high(v: u64, modulus: u64) -> u64 {
    let x = v / modulus;
    let y = v % modulus;
    return (x * y) / modulus;
}

fn mul_sub_low(v: u64, modulus: u64) -> u64 {
    let x = v / modulus;
    let y = v % modulus;
    return (x * y) % modulus;
}

////////////////////////////////////////////////////////////////////////////////////////////////
/// LWE の加算（シフト付き）
/// x_shift は x をどれだけ左シフトするか
/// x の範囲: [x_shift, nx+x_shift)
/// y の範囲: [0, ny)
////////////////////////////////////////////////////////////////////////////////////////////////
pub fn lwe_add_int_shifted(x: &Vec<LweCiphertextOwned<u64>>, y: &Vec<LweCiphertextOwned<u64>>, x_shift: usize) -> Vec<LweCiphertextOwned<u64>> {
    let nx = x.len();
    let ny = y.len();
    let nz = std::cmp::max(ny, nx + x_shift)+1;
    let mut result: Vec<LweCiphertextOwned<u64>> = Vec::with_capacity(nz);
    let mut c = trivial_const(0);
    //let mut sum = trivial_const(0);
    let mut sum: LweCiphertextOwned<u64>;
    if nx + x_shift > ny {
        for i in 0..x_shift {
            result.push(y[i].clone());
        }
        for i in x_shift..ny {
            (c, sum) = lwe_add3(&x[i - x_shift], &y[i], &c);
            result.push(sum);
        }
        for i in ny..nz-1 {
            (c, sum) = lwe_add3(&x[i - x_shift], &trivial_const(0), &c);
            result.push(sum);
        }
        result.push(c);
    } else {
        for i in 0..x_shift {
            result.push(y[i].clone());
        }
        for i in x_shift..nx+x_shift {
            (c, sum) = lwe_add3(&x[i - x_shift], &y[i], &c);
            result.push(sum);
        }
        for i in nx+x_shift..nz-1 {
            (c, sum) = lwe_add3(&trivial_const(0), &y[i], &c);
            result.push(sum);
        }
        result.push(c);
    }
    return result;
}


////////////////////////////////////////////////////////////////////////////////////////////////
/// LWE の掛け算
/// 答えは2桁のLWE
////////////////////////////////////////////////////////////////////////////////////////////////
pub fn lwe_mul(x: &LweCiphertextOwned<u64>, y: &LweCiphertextOwned<u64>) -> (LweCiphertextOwned<u64>, LweCiphertextOwned<u64>) {
    let modulus = TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        tfhe_params.message_modulus
    });
    let table_high: Vec<u64> = (0..modulus*modulus).map(|j| mul_sub_high(j, modulus)).collect();
    let table_low: Vec<u64> = (0..modulus*modulus).map(|j| mul_sub_low(j, modulus)).collect();
    let v = lwe_mul_const(x, modulus);
    let w = lwe_add(&v, y);
    let q = lwe_lookup_plain(&w, &table_high);
    let r = lwe_lookup_plain(&w, &table_low);
    (q, r)
}

pub fn lwe_mul_int_sub(x: &Vec<LweCiphertextOwned<u64>>, y: &LweCiphertextOwned<u64>) -> Vec<LweCiphertextOwned<u64>> {
    let n = x.len();
    let mut result: Vec<LweCiphertextOwned<u64>> = Vec::with_capacity(n+1);
    let mut c = trivial_const(0);
    let mut sum: LweCiphertextOwned<u64>;
    for i in 0..n {
        let (ctmp, sum_tmp) = lwe_mul(&x[i], &y);
        let (ctmp2, sum_final) = lwe_add3(&sum_tmp, &c, &trivial_const(0));
        result.push(sum_final);
        c = lwe_add(&ctmp, &ctmp2);
    }
    result.push(c);
    return result;
}

pub fn lwe_mul_int(x: &Vec<LweCiphertextOwned<u64>>, y: &Vec<LweCiphertextOwned<u64>>) -> Vec<LweCiphertextOwned<u64>> {
    let nx = x.len();
    let ny = y.len();
    let n = nx + ny + 1;
    let mut result: Vec<LweCiphertextOwned<u64>> = Vec::with_capacity(n);
    result.push(trivial_const(0));
    for i in 0..ny {
        let xy_tmp = lwe_mul_int_sub(&x, &y[i]);
        let xy = lwe_add_int_shifted(&result, &xy_tmp, i);
        result = xy;
    }
    return result;
}

fn eq_sub(v: u64, modulus: u64) -> u64 {
    let x = v / modulus;
    let y = v % modulus;
    return (x == y) as u64;
}

pub fn lwe_eq(x: &LweCiphertextOwned<u64>, y: &LweCiphertextOwned<u64>) -> LweCiphertextOwned<u64> {
    let modulus = TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        tfhe_params.message_modulus
    });
    let table_eq: Vec<u64> = (0..modulus*modulus).map(|j| eq_sub(j, modulus)).collect();
    let v = lwe_mul_const(x, modulus);
    let w = lwe_add(&v, y);
    let x = lwe_lookup_plain(&w, &table_eq);
    x
}

pub fn lwe_eq_int(x: &Vec<LweCiphertextOwned<u64>>, y: &Vec<LweCiphertextOwned<u64>>) -> LweCiphertextOwned<u64> {
    let n = x.len();
    let mut result = trivial_const(1);
    for i in 0..n {
        let eq_bit = lwe_eq(&x[i], &y[i]);
        result = and2(&result, &eq_bit);
    }
    result
}

fn xor_int_sub(v: u64, modulus: u64) -> u64 {
    let x = v / modulus;
    let y = v % modulus;
    return (x ^ y) as u64;
}

pub fn lwe_xor_int(x: &Vec<LweCiphertextOwned<u64>>, y: &Vec<LweCiphertextOwned<u64>>) -> Vec<LweCiphertextOwned<u64>> {
    let modulus = TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        tfhe_params.message_modulus
    });
    let table_xor: Vec<u64> = (0..modulus*modulus).map(|j| xor_int_sub(j, modulus)).collect();
    let v = lwe_mul_const(&x[0], modulus);
    let w = lwe_add(&v, &y[0]);
    let z = lwe_lookup_plain(&w, &table_xor);

    let mut result = x.clone();
    result[0] = z;
    result
}

fn mod_int_sub(v: u64, modulus: u64) -> u64 {
    let x = v / modulus;
    let y = v % modulus;
    if y == 0 {
        return 0;
    }
    return (x % y) as u64;
}

pub fn lwe_mod_int(x: &Vec<LweCiphertextOwned<u64>>, y: &Vec<LweCiphertextOwned<u64>>) -> Vec<LweCiphertextOwned<u64>> {
    let modulus = TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        tfhe_params.message_modulus
    });
    let table_mod: Vec<u64> = (0..modulus*modulus).map(|j| mod_int_sub(j, modulus)).collect();
    let v = lwe_mul_const(&x[0], modulus);
    let w = lwe_add(&v, &y[0]);
    let z = lwe_lookup_plain(&w, &table_mod);

    let mut result = Vec::new();
    result.push(z);
    for i in 1..x.len() {
        result.push(trivial_const(0));
    }
    result
}

pub fn lwe_mod(x: &LweCiphertextOwned<u64>, y: &LweCiphertextOwned<u64>) -> LweCiphertextOwned<u64> {
    let modulus = TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        tfhe_params.message_modulus
    });
    let table_mod: Vec<u64> = (0..modulus*modulus).map(|j| mod_int_sub(j, modulus)).collect();
    let v = lwe_mul_const(&x, modulus);
    let w = lwe_add(&v, &y);
    let z = lwe_lookup_plain(&w, &table_mod);

    z
}


pub fn not2(a: &LweCiphertextOwned<u64>)-> LweCiphertextOwned<u64> {
        lwe_sub(&trivial_const(1), &a)
}

pub fn xor2(a: &LweCiphertextOwned<u64>, b: &LweCiphertextOwned<u64>)-> LweCiphertextOwned<u64> {
        let b_bar = not2(&b);
        let table = vec![b.clone(), b_bar.clone()];
        lwe_lookup(&a, &table)
}

pub fn and2(a: &LweCiphertextOwned<u64>, b: &LweCiphertextOwned<u64>)-> LweCiphertextOwned<u64> {
        let table = vec![trivial_const(0), b.clone()];
        lwe_lookup(&a, &table)
}

pub fn or2(a: &LweCiphertextOwned<u64>, b: &LweCiphertextOwned<u64>)-> LweCiphertextOwned<u64> {
        let table = vec![b.clone(), trivial_const(1)];
        lwe_lookup(&a, &table)
}



pub fn lwe_add_int(x: &Vec<LweCiphertextOwned<u64>>, y: &Vec<LweCiphertextOwned<u64>>) -> (LweCiphertextOwned<u64>, Vec<LweCiphertextOwned<u64>>) {
    let n = x.len();
    let mut result: Vec<LweCiphertextOwned<u64>> = Vec::with_capacity(n);
    let mut c = trivial_const(0);
    for i in 0..n {
        let (ctmp, sum) = lwe_add3(&x[i], &y[i], &c);
        result.push(sum);
        c = ctmp;
    }
    return (c, result);
}

pub fn lwe_sub_int(x: &Vec<LweCiphertextOwned<u64>>, y: &Vec<LweCiphertextOwned<u64>>) -> (LweCiphertextOwned<u64>, Vec<LweCiphertextOwned<u64>>) {
    let n = x.len();
    let mut result: Vec<LweCiphertextOwned<u64>> = Vec::with_capacity(n);
    let mut c = trivial_const(0);
    for i in 0..n {
        let (ctmp, sum) = lwe_sub3(&x[i], &y[i], &c);
        result.push(sum);
        c = ctmp;
    }
    return (c, result);
}
