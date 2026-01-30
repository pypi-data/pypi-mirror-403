use rayon::prelude::*;

const PARALLEL_MIN_ELEMENTS: usize = 128 * 128;
const TILE_DEFAULT: usize = 32;
const TILE_SMALL: usize = 16;
const TILE_LARGE: usize = 64;
const DIM_THRESHOLD_SMALL: usize = 1024;
const DIM_THRESHOLD_MEDIUM: usize = 1536;
const DIM_THRESHOLD_LARGE: usize = 2048;

pub fn transpose<T: Copy + Send + Sync>(
    input: &[T],
    output: &mut [T],
    width: usize,
    height: usize,
) {
    let tile = select_tile(width, height);
    let len = width
        .checked_mul(height)
        .expect("matrix dimensions overflow usize");
    assert_eq!(input.len(), len, "input length must match width*height");
    assert_eq!(output.len(), len, "output length must match width*height");
    if len == 0 {
        return;
    }
    if should_parallel(width, height, len, tile) {
        parallel_transpose(input, output, width, height, tile);
    } else {
        transpose_scalar(input, output, width, height);
    }
}

fn select_tile(width: usize, height: usize) -> usize {
    let min_dim = width.min(height);
    if min_dim >= DIM_THRESHOLD_LARGE {
        TILE_LARGE
    } else if min_dim >= DIM_THRESHOLD_MEDIUM {
        TILE_DEFAULT
    } else if min_dim >= DIM_THRESHOLD_SMALL {
        TILE_SMALL
    } else {
        TILE_DEFAULT
    }
}

fn should_parallel(width: usize, height: usize, len: usize, tile: usize) -> bool {
    width >= tile * 2
        && height >= tile * 2
        && len >= PARALLEL_MIN_ELEMENTS
        && rayon::current_num_threads() > 1
}

fn parallel_transpose<T: Copy + Send + Sync>(
    input: &[T],
    output: &mut [T],
    width: usize,
    height: usize,
    tile: usize,
) {
    let tiles_x = width.div_ceil(tile);
    let tiles_y = height.div_ceil(tile);
    let total_tiles = tiles_x * tiles_y;

    #[derive(Clone, Copy)]
    struct SharedMutPtr<T>(*mut T);

    impl<T> SharedMutPtr<T> {
        #[inline]
        fn ptr(self) -> *mut T {
            self.0
        }
    }

    // Safety: parallel_transpose partitions the input into disjoint tiles and each tile writes to a
    // disjoint region of `output` (transpose is a bijection). Sharing the raw pointer across
    // threads is safe under this invariant.
    unsafe impl<T> Send for SharedMutPtr<T> {}
    unsafe impl<T> Sync for SharedMutPtr<T> {}

    #[derive(Clone, Copy)]
    struct SharedConstPtr<T>(*const T);

    impl<T> SharedConstPtr<T> {
        #[inline]
        fn ptr(self) -> *const T {
            self.0
        }
    }

    unsafe impl<T> Send for SharedConstPtr<T> {}
    unsafe impl<T> Sync for SharedConstPtr<T> {}

    let in_ptr = SharedConstPtr(input.as_ptr());
    let out_ptr = SharedMutPtr(output.as_mut_ptr());
    (0..total_tiles).into_par_iter().for_each(move |tile_idx| {
        let tile_y = tile_idx / tiles_x;
        let tile_x = tile_idx % tiles_x;
        let x_start = tile_x * tile;
        let y_start = tile_y * tile;
        let x_end = (x_start + tile).min(width);
        let y_end = (y_start + tile).min(height);
        let bounds = TileBounds {
            x_start,
            x_end,
            y_start,
            y_end,
        };
        unsafe {
            copy_tile(
                in_ptr.ptr(),
                out_ptr.ptr(),
                MatrixDims { width, height },
                bounds,
            );
        }
    });
}

#[derive(Clone, Copy)]
pub(super) struct MatrixDims {
    width: usize,
    height: usize,
}

#[derive(Clone, Copy)]
pub(super) struct TileBounds {
    x_start: usize,
    x_end: usize,
    y_start: usize,
    y_end: usize,
}

unsafe fn copy_tile<T: Copy>(
    input: *const T,
    output: *mut T,
    dims: MatrixDims,
    bounds: TileBounds,
) {
    if simd::copy_tile_simd(input, output, dims, bounds) {
        return;
    }
    copy_tile_scalar(input, output, dims, bounds);
}

pub(super) unsafe fn copy_tile_scalar<T: Copy>(
    input: *const T,
    output: *mut T,
    dims: MatrixDims,
    bounds: TileBounds,
) {
    for y in bounds.y_start..bounds.y_end {
        let row_offset = y * dims.width;
        for x in bounds.x_start..bounds.x_end {
            let src_idx = row_offset + x;
            let dst_idx = x * dims.height + y;
            let value = input.add(src_idx).read();
            output.add(dst_idx).write(value);
        }
    }
}

fn transpose_scalar<T: Copy>(input: &[T], output: &mut [T], width: usize, height: usize) {
    transpose_crate::transpose(input, output, width, height);
}

mod transpose_crate {
    pub use transpose::transpose;
}

mod simd {
    use super::{copy_tile_scalar, MatrixDims, TileBounds};
    use core::mem::size_of;

    #[inline]
    pub(super) unsafe fn copy_tile_simd<T: Copy>(
        input: *const T,
        output: *mut T,
        dims: MatrixDims,
        bounds: TileBounds,
    ) -> bool {
        if size_of::<T>() != 8 {
            return false;
        }
        if bounds.x_end - bounds.x_start < 2 || bounds.y_end - bounds.y_start < 2 {
            return false;
        }
        cfg_if::cfg_if! {
            if #[cfg(target_arch = "aarch64")] {
                neon::copy_tile_u64(input, output, dims, bounds);
                true
            } else if #[cfg(any(target_arch = "x86", target_arch = "x86_64"))] {
                x86::copy_tile_u64(input, output, dims, bounds)
            } else {
                false
            }
        }
    }

    #[cfg(target_arch = "aarch64")]
    mod neon {
        use super::{copy_tile_scalar, MatrixDims, TileBounds};
        use core::mem::size_of;
        use std::arch::aarch64::*;

        pub(super) unsafe fn copy_tile_u64<T: Copy>(
            input: *const T,
            output: *mut T,
            dims: MatrixDims,
            bounds: TileBounds,
        ) {
            debug_assert_eq!(size_of::<T>(), 8);
            let MatrixDims { width, height } = dims;
            let mut y = bounds.y_start;
            while y + 1 < bounds.y_end {
                let row0_offset = y * width;
                let row1_offset = (y + 1) * width;
                let mut x = bounds.x_start;
                while x + 1 < bounds.x_end {
                    let src0 = input.add(row0_offset + x) as *const u8;
                    let src1 = input.add(row1_offset + x) as *const u8;
                    let row0 = vld1q_u8(src0);
                    let row1 = vld1q_u8(src1);
                    let row0_u64 = vreinterpretq_u64_u8(row0);
                    let row1_u64 = vreinterpretq_u64_u8(row1);
                    let lo = vzip1q_u64(row0_u64, row1_u64);
                    let hi = vzip2q_u64(row0_u64, row1_u64);
                    let dst0 = output.add(x * height + y) as *mut u8;
                    let dst1 = output.add((x + 1) * height + y) as *mut u8;
                    vst1q_u8(dst0, vreinterpretq_u8_u64(lo));
                    vst1q_u8(dst1, vreinterpretq_u8_u64(hi));
                    x += 2;
                }
                if x < bounds.x_end {
                    copy_tile_scalar(
                        input,
                        output,
                        dims,
                        TileBounds {
                            x_start: x,
                            x_end: bounds.x_end,
                            y_start: y,
                            y_end: (y + 2).min(bounds.y_end),
                        },
                    );
                }
                y += 2;
            }
            if y < bounds.y_end {
                copy_tile_scalar(
                    input,
                    output,
                    dims,
                    TileBounds {
                        x_start: bounds.x_start,
                        x_end: bounds.x_end,
                        y_start: y,
                        y_end: bounds.y_end,
                    },
                );
            }
        }
    }

    #[cfg(any(target_arch = "x86", target_arch = "x86_64"))]
    mod x86 {
        use super::{copy_tile_scalar, MatrixDims, TileBounds};
        use std::arch::is_x86_feature_detected;

        pub(super) unsafe fn copy_tile_u64<T: Copy>(
            input: *const T,
            output: *mut T,
            dims: MatrixDims,
            bounds: TileBounds,
        ) -> bool {
            if is_x86_feature_detected!("avx512f") {
                avx512::copy_tile_u64(input, output, dims, bounds);
                true
            } else if is_x86_feature_detected!("avx2") {
                avx2::copy_tile_u64(input, output, dims, bounds);
                true
            } else {
                false
            }
        }

        #[cfg(target_arch = "x86")]
        use std::arch::x86 as arch;
        #[cfg(target_arch = "x86_64")]
        use std::arch::x86_64 as arch;

        mod avx2 {
            use super::{arch, copy_tile_scalar, MatrixDims, TileBounds};
            use core::mem::size_of;

            #[target_feature(enable = "avx2")]
            pub(super) unsafe fn copy_tile_u64<T: Copy>(
                input: *const T,
                output: *mut T,
                dims: MatrixDims,
                bounds: TileBounds,
            ) {
                use arch::*;
                debug_assert_eq!(size_of::<T>(), 8);
                let MatrixDims { width, height } = dims;
                let mut y = bounds.y_start;
                while y + 1 < bounds.y_end {
                    let row0_offset = y * width;
                    let row1_offset = (y + 1) * width;
                    let mut x = bounds.x_start;
                    while x + 3 < bounds.x_end {
                        // Note: `_mm256_unpack*epi64` interleaves within 128-bit lanes, which
                        // produces (x, x+2) / (x+1, x+3) column groupings. Use 128-bit loads to
                        // keep adjacent columns together for the transpose writeback.
                        let src0_lo = input.add(row0_offset + x) as *const __m128i;
                        let src0_hi = input.add(row0_offset + x + 2) as *const __m128i;
                        let src1_lo = input.add(row1_offset + x) as *const __m128i;
                        let src1_hi = input.add(row1_offset + x + 2) as *const __m128i;

                        let row0_lo = _mm_loadu_si128(src0_lo);
                        let row0_hi = _mm_loadu_si128(src0_hi);
                        let row1_lo = _mm_loadu_si128(src1_lo);
                        let row1_hi = _mm_loadu_si128(src1_hi);

                        store_lane(_mm_unpacklo_epi64(row0_lo, row1_lo), output, height, y, x);
                        store_lane(
                            _mm_unpackhi_epi64(row0_lo, row1_lo),
                            output,
                            height,
                            y,
                            x + 1,
                        );
                        store_lane(
                            _mm_unpacklo_epi64(row0_hi, row1_hi),
                            output,
                            height,
                            y,
                            x + 2,
                        );
                        store_lane(
                            _mm_unpackhi_epi64(row0_hi, row1_hi),
                            output,
                            height,
                            y,
                            x + 3,
                        );
                        x += 4;
                    }
                    if x < bounds.x_end {
                        copy_tile_scalar(
                            input,
                            output,
                            dims,
                            TileBounds {
                                x_start: x,
                                x_end: bounds.x_end,
                                y_start: y,
                                y_end: (y + 2).min(bounds.y_end),
                            },
                        );
                    }
                    y += 2;
                }
                if y < bounds.y_end {
                    copy_tile_scalar(
                        input,
                        output,
                        dims,
                        TileBounds {
                            x_start: bounds.x_start,
                            x_end: bounds.x_end,
                            y_start: y,
                            y_end: bounds.y_end,
                        },
                    );
                }
            }

            #[target_feature(enable = "avx2")]
            unsafe fn store_lane<T: Copy>(
                lane: arch::__m128i,
                output: *mut T,
                height: usize,
                y: usize,
                column: usize,
            ) {
                use arch::*;
                let dst = output.add(column * height + y) as *mut __m128i;
                _mm_storeu_si128(dst, lane);
            }
        }

        mod avx512 {
            use super::{arch, copy_tile_scalar, MatrixDims, TileBounds};
            use core::mem::size_of;

            #[target_feature(enable = "avx512f")]
            pub(super) unsafe fn copy_tile_u64<T: Copy>(
                input: *const T,
                output: *mut T,
                dims: MatrixDims,
                bounds: TileBounds,
            ) {
                use arch::*;
                debug_assert_eq!(size_of::<T>(), 8);
                let MatrixDims { width, height } = dims;
                let mut y = bounds.y_start;
                while y + 1 < bounds.y_end {
                    let row0_offset = y * width;
                    let row1_offset = (y + 1) * width;
                    let mut x = bounds.x_start;
                    // Same lane-interleaving caveat as AVX2: `_mm512_unpack*epi64` works within
                    // 128-bit lanes, which does not preserve adjacent columns. Use 128-bit
                    // operations to guarantee correctness.
                    while x + 7 < bounds.x_end {
                        let src0_0 = input.add(row0_offset + x) as *const __m128i;
                        let src0_1 = input.add(row0_offset + x + 2) as *const __m128i;
                        let src0_2 = input.add(row0_offset + x + 4) as *const __m128i;
                        let src0_3 = input.add(row0_offset + x + 6) as *const __m128i;
                        let src1_0 = input.add(row1_offset + x) as *const __m128i;
                        let src1_1 = input.add(row1_offset + x + 2) as *const __m128i;
                        let src1_2 = input.add(row1_offset + x + 4) as *const __m128i;
                        let src1_3 = input.add(row1_offset + x + 6) as *const __m128i;

                        let row0_0 = _mm_loadu_si128(src0_0);
                        let row0_1 = _mm_loadu_si128(src0_1);
                        let row0_2 = _mm_loadu_si128(src0_2);
                        let row0_3 = _mm_loadu_si128(src0_3);
                        let row1_0 = _mm_loadu_si128(src1_0);
                        let row1_1 = _mm_loadu_si128(src1_1);
                        let row1_2 = _mm_loadu_si128(src1_2);
                        let row1_3 = _mm_loadu_si128(src1_3);

                        store_lane(_mm_unpacklo_epi64(row0_0, row1_0), output, height, y, x);
                        store_lane(_mm_unpackhi_epi64(row0_0, row1_0), output, height, y, x + 1);
                        store_lane(_mm_unpacklo_epi64(row0_1, row1_1), output, height, y, x + 2);
                        store_lane(_mm_unpackhi_epi64(row0_1, row1_1), output, height, y, x + 3);
                        store_lane(_mm_unpacklo_epi64(row0_2, row1_2), output, height, y, x + 4);
                        store_lane(_mm_unpackhi_epi64(row0_2, row1_2), output, height, y, x + 5);
                        store_lane(_mm_unpacklo_epi64(row0_3, row1_3), output, height, y, x + 6);
                        store_lane(_mm_unpackhi_epi64(row0_3, row1_3), output, height, y, x + 7);

                        x += 8;
                    }
                    if x < bounds.x_end {
                        copy_tile_scalar(
                            input,
                            output,
                            dims,
                            TileBounds {
                                x_start: x,
                                x_end: bounds.x_end,
                                y_start: y,
                                y_end: (y + 2).min(bounds.y_end),
                            },
                        );
                    }
                    y += 2;
                }
                if y < bounds.y_end {
                    copy_tile_scalar(
                        input,
                        output,
                        dims,
                        TileBounds {
                            x_start: bounds.x_start,
                            x_end: bounds.x_end,
                            y_start: y,
                            y_end: bounds.y_end,
                        },
                    );
                }
            }

            #[target_feature(enable = "avx512f")]
            unsafe fn store_lane<T: Copy>(
                lane: arch::__m128i,
                output: *mut T,
                height: usize,
                y: usize,
                column: usize,
            ) {
                use arch::*;
                let dst = output.add(column * height + y) as *mut __m128i;
                _mm_storeu_si128(dst, lane);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::transpose;

    #[test]
    fn matches_scalar_small() {
        check_shape(8, 16);
        check_shape(16, 8);
    }

    #[test]
    fn matches_scalar_large() {
        check_shape(256, 512);
        check_shape(512, 256);
        check_shape(1024, 1024);
    }

    #[test]
    fn matches_scalar_parallel_u32() {
        // Forces the parallel tiling path (independent of host thread count) while also ensuring
        // the SIMD fast path is disabled (u32 is not 8 bytes).
        rayon::ThreadPoolBuilder::new()
            .num_threads(2)
            .build()
            .unwrap()
            .install(|| check_shape_u32(256, 512));
    }

    fn check_shape(height: usize, width: usize) {
        let len = height * width;
        let mut input = Vec::with_capacity(len);
        for idx in 0..len {
            input.push(idx as u64);
        }
        let mut expected = vec![0u64; len];
        super::transpose_scalar(&input, &mut expected, width, height);
        let mut actual = vec![0u64; len];
        transpose(&input, &mut actual, width, height);
        if expected != actual {
            let first_mismatch = expected.iter().zip(actual.iter()).position(|(a, b)| a != b);
            match first_mismatch {
	                Some(idx) => {
	                    let start = idx.saturating_sub(4);
	                    let end = (idx + 5).min(len);
	                    panic!(
	                        "transpose mismatch at index {idx} (height={height} width={width}): expected={} actual={}\nwindow expected[{start}..{end}]={:?}\nwindow actual  [{start}..{end}]={:?}",
	                        expected[idx],
	                        actual[idx],
	                        &expected[start..end],
	                        &actual[start..end],
	                    )
	                }
	                None => panic!(
	                    "transpose mismatch (height={height} width={width}) but no differing element found"
	                ),
	            }
        }
    }

    fn check_shape_u32(height: usize, width: usize) {
        let len = height * width;
        let mut input = Vec::with_capacity(len);
        for idx in 0..len {
            input.push(idx as u32);
        }
        let mut expected = vec![0u32; len];
        super::transpose_scalar(&input, &mut expected, width, height);
        let mut actual = vec![0u32; len];
        transpose(&input, &mut actual, width, height);
        if expected != actual {
            let first_mismatch = expected.iter().zip(actual.iter()).position(|(a, b)| a != b);
            match first_mismatch {
	                Some(idx) => {
	                    let start = idx.saturating_sub(4);
	                    let end = (idx + 5).min(len);
	                    panic!(
	                        "transpose mismatch at index {idx} (height={height} width={width}): expected={} actual={}\nwindow expected[{start}..{end}]={:?}\nwindow actual  [{start}..{end}]={:?}",
	                        expected[idx],
	                        actual[idx],
	                        &expected[start..end],
	                        &actual[start..end],
	                    )
	                }
	                None => panic!(
	                    "transpose mismatch (height={height} width={width}) but no differing element found"
	                ),
	            }
        }
    }
}
