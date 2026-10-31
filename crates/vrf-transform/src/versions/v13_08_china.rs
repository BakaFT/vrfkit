//! `++Ares-Core+release-china-13.08`

use super::SeededTransform;
use crate::helpers::{
    substitute_bytes_u32, substitute_bytes_u64, swap_adjacent_bits_u8, swap_adjacent_bits_u32,
    swap_adjacent_bits_u64,
};
use crate::sbox::{SBOX_8, SBOX_32, SBOX_64};

const POW11_3: u32 = 1_331;
const POW11_5: u32 = 161_051;
const POW11_7: u32 = 19_487_171;

/// `++Ares-Core+release-china-13.08`
///
/// Recovered from replay measurements with `tools/china_release/recover.py`.
/// Four exact first words at different states fixed the shortest six-operation
/// family; seven 47-bit and seven 9-bit ceremony blocks fixed the short lanes,
/// whose final XOR is uncomplemented. Twelve TimedBomb zero words and seven
/// ceremony successor bytes reduced two exhaustive `u32` scans to one constant
/// family. Normal branch dispatch then walked all 735,446 ReplayData blocks of
/// a preserved replay with zero lost blocks; typed state matched all ten
/// players' final K/D against 157 independent death events and the 13-9 score.
/// A second replay (403,621 blocks, a match surrendered in round 12) passes the
/// same checks.
///
/// `tools/china_transform_oracle.py` is the independent implementation behind
/// eleven generated vectors at every 64/32/8/tail staging boundary.
pub struct V13_08China;

impl SeededTransform for V13_08China {
    const BRANCH: &'static str = "++Ares-Core+release-china-13.08";
    const SEED_ADDEND: u32 = 0x4a67_f535;
    const INIT_A_OFFSET: u32 = 0x4b;
    const TAIL_XOR: u8 = 0x35;

    fn word64(mut value: u64, state: u32) -> u64 {
        value = !value;
        value = swap_adjacent_bits_u64(value);
        value = value.wrapping_add(u64::from(state.rotate_right(5)));
        value = value.wrapping_sub(u64::from(state.rotate_right(7)));
        value = substitute_bytes_u64(value, &SBOX_64);
        value ^ !u64::from(state.rotate_right(3))
    }

    fn word32(mut value: u32, state: u32) -> u32 {
        value = !value;
        value = swap_adjacent_bits_u32(value);
        value = value.wrapping_add(state.rotate_left(5));
        value = value.wrapping_sub(state.rotate_left(7));
        value = substitute_bytes_u32(value, &SBOX_32);
        value ^ state.rotate_left(3)
    }

    fn byte(mut value: u8, state: u32) -> u8 {
        let mix3 = state.wrapping_mul(POW11_3);
        let mix5 = state.wrapping_mul(POW11_5);
        let mix7 = state.wrapping_mul(POW11_7);

        value = !value;
        value = swap_adjacent_bits_u8(value);
        value = value.wrapping_add(mix5 as u8);
        value = value.wrapping_sub(mix7 as u8);
        value = SBOX_8[value as usize];
        value ^ mix3 as u8
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn byte_lane_constants_match_the_word_rotations() {
        for (constant, exponent) in [(POW11_3, 3), (POW11_5, 5), (POW11_7, 7)] {
            assert_eq!(constant, 11u32.pow(exponent));
        }
    }

    /// A DefaultCeremony first word observed at actor 538, 64 bits.
    #[test]
    fn decodes_an_observed_ceremony_word() {
        let mut raw = [0xde, 0x8e, 0xd6, 0x08, 0xe3, 0x73, 0x0d, 0xce];
        crate::transform_in_place::<V13_08China>(&mut raw, 64, crate::seed_for(64, 538)).unwrap();
        assert_eq!(raw, [0x10, 0x0c, 0xa2, 0x61, 0x30, 0x0f, 0x81, 0x00]);
    }
}
