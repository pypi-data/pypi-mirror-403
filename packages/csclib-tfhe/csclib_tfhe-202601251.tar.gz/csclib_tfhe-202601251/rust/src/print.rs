use tfhe::core_crypto::prelude::*;
use crate::{algorithms::lwe_decrypt};
use crate::algorithms::{trivial_const};
//use crate::algorithms::TFHE_PARAMS;
use crate::{algorithms::*, print};

/* 
pub fn glwe_print0(glwe: &GlweCiphertextOwned<u64>, tfhe_params: &TfheParam, nth: usize) {
    let mut x = trivial_const0(0, tfhe_params);
    //let mut x = lwe_new_to_lwe(&tfhe_params);
    print!("glwe ");
    for i in 0..tfhe_params.polynomial_size.0 {
        extract_lwe_sample_from_glwe_ciphertext(
            &glwe,
            &mut x,
                   MonomialDegree(i),
        );
        if i == nth {
            print!("[ ");
        }
        print!("{} ", lwe_decrypt_big0(&x, tfhe_params));    
        //print!("{} ", lwe_decrypt(&lwe_keyswitch(&x, tfhe_params), tfhe_params));    
        if i == nth {
            print!("] ");
        }
    }
    print!("\n");
}
*/
pub fn glwe_print(glwe: &GlweCiphertextOwned<u64>, nth: usize) {
    let mut x = trivial_const(0);
    //let mut x = lwe_new_to_lwe(&tfhe_params);
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        print!("glwe ");
        for i in 0..tfhe_params.polynomial_size.0 {
            extract_lwe_sample_from_glwe_ciphertext(
                &glwe,
                &mut x,
                       MonomialDegree(i),
            );
            if i == nth {
                print!("[ ");
            }
            print!("{} ", lwe_decrypt(&x));    
            //print!("{} ", lwe_decrypt(&lwe_keyswitch(&x, tfhe_params), tfhe_params));    
            if i == nth {
                print!("] ");
            }
        }
        print!("\n");
    });
}

/* 
pub fn print_ctx_list0 (lwe_list: &Vec<LweCiphertextOwned<u64>>, tfhe_params: &TfheParam) {
    //let message_modulus = tfhe_param.message_modulus;
    //let carry_modulus = tfhe_param.carry_modulus;
    //let delta = tfhe_param.delta; 
    //let rounding_bit = delta >> 1;

    let arr_len = lwe_list.len();


    for i in 0..arr_len {
        //let lwe_list_plaintext: Plaintext<u64> =
        //    decrypt_lwe_ciphertext(&tfhe_param.big_lwe_sk, &lwe_list[i]);
        //let lwe_list_result: u64 =
        //    (lwe_list_plaintext.0.wrapping_add((lwe_list_plaintext.0 & rounding_bit) << 1) / delta) % message_modulus.0 as u64;
        //let lwe_list_result = lwe_decrypt_short(&lwe_list[i], 1, tfhe_param);
        let lwe_list_result = lwe_decrypt_big0(&lwe_list[i], tfhe_params);
        print!("{} ", lwe_list_result);
    }
    println!("");
}
*/
pub fn print_ctx_list (lwe_list: &Vec<LweCiphertextOwned<u64>>) {
    let arr_len = lwe_list.len();

    for i in 0..arr_len {
        let lwe_list_result = lwe_decrypt(&lwe_list[i]);
        print!("{} ", lwe_list_result);
    }
    println!("");
}

pub fn print_ctx_list_short (lwe_list: &Vec<LweShort>) {
    let arr_len = lwe_list.len();

    for i in 0..arr_len {
        let lwe_list_result = lwe_list[i].dec();
        print!("{} ", lwe_list_result);
    }
    println!("");
}

/* 
pub fn print_ctx0 (lwe: &LweCiphertextOwned<u64>, tfhe_params: &TfheParam) {
    //let message_modulus = tfhe_param.message_modulus;
    //let carry_modulus = tfhe_param.carry_modulus;
    //let delta = tfhe_param.delta; 
    //let rounding_bit = tfhe_param.rounding_bit;

    //let lwe_plaintext: Plaintext<u64> =
    //    decrypt_lwe_ciphertext(&tfhe_param.big_lwe_sk, &lwe);
    //let lwe_result: u64 =
    //    (lwe_plaintext.0.wrapping_add((lwe_plaintext.0 & rounding_bit) << 1) / delta) % message_modulus.0 as u64;
    //let lwe_result = lwe_decrypt_short(&lwe, 1, tfhe_param);
    let lwe_result = lwe_decrypt_big0(&lwe, tfhe_params);
    print!("{} ", lwe_result);
    println!("");
}
*/
pub fn print_ctx (lwe: &LweCiphertextOwned<u64>) {
        let lwe_result = lwe_decrypt(&lwe);
        print!("{} ", lwe_result);
        println!("");
}

/* 
pub fn print_ctx_list_multibit0(lwe_list: &Vec<Vec<LweCiphertextOwned<u64>>>, tfhe_params: &TfheParam) {
    let arr_len = lwe_list.len();
    let bit_size = lwe_list[0].len();
    //let message_modulus = tfhe_param.message_modulus;
    let modulus = tfhe_params.message_modulus.0 * tfhe_params.carry_modulus.0;
    let w = blog(modulus -1) as u32 +1;
    //let w = 1;
    let delta = tfhe_params.delta; 
    let rounding_bit = tfhe_params.rounding_bit;

    for i in 0..arr_len {
        let mut sum = 0;
        for j in 0..bit_size {
            let decomped_plaintext: Plaintext<u64> =
                decrypt_lwe_ciphertext(&tfhe_params.big_lwe_sk, &lwe_list[i][j]);
            let decomped_result: u64 =
                (decomped_plaintext.0.wrapping_add((decomped_plaintext.0 & rounding_bit) << 1) / delta) % modulus as u64;
            //sum += decomped_result << ((message_modulus.0 as f64).log2() as usize * j);
            sum += decomped_result << w*j as u32;
        }
        print!("{} ", sum);
    }
    print!("\n");

}
*/
pub fn print_ctx_list_multibit(lwe_list: &Vec<Vec<LweCiphertextOwned<u64>>>) {
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let arr_len = lwe_list.len();
        let bit_size = lwe_list[0].len();
        //let message_modulus = tfhe_param.message_modulus;
        let modulus = tfhe_params.message_modulus * tfhe_params.carry_modulus;
        let w = blog(modulus -1) as u32 +1;
        //let w = 1;
        let delta = tfhe_params.delta; 
        let rounding_bit = tfhe_params.rounding_bit;

        for i in 0..arr_len {
            let mut sum = 0;
            for j in 0..bit_size {
                let decomped_plaintext: Plaintext<u64> =
                    decrypt_lwe_ciphertext(&tfhe_params.big_lwe_sk, &lwe_list[i][j]);
                let decomped_result: u64 =
                    (decomped_plaintext.0.wrapping_add((decomped_plaintext.0 & rounding_bit) << 1) / delta) % modulus as u64;
                sum += decomped_result << w*j as u32;
            }
            print!("{} ", sum);
        }
        print!("\n");
    });
}

/* 
pub fn print_ctx_list_int(lwe_list: &Vec<LweInt>) {
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let arr_len = lwe_list.len();
        let bit_size = lwe_list[0].bit_size();
        //let message_modulus = tfhe_param.message_modulus;
        //let modulus = tfhe_params.message_modulus.0 * tfhe_params.carry_modulus.0;
        let modulus = tfhe_params.message_modulus.0;
        let w = blog(modulus -1) as u32 +1;
        //let w = 1;
        //let delta = tfhe_params.delta; 
        //let rounding_bit = tfhe_params.rounding_bit;

        for i in 0..arr_len {
            let mut sum = 0;
            for j in 0..bit_size {
                //let decomped_plaintext: Plaintext<u64> =
                //    decrypt_lwe_ciphertext(&tfhe_params.big_lwe_sk, &lwe_list[i][j]);
                //let decomped_result: u64 =
                //    (decomped_plaintext.0.wrapping_add((decomped_plaintext.0 & rounding_bit) << 1) / delta) % modulus as u64;
                let decomped_result = lwe_list[i].dec() % modulus as u64;
                sum += decomped_result << w*j as u32;
            }
            print!("{} ", sum);
        }
        print!("\n");
    });
}
*/

pub fn print_ctx_list_packed(lwe_list: &Vec<LwePacked>) {
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let arr_len = lwe_list.len();
        //let bit_size = lwe_list[0].bit_size();
        //let message_modulus = tfhe_param.message_modulus;
        let modulus = tfhe_params.message_modulus * tfhe_params.carry_modulus;
        //let modulus = tfhe_params.message_modulus.0;
        //let w = blog(modulus -1) as u32 +1;
        //let w = 1;

        for i in 0..arr_len {
            //let mut sum = 0;
            //for j in 0..bit_size {
            //    //let decomped_result = lwe_decrypt_big(&lwe_list[i][j]) % modulus as u64;
            //    let decomped_result = lwe_list[i].dec() % modulus as u64;
            //    sum += decomped_result << w*j as u32;
            //}
            let sum = lwe_list[i].dec() % modulus as u64;
            print!("{} ", sum);
        }
        print!("\n");
    });
}

use crate::algorithms::blog;

