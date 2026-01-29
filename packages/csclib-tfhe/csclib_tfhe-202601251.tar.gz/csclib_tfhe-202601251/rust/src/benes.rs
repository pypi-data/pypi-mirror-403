use tfhe::core_crypto::prelude::*;
use crate::print::*;
//use crate::print_ctx_list;
//use crate::print::*;
use crate::keyswitch::*;
use crate::algorithms::*;
//use crate::TfheParam;
use crate::arith::*;
use core::panic;
//use std::fmt;

pub struct BenesNetwork {
    pub switch_l: Option<Vec<LweShort>>,
    pub network1: Option<LweShort>,
    pub network2: Option<LweShort>,
    pub switch_r: Option<Vec<LweShort>>,
}



pub struct  BenesNetworkNested {
    pub switch_l: Vec<LweShort>,
    pub network1: Box<BenesNetworkEnum>,
    pub network2: Box<BenesNetworkEnum>,
    pub switch_r: Vec<LweShort>,
}

pub enum BenesNetworkEnum {
    NoNest(BenesNetwork),
    Nested(BenesNetworkNested),
}


pub fn butterfly<T: Clone>(x: &Vec<T>) -> Vec<T> {
    let n = x.len();
    let mut y = x.clone();
    let k = n / 2;
    let mut i = 0;
    while i < k {
        y[i] = x[2*i].clone();
        y[i+k] = x[2*i+1].clone();
        i += 1;
    }
    return y;
}


pub fn butterfly_inv<T: Clone>(x: &Vec<T>) -> Vec<T> {
    let n = x.len();
    let mut y = x.clone();
    let k = n / 2;
    let mut i = 0;
    while i < k {
        y[2*i] = x[i].clone();
        y[2*i+1] = x[i+k].clone();
        i += 1;
    }
    return y;
}



pub fn benes_construct_sub(x: &Vec<LweShort>)
    -> (BenesNetworkEnum, Vec<LweShort>) {
            let n = x.len();
    println!("benes_construct_sub n = {}", n);
    let np = 1 << (blog((n - 1) as u64) + 1) as usize;

    let trivial_zero = LweShort::new(0);
    let trivial_one = LweShort::new(1);

    let mut x_new = x.clone();  

    if n != np {
        panic!("n != np");
    }
    if n > 2 {
        let mut rank: Vec<LweShort> = Vec::new();
        rank.push(trivial_one.clone());
        //rank.push(trivial_one.clone());

        let mut switch_l: Vec<LweShort> = Vec::new();
        for _ in 0..n/2 {
            switch_l.push(trivial_zero.clone());
        }

        let mut i = 0;
        while i < n {
            let c0 = x_new[i].clone();
            //let c0_bar = c0.not();
            let c0_bar = !c0;
            //rank[0] = rank[0].xor(&c0_bar);
            rank[0] ^= c0_bar;

            switch_l[i/2] = rank[0].clone();

            let c1 = x_new[i+1].clone();
            //let c1_bar = c1.not();
            let c1_bar = !c1;
            //rank[0] = rank[0].xor(&c1_bar);
            rank[0] ^= c1_bar;

            i += 2;
        }

        let mut i = 0;
        while i < n {
            cswap_short(&switch_l[i/2].clone(), &mut x_new, i, i+1);
            i += 2;
        }

        let mut switch_r: Vec<LweShort> = Vec::new();
        let r = rank[0].clone();

        let x_tmp = butterfly(&x_new);
        let (network1, x1_sorted) = benes_construct_sub(&x_tmp[0..n/2].to_vec());
        let (network2, x2_sorted) = benes_construct_sub(&x_tmp[n/2..n].to_vec());

        let x_sorted = butterfly_inv(&[x1_sorted, x2_sorted].concat());

        let mut i = 0;
        while i < n {
            let a = r.and(&x_sorted[i]);
            //let a = r.clone() & x_sorted[i].clone();
            //let a = r.clone() & &x_sorted[i];
            switch_r.push(a);
            i += 2;
        }


        let z = BenesNetworkNested {
            switch_l: switch_l,
            network1: Box::new(network1),
            network2: Box::new(network2),
            switch_r: switch_r,
        };
        return (BenesNetworkEnum::Nested(z), x_sorted);

    }

    else {
        let x_1_bar = x_new[1].not();
        //let x_1_bar = !x_new[1].clone();
        let c = x_new[0].and(&x_1_bar);
        //let c = x_new[0].clone() & !x_new[1].clone();
        cswap_short(&c, &mut x_new, 0, 1);
        let z = BenesNetwork {
            switch_l: vec![c].into(),
            network1: None,
            network2: None,
            switch_r: None,
        };
        return (BenesNetworkEnum::NoNest(z), x_new);

    }

}

pub fn benes_construct(x: &Vec<LweShort>) -> (BenesNetworkEnum, Vec<LweShort>) {
    let n = x.len();
    let np = 1 << (blog((n - 1) as u64) + 1) as usize;
    let mut x_tmp = x.clone();
    let trivial_one = LweShort::new(1);
    

    if np > n {
        for _ in 0..(np-n) {
            x_tmp.push(trivial_one.clone());
        }
    }

    let (z, x_sorted) = benes_construct_sub(&x_tmp);

    return (z, x_sorted);

    
}


pub fn benes_apply_sub(x: &Vec<LwePacked>, network: &BenesNetworkEnum, inverse: bool)
    -> Vec<LwePacked> {
    let n = x.len();
    let np = 1 << (blog((n - 1) as u64) + 1) as usize;
    let mut x_new = x.clone();
    
    
    if n != np {
        panic!("n != np");
    }
    match network {
        BenesNetworkEnum::Nested(network_nested) => {
            let switch_l: Vec<LweShort>;
            let switch_r: Vec<LweShort>;

            let network1 = &network_nested.network1;
            let network2 = &network_nested.network2;
            if inverse {
                switch_l = network_nested.switch_r.clone().into();
                switch_r = network_nested.switch_l.clone().into();
            }
            else {
                switch_l = network_nested.switch_l.clone().into();
                switch_r = network_nested.switch_r.clone().into();
            }

            if n <= 2 {
                panic!("n <= 2");
            }
            let mut i = 0;
            if inverse {
                i = 0;
                while i < n {
                    let sr = &switch_l[i/2];
                    cswap_packed(&sr, &mut x_new, i, i+1);
                    i += 2;
                }
            } else {
                i = 0;
                while i < n {
                    let sl = &switch_l[i/2];
                    cswap_packed(&sl, &mut x_new, i, i+1);
                    i += 2;
                }
            }
            let x_tmp = butterfly(&x_new);
            let mut x_tmp1 = benes_apply_sub(&x_tmp[0..n/2].to_vec(), &network1, inverse);
            let x_tmp2 = benes_apply_sub(&x_tmp[n/2..n].to_vec(), &network2, inverse);
                
            x_tmp1.extend(x_tmp2);

            x_new = butterfly_inv(&x_tmp1);

            if inverse {
                i = 0;
                while i < n {
                    let sr = &switch_r[i/2];
                    cswap_packed(&sr, &mut x_new, i, i+1);
                    i += 2;
                }
            } else {
                i = 0;
                while i < n {
                    let sr = &switch_r[i/2];
                    cswap_packed(&sr, &mut x_new, i, i+1);
                    i += 2;
                }
            }
        },
        BenesNetworkEnum::NoNest(network_nonest) => {
            if n > 2 {
                panic!("n > 2");
            }
            let switch_l = network_nonest.switch_l.clone(); 
            
            if let Some(switch_l_vec) = switch_l {
                let sl = &switch_l_vec[0];
                cswap_packed(&sl, &mut x_new, 0, 1);
            } else {
                panic!("switch_l is None");
            }
        },
    }
    return x_new;
}


pub fn benes_apply(x: &Vec<LwePacked>, network: &BenesNetworkEnum, inverse: bool)
    -> Vec<LwePacked> {
        let bit_size = x[0].bit_size();
        let mut x_tmp = x.clone();
        let n = x.len();

        let np = 1 << (blog((n - 1) as u64) + 1) as usize;
        //let trivial_zero = trivial_const(0, tfhe_params);
        //let trivial_zero = lwe_encrypt_int(0, bit_size);
        let trivial_zero = LwePacked::new(0, bit_size);
        for _ in 0..(np-n) {
            //let mut x_tmp_i: Vec<LweCiphertextOwned<u64>> = Vec::new();
            //for _i in 0..bit_size {
            //    x_tmp_i.push(trivial_zero.clone());
            //}
            //x_tmp.push(x_tmp_i.clone());
            x_tmp.push(trivial_zero.clone());
        }

        let mut x_new = benes_apply_sub(&x_tmp, network, inverse);

        if np > n {
            x_new = x_new[0..n].to_vec();
        }

        return x_new;
}

