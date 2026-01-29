use core::panic;
use std::cell::RefCell;
//use bincode::de;
//use tfhe::core_crypto::commons::math::decomposition;
use tfhe::core_crypto::prelude::*;
use tfhe::core_crypto::algorithms::polynomial_algorithms::polynomial_wrapping_monic_monomial_mul_assign;
use tfhe::core_crypto::algorithms::slice_algorithms::{
    slice_wrapping_add_assign,/* slice_wrapping_sub_scalar_mul_assign, */
};

//use tfhe::core_crypto::commons::dispersion;

use tfhe::shortint::{CarryModulus, MessageModulus};
use tfhe::shortint::parameters::ClassicPBSParameters;
//use tfhe::shortint::parameters::ShortintParameterSet;

use crate::{arith::*, print};
use crate::print::*;
use std::fs;
use std::path::Path;
use anyhow::Result;
use serde::{Serialize, de::DeserializeOwned};

pub fn save_bin<T: Serialize>(path: &str, value: &T) -> Result<()> {
    let bytes = bincode::serialize(value)?;
    if let Some(parent) = std::path::Path::new(path).parent() {
        if !parent.as_os_str().is_empty() { fs::create_dir_all(parent)?; }
    }
    fs::write(path, &bytes)?;
    Ok(())
}

pub fn load_bin<T: DeserializeOwned>(path: &str) -> Result<T> {
    let bytes = fs::read(path)?;
    Ok(bincode::deserialize(&bytes)?)
}

pub fn blog(mut x: u64) -> i32 {
    let mut l = -1;
    while x > 0 {
        x >>= 1;
        l += 1;
    }
    return l;
}

////////////////////////////////////////////////////////////////////////////////////
/// 共通の乱数生成器
/// 初めて必要になった時に実行される．
////////////////////////////////////////////////////////////////////////////////////
thread_local!(
    pub static ENCRYPTION_GENERATOR: RefCell<EncryptionRandomGenerator<DefaultRandomGenerator>> = {
        print!("Initializing PRNG...\n"); 
        let mut boxed_seeder = new_seeder();
        let seeder = boxed_seeder.as_mut();
        let encryption_generator = EncryptionRandomGenerator::<DefaultRandomGenerator>::new(seeder.seed(), seeder);
        RefCell::new(encryption_generator)
    }   
);

  
use std::sync::LazyLock;
pub static TFHE_PARAMS2: LazyLock<TfheParam> = LazyLock::new(|| { // 非常に遅い
    print!("Initializing TFHE_PARAMS2...\n");
    TfheParam::new_params(V1_4_PARAM_MESSAGE_4_CARRY_0_KS_PBS_GAUSSIAN_2M128)
});


use tfhe::shortint::parameters::{PARAM_MESSAGE_2_CARRY_2_KS_PBS};
use tfhe::shortint::parameters::v1_4::{V1_4_PARAM_MESSAGE_4_CARRY_0_KS_PBS_GAUSSIAN_2M128};
thread_local!(
    pub static TFHE_PARAMS: RefCell<TfheParam> = {
        //let tfhe_params = TfheParam::new_params(PARAM_MESSAGE_2_CARRY_2_KS_PBS);
        let tfhe_params = TfheParam::new_params(V1_4_PARAM_MESSAGE_4_CARRY_0_KS_PBS_GAUSSIAN_2M128);
        RefCell::new(tfhe_params)
    }   
);

#[derive(Clone)]
pub struct TfheParam {
    pub lwe_dimension: LweDimension,
    pub glwe_dimension: GlweDimension,
    //pub lwe_modular_std_dev: StandardDev,
    pub lwe_noise_distribution: DynamicDistribution<u64>,
    //glwe_modular_std_dev: StandardDev,
    pub glwe_noise_distribution: DynamicDistribution<u64>,
    pbs_base_log: DecompositionBaseLog,
    pbs_level: DecompositionLevelCount,
    pub ks_level: DecompositionLevelCount,
    pub ks_base_log: DecompositionBaseLog,
    grouping_factor: LweBskGroupingFactor,
    //thread_count: ThreadCount,
    pub thread_count: ThreadCount,

    pub small_lwe_sk: LweSecretKey<Vec<u64>>, // 復号に使用（使ってない？）
    pub glwe_sk: GlweSecretKey<Vec<u64>>, // big_lwe_sk の生成に使用
    //pub secret_generator: SecretRandomGenerator<DefaultRandomGenerator>, // 秘密鍵の生成時に使用するだけ

    //pub encryption_generator: EncryptionRandomGenerator<DefaultRandomGenerator>, // bootstrap key, keyswitch key 生成，暗号文生成に使用

    bsk: LweMultiBitBootstrapKey<Vec<u64>>,
    //fourier_bsk: FourierLweMultiBitBootstrapKeyOwned,
    pub multi_bit_bsk: FourierLweMultiBitBootstrapKeyOwned,
    pub ksk: LweKeyswitchKey<Vec<u64>>,
    pub pksk: LwePackingKeyswitchKey<Vec<u64>>,

    pub polynomial_size: PolynomialSize,
    pub ciphertext_modulus: CiphertextModulus<u64>,
    //pub message_modulus: MessageModulus,
    pub message_modulus: u64,
    pub delta: u64,
    pub rounding_bit: u64,
    //pub carry_modulus: CarryModulus,
    pub carry_modulus: u64,
    pub box_size: usize,


    pub big_lwe_sk: LweSecretKey<Vec<u64>>, // 秘密鍵．暗号文の復号に使用
}

/*
impl TfheParam {
  pub fn new_params(params: ClassicPBSParameters) -> Self {

    let small_lwe_dimension = params.lwe_dimension;
    let glwe_dimension = params.glwe_dimension;
    let polynomial_size = params.polynomial_size;

    let lwe_modular_std_dev= params.lwe_noise_distribution;
    let glwe_modular_std_dev = params.glwe_noise_distribution;

    let pbs_base_log = params.pbs_base_log;
    let pbs_level = params.pbs_level;
    let grouping_factor = LweBskGroupingFactor(2);
    let ciphertext_modulus = params.ciphertext_modulus;

    let mut boxed_seeder = new_seeder();
    let seeder = boxed_seeder.as_mut();

    let mut secret_generator =
        SecretRandomGenerator::<DefaultRandomGenerator>::new(seeder.seed());
    //let mut encryption_generator = EncryptionRandomGenerator::<DefaultRandomGenerator>::new(seeder.seed(), seeder);
    
    println!("Generating keys...");

    let small_lwe_sk =
        LweSecretKey::generate_new_binary(small_lwe_dimension, &mut secret_generator);
    let glwe_sk =
        GlweSecretKey::generate_new_binary(glwe_dimension, polynomial_size, &mut secret_generator);

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

    //print!("Generating BSK...\n");
    ENCRYPTION_GENERATOR.with(|gen| {
        let mut encryption_generator = gen.borrow_mut();
        par_generate_lwe_multi_bit_bootstrap_key(
            &small_lwe_sk,
            &glwe_sk,
            &mut bsk,
            glwe_modular_std_dev,
            &mut *encryption_generator,
        );
    });

    let mut fourier_bsk = FourierLweMultiBitBootstrapKey::new(
        bsk.input_lwe_dimension(),
        bsk.glwe_size(),
        bsk.polynomial_size(),
        bsk.decomposition_base_log(),
        bsk.decomposition_level_count(),
        bsk.grouping_factor(),
    );
    par_convert_standard_lwe_multi_bit_bootstrap_key_to_fourier(&bsk, &mut fourier_bsk);

    let message_modulus = params.message_modulus;

    let carry_modulus = params.carry_modulus;
    let delta = (1_u64 << 63) / (message_modulus.0 as u64 * carry_modulus.0 as u64);

    let box_size = polynomial_size.0 / (message_modulus.0 * carry_modulus.0) as usize;



    let ks_level = params.ks_level;
    let ks_base_log = params.ks_base_log;
    //print!("Generating KSK...\n");
    ENCRYPTION_GENERATOR.with(|gen| {
        let mut encryption_generator = gen.borrow_mut();
        let ksk = allocate_and_generate_new_lwe_keyswitch_key(
            &big_lwe_sk,
            &small_lwe_sk,
            ks_base_log,
            ks_level,
            lwe_modular_std_dev,
            ciphertext_modulus,
            &mut *encryption_generator,
        );
        let pksk = allocate_and_generate_new_lwe_packing_keyswitch_key(
            &big_lwe_sk,
            &glwe_sk,
            pbs_base_log,
            pbs_level,
            glwe_modular_std_dev,
            ciphertext_modulus,
            &mut *encryption_generator,
        );

    let p = TfheParam {
        small_lwe_dimension: small_lwe_dimension,
        glwe_dimension: glwe_dimension,
        polynomial_size: polynomial_size,
        lwe_modular_std_dev: lwe_modular_std_dev,
        glwe_modular_std_dev: glwe_modular_std_dev,
        pbs_base_log: pbs_base_log,
        pbs_level: pbs_level,
        ks_level: ks_level,
        ks_base_log: ks_base_log,
        message_modulus: message_modulus,
        carry_modulus: carry_modulus,
        ciphertext_modulus: ciphertext_modulus,
        grouping_factor: grouping_factor,
        thread_count: ThreadCount(8),
        delta: delta, 
        rounding_bit: delta >> 1,
        box_size: box_size,

        small_lwe_sk: small_lwe_sk,
        glwe_sk: glwe_sk,
        //secret_generator: secret_generator,
        //encryption_generator: encryption_generator,
        //encryption_generator: EncryptionRandomGenerator::<DefaultRandomGenerator>::new(seeder.seed(), seeder),
        bsk: bsk,
        fourier_bsk: fourier_bsk,
        ksk: ksk,
        pksk: pksk,

        big_lwe_sk: big_lwe_sk, // 秘密鍵
    };
    print!("Done.\n");
    p
    })
  }  

}
*/

impl TfheParam {
  pub fn new_params(params: ClassicPBSParameters) -> Self {

    let lwe_dimension = params.lwe_dimension;
    let glwe_dimension = params.glwe_dimension;
    let polynomial_size = params.polynomial_size;

    let lwe_noise_distribution= params.lwe_noise_distribution;
    let glwe_noise_distribution = params.glwe_noise_distribution;

    let pbs_base_log = params.pbs_base_log;
    let pbs_level = params.pbs_level;
    //let grouping_factor = LweBskGroupingFactor(2);
    let grouping_factor = LweBskGroupingFactor(1);
    let ciphertext_modulus = params.ciphertext_modulus;

    let mut boxed_seeder = new_seeder();
    let seeder = boxed_seeder.as_mut();

    let mut secret_generator =
        SecretRandomGenerator::<DefaultRandomGenerator>::new(seeder.seed());
    //let mut encryption_generator = EncryptionRandomGenerator::<DefaultRandomGenerator>::new(seeder.seed(), seeder);
    
    println!("Generating keys...1");
    let modulus = params.message_modulus.0 * params.carry_modulus.0;

    let s = format!("./keys/small_lwe_sk_{}.bin", modulus);
    let path = Path::new(&s);
    //let path = Path::new(&format!("../../keygen/keys/small_lwe_sk_{}.bin", params.message_modulus.0));
    let small_lwe_sk = if path.is_file() == false {
        print!("Generating lwe_sk...\n");
        let sk = LweSecretKey::generate_new_binary(lwe_dimension, &mut secret_generator);
        save_bin(&s, &sk).unwrap();
        sk
    } else {
        //load_bin(&format!("../../keygen/keys/small_lwe_sk_{}.bin", params.message_modulus.0)).unwrap()
        print!("loading lwe_sk...\n");
        load_bin(&s).unwrap()
    };

    let s = format!("./keys/glwe_sk_{}.bin", modulus);
    let path = Path::new(&s);
    let glwe_sk = if path.is_file() == false {
        print!("Generating glwe_sk...\n");
        let sk = GlweSecretKey::generate_new_binary(glwe_dimension, polynomial_size, &mut secret_generator);
        save_bin(&s, &sk).unwrap();
        sk
    } else {
        print!("loading glwe_sk...\n");
        load_bin(&s).unwrap()
    };

    let s = format!("./keys/big_lwe_sk_{}.bin", modulus);
    let path = Path::new(&s);
    let big_lwe_sk: LweSecretKey<Vec<u64>> = if path.is_file() == false {
        print!("Generating bit_lwe_sk...\n");
        let sk = glwe_sk.clone().into_lwe_secret_key();
        save_bin(&s, &sk).unwrap();
        sk
    } else {
        print!("loading bit_lwe_sk...\n");
        load_bin(&s).unwrap()
    };

    let mut bsk = LweMultiBitBootstrapKey::new(
        0u64,
        glwe_dimension.to_glwe_size(),
        polynomial_size,
        pbs_base_log,
        pbs_level,
        lwe_dimension,
        grouping_factor,
        ciphertext_modulus,
    );

    let mut multi_bit_bsk: FourierLweMultiBitBootstrapKeyOwned;
    let s = format!("./keys/mb_bsk_{}.bin", modulus);
    let path = Path::new(&s);
    if path.is_file() == false {
        print!("Generating multi_bit_bsk...\n");
        multi_bit_bsk = FourierLweMultiBitBootstrapKey::new(
            bsk.input_lwe_dimension(),
            bsk.glwe_size(),
            bsk.polynomial_size(),
            bsk.decomposition_base_log(),
            bsk.decomposition_level_count(),
            bsk.grouping_factor(),
        );
        ENCRYPTION_GENERATOR.with(|g| {
            let mut encryption_generator = g.borrow_mut();
            par_generate_lwe_multi_bit_bootstrap_key(
                &small_lwe_sk,
                &glwe_sk,
                &mut bsk,
                glwe_noise_distribution,
                &mut *encryption_generator,
            );
        });

        par_convert_standard_lwe_multi_bit_bootstrap_key_to_fourier(&bsk, &mut multi_bit_bsk);
        save_bin(&s, &multi_bit_bsk).unwrap();
    } else {
        print!("loading multi_bit_bsk...\n");
        multi_bit_bsk = load_bin(&s).unwrap();
    }

    
    //let message_modulus = params.message_modulus.0;
    //let carry_modulus = params.carry_modulus.0;
    let message_modulus = 4;
    let carry_modulus = 4;

    let delta = (1_u64 << 63) / (message_modulus as u64 * carry_modulus as u64);

    let box_size = polynomial_size.0 / (message_modulus * carry_modulus) as usize;



    let ks_level = params.ks_level;
    let ks_base_log = params.ks_base_log;
ENCRYPTION_GENERATOR.with(|g| {
    let mut encryption_generator = g.borrow_mut();
    let ksk: LweKeyswitchKey<Vec<u64>>;
    let pksk: LwePackingKeyswitchKey<Vec<u64>>;
    //print!("Generating KSK...\n");
        let s = format!("./keys/ksk_{}.bin", modulus);
        let path = Path::new(&s);
        if path.is_file() == false {
            print!("Generating KSK...\n");
            ksk = allocate_and_generate_new_lwe_keyswitch_key(
                &big_lwe_sk,
                &small_lwe_sk,
                ks_base_log,
                ks_level,
                lwe_noise_distribution,
                ciphertext_modulus,
                &mut *encryption_generator,
            );
            save_bin(&s, &ksk).unwrap();
        } else {
            print!("loading KSK...\n");
            ksk = load_bin(&s).unwrap();
        }
        let s = format!("./keys/pksk_{}.bin", modulus);
        let path = Path::new(&s);
        if path.is_file() == false {
            print!("Generating PKSK...\n");
            pksk = allocate_and_generate_new_lwe_packing_keyswitch_key(
                &big_lwe_sk,
                &glwe_sk,
                pbs_base_log,
                pbs_level,
                glwe_noise_distribution,
                ciphertext_modulus,
                &mut *encryption_generator,
            );
            save_bin(&s, &pksk).unwrap();
        } else {
            print!("loading PKSK...\n");
            pksk = load_bin(&s).unwrap();
        }

        let p = TfheParam {
            lwe_dimension: lwe_dimension,
            glwe_dimension: glwe_dimension,
            polynomial_size: polynomial_size,
            lwe_noise_distribution: lwe_noise_distribution,
            glwe_noise_distribution: glwe_noise_distribution,
            pbs_base_log: pbs_base_log,
            pbs_level: pbs_level,
            ks_level: ks_level,
            ks_base_log: ks_base_log,
            message_modulus: message_modulus,
            carry_modulus: carry_modulus,
            ciphertext_modulus: ciphertext_modulus,
            grouping_factor: grouping_factor,
            thread_count: ThreadCount(8),
            delta: delta, 
            rounding_bit: delta >> 1,
            box_size: box_size,

            small_lwe_sk: small_lwe_sk,
            glwe_sk: glwe_sk,
            //secret_generator: secret_generator,
            //encryption_generator: encryption_generator,
            //encryption_generator: EncryptionRandomGenerator::<DefaultRandomGenerator>::new(seeder.seed(), seeder),
            bsk: bsk,
            multi_bit_bsk: multi_bit_bsk,
            ksk: ksk,
            pksk: pksk,

            big_lwe_sk: big_lwe_sk, // 秘密鍵
        };
        print!("Done.\n");
        p
    })
  }  

}

pub fn lwe_get_modulus() -> u64 {
    let modulus = TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        tfhe_params.message_modulus
    });
    return modulus;
}

pub fn lwe_get_carry_modulus() -> u64 {
    let modulus = TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        tfhe_params.carry_modulus
    });
    return modulus;
}



////////////////////////////////////////////////////////////////////////////////
/// 整数の表現は3通り
/// 1. ビット (LweShort)
/// 2. 任意の桁数の整数 (LweInt)
///    1つのLWE暗号文に2ビットずつ保存．算術演算ができる．
/// 3. 任意の桁数の整数（パック済み）(LwePacked)
///    1つのLWE暗号文に4ビットずつ保存．算術演算ができない．
////////////////////////////////////////////////////////////////////////////////

/*
pub fn lwe_encrypt_big0(plain_x: u32, tfhe_params: &TfheParam) -> LweCiphertext<Vec<u64>> {
    ENCRYPTION_GENERATOR.with(|gen| {
        let mut encryption_generator = gen.borrow_mut();
        let lwe_x = allocate_and_encrypt_new_lwe_ciphertext(
            &tfhe_params.big_lwe_sk,
            Plaintext(plain_x as u64 * tfhe_params.delta),
            tfhe_params.lwe_modular_std_dev,
            tfhe_params.ciphertext_modulus,
            //&mut tfhe_params.encryption_generator,
            &mut *encryption_generator,
        );
        //return lwe_x;
        lwe_x
    })
}


pub fn lwe_get_modulus() -> u64 {
    let modulus = TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        tfhe_params.message_modulus
    });
    return modulus;
}

pub fn lwe_get_carry_modulus() -> u64 {
    let modulus = TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        tfhe_params.carry_modulus
    });
    return modulus;
}
*/

pub fn lwe_encrypt0(plain_x: u32) -> LweCiphertext<Vec<u64>> {
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        ENCRYPTION_GENERATOR.with(|gen| {
            let mut encryption_generator = gen.borrow_mut();
            let lwe_x = allocate_and_encrypt_new_lwe_ciphertext(
                &tfhe_params.big_lwe_sk,
                Plaintext(plain_x as u64 * tfhe_params.delta),
                tfhe_params.lwe_noise_distribution,
                tfhe_params.ciphertext_modulus,
                //&mut tfhe_params.encryption_generator,
                &mut *encryption_generator,
            );
            //return lwe_x;
            lwe_x
        })
    })
}

pub fn lwe_encrypt(plain_x: u32) -> LweCiphertext<Vec<u64>> {
    //let tfhe_params = &TFHE_PARAMS2.clone();
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        ENCRYPTION_GENERATOR.with(|gen| {
            let mut encryption_generator = gen.borrow_mut();
            //let tfhe_params = &TFHE_PARAMS2.clone();
            let lwe_x = allocate_and_encrypt_new_lwe_ciphertext(
                &tfhe_params.big_lwe_sk,
                Plaintext(plain_x as u64 * tfhe_params.delta),
                tfhe_params.lwe_noise_distribution,
                tfhe_params.ciphertext_modulus,
                //&mut tfhe_params.encryption_generator,
                &mut *encryption_generator,
            );
            //return lwe_x;
            lwe_x
        })
    })
}

/* 
pub fn lwe_encrypt_(plain_x: u32, tfhe_params: &TfheParam) -> LweCiphertext<Vec<u64>> {
    //let tfhe_params = &TFHE_PARAMS2.clone();
    //TFHE_PARAMS.with(|params| {
    //    let tfhe_params = params.borrow();
        ENCRYPTION_GENERATOR.with(|gen| {
            let mut encryption_generator = gen.borrow_mut();
            //let tfhe_params = &TFHE_PARAMS2.clone();
            let lwe_x = allocate_and_encrypt_new_lwe_ciphertext(
                &tfhe_params.big_lwe_sk,
                Plaintext(plain_x as u64 * tfhe_params.delta),
                tfhe_params.lwe_noise_distribution,
                tfhe_params.ciphertext_modulus,
                //&mut tfhe_params.encryption_generator,
                &mut *encryption_generator,
            );
            //return lwe_x;
            lwe_x
        })
    //})
}
*/

////////////////////////////////////////////////////////////////////////////////
/// 整数を分解して暗号化
/// (2 bit ずつに分解)
////////////////////////////////////////////////////////////////////////////////
/* 
pub fn lwe_encrypt_int0(plain_x: u32, bit_size: usize, tfhe_params: &TfheParam) -> Vec<LweCiphertext<Vec<u64>>> {
    let mut value: Vec<LweCiphertextOwned<u64>> = Vec::new();
    //let modulus = tfhe_params.message_modulus.0 * tfhe_params.carry_modulus.0;
    let modulus = tfhe_params.message_modulus.0;
    let w = blog(modulus -1) as u32 +1;
    //let w = 1;

    let mask = 1 << w;
    for k in 0..(bit_size as u32+w-1) as u32 /w {
        let decomped_k = (plain_x >> (w * k)) & (mask-1);
        let decomped_ctx_k = lwe_encrypt_big0(decomped_k, tfhe_params);
        value.push(decomped_ctx_k);
    }
    return value;
}
*/
pub fn lwe_encrypt_int(plain_x: u32, bit_size: usize) -> Vec<LweCiphertext<Vec<u64>>> {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let mut value: Vec<LweCiphertextOwned<u64>> = Vec::new();
        //let modulus = tfhe_params.message_modulus.0 * tfhe_params.carry_modulus.0;
        let modulus = tfhe_params.message_modulus;
        let w = blog(modulus -1) as u32 +1;
        //let w = 1;

        let mask = 1 << w;
        for k in 0..(bit_size as u32+w-1) as u32 /w {
            let decomped_k = (plain_x >> (w * k)) & (mask-1);
            let decomped_ctx_k = lwe_encrypt(decomped_k);
            value.push(decomped_ctx_k);
        }
        //return value;
        value
    })
}

////////////////////////////////////////////////////////////////////////////////
/// 整数を分解して暗号化
/// (4 bit ずつに分解)
////////////////////////////////////////////////////////////////////////////////
pub fn lwe_encrypt_packed(plain_x: u32, bit_size: usize) -> Vec<LweCiphertext<Vec<u64>>> {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let mut value: Vec<LweCiphertextOwned<u64>> = Vec::new();
        let modulus = tfhe_params.message_modulus * tfhe_params.carry_modulus;
        let w = blog(modulus -1) as u32 +1;
        //let w = 1;

        let mask = 1 << w;
        for k in 0..(bit_size as u32+w-1) as u32 /w {
            let decomped_k = (plain_x >> (w * k)) & (mask-1);
            let decomped_ctx_k = lwe_encrypt(decomped_k);
            value.push(decomped_ctx_k);
        }
        //return value;
        value
    })
}


////////////////////////////////////////////////////////////////////////////////
/// ビット分解された整数の，下から ith ビット目を取得する
/// (ビット分解されていない整数に対しては使えない)
////////////////////////////////////////////////////////////////////////////////
/* 
pub fn lwe_geti_int0(lwe: &Vec<LweCiphertext<Vec<u64>>>, i: usize, tfhe_params: &TfheParam) -> LweCiphertext<Vec<u64>> {
    //return lwe[i].clone();
    //let modulus = tfhe_params.message_modulus.0 * tfhe_params.carry_modulus.0;
    let modulus = tfhe_params.message_modulus.0;
    let w = blog(modulus -1) as u64 +1;
    let q = i as u64 / w;
    let r = i as u64 % w;
    let x = &lwe[q as usize];

    let table: Vec<u64> = (0..(1 << w)).map(|j| ((j >> r) & 1 as u64)).collect();
    let table_glwe = generate_lut_plain0(&table, tfhe_params);

    let ans = lwe_lookup_glwe0(&x, &table_glwe, tfhe_params);
    return ans;
}
*/

pub fn lwe_geti_int(lwe: &Vec<LweCiphertext<Vec<u64>>>, i: usize) -> LweCiphertext<Vec<u64>> {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        //let modulus = tfhe_params.message_modulus.0 * tfhe_params.carry_modulus.0;
        let modulus = tfhe_params.message_modulus;
        let w = blog(modulus -1) as u64 +1;
        //let q = i as u64 / modulus;
        //let r = i as u64 % modulus;
        let q = i as u64 / w;
        let r = i as u64 % w;
        let x = &lwe[q as usize];

        let table: Vec<u64> = (0..(1 << w)).map(|j| (j >> r) & 1 as u64).collect();
        let table_glwe = generate_lut_plain(&table);

        let ans = lwe_lookup_glwe(&x, &table_glwe);
        //return ans;
        ans
    })
}

pub fn lwe_geti_packed(lwe: &Vec<LweCiphertext<Vec<u64>>>, i: usize) -> LweCiphertext<Vec<u64>> {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let modulus = tfhe_params.message_modulus * tfhe_params.carry_modulus;
        let w = blog(modulus -1) as u64 +1;
        let q = i as u64 / w;
        let r = i as u64 % w;
        let x = &lwe[q as usize];

        let table: Vec<u64> = (0..(1 << w)).map(|j| (j >> r) & 1 as u64).collect();
        let table_glwe = generate_lut_plain(&table);

        let ans = lwe_lookup_glwe(&x, &table_glwe);
        //return ans;
        ans
    })
}

/* 
pub fn lwe_decrypt_big0(lwe: &LweCiphertext<Vec<u64>>, tfhe_params: &TfheParam) -> u64 {
    let message_modulus = tfhe_params.message_modulus;
    let delta = tfhe_params.delta; 
    let rounding_bit = tfhe_params.rounding_bit;

    let lwe_plaintext: Plaintext<u64> =
        decrypt_lwe_ciphertext(&tfhe_params.big_lwe_sk, &lwe);
    let lwe_result: u64 =
        (lwe_plaintext.0.wrapping_add((lwe_plaintext.0 & rounding_bit) << 1) / delta) % message_modulus.0 as u64;
    
    return lwe_result;
}
*/

pub fn lwe_decrypt(lwe: &LweCiphertext<Vec<u64>>) -> u64 {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        //let message_modulus = tfhe_params.message_modulus;
        let delta = tfhe_params.delta; 
        let rounding_bit = tfhe_params.rounding_bit;

        let lwe_plaintext: Plaintext<u64> =
            decrypt_lwe_ciphertext(&tfhe_params.big_lwe_sk, &lwe);
        let lwe_result: u64 =
            //(lwe_plaintext.0.wrapping_add((lwe_plaintext.0 & rounding_bit) << 1) / delta) % message_modulus.0 as u64;
            (lwe_plaintext.0.wrapping_add((lwe_plaintext.0 & rounding_bit) << 1) / delta) as u64;
    
        //return lwe_result;
        lwe_result
    })
}

/* 
pub fn lwe_decrypt_int0(lwe: &Vec<LweCiphertext<Vec<u64>>>, bit_size: usize, tfhe_params: &TfheParam) -> u64 {
    //let modulus = tfhe_params.message_modulus.0 * tfhe_params.carry_modulus.0;
    let modulus = tfhe_params.message_modulus.0;
    let delta = tfhe_params.delta; 
    let rounding_bit = tfhe_params.rounding_bit;
    //let w = blog(message_modulus.0 as u64 -1) as u32 +1;
    let w = blog(modulus -1) as u32 +1;
    //let w  = 1;

    let mut sum = 0;
    for j in 0..((bit_size as u32 +w-1) /w) as usize {
        let decomped_plaintext: Plaintext<u64> =
            decrypt_lwe_ciphertext(&tfhe_params.big_lwe_sk, &lwe[j]);
        let decomped_result: u64 =
            (decomped_plaintext.0.wrapping_add((decomped_plaintext.0 & rounding_bit) << 1) / delta) % modulus as u64;
        sum += decomped_result << (w * j as u32);
    }
    return sum;
}
*/

pub fn lwe_decrypt_int(lwe: &Vec<LweCiphertext<Vec<u64>>>, bit_size: usize) -> u64 {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        //let modulus = tfhe_params.message_modulus.0 * tfhe_params.carry_modulus.0;
        let modulus = tfhe_params.message_modulus;
        let delta = tfhe_params.delta; 
        let rounding_bit = tfhe_params.rounding_bit;
        //let w = blog(message_modulus.0 as u64 -1) as u32 +1;
        let w = blog(modulus -1) as u32 +1;
        //let w  = 1;

        let mut sum = 0;
        for j in 0..((bit_size as u32 +w-1) /w) as usize {
            let decomped_plaintext: Plaintext<u64> =
                decrypt_lwe_ciphertext(&tfhe_params.big_lwe_sk, &lwe[j]);
            let decomped_result: u64 =
                (decomped_plaintext.0.wrapping_add((decomped_plaintext.0 & rounding_bit) << 1) / delta) % modulus as u64;
            //print!("lwe_decrypt_int: k={}, decomped_result={}\n", j, decomped_result);
            sum += decomped_result << (w * j as u32);
        }
        //return sum;
        sum
    })
}

pub fn lwe_decrypt_packed(lwe: &Vec<LweCiphertext<Vec<u64>>>, bit_size: usize) -> u64 {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let modulus = tfhe_params.message_modulus * tfhe_params.carry_modulus;
        let delta = tfhe_params.delta; 
        let rounding_bit = tfhe_params.rounding_bit;
        //let w = blog(message_modulus.0 as u64 -1) as u32 +1;
        let w = blog(modulus -1) as u32 +1;
        //let w  = 1;

        let mut sum = 0;
        for j in 0..((bit_size as u32 +w-1) /w) as usize {
            let decomped_plaintext: Plaintext<u64> =
                decrypt_lwe_ciphertext(&tfhe_params.big_lwe_sk, &lwe[j]);
            let decomped_result: u64 =
                (decomped_plaintext.0.wrapping_add((decomped_plaintext.0 & rounding_bit) << 1) / delta) % modulus as u64;
            sum += decomped_result << (w * j as u32);
        }
        //return sum;
        sum
    })
}

/* 
pub fn trivial_const0(x: u64, tfhe_params: &TfheParam) -> LweCiphertextOwned<u64> {
    let trivial_value = allocate_and_trivially_encrypt_new_lwe_ciphertext(
        LweSize(tfhe_params.polynomial_size.0*tfhe_params.glwe_dimension.0+1),
         Plaintext(x * tfhe_params.delta), tfhe_params.ciphertext_modulus);
    return trivial_value;
}
*/

pub fn trivial_const(x: u64) -> LweCiphertextOwned<u64> {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let trivial_value = allocate_and_trivially_encrypt_new_lwe_ciphertext(
            LweSize(tfhe_params.polynomial_size.0*tfhe_params.glwe_dimension.0+1),
             Plaintext(x * tfhe_params.delta), tfhe_params.ciphertext_modulus);
        //return trivial_value;
        trivial_value
    })
}

/* 
fn lwe_new_to_lwe0(tfhe_params: &TfheParam) -> LweCiphertextOwned<u64> {
    let x = LweCiphertext::new(
        0,
        tfhe_params.small_lwe_dimension.to_lwe_size(),
        tfhe_params.ciphertext_modulus,
    );
    return x;    
}
*/

fn lwe_new_to_lwe() -> LweCiphertextOwned<u64> {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let x = LweCiphertext::new(
            0,
            tfhe_params.lwe_dimension.to_lwe_size(),
            tfhe_params.ciphertext_modulus,
        );
        //return x;
        x
    })    
}

/* 
pub fn glwe_new0(tfhe_params: &TfheParam) -> GlweCiphertextOwned<u64> {
    let x = GlweCiphertext::new(
        0u64,
        tfhe_params.glwe_dimension.to_glwe_size(),
        tfhe_params.polynomial_size,
        tfhe_params.ciphertext_modulus,
    );
    return x;
}
*/

pub fn glwe_new() -> GlweCiphertextOwned<u64> {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let x = GlweCiphertext::new(
            0u64,
            tfhe_params.glwe_dimension.to_glwe_size(),
            tfhe_params.polynomial_size,
            tfhe_params.ciphertext_modulus,
        );
        //return x;
        x
    })
}

/* 
pub fn lwe_keyswitch0(a: &LweCiphertextOwned<u64>, tfhe_params: &TfheParam) -> LweCiphertextOwned<u64> {
    let mut a_keyswitched = lwe_new_to_lwe0(tfhe_params);
    par_keyswitch_lwe_ciphertext(&tfhe_params.ksk, &a, &mut a_keyswitched);
    return a_keyswitched;
}
*/
pub fn lwe_keyswitch(a: &LweCiphertextOwned<u64>) -> LweCiphertextOwned<u64> {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let mut a_keyswitched = lwe_new_to_lwe();
        par_keyswitch_lwe_ciphertext(&tfhe_params.ksk, &a, &mut a_keyswitched);
        //return a_keyswitched;
        a_keyswitched
    })
}


/* 
pub fn glwe_sample_extract_big0(glwe: &GlweCiphertextOwned<u64>, nth: usize, tfhe_params: &TfheParam) -> LweCiphertextOwned<u64> {

    let equivalent_lwe_sk = tfhe_params.big_lwe_sk.clone();
    let mut extracted_sample = LweCiphertext::new(
     0u64,
        equivalent_lwe_sk.lwe_dimension().to_lwe_size(),
        tfhe_params.ciphertext_modulus,
    );

    extract_lwe_sample_from_glwe_ciphertext(
        &glwe,
        &mut extracted_sample,
               MonomialDegree(nth),
    );
    return extracted_sample;
}
*/

pub fn glwe_sample_extract(glwe: &GlweCiphertextOwned<u64>, nth: usize) -> LweCiphertextOwned<u64> {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();

        let equivalent_lwe_sk = tfhe_params.big_lwe_sk.clone();
        let mut extracted_sample = LweCiphertext::new(
        0u64,
            equivalent_lwe_sk.lwe_dimension().to_lwe_size(),
            tfhe_params.ciphertext_modulus,
        );

        extract_lwe_sample_from_glwe_ciphertext(
            &glwe,
            &mut extracted_sample,
                   MonomialDegree(nth),
        );
        //return extracted_sample;
        extracted_sample
    })
}

/* 
pub fn cmux0(c: &LweCiphertextOwned<u64>, x: &LweCiphertextOwned<u64>, y: &LweCiphertextOwned<u64>,
    tfhe_params: &TfheParam) -> (LweCiphertextOwned<u64>, LweCiphertextOwned<u64>) {

    let table = vec![x.clone(), y.clone()];

    let z = lwe_lookup0(c, &table, tfhe_params);
    let sum = lwe_add0(x, y, tfhe_params);
    let w = lwe_sub0(&sum, &z, tfhe_params);

    return (z, w);
}
*/

pub fn cmux(c: &LweCiphertextOwned<u64>, x: &LweCiphertextOwned<u64>, y: &LweCiphertextOwned<u64>) -> (LweCiphertextOwned<u64>, LweCiphertextOwned<u64>) {
        let table = vec![x.clone(), y.clone()];

        let z = lwe_lookup(c, &table);
        let sum = lwe_add(x, y);
        let w = lwe_sub(&sum, &z);

        //return (z, w);
        (z, w)
}

pub fn cmux_short(c: &LweShort, x: &LweShort, y: &LweShort) -> (LweShort, LweShort) {
        let table = vec![x.get_lwe(), y.get_lwe()];

        let z = lwe_lookup(&c.get_lwe(), &table);
        let sum = lwe_add(&x.get_lwe(), &y.get_lwe());
        let w = lwe_sub(&sum, &z);

        //return (z, w);
        (LweShort::set_lwe(z, /*x.bit_size*/), LweShort::set_lwe(w, /*x.bit_size*/))
}

pub fn cmux_int(c: &LweCiphertextOwned<u64>, x: &Vec<LweCiphertextOwned<u64>>, y: &Vec<LweCiphertextOwned<u64>>) -> (Vec<LweCiphertextOwned<u64>>, Vec<LweCiphertextOwned<u64>>) {
        let mut z: Vec<LweCiphertextOwned<u64>> = Vec::new();
        let mut w: Vec<LweCiphertextOwned<u64>> = Vec::new();

        for bit in 0..x.len() {
            //z.push(cmux(&c, &x[bit], &y[bit], tfhe_params));
            let (z0, w0) = cmux(&c, &x[bit], &y[bit]);
            z.push(z0);
            w.push(w0);
        }
        //return (z, w);
        (z, w)
}

pub fn cmux_Int(c: &LweShort, x: &LweInt, y: &LweInt) -> (LweInt, LweInt) {
        let mut z: Vec<LweCiphertextOwned<u64>> = Vec::new();
        let mut w: Vec<LweCiphertextOwned<u64>> = Vec::new();

        for i in 0..x.x.len() {
            //z.push(cmux(&c, &x[bit], &y[bit], tfhe_params));
            let (z0, w0) = cmux(&c.get_lwe(), &x.x[i], &y.x[i]);
            z.push(z0);
            w.push(w0);
        }
        //return (z, w);
        (LweInt::set_lwe(z, x.bit_size), LweInt::set_lwe(w, x.bit_size))
}

pub fn cmux_packed(c: &LweShort, x: &LwePacked, y: &LwePacked) -> (LwePacked, LwePacked) {
        let mut z: Vec<LweCiphertextOwned<u64>> = Vec::new();
        let mut w: Vec<LweCiphertextOwned<u64>> = Vec::new();

        for i in 0..x.x.len() {
            let (z0, w0) = cmux(&c.get_lwe(), &x.get_lwe()[i], &y.get_lwe()[i]);
            z.push(z0);
            w.push(w0);
        }
        (LwePacked::set_lwe(z, x.bit_size), LwePacked::set_lwe(w, x.bit_size))
}

pub fn cswap(c: &LweCiphertextOwned<u64>, x: &mut Vec<LweCiphertextOwned<u64>>, i: usize, j: usize) {

    let (x_i_new, x_j_new) = cmux(c, &x[i], &x[j]);
    x[i] = x_i_new;
    x[j] = x_j_new;
}

pub fn cswap_short(c: &LweShort, x: &mut Vec<LweShort>, i: usize, j: usize) {

    let (x_i_new, x_j_new) = cmux_short(c, &x[i], &x[j]);
    x[i] = x_i_new;
    x[j] = x_j_new;
}

pub fn cswap_multibit(c: &LweCiphertextOwned<u64>, x: &mut Vec<Vec<LweCiphertextOwned<u64>>>, i: usize, j: usize) {

    let (x_i_new, x_j_new) = cmux_int(&c, &x[i], &x[j]);
    x[i] = x_i_new;
    x[j] = x_j_new;
}

pub fn cswap_packed(c: &LweShort, x: &mut Vec<LwePacked>, i: usize, j: usize) {

    let (x_i_new, x_j_new) = cmux_packed(&c, &x[i], &x[j]);
    x[i] = x_i_new;
    x[j] = x_j_new;
}


///////////////////////////////////////////////////////////////////////////
/// LWE の配列から LUT を生成する
/// carry ビットと message ビットを連結した値に対する表とみなしている
///////////////////////////////////////////////////////////////////////////
/* 
pub fn generate_lut_lwe0(table: &Vec<LweCiphertextOwned<u64>>, tfhe_params: &TfheParam) -> GlweCiphertextOwned<u64> {
    let mut output_glwe_ciphertext = glwe_new0(tfhe_params);
    let lwe_pksk: &LwePackingKeyswitchKeyOwned<u64> = &tfhe_params.pksk;

    let table_len = table.len();
    //let box_size = tfhe_params.polynomial_size.0 / table_len;
    //let box_size = tfhe_params.polynomial_size.0 / tfhe_params.message_modulus.0 as usize;
    let box_size = tfhe_params.polynomial_size.0 / (tfhe_params.message_modulus.0 * tfhe_params.carry_modulus.0) as usize;


    output_glwe_ciphertext.as_mut().fill(0);
    let mut buffer = GlweCiphertext::new(
        0u64,
        output_glwe_ciphertext.glwe_size(),
        output_glwe_ciphertext.polynomial_size(),
        output_glwe_ciphertext.ciphertext_modulus(),
    );

    for i in 0..table_len {
        keyswitch_lwe_ciphertext_into_glwe_ciphertext(&lwe_pksk, &table[i], &mut buffer);
        for degree in 0..box_size {
            let mut buffer_iter = buffer.clone();
            buffer_iter
                .as_mut_polynomial_list()
                .iter_mut()
                .for_each(|mut poly| {
                    polynomial_wrapping_monic_monomial_mul_assign(&mut poly, MonomialDegree(degree + i*box_size))
                });
            slice_wrapping_add_assign(output_glwe_ciphertext.as_mut(), buffer_iter.as_ref());
        }
            
    }

    return output_glwe_ciphertext;
}
*/

pub fn generate_lut_lwe(table: &Vec<LweCiphertextOwned<u64>>) -> GlweCiphertextOwned<u64> {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let mut output_glwe_ciphertext = glwe_new();
        let lwe_pksk: &LwePackingKeyswitchKeyOwned<u64> = &tfhe_params.pksk;

        let table_len = table.len();
        //let box_size = tfhe_params.polynomial_size.0 / table_len;
        //let box_size = tfhe_params.polynomial_size.0 / tfhe_params.message_modulus.0 as usize;
        let box_size = tfhe_params.polynomial_size.0 / (tfhe_params.message_modulus * tfhe_params.carry_modulus) as usize;


        output_glwe_ciphertext.as_mut().fill(0);
        let mut buffer = GlweCiphertext::new(
            0u64,
            output_glwe_ciphertext.glwe_size(),
            output_glwe_ciphertext.polynomial_size(),
            output_glwe_ciphertext.ciphertext_modulus(),
        );

        for i in 0..table_len {
            keyswitch_lwe_ciphertext_into_glwe_ciphertext(&lwe_pksk, &table[i], &mut buffer);
            for degree in 0..box_size {
                let mut buffer_iter = buffer.clone();
                buffer_iter
                    .as_mut_polynomial_list()
                    .iter_mut()
                    .for_each(|mut poly| {
                        polynomial_wrapping_monic_monomial_mul_assign(&mut poly, MonomialDegree(degree + i*box_size))
                    });
                slice_wrapping_add_assign(output_glwe_ciphertext.as_mut(), buffer_iter.as_ref());
            }
            
        }

        //return output_glwe_ciphertext;
        output_glwe_ciphertext
    })
}


////////////////////////////////////////////////////////////////////////////
/// 表を引く
/// 表は LWE 暗号文の配列で与えられる
////////////////////////////////////////////////////////////////////////////
/* 
pub fn lwe_lookup0(a: &LweCiphertextOwned<u64>, table: &Vec<LweCiphertextOwned<u64>>, tfhe_params: &TfheParam)
    -> LweCiphertextOwned<u64> {
    //let message_modulus = tfhe_params.message_modulus.0 as u64;
    //print!("lwe_lookup message_modulus {}\n", message_modulus);
    //print!("lwe_lookup box_size {}\n", tfhe_params.box_size);
    let box_size = tfhe_params.box_size as u64;
    let mut accumulator = generate_lut_lwe0(table, tfhe_params);

    //let a_dec = lwe_decrypt(&a, tfhe_params);
    //print!("lwe_lookup a {} \n", a_dec);
    //let a_enc = lwe_encrypt_short(a_dec as u32, 1, tfhe_params);

    let a_keyswitched = lwe_keyswitch0(a, tfhe_params);
    //let a_keyswitched = lwe_keyswitch(&a_enc, tfhe_params);
    //glwe_print(&accumulator, tfhe_params, (box_size / 2) as usize);

    // BR
    modulus_switch_multi_bit_blind_rotate_assign(
        &a_keyswitched,
        &mut accumulator,
        &tfhe_params.fourier_bsk,
        tfhe_params.thread_count,
        true
    );

/* 
    let grouping_factor = tfhe_params.fourier_bsk.grouping_factor();
    print!("grouping_factor {:?}\n", grouping_factor);
    let lut_poly_size = accumulator.polynomial_size();
    print!("lut_poly_size {:?}\n", lut_poly_size);
    print!("log_modulus {:?}\n", lut_poly_size.to_blind_rotation_input_modulus_log());
    let multi_bit_modulus_switched_input = StandardMultiBitModulusSwitchedCt {
        input: a_keyswitched.as_view(),
        grouping_factor,
        log_modulus: lut_poly_size.to_blind_rotation_input_modulus_log(),
    };
    multi_bit_blind_rotate_assign(
        &multi_bit_modulus_switched_input,
        &mut accumulator,
        &tfhe_params.fourier_bsk,
        tfhe_params.thread_count,
        true,
    );
*/
    //print!("after BR ");
    //glwe_print(&accumulator, tfhe_params, (box_size / 2) as usize);
    //let x = glwe_sample_extract(&accumulator, tfhe_params.box_size/2, tfhe_params);
    let x = glwe_sample_extract_big0(&accumulator, (box_size / 2) as usize, tfhe_params);
    //let x = glwe_sample_extract(&accumulator, 0, tfhe_params);
    //let mut x = lwe_new_to_glwe(&tfhe_params);
    //extract_lwe_sample_from_glwe_ciphertext(&accumulator, &mut x, MonomialDegree((box_size / 2) as usize));
    return x;
}
*/

pub fn lwe_lookup(a: &LweCiphertextOwned<u64>, table: &Vec<LweCiphertextOwned<u64>>)
    -> LweCiphertextOwned<u64> {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let box_size = tfhe_params.box_size as u64;
        let mut accumulator = generate_lut_lwe(table);

        let a_keyswitched = lwe_keyswitch(a);

        // BR
        modulus_switch_multi_bit_blind_rotate_assign(
            &a_keyswitched,
            &mut accumulator,
            &tfhe_params.multi_bit_bsk,
            tfhe_params.thread_count,
            true
        );

        let x = glwe_sample_extract(&accumulator, (box_size / 2) as usize);
        //return x;
        x
    })
}


///////////////////////////////////////////////////////////////////////////
/// 平文の配列から LUT を生成する
/// carry ビットと message ビットを連結した値に対する表とみなしている
///////////////////////////////////////////////////////////////////////////
/* 
pub fn generate_lut_plain0(table: &Vec<u64>, tfhe_params: &TfheParam) -> GlweCiphertextOwned<u64>
{
    let message_modulus = tfhe_params.message_modulus.0 as usize;
    let carry_modulus = tfhe_params.carry_modulus.0 as usize;
    let polynomial_size = tfhe_params.polynomial_size.0;
    let glwe_size = tfhe_params.glwe_dimension.to_glwe_size();
    let ciphertext_modulus = tfhe_params.ciphertext_modulus;
    let delta = tfhe_params.delta;
    //let box_size = polynomial_size / message_modulus;
    let box_size = polynomial_size / (message_modulus * carry_modulus);

    let mut accumulator_scalar = vec![(message_modulus-1) as u64; polynomial_size];

    let n = table.len();
    if n > message_modulus * carry_modulus {
        panic!("generate_lut_plain: LUT size {} exceeds message modulus {} * carry_modulus {}", n, message_modulus, carry_modulus);
    }
    for i in 0..n {
        let index = i * box_size;
        for j in 0..box_size {
            accumulator_scalar[index + j] = (table[i] % message_modulus as u64) * delta;
        }
    }

    let accumulator_plaintext = PlaintextList::from_container(accumulator_scalar);

    return allocate_and_trivially_encrypt_new_glwe_ciphertext(
        glwe_size,
        &accumulator_plaintext,
        ciphertext_modulus,
    )
}
*/

pub fn generate_lut_plain(table: &Vec<u64>) -> GlweCiphertextOwned<u64>
{
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let message_modulus = tfhe_params.message_modulus as usize;
        let carry_modulus = tfhe_params.carry_modulus as usize;
        let polynomial_size = tfhe_params.polynomial_size.0;
        let glwe_size = tfhe_params.glwe_dimension.to_glwe_size();
        let ciphertext_modulus = tfhe_params.ciphertext_modulus;
        let delta = tfhe_params.delta;
        //let box_size = polynomial_size / message_modulus;
        let box_size = polynomial_size / (message_modulus * carry_modulus);

        let mut accumulator_scalar = vec![(message_modulus-1) as u64; polynomial_size];

        let n = table.len();
        if n > message_modulus * carry_modulus {
            panic!("generate_lut_plain: LUT size {} exceeds message modulus {} * carry_modulus {}", n, message_modulus, carry_modulus);
        }
        for i in 0..n {
            let index = i * box_size;
            for j in 0..box_size {
                accumulator_scalar[index + j] = (table[i] % message_modulus as u64) * delta;
            }
        }

        let accumulator_plaintext = PlaintextList::from_container(accumulator_scalar);

        //return allocate_and_trivially_encrypt_new_glwe_ciphertext(
        //    glwe_size,
        //    &accumulator_plaintext,
        //    ciphertext_modulus,
        //)
        allocate_and_trivially_encrypt_new_glwe_ciphertext(
            glwe_size,
            &accumulator_plaintext,
            ciphertext_modulus,
        )
    })
}

////////////////////////////////////////////////////////////////////////////
/// 表を引く
/// 表は GLWE 暗号文で与えられる
////////////////////////////////////////////////////////////////////////////
/* 
pub fn lwe_lookup_glwe0(a: &LweCiphertextOwned<u64>, table: &GlweCiphertextOwned<u64> , tfhe_params: &TfheParam)
    -> LweCiphertextOwned<u64> {
    //let message_modulus = tfhe_params.message_modulus.0 as u64;
    //let box_size = tfhe_params.box_size * tfhe_params.carry_modulus.0 as usize;
    let box_size = tfhe_params.box_size as usize;
    //print!("lwe_lookup_glwe box_size {} message_modulus {} carry_modulus {} poly {}\n", box_size, message_modulus, tfhe_params.carry_modulus.0, tfhe_params.polynomial_size.0);

    let mut table2 = table.clone(); 

    let a_keyswitched = lwe_keyswitch0(a, tfhe_params);

    //glwe_print(&table2, tfhe_params, (box_size / 2) as usize);

    // BR
    modulus_switch_multi_bit_blind_rotate_assign(
        &a_keyswitched,
        //&a,
        &mut table2,
        &tfhe_params.fourier_bsk,
        tfhe_params.thread_count,
        true
    );

    //print!("after BR ");
    //glwe_print(&table2, tfhe_params, (box_size / 2) as usize);

    //let x = glwe_sample_extract(&table2, (box_size / 2) as usize, tfhe_params);
    let x = glwe_sample_extract_big0(&table2, (box_size / 2) as usize, tfhe_params);
    return x;
}
*/

pub fn lwe_lookup_glwe(a: &LweCiphertextOwned<u64>, table: &GlweCiphertextOwned<u64>)
    -> LweCiphertextOwned<u64> {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let box_size = tfhe_params.box_size as usize;
    
        let mut table2 = table.clone(); 

        let a_keyswitched = lwe_keyswitch(a);

        // BR
        modulus_switch_multi_bit_blind_rotate_assign(
            &a_keyswitched,
            &mut table2,
            &tfhe_params.multi_bit_bsk,
            tfhe_params.thread_count,
            true
        );

        let x = glwe_sample_extract(&table2, (box_size / 2) as usize);
        //return x;
        x
    })
}

pub fn lwe_lookup_plain(a: &LweCiphertextOwned<u64>, table: &Vec<u64>)
    -> LweCiphertextOwned<u64> {
    let table_glwe = generate_lut_plain(table);
    return lwe_lookup_glwe(a, &table_glwe);
}

/* 
pub fn lwe_bit_decomposition0(a: &LweCiphertextOwned<u64>,
    tfhe_params: &TfheParam) -> Vec<LweCiphertextOwned<u64>> {

    let modulus = tfhe_params.message_modulus.0 * tfhe_params.carry_modulus.0;
    let w = blog(modulus -1) as u32 +1;

    let mut result: Vec<LweCiphertextOwned<u64>> = Vec::new();

    let table_q: Vec<u64> = (0..(1 << w)).map(|j| ((j >> 1) as u64)).collect();
    let table_r: Vec<u64> = (0..(1 << w)).map(|j| ((j & 1) as u64)).collect();
    let table_q_glwe = generate_lut_plain0(&table_q, tfhe_params);
    let table_r_glwe = generate_lut_plain0(&table_r, tfhe_params);

    let mut x = a.clone();
    for _i in 0..w {
        let r = lwe_lookup_glwe0(&x, &table_r_glwe, tfhe_params);
        result.push(r);
        x = lwe_lookup_glwe0(&x, &table_q_glwe, tfhe_params);
    }
    //print!("bit_decomposition: ");
    //print_ctx_list(&result, tfhe_params);

    return result;
}
*/

pub fn lwe_bit_decomposition(a: &LweCiphertextOwned<u64>) -> Vec<LweCiphertextOwned<u64>> {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();

        let modulus = tfhe_params.message_modulus * tfhe_params.carry_modulus;
        let w = blog(modulus -1) as u32 +1;

        let mut result: Vec<LweCiphertextOwned<u64>> = Vec::new();

        let table_q: Vec<u64> = (0..(1 << w)).map(|j| (j >> 1) as u64).collect();
        let table_r: Vec<u64> = (0..(1 << w)).map(|j| (j & 1) as u64).collect();
        let table_q_glwe = generate_lut_plain(&table_q);
        let table_r_glwe = generate_lut_plain(&table_r);

        let mut x = a.clone();
        for _i in 0..w {
            let r = lwe_lookup_glwe(&x, &table_r_glwe);
            result.push(r);
            x = lwe_lookup_glwe(&x, &table_q_glwe);
        }

        //return result;
        result
    })
}

pub fn lwe_bit_decomposition_width(a: &LweCiphertextOwned<u64>, width: usize) -> Vec<LweCiphertextOwned<u64>> {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();

        let modulus = tfhe_params.message_modulus * tfhe_params.carry_modulus;

        let mut result: Vec<LweCiphertextOwned<u64>> = Vec::new();

        let table_q: Vec<u64> = (0..modulus).map(|j| (j >> 1) as u64).collect();
        let table_r: Vec<u64> = (0..modulus).map(|j| (j & 1) as u64).collect();
        let table_q_glwe = generate_lut_plain(&table_q);
        let table_r_glwe = generate_lut_plain(&table_r);

        let mut x = a.clone();
        for _i in 0..width {
            let r = lwe_lookup_glwe(&x, &table_r_glwe);
            result.push(r);
            x = lwe_lookup_glwe(&x, &table_q_glwe);
        }
        result
    })
}

/* 
pub fn lwe_bit_decomposition_int0(a: &Vec<LweCiphertextOwned<u64>>, bit_size: usize,
    tfhe_params: &TfheParam) -> Vec<LweCiphertextOwned<u64>> {

    let mut result: Vec<LweCiphertextOwned<u64>> = Vec::new();

    for i in 0..a.len() {
        let bits = lwe_bit_decomposition0(&a[i], tfhe_params);
        result.append(bits.clone().as_mut());
    }
    return result[0..bit_size].to_vec();
}
*/

pub fn lwe_bit_decomposition_int(a: &Vec<LweCiphertextOwned<u64>>, bit_size: usize) -> Vec<LweCiphertextOwned<u64>> {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let modulus = tfhe_params.message_modulus;
        let w = blog(modulus -1) as u32 +1;

        let mut result: Vec<LweCiphertextOwned<u64>> = Vec::new();

        for i in 0..a.len() {
            let bits = lwe_bit_decomposition_width(&a[i], w as usize);
            result.append(bits.clone().as_mut());
        }
        //return result[0..bit_size].to_vec();
        result[0..bit_size].to_vec()
    })
}

pub fn lwe_bit_composition_int(a: &Vec<LweCiphertextOwned<u64>>) -> Vec<LweCiphertextOwned<u64>> {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let modulus = tfhe_params.message_modulus;
        let w = blog(modulus -1) as u32 +1;

        let mut result: Vec<LweCiphertextOwned<u64>> = Vec::new();
        let mut x = trivial_const(0);
        for i in (0..a.len()).rev() {
            x = lwe_add(&x, &x);
            x = lwe_add(&x, &a[i]);
            if i % w as usize == 0 {
                result.push(x.clone());
                x = trivial_const(0);
            }
        }
        result.reverse();
        result
    })
}

pub fn lwe_bit_lshift(a: &Vec<LweCiphertextOwned<u64>>, shift: usize) -> Vec<LweCiphertextOwned<u64>> {
    let n = a.len();
    let mut result: Vec<LweCiphertextOwned<u64>> = Vec::new();
    for i in 0..n {
        if i < shift {
            result.push(trivial_const(0));
        } else {
            result.push(a[i - shift].clone());
        }
    }
    //result.reverse();
    result
}

pub fn lwe_bit_rshift(a: &Vec<LweCiphertextOwned<u64>>, shift: usize) -> Vec<LweCiphertextOwned<u64>> {
    let n = a.len();
    let mut result: Vec<LweCiphertextOwned<u64>> = Vec::new();
    for i in 0..n {
        if i >= n-shift {
            result.push(trivial_const(0));
        } else {
            result.push(a[i + shift].clone());
        }
    }
    //result.reverse();
    result
}

pub fn lwe_bit_decomposition_packed(a: &Vec<LweCiphertextOwned<u64>>, bit_size: usize) -> Vec<LweCiphertextOwned<u64>> {
    //let tfhe_params = &TFHE_PARAMS2;
    TFHE_PARAMS.with(|params| {
        let tfhe_params = params.borrow();
        let modulus = tfhe_params.message_modulus * tfhe_params.carry_modulus;
        let w = blog(modulus -1) as u32 +1;

        let mut result: Vec<LweCiphertextOwned<u64>> = Vec::new();

        for i in 0..a.len() {
            let bits = lwe_bit_decomposition_width(&a[i], w as usize);
            result.append(bits.clone().as_mut());
        }
        //return result[0..bit_size].to_vec();
        result[0..bit_size].to_vec()
    })
}

#[derive(Clone)]
pub struct LweShort {
    pub x: LweCiphertextOwned<u64>,
}

impl LweShort {
    pub fn new(plain_x: u32) -> Self {
        let x = lwe_encrypt(plain_x);
        Self {x}
    }
    pub fn clone(&self) -> Self {
        Self {x: self.x.clone()}
    }
    pub fn get_lwe(&self) -> LweCiphertextOwned<u64> {
        self.x.clone()
    }
    pub fn get_modulus(&self) -> u64 {
        lwe_get_modulus()
    }
    pub fn get_carry_modulus(&self) -> u64 {
        lwe_get_carry_modulus()
    }
    //pub fn bit_size(&self) -> usize {
    //    self.bit_size
    //}
    fn set_plain(&mut self, x: u32) {
        let ctx = lwe_encrypt(x);
        self.x = ctx
    }
    pub fn set_lwe(x:LweCiphertextOwned<u64>) -> Self {
        Self {x}
    }
    pub fn dec(&self) -> u64 {
        let lwe_result = lwe_decrypt(&self.x);
        return lwe_result;
    }
    pub fn __str__(&self) -> String {
        return format!("[{}]", self.dec());
    }
    pub fn to_bit(&self) -> Vec<Self> {
        let bits = lwe_bit_decomposition(&self.x);
        let mut result: Vec<Self> = Vec::new();
        for i in 0..bits.len() {
            result.push(Self{x: bits[i].clone()});
        }
        result
    }
    pub fn to_int(&self, bit_size: usize) -> Vec<LweCiphertextOwned<u64>> {
        //let tfhe_params = &TFHE_PARAMS2;
        TFHE_PARAMS.with(|params| {
            let tfhe_params = params.borrow();
            let modulus = tfhe_params.message_modulus;
            let w = blog(modulus -1) as u32 +1;
            let k = bit_size / (w as usize); // 切り捨てているので注意

            let mut result: Vec<LweCiphertextOwned<u64>> = Vec::new();
            result.push(self.x.clone());
            for i in 1..k {
                result.push(trivial_const(0));
            }
            result
        })
    }
    pub fn addc(&self, other: &Self) -> (Self, Self) {
        //let sum = lwe_add(&self.x, &other.x);
        //let (high, low) = lwe_getqr(&sum);
        let (high, low) = lwe_add3(&self.x, &other.x, &trivial_const(0));
        (Self {x: high}, Self {x: low})
    }
    pub fn add(&self, other: &Self) -> Self {
        //let sum = lwe_add(&self.x, &other.x);
        //let (high, low) = lwe_getqr(&sum);
        let (high, low) = self.addc(&other);
        low
    }
    pub fn subc(&self, other: &Self) -> (Self, Self) {
        //let sum = lwe_sub(&self.x, &other.x);
        //LweShort {x: sum}
        let (high, low) = lwe_sub3(&self.x, &other.x, &trivial_const(0));
        (Self {x: high}, Self {x: low})
    }
    pub fn sub(&self, other: &Self) -> Self {
        //let sum = lwe_add(&self.x, &other.x);
        //let (high, low) = lwe_getqr(&sum);
        let (high, low) = self.subc(&other);
        low
    }
    pub fn mul(&self, other: &Self) -> (Self, Self) {
        let (high, low) = lwe_mul(&self.x, &other.x);
        (Self {x: high}, Self {x: low})
    }
    pub fn mul_const(&self, c: u64) -> (Self, Self) {
        let v = lwe_mul_const(&self.x, c);
        let (high, low) = lwe_getqr(&v);
        (Self {x: high}, Self {x: low})
    }
    pub fn __mod__(&self, other: &Self) -> Self {
        let result = lwe_mod(&self.x, &other.x);
        Self {x: result}
    }
    pub fn eq(&self, other: &Self) -> Self {
        let x = lwe_eq(&self.x, &other.x);
        Self {x}
    }
    pub fn lt(&self, other: &Self) -> Self {
        let (c, _) = self.subc(&other);
        c
    }
    pub fn ge(&self, other: &Self) -> Self {
        let (c, _) = self.subc(&other);
        c.not()
    }
    pub fn gt(&self, other: &Self) -> Self {
        let (c, _) = other.subc(&self);
        c
    }
    pub fn le(&self, other: &Self) -> Self {
        let (c, _) = other.subc(&self);
        c.not()
    }
    /// bitwise operations
    pub fn not(&self) -> Self {
        let result = not2(&self.x);
        Self {x: result}
    }
    pub fn xor(&self, other: &Self) -> Self {
        let result = xor2(&self.x, &other.x);
        Self {x: result}
    }
    pub fn and(&self, other: &Self) -> Self {
        let result = and2(&self.x, &other.x);
        Self {x: result}
    }
    pub fn or(&self, other: &Self) -> Self {
        let result = or2(&self.x, &other.x);
        Self {x: result}
    }
}


impl std::ops::BitAnd for LweShort {
    type Output = Self;
 
    fn bitand(self, Self{x:rhs}: Self) -> Self::Output {
        let Self{x:lhs} = self;
        //let result = self.and(&rhs);
        let result = and2(&lhs,&rhs);
        Self{x: result}
    }
}

impl std::ops::BitAnd<&LweShort> for LweShort {
    type Output = Self;
 
    fn bitand(self, rhs: &Self) -> Self::Output {
        //let result = self.and(&rhs);
        let result = and2(&self.x,&rhs.x);
        Self{x: result}
    }
}

impl std::ops::BitAndAssign for LweShort {
    fn bitand_assign(&mut self, rhs: Self) {
        let result = and2(&self.x,&rhs.x);
        self.x = result;
    }
}

impl std::ops::BitAndAssign<&LweShort> for LweShort {
    fn bitand_assign(&mut self, rhs: &Self) {
        let result = and2(&self.x,&rhs.x);
        self.x = result;
    }
}

impl std::ops::BitXor for LweShort {
    type Output = Self;
    fn bitxor(self, rhs: Self) -> Self::Output {
        let result = self.xor(&rhs);
        result
    }
}

impl std::ops::BitXor<&LweShort> for LweShort {
    type Output = Self;
    fn bitxor(self, rhs: &Self) -> Self::Output {
        let result = self.xor(&rhs);
        result
    }
}

impl std::ops::BitXorAssign for LweShort {
    fn bitxor_assign(&mut self, rhs: Self) {
        self.x = xor2(&self.x, &rhs.x);
    }
}

impl std::ops::BitXorAssign<&LweShort> for LweShort {
    fn bitxor_assign(&mut self, rhs: &Self) {
        self.x = xor2(&self.x, &rhs.x);
    }
}

impl std::ops::Not for LweShort {
    type Output = Self;
    fn not(self) -> Self::Output {
        //let result = self.not();
        //result
        let result = not2(&self.x);
        Self {x: result}
    }
}


#[derive(Clone)]
pub struct LwePacked {
    x: Vec<LweCiphertextOwned<u64>>,
    pub bit_size: usize,
}

impl LwePacked {
    pub fn new(plain_x: u32, bit_size: usize) -> Self {
        let x = lwe_encrypt_packed(plain_x, bit_size);
        Self {x, bit_size}
    }
    pub fn clone(&self) -> Self {
        Self {x: self.x.clone(), bit_size: self.bit_size}
    }
    pub fn get_lwe(&self) -> Vec<LweCiphertextOwned<u64>> {
        self.x.clone()
    }
    pub fn set_lwe(x:Vec<LweCiphertextOwned<u64>>, bit_size: usize) -> Self {
        Self {x, bit_size}
    }
    pub fn set_plain(&mut self, x: u32) {
        let ctx = lwe_encrypt_packed(x, self.bit_size);
        self.x = ctx
    }
    pub fn bit_size(&self) -> usize {
        self.bit_size
    }
    pub fn get_modulus(&self) -> u64 {
        //lwe_get_modulus()
        lwe_get_modulus() * lwe_get_carry_modulus()
    }
    pub fn get_carry_modulus(&self) -> u64 {
        //lwe_get_carry_modulus()
        return 1;
    }
    pub fn dec(&self) -> u64 {
        let lwe_result = lwe_decrypt_packed(&self.x, self.bit_size);
        return lwe_result;
    }
    pub fn __str__(&self) -> String {
        return format!("[{}]", self.dec());
    }
    /// 型変換
    pub fn to_bit(&self) -> Vec<LweShort> {
        let bits = lwe_bit_decomposition_packed(&self.x, self.bit_size);
        let mut result: Vec<LweShort> = Vec::new();
        for i in 0..bits.len() {
            result.push(LweShort{x: bits[i].clone()});
        }
        result
    }
    pub fn to_int(&self) -> LweInt {
        let (modulus_int, modulus_packed) = TFHE_PARAMS.with(|params| {
            let tfhe_params = params.borrow();
            (tfhe_params.message_modulus, tfhe_params.message_modulus * tfhe_params.carry_modulus)
        });
        let w_int = blog(modulus_int -1) as u32 +1;
        let w_packed = blog(modulus_packed -1) as u32 +1;
        if w_packed % w_int != 0 {
            panic!("LwePacked::to_int: incompatible modulus {} and {}\n", modulus_int, modulus_packed);
        }
        let k = w_packed / w_int;

        let mut result: Vec<LweCiphertextOwned<u64>> = Vec::new();

        let table_q: Vec<u64> = (0..(1 << w_packed)).map(|j| (j / modulus_int) as u64).collect();
        let table_r: Vec<u64> = (0..(1 << w_packed)).map(|j| (j % modulus_int) as u64).collect();
        let table_q_glwe = generate_lut_plain(&table_q);
        let table_r_glwe = generate_lut_plain(&table_r);

        for i in 0..((self.bit_size() as u32 +w_packed-1)/w_packed) as usize {
            let mut x = self.x[i as usize].clone();
            for j in 0..(k-1) as usize {
                if i*w_packed as usize +j*w_int as usize > self.bit_size +w_int as usize -1 {
                    break;
                }
                let r = lwe_lookup_glwe(&x, &table_r_glwe);
                //print!("LwePacked::to_int: i {} j {} r {}\n", i, j, lwe_decrypt_big(&r));
                result.push(r);
                x = lwe_lookup_glwe(&x, &table_q_glwe);
            }
            //print!("LwePacked::to_int: i {} x {}\n", i, lwe_decrypt_big(&x));
            result.push(x);
        }
        LweInt {x: result, bit_size: self.bit_size}
    }   
    pub fn geti(&self, i:usize) -> LweShort {
        if i >= self.bit_size {
            panic!("LweInt::geti: i {}\n", i);
        }
        LweShort{x: lwe_geti_packed(&self.x, i), /*bit_size: 1*/}
    }
}

#[derive(Clone)]
pub struct LweInt {
    pub x: Vec<LweCiphertextOwned<u64>>,
    pub bit_size: usize,
}

impl LweInt {
    pub fn new(plain_x: u32, bit_size: usize) -> Self {
        let x = lwe_encrypt_int(plain_x, bit_size);
        Self {x, bit_size}
    }
    pub fn clone(&self) -> Self {
        Self {x: self.x.clone(), bit_size: self.bit_size}
    }
    fn get_lwe(&self) -> Vec<LweCiphertextOwned<u64>> {
        self.x.clone()
    }
    pub fn set_lwe(x:Vec<LweCiphertextOwned<u64>>, bit_size: usize) -> Self {
        Self {x, bit_size}
    }
    pub fn bit_size(&self) -> usize {
        self.bit_size
    }
    pub fn get_modulus(&self) -> u64 {
        lwe_get_modulus()
    }
    pub fn get_carry_modulus(&self) -> u64 {
        lwe_get_carry_modulus()
    }
    pub fn set_plain(&mut self, x: u32) {
        let ctx = lwe_encrypt_int(x, self.bit_size);
        self.x = ctx
    }
    pub fn dec(&self) -> u64 {
        let lwe_result = lwe_decrypt_int(&self.x, self.bit_size);
        return lwe_result;
    }
    pub fn __str__(&self) -> String {
        return format!("[{}]", self.dec());
    }
    pub fn geti(&self, i:usize) -> LweShort {
        if i >= self.bit_size {
            panic!("LweInt::geti: i {}\n", i);
        }
        LweShort{x: lwe_geti_int(&self.x, i)}
    }
    pub fn slice(&self, start:usize, end:usize, step:usize) -> Self {
        if start >= end || end > self.bit_size {
            panic!("LweInt::slice: start {} end {}\n", start, end);
        }
        let mut result_x: Vec<LweCiphertextOwned<u64>> = Vec::new();
        for i in start..end {
            result_x.push(lwe_geti_int(&self.x, i));
        }
        let packed = lwe_bit_composition_int(&result_x);
        Self {x: result_x, bit_size: end - start}
    }

    /// 型変換
    pub fn to_bit(&self) -> Vec<LweShort> {
        let bits = lwe_bit_decomposition_int(&self.x, self.bit_size);
        let mut result: Vec<LweShort> = Vec::new();
        for i in 0..bits.len() {
            result.push(LweShort{x: bits[i].clone()});
        }
        result
    }
    pub fn to_short(&self, bit_size: usize) -> LweShort {
        LweShort { x: self.x[0].clone() }
    }
    pub fn to_packed(&self) -> LwePacked {
        let (modulus_int, modulus_packed) = TFHE_PARAMS.with(|params| {
            let tfhe_params = params.borrow();
            (tfhe_params.message_modulus, tfhe_params.message_modulus * tfhe_params.carry_modulus)
        });
        let w_int = blog(modulus_int -1) as u32 +1;
        let w_packed = blog(modulus_packed -1) as u32 +1;
        if w_packed % w_int != 0 {
            panic!("LweInt::to_packed: incompatible modulus {} and {}\n", modulus_int, modulus_packed);
        }
        let k = w_packed / w_int;
        let mut result_x: Vec<LweCiphertextOwned<u64>> = Vec::new();
        for i in 0..(self.bit_size as u32 + w_packed -1) as u32 / w_packed {
            let mut x = trivial_const(0);
            for j in (0..k).rev() {
                if i*k+j >= ((self.bit_size as u32)+w_int-1) / w_int {
                    continue;
                }
                for _ in 0..(w_packed-w_int) {
                    x = lwe_add(&x, &x);
                }
                //print!("LweInt::to_packed: i {} j {} x {}\n", i, j, lwe_decrypt_big(&x));
                x = lwe_add(&x, &self.x[(i*k+j) as usize]);
            }
            result_x.push(x);
        }
        LwePacked {x: result_x, bit_size: self.bit_size}
    }   

    /// 四則演算
    pub fn addc(&self, other: &Self) -> (LweShort, Self) {
        let (c, sum) = lwe_add_int(&self.x, &other.x);
        (LweShort {x: c}, Self {x: sum, bit_size: self.bit_size})
    }
    pub fn add(&self, other: &Self) -> Self {
        let (_, sum) = self.addc(&other);
        sum
    }
    pub fn subc(&self, other: &Self) -> (LweShort, Self) {
        let (c, sum) = lwe_sub_int(&self.x, &other.x);
        (LweShort {x: c}, Self {x: sum, bit_size: self.bit_size})
    }
    pub fn sub(&self, other: &Self) -> Self {
        let (_, sum) = self.subc(&other);
        sum
    }
    pub fn eq(&self, other: &Self) -> LweShort {
        let x = lwe_eq_int(&self.x, &other.x);
        LweShort {x}
    }
    pub fn lt(&self, other: &Self) -> LweShort {
        let (c, _) = self.subc(&other);
        c
    }
    pub fn ge(&self, other: &Self) -> LweShort {
        let (c, _) = self.subc(&other);
        c.not()
    }
    pub fn gt(&self, other: &Self) -> LweShort {
        let (c, _) = other.subc(&self);
        c
    }
    pub fn le(&self, other: &Self) -> LweShort {
        let (c, _) = other.subc(&self);
        c.not()
    }
 
    pub fn mul(&self, other: &Self) -> Self {
        let product = lwe_mul_int(&self.x, &other.x);
        let tmp = LweInt {x: product.clone(), bit_size: self.bit_size + other.bit_size + 2}; // +2 は適当
        tmp
    }

    /// 論理演算
    pub fn __xor__(&self, other: &Self) -> Self {
        let result = lwe_xor_int(&self.x, &other.x);
        Self {x: result, bit_size: self.bit_size}
    }
    pub fn __mod__(&self, other: &Self) -> Self {
        let result = lwe_mod_int(&self.x, &other.x);
        Self {x: result, bit_size: self.bit_size}
    }
    pub fn lshift(&self, shift: usize) -> Self {
        let decomp = lwe_bit_decomposition_int(&self.x, self.bit_size);
        let result = lwe_bit_lshift(&decomp, shift);
        let comp = lwe_bit_composition_int(&result);
        Self {x: comp, bit_size: self.bit_size}
    }
    pub fn rshift(&self, shift: usize) -> Self {
        let decomp = lwe_bit_decomposition_int(&self.x, self.bit_size);
        let result = lwe_bit_rshift(&decomp, shift);
        let comp = lwe_bit_composition_int(&result);
        Self {x: comp, bit_size: self.bit_size}
    }
}

impl std::ops::Add for LweInt {
    type Output = Self;
    fn add(self, rhs: Self) -> Self::Output {
        let (_, result) = self.addc(&rhs);
        result
    }
}

impl std::ops::Sub for LweInt {
    type Output = Self;
    fn sub(self, rhs: Self) -> Self::Output {
        let (_, result) = self.subc(&rhs);
        result
    }
}

