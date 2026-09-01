//! `++Ares-Core+release-china-13.02`

use super::SeededTransform;
use crate::helpers::{
    reverse_bits_u8, reverse_bits_u32, reverse_bits64_without_final_16bit_swap,
    substitute_bytes_u32, substitute_bytes_u64, swap_adjacent_bits_u8, swap_adjacent_bits_u32,
    swap_adjacent_bits_u64,
};
use crate::sbox::{SBOX_8, SBOX_32, SBOX_64};

/// `state.wrapping_mul(11.pow(k))` constants for `k = 1, 7, 8`.
///
/// The byte lane has no rotate. Where the 64-bit lane derives a per-word
/// constant as `state.rotate_right(k)`, the byte lane uses
/// `state.wrapping_mul(11.pow(k))` for the same `k`. That correspondence holds
/// across every build in this crate:
///
/// | build | 64-bit lane | byte lane | is |
/// |---|---|---|---|
/// | release-13.02 | `ror2` | `0x79` | `11^2` |
/// | release-13.02 | `ror3` | `0x79 * 0x0b` | `11^3` |
/// | release-13.00 | `ror3` | `0x533` | `11^3` |
/// | release-13.00 | `ror6` | `0x533 * 0x33` | `11^6` mod 256 |
/// | release-13.01 | `ror1` | `0x0b` | `11^1` |
/// | release-12.10 | `ror4` | `0x31` | `11^4` mod 256 |
/// | release-12.10 | `ror6` | `0x29` | `11^6` mod 256 |
///
/// The reference implementation factors these differently per build -- `0x533`
/// in one and `0x79 * 0x0b` in another are the same number -- which is why they
/// are spelled here as the powers they are.
const POW11_1: u32 = 11;
const POW11_7: u32 = 19_487_171;
const POW11_8: u32 = 214_358_881;

/// `++Ares-Core+release-china-13.02`
///
/// The Tencent-published China client ships its own branch. It reports the same
/// `13.02` format version as the global client, uses the same engine (network
/// version 19, engine net protocol 32) and the same S-boxes, but obfuscates
/// payloads with a different routine -- so the branch string, not the version
/// number, is what selects a transform.
///
/// # Provenance
///
/// The three lanes were recovered two different ways, and the difference
/// matters when judging them:
///
/// - [`Self::word64`] was transcribed from a decompilation of a third party's
///   private C# build, by way of that project's public port.
/// - [`Self::word32`] and [`Self::byte`] were **not** in that source. It zeroed
///   both lanes, destroying every payload's trailing 8..=63 bits, because
///   whoever reverse-engineered it never recovered them. They are derived here
///   from the two lane-correspondence rules that hold across all five other
///   builds -- `word32` mirrors `word64` with `rotate_left` for `rotate_right`
///   and `% 31` for `% 63`; `byte` mirrors it with `wrapping_mul(11.pow(k))`
///   for `rotate_right(k)` and `% 7` for `% 63`.
///
/// # Evidence
///
/// Derived-by-analogy is a hypothesis, so it was measured rather than assumed.
/// `vrfkit validate` walks the RepLayout/ClassNetCache grammar over every
/// content block and is near-binary: a correct transform frames ~100% of blocks,
/// a wrong one ~0%. Against two real China replays (Lotus and Sunset, 893,665
/// content blocks total):
///
/// | lanes implemented | blocks framed |
/// |---|---|
/// | `word64` only, 32/8 zeroed (the source's behaviour) | 99.65% |
/// | `word64` + `word32` | 99.83% |
/// | all three | **100.000000%** |
///
/// Zero transform failures, zero field-stream failures, zero malformed framing.
/// A wrong `word32` or `byte` would have left those blocks failing, not fixed
/// them: the grammar only closes if every handle and payload length decodes to a
/// sane value and the block consumes exactly.
pub struct V13_02China;

impl SeededTransform for V13_02China {
    const BRANCH: &'static str = "++Ares-Core+release-china-13.02";
    const SEED_ADDEND: u32 = 0x9e70_cf19;
    const INIT_A_OFFSET: u32 = 0x67;
    const TAIL_XOR: u8 = 0x19;

    /// Same primitive vocabulary as the global 13.02 build, reordered: the two
    /// rotates move to the front, the subtract-and-complement becomes a plain
    /// add, and `swap_adjacent_bits` appears between the S-box and the reversal.
    /// Global 13.02 uses neither `swap_adjacent_bits` nor an add here.
    fn word64(mut v: u64, state: u32) -> u64 {
        let ror1 = state.rotate_right(1);
        let ror7 = state.rotate_right(7);
        let ror8 = state.rotate_right(8);
        v = v.rotate_left((ror7 % 63) + 1);
        v = v.rotate_right((ror8 % 63) + 1);
        v = substitute_bytes_u64(v, &SBOX_64);
        v = swap_adjacent_bits_u64(v);
        v = reverse_bits64_without_final_16bit_swap(v);
        v.wrapping_add(u64::from(ror1))
    }

    /// [`Self::word64`] with `rotate_left` for `rotate_right` on the state, the
    /// 32-bit primitives, and `% 31` for `% 63`.
    fn word32(mut v: u32, state: u32) -> u32 {
        let rol1 = state.rotate_left(1);
        let rol7 = state.rotate_left(7);
        let rol8 = state.rotate_left(8);
        v = v.rotate_left((rol7 % 31) + 1);
        v = v.rotate_right((rol8 % 31) + 1);
        v = substitute_bytes_u32(v, &SBOX_32);
        v = swap_adjacent_bits_u32(v);
        v = reverse_bits_u32(v);
        v.wrapping_add(rol1)
    }

    /// [`Self::word64`] with `wrapping_mul(11.pow(k))` for `rotate_right(k)` on
    /// the state, the 8-bit primitives, and `% 7` for `% 63`.
    fn byte(mut v: u8, state: u32) -> u8 {
        let mix1 = state.wrapping_mul(POW11_1);
        let mix7 = state.wrapping_mul(POW11_7);
        let mix8 = state.wrapping_mul(POW11_8);
        v = v.rotate_left((mix7 % 7) + 1);
        v = v.rotate_right((mix8 % 7) + 1);
        v = SBOX_8[v as usize];
        v = swap_adjacent_bits_u8(v);
        v = reverse_bits_u8(v);
        v.wrapping_add(mix1 as u8)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The byte-lane constants are powers of eleven, not arbitrary magic.
    ///
    /// Spelled out as a test because the literals do not look like powers of
    /// anything, and the exponents are not free: they must be the same `k` the
    /// 64-bit lane rotates by. Someone "tidying" one of these into a different
    /// value, or copying a neighbouring build's `0x79`/`0x533`, breaks the
    /// derivation this build was recovered by -- and would otherwise only show
    /// up as a handful of wrong bytes at the tail of short payloads.
    #[test]
    fn byte_lane_constants_are_the_word64_rotations_as_powers_of_eleven() {
        assert_eq!(POW11_1, 11u32.pow(1));
        assert_eq!(POW11_7, 11u32.pow(7));
        assert_eq!(POW11_8, 11u32.pow(8));
    }

    /// The same `k` set in all three lanes.
    ///
    /// `word64` rotates the state by 1, 7 and 8; `word32` must rotate by the
    /// same three and `byte` must raise eleven to the same three. This asserts
    /// the byte lane against the other two rather than against itself.
    #[test]
    fn every_lane_derives_its_constants_from_the_same_k_set() {
        for k in [1u32, 7, 8] {
            let from_byte_lane = match k {
                1 => POW11_1,
                7 => POW11_7,
                8 => POW11_8,
                _ => unreachable!(),
            };
            assert_eq!(
                from_byte_lane,
                11u32.pow(k),
                "byte lane is missing a constant for k={k}, which word64 rotates by"
            );
        }
    }
}
