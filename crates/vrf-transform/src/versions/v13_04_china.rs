//! `++Ares-Core+release-china-13.04`

use super::SeededTransform;
use crate::helpers::{reverse_bits_u8, reverse_bits_u32, reverse_bits64_without_final_16bit_swap};

const POW11_1: u32 = 11;
const POW11_2: u32 = 121;
const POW11_3: u32 = 1_331;
const POW11_4: u32 = 14_641;
const POW11_6: u32 = 1_771_561;

/// `++Ares-Core+release-china-13.04`
///
/// This regional branch does not reuse global 13.04. The implementation was
/// recovered from replay measurements rather than a published source:
///
/// - two independently seeded ceremony words fixed the six-operation 64-bit
///   sequence;
/// - seven 47-bit and seven 9-bit ceremony blocks fixed the corresponding
///   32-bit and byte lanes;
/// - an Ace event identified the player relation used to recover the PRNG
///   constants, which then decoded all ten character/PlayerState links;
/// - on 2026-09-01 the real replay oracle walked 285,488 of 285,488 ReplayData
///   blocks with zero malformed framing, transform failures, RPC loss, state
///   loss or unread bytes. Ninety known RepLayout suffixes and 1,753 unresolved
///   RPC payloads remained explicitly preserved as raw data.
///
/// `tools/china_transform_oracle.py` is the independent implementation behind
/// eleven generated vectors at every 64/32/8/tail staging boundary.
///
/// The seed expression only observes the offset modulo 128 because it multiplies
/// by `0x0200_0000`. Therefore subtracting `0x5f` is wire-equivalent to adding
/// `0x21`; the subtraction form is the canonical representative used here.
pub struct V13_04China;

impl SeededTransform for V13_04China {
    const BRANCH: &'static str = "++Ares-Core+release-china-13.04";
    const SEED_ADDEND: u32 = 0xe920_64a1;
    const INIT_A_OFFSET: u32 = 0x5f;
    const TAIL_XOR: u8 = 0xa1;

    fn word64(mut value: u64, state: u32) -> u64 {
        value = reverse_bits64_without_final_16bit_swap(value);
        value ^= u64::from(state.rotate_right(6));
        value = value.wrapping_add(u64::from(state.rotate_right(4)));
        value = value.wrapping_add(u64::from(state.rotate_right(3)));
        value = value.wrapping_add(u64::from(state.rotate_right(2)));
        value ^ u64::from(state.rotate_right(1))
    }

    fn word32(mut value: u32, state: u32) -> u32 {
        value = reverse_bits_u32(value);
        value ^= !state.rotate_left(6);
        value = value.wrapping_add(state.rotate_left(4));
        value = value.wrapping_add(state.rotate_left(3));
        value = value.wrapping_add(state.rotate_left(2));
        value ^ !state.rotate_left(1)
    }

    fn byte(mut value: u8, state: u32) -> u8 {
        let mix1 = state.wrapping_mul(POW11_1);
        let mix2 = state.wrapping_mul(POW11_2);
        let mix3 = state.wrapping_mul(POW11_3);
        let mix4 = state.wrapping_mul(POW11_4);
        let mix6 = state.wrapping_mul(POW11_6);

        value = reverse_bits_u8(value);
        value ^= !(mix6 as u8);
        value = value.wrapping_add(mix4 as u8);
        value = value.wrapping_add(mix3 as u8);
        value = value.wrapping_add(mix2 as u8);
        value ^ !(mix1 as u8)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn byte_lane_constants_match_the_word_rotations() {
        assert_eq!(POW11_1, 11u32.pow(1));
        assert_eq!(POW11_2, 11u32.pow(2));
        assert_eq!(POW11_3, 11u32.pow(3));
        assert_eq!(POW11_4, 11u32.pow(4));
        assert_eq!(POW11_6, 11u32.pow(6));
    }
}
