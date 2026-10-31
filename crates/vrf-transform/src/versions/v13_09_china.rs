//! `++Ares-Core+release-china-13.09`

use super::SeededTransform;
use crate::helpers::{
    reverse_bits_u8, reverse_bits_u32, reverse_bits64_without_final_16bit_swap,
    substitute_bytes_u32, substitute_bytes_u64,
};
use crate::sbox::{SBOX_8, SBOX_32, SBOX_64};

const POW11_4: u32 = 14_641;
const POW11_6: u32 = 1_771_561;

/// `++Ares-Core+release-china-13.09`
///
/// Recovered from replay measurements with `tools/china_release/recover.py`.
/// The four 13.08 first-word plaintexts admit six representatives at the
/// shortest length, six, in two families that agree on those words only; seven
/// 47-bit and seven 9-bit ceremony blocks reject one family and accept the
/// other, whose representatives are algebraically equal. One TimedBomb zero
/// word anchored two exhaustive `u32` scans; two further TimedBomb words and
/// seven ceremony successor bytes left one constant family. There is no XOR
/// step, so the short-lane complement question does not arise.
///
/// Checks the search did not use: the 127-bit TimedBomb block and all seven
/// 47-bit ceremony blocks (including the 7-bit tail, hence `TAIL_XOR`) decode
/// byte for byte to the 13.08 plaintext. Normal branch dispatch walked five
/// preserved replays (two Swiftplay, three competitive) with zero lost blocks,
/// and typed state matched every player's final K/D against independent death
/// events.
///
/// `tools/china_transform_oracle.py` is the independent implementation behind
/// eleven generated vectors at every 64/32/8/tail staging boundary.
pub struct V13_09China;

impl SeededTransform for V13_09China {
    const BRANCH: &'static str = "++Ares-Core+release-china-13.09";
    const SEED_ADDEND: u32 = 0x350f_7d3f;
    const INIT_A_OFFSET: u32 = 0x41;
    const TAIL_XOR: u8 = 0x3f;

    fn word64(mut value: u64, state: u32) -> u64 {
        value = !value;
        value = value.wrapping_sub(u64::from(state.rotate_right(6)));
        value = reverse_bits64_without_final_16bit_swap(value);
        value = value.wrapping_add(u64::from(state.rotate_right(4)));
        value = reverse_bits64_without_final_16bit_swap(value);
        substitute_bytes_u64(value, &SBOX_64)
    }

    fn word32(mut value: u32, state: u32) -> u32 {
        value = !value;
        value = value.wrapping_sub(state.rotate_left(6));
        value = reverse_bits_u32(value);
        value = value.wrapping_add(state.rotate_left(4));
        value = reverse_bits_u32(value);
        substitute_bytes_u32(value, &SBOX_32)
    }

    fn byte(mut value: u8, state: u32) -> u8 {
        let mix4 = state.wrapping_mul(POW11_4);
        let mix6 = state.wrapping_mul(POW11_6);

        value = !value;
        value = value.wrapping_sub(mix6 as u8);
        value = reverse_bits_u8(value);
        value = value.wrapping_add(mix4 as u8);
        value = reverse_bits_u8(value);
        SBOX_8[value as usize]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn byte_lane_constants_match_the_word_rotations() {
        for (constant, exponent) in [(POW11_4, 4), (POW11_6, 6)] {
            assert_eq!(constant, 11u32.pow(exponent));
        }
    }

    /// A DefaultCeremony first word observed at actor 588, 64 bits.
    #[test]
    fn decodes_an_observed_ceremony_word() {
        let mut raw = [0x23, 0xf6, 0xcb, 0x85, 0xed, 0x75, 0xa4, 0x13];
        crate::transform_in_place::<V13_09China>(&mut raw, 64, crate::seed_for(64, 588)).unwrap();
        assert_eq!(raw, [0x10, 0x0c, 0xa2, 0x61, 0x30, 0x0f, 0x81, 0x00]);
    }

    /// A 47-bit DefaultCeremony block at actor 588: one 32-bit word, one byte
    /// and a 7-bit tail, so every short stage and `TAIL_XOR` are exercised.
    #[test]
    fn decodes_an_observed_ceremony_block_with_tail() {
        let mut raw = [0xde, 0x8d, 0x80, 0x6a, 0x71, 0x28];
        crate::transform_in_place::<V13_09China>(&mut raw, 47, crate::seed_for(47, 588)).unwrap();
        assert_eq!(raw, [0x10, 0x0c, 0xa2, 0x61, 0x30, 0x00]);
    }
}
