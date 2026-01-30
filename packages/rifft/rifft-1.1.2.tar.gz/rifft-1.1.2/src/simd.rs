use num_complex::Complex32;

#[cfg(target_arch = "x86")]
use core::arch::x86::*;
#[cfg(target_arch = "x86_64")]
use core::arch::x86_64::*;

pub fn complex_mul_inplace(a: &mut [Complex32], b: &[Complex32]) {
    assert_eq!(a.len(), b.len());
    if a.is_empty() {
        return;
    }
    #[cfg(target_arch = "aarch64")]
    {
        neon_complex_mul(a, b);
    }
    #[cfg(not(target_arch = "aarch64"))]
    {
        #[cfg(any(target_arch = "x86", target_arch = "x86_64"))]
        {
            if try_x86_avx2(a, b) {
                return;
            }
        }
        complex_mul_scalar(a, b);
    }
}

fn complex_mul_scalar(a: &mut [Complex32], b: &[Complex32]) {
    for (lhs, rhs) in a.iter_mut().zip(b.iter()) {
        *lhs *= *rhs;
    }
}

#[cfg(target_arch = "aarch64")]
fn neon_complex_mul(a: &mut [Complex32], b: &[Complex32]) {
    use core::arch::aarch64::*;

    let len = a.len();
    let mut i = 0;
    unsafe {
        while i + 4 <= len {
            let a_ptr = a.as_mut_ptr().add(i) as *mut f32;
            let b_ptr = b.as_ptr().add(i) as *const f32;
            let a_vals = vld2q_f32(a_ptr as *const f32);
            let b_vals = vld2q_f32(b_ptr);
            let are = a_vals.0;
            let aim = a_vals.1;
            let bre = b_vals.0;
            let bim = b_vals.1;
            let real = vsubq_f32(vmulq_f32(are, bre), vmulq_f32(aim, bim));
            let imag = vaddq_f32(vmulq_f32(are, bim), vmulq_f32(aim, bre));
            let out = float32x4x2_t(real, imag);
            vst2q_f32(a_ptr, out);
            i += 4;
        }
    }
    if i < len {
        complex_mul_scalar(&mut a[i..], &b[i..]);
    }
}

#[cfg(any(target_arch = "x86", target_arch = "x86_64"))]
fn try_x86_avx2(a: &mut [Complex32], b: &[Complex32]) -> bool {
    if std::arch::is_x86_feature_detected!("avx2") {
        unsafe { complex_mul_avx2(a, b) };
        true
    } else {
        false
    }
}

#[cfg(any(target_arch = "x86", target_arch = "x86_64"))]
#[target_feature(enable = "avx2")]
unsafe fn complex_mul_avx2(a: &mut [Complex32], b: &[Complex32]) {
    let len = a.len();
    let mut i = 0;
    while i + 4 <= len {
        let a_ptr = a.as_mut_ptr().add(i) as *mut f32;
        let b_ptr = b.as_ptr().add(i) as *const f32;
        let a_vec = _mm256_loadu_ps(a_ptr);
        let b_vec = _mm256_loadu_ps(b_ptr);
        let a_real = _mm256_moveldup_ps(a_vec);
        let a_imag = _mm256_movehdup_ps(a_vec);
        let b_swapped = _mm256_shuffle_ps(b_vec, b_vec, 0b1011_0001);
        let mult_re = _mm256_mul_ps(a_real, b_vec);
        let mult_im = _mm256_mul_ps(a_imag, b_swapped);
        let result = _mm256_addsub_ps(mult_re, mult_im);
        _mm256_storeu_ps(a_ptr, result);
        i += 4;
    }
    if i < len {
        complex_mul_scalar(&mut a[i..], &b[i..]);
    }
}

#[cfg(test)]
mod tests {
    use super::complex_mul_inplace;
    use num_complex::Complex32;

    #[test]
    fn complex_mul_matches_scalar() {
        let mut lhs = (0..37)
            .map(|i| Complex32::new(i as f32 * 0.5, -(i as f32) * 0.25))
            .collect::<Vec<_>>();
        let rhs = (0..37)
            .map(|i| Complex32::new((i as f32).sin(), (i as f32).cos()))
            .collect::<Vec<_>>();
        let mut expected = lhs.clone();
        for (a, b) in expected.iter_mut().zip(rhs.iter()) {
            *a *= *b;
        }
        complex_mul_inplace(&mut lhs, &rhs);
        for (got, want) in lhs.iter().zip(expected.iter()) {
            assert!((got.re - want.re).abs() < 1e-6);
            assert!((got.im - want.im).abs() < 1e-6);
        }
    }
}
