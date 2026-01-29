use tfhe::core_crypto::prelude::*;
use tfhe::core_crypto::entities::{
    GlweCiphertext, LweCiphertext,/* LweCiphertextList, */ LwePackingKeyswitchKey,
};

//use crate::{glwe_print, TfheParam};
use crate::algorithms::*;

/*
fn test_keyswitch(p1: &mut TfheParam, p2: &mut TfheParam) {
    let input_lwe_dimension = LweDimension(742);
    print!("input_lwe_dim {}\n", input_lwe_dimension.0); // 742
    print!("{} {}\n", p1.small_lwe_dimension.0, p2.small_lwe_dimension.0); // 648 742
    //let lwe_modular_std_dev = StandardDev(0.000007069849454709433);
    //let output_lwe_dimension = LweDimension(2048);
    //let decomp_base_log = DecompositionBaseLog(3);
    //let decomp_level_count = DecompositionLevelCount(5);
    //let ciphertext_modulus = CiphertextModulus::new_native();

    print!("base_log {} level_count {}\n", p1.ks_base_log.0, p1.ks_level.0);
    print!("base_log {} level_count {}\n", p2.ks_base_log.0, p2.ks_level.0);

    // Create the LweSecretKey
    //let input_lwe_secret_key =
    //    allocate_and_generate_new_binary_lwe_secret_key(input_lwe_dimension, &mut p1.secret_generator);
    //let input_lwe_secret_key = &p1.big_lwe_sk;

    //let output_lwe_secret_key = 
    //    allocate_and_generate_new_binary_lwe_secret_key(output_lwe_dimension,&mut p2.secret_generator,);
    //let output_lwe_secret_key = &mut p2.big_lwe_sk;

    let ksk = allocate_and_generate_new_lwe_keyswitch_key(
        //&input_lwe_secret_key,
        &p1.big_lwe_sk,
        //&output_lwe_secret_key,
        &p2.big_lwe_sk,
        //decomp_base_log,
        p2.ks_base_log,
        //decomp_level_count,
        p2.ks_level,
        p2.lwe_modular_std_dev,
        p2.ciphertext_modulus,
        &mut p2.encryption_generator,
    );

    print!("delta1 {} {}\n", blog(p1.delta-1)+1, p1.delta);
    print!("delta2 {} {}\n", blog(p2.delta-1)+1, p2.delta);

    // Create the plaintext
    //let msg = 1u64;
    //let plaintext = Plaintext(msg * p1.delta);
    // Create a new LweCiphertext
    //let input_lwe = allocate_and_encrypt_new_lwe_ciphertext(
    //    &input_lwe_secret_key,
    //    plaintext,
    //    lwe_modular_std_dev,
    //    ciphertext_modulus,
    //    &mut p1.encryption_generator,
    //);
    let input_lwe = lwe_encrypt_big(1, p1);

    //let mut output_lwe = LweCiphertext::new(
    //    0,
    //    output_lwe_secret_key.lwe_dimension().to_lwe_size(),
    //    ciphertext_modulus,
    //);
    let mut output_lwe = trivial_const(0, p2);
   
    // Use all threads available in the current rayon thread pool
    par_keyswitch_lwe_ciphertext(&ksk, &input_lwe, &mut output_lwe);

    //let decrypted_plaintext = decrypt_lwe_ciphertext(&output_lwe_secret_key, &output_lwe);
    //let decrypted_plaintext = decrypt_lwe_ciphertext(&p2.big_lwe_sk, &output_lwe);

    // Round and remove encoding
    // First create a decomposer working on the high 4 bits corresponding to our encoding.
    //let decomposer = SignedDecomposer::new(DecompositionBaseLog(4), DecompositionLevelCount(1));
    //let rounded = decomposer.closest_representable(decrypted_plaintext.0);

    // Remove the encoding
    //let cleartext = rounded >> 60;
    let cleartext = lwe_decrypt_big(&output_lwe, p2);
    print!("clear text {}\n", cleartext);

}
*/

//use std::cell::RefCell;
use crate::algorithms::ENCRYPTION_GENERATOR;

pub fn lwe_generate_ksk(from: &TfheParam, to: &TfheParam) -> LweKeyswitchKey<Vec<u64>> {
    ENCRYPTION_GENERATOR.with(|gen| {
        let mut encryption_generator = gen.borrow_mut();
        let ksk = allocate_and_generate_new_lwe_keyswitch_key(
            //&input_lwe_secret_key,
            &from.big_lwe_sk,
            //&output_lwe_secret_key,
            &to.big_lwe_sk,
            //decomp_base_log,
            to.ks_base_log,
            //decomp_level_count,
            to.ks_level,
            to.lwe_noise_distribution,
            to.ciphertext_modulus,
            //&mut to.encryption_generator,
            &mut *encryption_generator,
        );
        //return ksk;
        ksk
    })
}

pub fn lwe_to_lwe(input_lwe: &LweCiphertext<Vec<u64>>, ksk: &LweKeyswitchKey<Vec<u64>>) -> LweCiphertext<Vec<u64>> {
    //let mut output_lwe = trivial_const0(0, output_param);
    let mut output_lwe = trivial_const(0);
    par_keyswitch_lwe_ciphertext(&ksk, &input_lwe, &mut output_lwe);
    return output_lwe;
}

/*
pub fn test_keyswitch2(p1: &mut TfheParam, p2: &mut TfheParam) {

    let ksk = lwe_generate_ksk(p1, p2);

    let message_modulus = p1.message_modulus.0;

    for i in 0..message_modulus {
        let x = trivial_const(i as u64, p1);
        //let x = lwe_add(&x, &x, p1);
        let y = lwe_to_lwe(&x, p2, &ksk);
        print!("x {} y {}\n", lwe_decrypt_big(&x, p1), lwe_decrypt_big(&y, p2));
    }


}
*/


