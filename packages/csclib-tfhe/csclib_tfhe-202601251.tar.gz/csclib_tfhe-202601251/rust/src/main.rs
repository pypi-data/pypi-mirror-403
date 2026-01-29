
use tfhe::boolean::backward_compatibility::public_key;
//use tfhe::{core_crypto::prelude::*, integer::parameters::PARAM_MESSAGE_4_CARRY_4_KS_PBS_16_BITS, shortint::{CarryModulus, MessageModulus, parameters::classic}};
use tfhe::{core_crypto::prelude::*};
//use tfhe::shortint::parameters::{PARAM_MESSAGE_4_CARRY_0_KS_PBS, PARAM_MESSAGE_4_CARRY_1_KS_PBS, PARAM_MESSAGE_1_CARRY_0_KS_PBS, ShortintParameterSet};
//use tfhe::integer::parameters::{PARAM_MESSAGE_4_CARRY_0_KS_PBS, PARAM_MESSAGE_4_CARRY_1_KS_PBS, PARAM_MESSAGE_1_CARRY_0_KS_PBS, ShortintParameterSet};
//use tfhe::shortint::parameters::{PARAM_MESSAGE_3_CARRY_3_KS_PBS_GAUSSIAN_2M128, ShortintParameterSet};
//use tfhe::shortint::parameters::{ClassicPBSParameters};
//use tfhe::shortint::parameters::{PBSParameters};
//use tfhe::shortint::parameters::{PARAM_MESSAGE_2_CARRY_2_KS_PBS_GAUSSIAN_2M128};
//use tfhe::integer::parameters::{PARAM_MESSAGE_4_CARRY_4_KS_PBS_32_BITS};
//use tfhe::shortint::parameters::{PARAM_MESSAGE_2_CARRY_2_KS_PBS};
use tfhe::shortint::parameters::v1_4::{V1_4_PARAM_MESSAGE_4_CARRY_0_KS_PBS_GAUSSIAN_2M128};

//use keyswitch::*;
mod params;
mod print;
use print::*;
mod benes;
use benes::*;
mod keyswitch;
mod algorithms;
mod arith;
use crate::algorithms::*;
//use crate::algorithms::TfheParam;
use std::{time, env};
use std::time::{Duration, Instant};
use std::thread::sleep;
//use crate::params::PARAMS;
use rand::Rng;


//use tfhe::shortint::parameters::{LEGACY_WOPBS_PARAM_MESSAGE_4_CARRY_0_KS_PBS,LEGACY_WOPBS_PARAM_MESSAGE_4_CARRY_1_KS_PBS,LEGACY_WOPBS_PARAM_MESSAGE_1_CARRY_0_KS_PBS,LEGACY_WOPBS_PARAM_MESSAGE_2_CARRY_0_KS_PBS};

pub fn f(x: i64) -> i64 {
    (3 * x * x - 7*x + 3).abs() as i64
    // x
}

fn main() {
    let args: Vec<String> = env::args().collect();

    //let parameter_set = TfheParam::new_params(V1_4_PARAM_MESSAGE_4_CARRY_0_KS_PBS_GAUSSIAN_2M128);
    let parameter_set = TFHE_PARAMS.with(|p| p.borrow().clone());

/* 
    let mut a: Vec<LweCiphertextOwned<u64>> = Vec::new();
    let start_time = Instant::now();
    for i in 0..100000 {
        //print!("{}\n", i);
        a.push(lwe_encrypt(i as u32));
        //a.push(lwe_encrypt_(i as u32, &parameter_set));
    }
    let end_time = Instant::now();
    print!("run time:\n{:?}\n", end_time.duration_since(start_time));

    return;
*/

    //let l = 4; // 表の分割数
    let width = 11; // 表の幅 (ビット数)

/*
    let large_lut = LargeLUTparams::new(
        //&parameter_set,
        width,
        ThreadCount(8),
    );
*/












    return;


//    let parameter_set = TfheParam::new_params(V1_4_PARAM_MESSAGE_4_CARRY_0_KS_PBS_GAUSSIAN_2M128);

/* 
    let small_lwe_dimension = LweDimension(742);
    let glwe_dimension = GlweDimension(1);
    let polynomial_size = PolynomialSize(2048);
    let lwe_noise_distribution =
        Gaussian::from_dispersion_parameter(StandardDev(0.000007069849454709433), 0.0);
    let glwe_noise_distribution =
        Gaussian::from_dispersion_parameter(StandardDev(0.00000000000000029403601535432533), 0.0);
    let pbs_base_log = DecompositionBaseLog(23);
    let pbs_level = DecompositionLevelCount(1);
    let grouping_factor = LweBskGroupingFactor(2); // Group bits in pairs
    let ciphertext_modulus = CiphertextModulus::new_native();
   
    // Request the best seeder possible, starting with hardware entropy sources and falling back to
    // /dev/random on Unix systems if enabled via cargo features
    let mut boxed_seeder = new_seeder();
    // Get a mutable reference to the seeder as a trait object from the Box returned by new_seeder
    let seeder = boxed_seeder.as_mut();
   
    // Create a generator which uses a CSPRNG to generate secret keys
    let mut secret_generator = SecretRandomGenerator::<DefaultRandomGenerator>::new(seeder.seed());
   
    // Create a generator which uses two CSPRNGs to generate public masks and secret encryption
    // noise
    let mut encryption_generator =
        EncryptionRandomGenerator::<DefaultRandomGenerator>::new(seeder.seed(), seeder);
   
    println!("Generating keys...");
   
    // Generate an LweSecretKey with binary coefficients
    let small_lwe_sk =
        LweSecretKey::generate_new_binary(small_lwe_dimension, &mut secret_generator);
   
    // Generate a GlweSecretKey with binary coefficients
    let glwe_sk =
        GlweSecretKey::generate_new_binary(glwe_dimension, polynomial_size, &mut secret_generator);
   
    // Create a copy of the GlweSecretKey re-interpreted as an LweSecretKey
    let big_lwe_sk = glwe_sk.clone().into_lwe_secret_key();
   
    let mut bsk = LweMultiBitBootstrapKey::new(
        0u64,
        glwe_dimension.to_glwe_size(),
        polynomial_size,
        pbs_base_log,
        pbs_level,
        small_lwe_dimension,
        grouping_factor,
        ciphertext_modulus,
    );
   
    par_generate_lwe_multi_bit_bootstrap_key(
        &small_lwe_sk,
        &glwe_sk,
        &mut bsk,
        glwe_noise_distribution,
        &mut encryption_generator,
    );
   
    let mut multi_bit_bsk = FourierLweMultiBitBootstrapKey::new(
        bsk.input_lwe_dimension(),
        bsk.glwe_size(),
        bsk.polynomial_size(),
        bsk.decomposition_base_log(),
        bsk.decomposition_level_count(),
        bsk.grouping_factor(),
    );
   
    par_convert_standard_lwe_multi_bit_bootstrap_key_to_fourier(&bsk, &mut multi_bit_bsk);
   
    // We don't need the standard bootstrapping key anymore
    drop(bsk);
   
    // Our 4 bits message space
    let message_modulus = 1u64 << 4;
   
    // Our input message
    let input_message = 3u64;
   
    // Delta used to encode 4 bits of message + a bit of padding on u64
    let delta = (1_u64 << 63) / message_modulus;
   
    // Apply our encoding
    let plaintext = Plaintext(input_message * delta);
   
    // Allocate a new LweCiphertext and encrypt our plaintext
    let lwe_ciphertext_in: LweCiphertextOwned<u64> = allocate_and_encrypt_new_lwe_ciphertext(
        &small_lwe_sk,
        plaintext,
        lwe_noise_distribution,
        ciphertext_modulus,
        &mut encryption_generator,
    );
   
    // Now we will use a PBS to compute a multiplication by 2, it is NOT the recommended way of
    // doing this operation in terms of performance as it's much more costly than a multiplication
    // with a cleartext, however it resets the noise in a ciphertext to a nominal level and allows
    // to evaluate arbitrary functions so depending on your use case it can be a better fit.
   
    // Generate the accumulator for our multiplication by 2 using a simple closure
    let mut accumulator: GlweCiphertextOwned<u64> = generate_programmable_bootstrap_glwe_lut(
        polynomial_size,
        glwe_dimension.to_glwe_size(),
        message_modulus as usize,
        ciphertext_modulus,
        delta,
        |x: u64| 2 * x,
    );
    let box_size = polynomial_size.0 / message_modulus as usize;
    glwe_print_tmp(&accumulator, polynomial_size.0, message_modulus, delta, ciphertext_modulus, big_lwe_sk.clone(), 0);
   
    // Allocate the LweCiphertext to store the result of the PBS
    let mut pbs_multiplication_ct = LweCiphertext::new(
        0u64,
        big_lwe_sk.lwe_dimension().to_lwe_size(),
        ciphertext_modulus,
    );
    println!("Performing blind rotation...");
    // Use 4 threads for the multi-bit blind rotation for example
    modulus_switch_multi_bit_blind_rotate_assign(
        &lwe_ciphertext_in,
        &mut accumulator,
        &multi_bit_bsk,
        ThreadCount(4),
        false,
    );
    glwe_print_tmp(&accumulator, polynomial_size.0, message_modulus, delta, ciphertext_modulus, big_lwe_sk.clone(), 0);

    println!("Performing sample extraction...");
    extract_lwe_sample_from_glwe_ciphertext(
        &accumulator,
        &mut pbs_multiplication_ct,
        MonomialDegree(0),
    );
   
    // Decrypt the PBS multiplication result
    let pbs_multiplication_plaintext: Plaintext<u64> =
        decrypt_lwe_ciphertext(&big_lwe_sk, &pbs_multiplication_ct);
   
    // Create a SignedDecomposer to perform the rounding of the decrypted plaintext
    // We pass a DecompositionBaseLog of 5 and a DecompositionLevelCount of 1 indicating we want to
    // round the 5 MSB, 1 bit of padding plus our 4 bits of message
    let signed_decomposer =
        SignedDecomposer::new(DecompositionBaseLog(5), DecompositionLevelCount(1));
   
    // Round and remove our encoding
    let pbs_multiplication_result: u64 =
        signed_decomposer.closest_representable(pbs_multiplication_plaintext.0) / delta;
   
    println!("Checking result...");
    assert_eq!(6, pbs_multiplication_result);
    println!(
        "Multiplication via PBS result is correct! Expected 6, got {pbs_multiplication_result}"
    );

    //return;
*/


    //let mut tfhe_params16 = TfheParam::new_params(PARAM_MESSAGE_3_CARRY_3_KS_PBS_GAUSSIAN_2M128);
    //let mut tfhe_params = TfheParam::new_params(PARAM_MESSAGE_2_CARRY_2_KS_PBS);
    //print!("param.big_lwe_sk: ");  print_lwe_sk(&tfhe_params.big_lwe_sk);  print!("\n");


    //print!("done\n");
/*
    for i in 0..64 {
        let x = lwe_encrypt_int(i, 6, &mut tfhe_params);
        let y = lwe_bit_decomposition_int(&x, 6, &mut tfhe_params);
        print!("i {} ", i);
        print_ctx_list(&y, &mut tfhe_params);
    }
*/

/* 
    print!("message_modulus {} carry_modulus {}\n", tfhe_params.message_modulus.0, tfhe_params.carry_modulus.0);
    print!("delta {}\n", tfhe_params.delta);
    print!("polynomial_size {}\n", tfhe_params.polynomial_size.0);
    print!("ciphertext_modulus {}\n", tfhe_params.ciphertext_modulus);

    let c = lwe_encrypt_big(1, &mut tfhe_params);
    let mut x = vec![lwe_encrypt_big(0, &mut tfhe_params), lwe_encrypt_big(1, &mut tfhe_params)];
    cswap(&c, &mut x, 0, 1, &mut tfhe_params);
    print!("x0 {} x1 {}\n", lwe_decrypt_big(&x[0], &mut tfhe_params), lwe_decrypt_big(&x[1], &mut tfhe_params));
    return;
*/

/* 
//    let a = trivial_const(1, &mut tfhe_params);
//    print!("a {}\n", lwe_decrypt(&a, &mut tfhe_params));
    let b = lwe_encrypt(1, &mut tfhe_params);
    print!("b {}\n", lwe_decrypt(&b, &mut tfhe_params));
    for x in 0..2 {
        for y in 0..2 {
            for z in 0..2 {
                let x_enc = lwe_encrypt_big(x, &mut tfhe_params);
                let y_enc = lwe_encrypt_big(y, &mut tfhe_params);
                let z_enc = lwe_encrypt_big(z, &mut tfhe_params);
                let w_enc = xor_new_big(&x_enc, &y_enc, &mut tfhe_params);
                let v_enc = xor_new_big(&w_enc, &z_enc, &mut tfhe_params);
            //print!("x {} y {} z {}\n", x, y, lwe_decrypt2(&z_enc, &mut tfhe_params));
                print!("x {} y {} z {} v {}\n", x, y, z, lwe_decrypt_big(&v_enc, &mut tfhe_params));
            }
        }
    }
    return;
*/

/*  
    let x = trivial_const(1, &mut tfhe_params);
    print!("x {}\n", lwe_decrypt_tmp(&x, &mut tfhe_params));
    let y = lwe_add(&x, &x, &mut tfhe_params);
    print!("2x {}\n", lwe_decrypt_tmp(&y, &mut tfhe_params));
    let z = not(&y, &mut tfhe_params);
*/

/* 
    test_keyswitch2(&mut tfhe_params, &mut tfhe_params16);
*/

/*  // OK
    //let mut table = vec![0;4];
    let mut table: Vec<LweCiphertextOwned<u64>> = Vec::new();
    for i in 0..16 {
        table.push(trivial_const(i as u64, &mut tfhe_params));
    }
    let mut z = trivial_const(0, &mut tfhe_params);
    for i in 0..16 {
        //let x = trivial_const(i, &mut tfhe_params);
        let x = trivial_const(1, &mut tfhe_params);
        z = lwe_add(&z, &x, &mut tfhe_params);
        print!("z {} \n", lwe_decrypt(&z, &mut tfhe_params));
        //let y = lwe_lookup(&x, &table, &mut tfhe_params);
        let y = lwe_lookup(&z, &table, &mut tfhe_params);
        print!("i {} y {}\n", i, lwe_decrypt(&y, &mut tfhe_params));
    }
    return;
*/

/* 
    let table = vec![0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30];
    let table_glwe = generate_lut(&table, &mut tfhe_params);
    for i in 0..16 {
        //let x = trivial_const(i, &mut tfhe_params);
        let x = lwe_encrypt(i, &mut tfhe_params);
        let y = lwe_lookup_new(&x, &table_glwe, &mut tfhe_params);
        print!("i {} x {} y {}\n", i, lwe_decrypt(&x, &mut tfhe_params), lwe_decrypt_secret_key(&y, &mut tfhe_params));
    }
    return;
*/

/*  
    let mut x = trivial_const_short(0, 4, &mut tfhe_params);
    for _ in 0..128 {
        x = lwe_add(&x, &trivial_const_short(1, 4, &mut tfhe_params), &mut tfhe_params);
        print!("x {}\n", lwe_decrypt_tmp(&x, &mut tfhe_params));
        let y = lwe_denoise(&x, &mut tfhe_params);
        print!("y {}\n", lwe_decrypt_tmp(&y, &mut tfhe_params));
    }
    return;
*/

/*  
    let x = trivial_const(1, &mut tfhe_params);
    print!("x {}\n", lwe_decrypt_tmp(&x, &mut tfhe_params));
    let y = lwe_add(&x, &x, &mut tfhe_params);
    print!("2x {}\n", lwe_decrypt_tmp(&y, &mut tfhe_params));
    let z = not(&y, &mut tfhe_params);
    print!("not(2x) {}\n", lwe_decrypt_tmp(&z, &mut tfhe_params));
    let table = vec![trivial_const(1, &mut tfhe_params), trivial_const(0, &mut tfhe_params)];
    //let a = lwe_lookup_1bit(&y, &table, &mut tfhe_params);
    let a = lwe_lookup(&y, &table, &mut tfhe_params);
    print!("table[2x] {}\n", lwe_decrypt_tmp(&a, &mut tfhe_params));
    //let b = lwe_lookup_1bit(&z, &table, &mut tfhe_params);
    let b = lwe_lookup(&z, &table, &mut tfhe_params);
    print!("table[z] {}\n", lwe_decrypt_tmp(&b, &mut tfhe_params));
    return;
*/


    
//    let bit_size = 4;
//    for i in 0..(1<<bit_size) {
//        let x = lwe_encrypt_short(i, bit_size, &mut tfhe_params);
        /*
        for j in 0..(1<<bit_size) {
            let y = lwe_encrypt_short(j, bit_size, &mut tfhe_params);
            let z = lwe_add(&x, &y, &mut tfhe_params);
            let zi = lwe_decrypt_short(&z, bit_size, &mut tfhe_params);
            print!("i {} j {} z {}\n", i, j, zi);
        }
        */
//        let mut x_bar = x.clone();
//        lwe_ciphertext_opposite_assign(&mut x_bar);
//        let xi = lwe_decrypt_short(&x_bar, bit_size, &mut tfhe_params);
//        print!("i {} {}\n", i, xi);
//    }

/*
    let mut aaa = LweBit::new(1, &mut tfhe_params);
    print!("aaa {}\n", aaa.dec());
    aaa.set_plain(0);
    print!("aaa {}\n", aaa.dec());

    let mut bbb = LweInt::new(99, 16, &mut tfhe_params);
    print!("bbb {}\n", bbb.dec());
    bbb.set_plain(55);
    print!("bbb {}\n", bbb.dec());
*/

/*
    for x in 0..2 {
        for y in 0..2 {
            let xl = lwe_encrypt_short(x, 1, &mut tfhe_params);
            let yl = lwe_encrypt_short(y, 1, &mut tfhe_params);
            let c = xor3(&xl, &yl, &mut tfhe_params);
            print!("x {} {} y {} {} c {}\n", x, lwe_decrypt_short(&xl, 1, &mut tfhe_params), y, lwe_decrypt_short(&yl, 1, &mut tfhe_params), lwe_decrypt_short(&c, 1, &mut tfhe_params));
        }
    }
    //return;
*/

/* 
  for i in 0..16 {
    let x = (i>>1) & 1;
    let y = i & 1;
    let xl = lwe_encrypt(x, &mut tfhe_params);
    let yl = lwe_encrypt( y, &mut tfhe_params);
    let c = xor(&xl, &yl, &mut tfhe_params);
    print!("x {} {} y {} {} c {}\n", x, lwe_decrypt(&xl, &mut tfhe_params), y, lwe_decrypt(&yl, &mut tfhe_params), lwe_decrypt(&c, &mut tfhe_params));
  }
*/

/*
    let mut sum = lwe_encrypt(1, &mut tfhe_params);
    let one = lwe_encrypt(1, &mut tfhe_params);
    for i in 0..10000 {
        //let sum2 = lwe_add(&sum, &one, &mut tfhe_params);
        //let sum = sum2.clone();
        let sum2 = sum.clone();
        lwe_ciphertext_add(&mut sum, &sum2, &one);
        let j = lwe_decrypt(&sum, &mut tfhe_params);
        print!("i {} sum {}\n", i, j);
        if i % 2 != j {
            break;
        }
    }
    return;
*/


/* 
    let x = lwe_encrypt(0, &mut tfhe_params);
    let now = time::Instant::now();
    for _ in 0..10 {
        let x = lwe_encrypt(0, &mut tfhe_params);
    }
    println!("lwe_encrypt {:?}", now.elapsed()); // 0.5 ms
    let y = lwe_encrypt(1, &mut tfhe_params);
    let now = time::Instant::now();
    for _ in 0..10 {
        let y = lwe_encrypt(1, &mut tfhe_params);
    }
    println!("lwe_encrypt {:?}", now.elapsed());
    let mut accumulator = glwe_new(&mut tfhe_params);
    let now = time::Instant::now();
    for _ in 0..10 {
        let mut accumulator = glwe_new(&mut tfhe_params);
    }
    println!("glwe_new {:?}", now.elapsed()); // 0.7 ns
    let now = time::Instant::now();
    for _ in 0..10 {
        packing_two_lwe_into_glwe_index_0_1_bit(
            &tfhe_params.pksk, 
            &x, 
            &y, 
            &mut accumulator,
            tfhe_params.box_size,
        );
    }
    println!("packing {:?}", now.elapsed()); // 85 ms
    let c = lwe_encrypt(1, &mut tfhe_params);
    let now = time::Instant::now();
    for _ in 0..10 {
        let c = lwe_encrypt(1, &mut tfhe_params);
    }
    println!("lwe_encrypt {:?}", now.elapsed());
    let c_bar = not(&c, &mut tfhe_params);
    let now = time::Instant::now();
    for _ in 0..10 {
        let c_bar = not(&c, &mut tfhe_params);
    }
    println!("not {:?}", now.elapsed()); // 16 ns
    let w = and2(&x, &y, &mut tfhe_params);
    let now = time::Instant::now();
    for _ in 0..1 {
        let w = and2(&x, &y, &mut tfhe_params);
    }
    println!("and2 {:?}", now.elapsed()); // 0.7 s
    //println!("and {:?}", now.elapsed()); // 1.2 s
    let w = xor2(&x, &y, &mut tfhe_params);
    let now = time::Instant::now();
    for _ in 0..1 {
        let w = xor2(&x, &y, &mut tfhe_params);
    }
    println!("xor2 {:?}", now.elapsed()); // 0.7 s
    //println!("xor {:?}", now.elapsed()); // 1.2 s
    let c_keyswitched = lwe_keyswitch(&c, &mut tfhe_params);
    let now = time::Instant::now();
    for _ in 0..10 {
        let c_keyswitched = lwe_keyswitch(&c, &mut tfhe_params);
    }
    println!("lwe_keyswitch {:?}", now.elapsed()); // 10 ms
    let now = time::Instant::now();
    for _ in 0..1 {
        modulus_switch_multi_bit_blind_rotate_assign(
                &c_keyswitched,
                      &mut accumulator,
        &tfhe_params.fourier_bsk,
                      tfhe_params.thread_count,
                      true
        );
    }
    println!("blind_rotate {:?}", now.elapsed()); // 0.6 s
    let z = glwe_sample_extract(&accumulator, tfhe_params.box_size/2, &mut tfhe_params);
    let now = time::Instant::now();
    for _ in 0..10 {
        let z = glwe_sample_extract(&accumulator, tfhe_params.box_size/2, &mut tfhe_params);
    }
    println!("sample_extract {:?}", now.elapsed()); // 19 ns

    let mut x = lwe_new_to_glwe(&tfhe_params);
    let now = time::Instant::now();
    for nth in 0..tfhe_params.box_size*2 {
        extract_lwe_sample_from_glwe_ciphertext(
            &accumulator,
            &mut x,
                   MonomialDegree(nth),
        );
        //print!("nth {} x {}\n", nth, lwe_decrypt(&x, &mut tfhe_params));    
    }
    println!("extract {:?}", now.elapsed());


    print!("x {} y {} z {}\n", lwe_decrypt(&x, &mut tfhe_params), lwe_decrypt(&y, &mut tfhe_params), lwe_decrypt(&z, &mut tfhe_params));    
    return;
*/

/* 
    let lut_u64 = vec![0,1,2,3];
    let mut table = glwe_list_short(lut_u64, 4, &mut tfhe_params);
    let lut_u64 = vec![0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15];
    let mut table = glwe_list_short(lut_u64, 4, &mut tfhe_params);
    let mut x = lwe_new_to_glwe(&tfhe_params);
 
    for nth in 0..tfhe_params.box_size*2 {
        extract_lwe_sample_from_glwe_ciphertext(
            &table,
            &mut x,
                   MonomialDegree(nth),
        );
        print!("nth {} x {}\n", nth, lwe_decrypt_short(&x, 4, &mut tfhe_params));    
    }
    return;
*/

/* 
    lut_print_short(&table, 4, &mut tfhe_params);
    //let c = lwe_encrypt_short(0, 1, &mut tfhe_params);
    let c = lwe_encrypt(0, &mut tfhe_params);
    let c_keyswitched = lwe_keyswitch(&c, &mut tfhe_params);
    lut_rotate_short(&c_keyswitched, &mut table, &mut tfhe_params);
    lut_print_short(&table, 4, &mut tfhe_params);
*/

/*
    //let x0 = trivial_const_short(0, 1, &mut tfhe_params);
    //let x1 = trivial_const_short(1, 1, &mut tfhe_params);
    let x0 = trivial_const(3, &mut tfhe_params);
    let x1 = trivial_const(9, &mut tfhe_params);
    print!("x0 {}\n", lwe_decrypt(&x0, &mut tfhe_params));
    print!("x1 {}\n", lwe_decrypt(&x1, &mut tfhe_params));
    let table = vec![x0.clone(), x1.clone()];
    let z = lwe_lookup(&trivial_const_short(0, 1, &mut tfhe_params), &table, &mut tfhe_params);
    print!("z0 {}\n", lwe_decrypt(&z, &mut tfhe_params));
    let z = lwe_lookup(&trivial_const_short(1, 1, &mut tfhe_params), &table, &mut tfhe_params);
    print!("z1 {}\n", lwe_decrypt(&z, &mut tfhe_params));
    return;
*/

/* 
    let mut a = LweInt::new(10000, 16, &mut tfhe_params);
    print!("a {}\n", a.dec(&mut tfhe_params));
    //let mut b = LweInt::new(20000, 16, &tfhe_params);
//    let mut b = &mut a;
    //let b = &mut a;
    let b = a.clone();
    a.set_plain(30000, &mut tfhe_params);
    print!("a {}\n", a.dec(&mut tfhe_params));
    print!("b {}\n", b.dec(&mut tfhe_params));
*/



    // bit size長の配列をAに従って並び替える．
    let bit_size = 4;
    let a_ptx = [0, 0, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1];
    //let a_ptx = [0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0];
    //let a_ptx = [0, 1, 1, 0, 0, 0, 0, 0];
    //let a_ptx = [0, 1, 1, 0];
    // let a_ptx = [0, 1, 0, 1];
    // let a_ptx = [1, 0, 1, 0];
    let value_ptx: Vec<u32> = (0..a_ptx.len() as u32).collect();
    let a_len = a_ptx.len();

    // encryption 

/* 
    let mut a: Vec<LweCiphertextOwned<u64>> = Vec::new();
    for j in 0..a_len {
        let decomped_ctx = lwe_encrypt(a_ptx[j]);
        a.push(decomped_ctx);
    }
 
    let mut value: Vec<Vec<LweCiphertextOwned<u64>>> = Vec::new();
    for j in 0..a_len {
        let value_j = lwe_encrypt_packed(j as u32, 4);
        value.push(value_j);
    }

    print!("A = ");
    print_ctx_list(&a);
    print!("value = ");
    print_ctx_list_packed(&value);
    print!("\n");
*/

    let mut a: Vec<LweShort> = Vec::new();
    for j in 0..a_len {
        let decomped_ctx = LweShort::new(a_ptx[j], /*4*/);
        a.push(decomped_ctx);
    }
 
    let mut value: Vec<LwePacked> = Vec::new();
    for j in 0..a_len {
        let value_j = LwePacked::new(j as u32, 4);
        value.push(value_j);
    }

    print!("A = ");
    print_ctx_list_short(&a);
    print!("value = ");
    print_ctx_list_packed(&value);
    print!("\n");

    let now = time::Instant::now();
    let (network, a_sorted) = benes_construct(&a);
    println!("benes_construct {:?}", now.elapsed());
    print!("sorted A : ");
    print_ctx_list_short(&a_sorted);
    //let now = time::Instant::now();
    //a = benes_apply(&a, &network, &mut tfhe_params);
    //print!("sorted A : ");
    //print_ctx_list(&a, &mut tfhe_params);
    //println!("benes_apply {:?}", now.elapsed());

    //let ksk = lwe_generate_ksk(&mut tfhe_params, &mut tfhe_params16);


    let now = time::Instant::now();
    //let value_new = benes_apply_multibit(&value, &network, &mut tfhe_params);
    //let value_new = benes_apply_multibit_keyswitch(&value, &network, &a, &mut tfhe_params, &ksk);
    let value_new = benes_apply(&value, &network, false);
    println!("benes_apply {:?}", now.elapsed());
    print!("value : ");
    //print_ctx_list_multibit(&value_new, &mut tfhe_params16);
    print_ctx_list_packed(&value_new);

    let now = time::Instant::now();
    //let value_new_inv = benes_apply_inv_multibit(&value, &network, &mut tfhe_params);
    //let value_new_inv = benes_apply_inv_multibit_keyswitch(&value, &network, &a,  &mut tfhe_params, &ksk);
    let value_new_inv = benes_apply(&value, &network, true);
    println!("benes_apply {:?}", now.elapsed());
    print!("value2 : ");
    //print_ctx_list_multibit(&value_new_inv, &mut tfhe_params16);
    print_ctx_list_packed(&value_new_inv);

    // // print!("A = ");
    // // print_ctx_list(&big_lwe_sk, &a_new);
    // // print!("value = ");
    // // print_ctx_list(&big_lwe_sk, &value_new);
    // // print_ctx_list(&big_lwe_sk, &value_new_inv);
    return;


// 1 ビットのソート
    let mut rng = rand::thread_rng();


    let mut n = 16;
    //n = args[1].parse::<i32>().unwrap();
    if args.len() >= 2 {
        n = args[1].parse::<usize>().unwrap();
    }
    let mut a: Vec<LweShort> = Vec::new();
    //let value = [0, 1, 0, 1, 0, 0, 1, 1];
    //let value = [0, 1, 0, 1];
    //let value = [1, 0];
    //n = value.len();
    for j in 0..n {
        let r : u32 = rng.gen();
        //let r = value[j];
        println!("{} ", r % 2);
        //let a_j = lwe_encrypt_short(r % 2, 1, &mut tfhe_params);
        let a_j = LweShort::new(r % 2, /*1*/);
        a.push(a_j);
    }
    let now = time::Instant::now();
    let (network, a_sorted) = benes_construct(&a);
    println!("benes_construct {:?}", now.elapsed());
    print!("sorted A : ");
    print_ctx_list_short(&a_sorted);


  // 整数のソート 
    let value_ptx = [5, 3, 2, 8, 4, 10, 1, 9];
    let mut value: Vec<Vec<LweCiphertextOwned<u64>>> = Vec::new();
    for j in 0..value_ptx.len() {
        let value_j = lwe_encrypt_int(value_ptx[j], 4);
        value.push(value_j);
    }
    print!("value = ");
    print_ctx_list_multibit(&value);
    print!("\n");


    return;
    
    // // let test = func(&vec![1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,]);
    // // print!("{}", test);

/* 
    let pi_ptx = [9,13,15,7,8,0,10,3,6,5,9,8,11,14,12,2];

    let x_ptx = [14,11,13,9,13,11,0,2,6,4,9,6,9,13,5,8];
    let x_len = x_ptx.len();
 
    // encryption 
    let mut x: Vec<Vec<LweCiphertextOwned<u64>>> = Vec::new();
    for j in 0..x_len {
        let mut x_j: Vec<LweCiphertextOwned<u64>> = Vec::new();
        for k in 0..bit_size {
            let decomped_k = (x_ptx[j] >> ((message_modulus.0 as f64).log2() as usize * k)) & 2_u32.pow((message_modulus.0 as f64).log2() as u32) - 1;
            let decomped_ctx_k = allocate_and_encrypt_new_lwe_ciphertext(
                &big_lwe_sk,
                Plaintext(decomped_k as u64 * delta),
                lwe_modular_std_dev,
                ciphertext_modulus,
                &mut encryption_generator,
            );
            x_j.push(decomped_ctx_k);
        }
        x.push(x_j);
    }
    let mut pi: Vec<Vec<LweCiphertextOwned<u64>>> = Vec::new();
    for j in 0..x_len {
        let mut pi_j: Vec<LweCiphertextOwned<u64>> = Vec::new();
        for k in 0..bit_size {
            let decomped_k = (pi_ptx[j] >> ((message_modulus.0 as f64).log2() as usize * k)) & 2_u32.pow((message_modulus.0 as f64).log2() as u32) - 1;
            let decomped_ctx_k = allocate_and_encrypt_new_lwe_ciphertext(
                &big_lwe_sk,
                Plaintext(decomped_k as u64 * delta),
                lwe_modular_std_dev,
                ciphertext_modulus,
                &mut encryption_generator,
            );
            pi_j.push(decomped_ctx_k);
        }
        pi.push(pi_j);
    }

    print!("x : ");
    print_ctx_list_multibit(&big_lwe_sk, &x);
    print!("pi : ");
    print_ctx_list_multibit(&big_lwe_sk, &pi);
    let x_new = appperm(&x, &pi, &ksk, &pksk, &fourier_bsk, thread_count, &big_lwe_sk);
    print!("permutated x : ");
    print_ctx_list_multibit(&big_lwe_sk, &x_new);
*/    

    


    

}

