//! `++Ares-Core+release-china-13.05`

use super::SeededTransform;

const POW11_1: u32 = 11;
const POW11_2: u32 = 121;
const POW11_4: u32 = 14_641;
const POW11_6: u32 = 1_771_561;
const POW11_7: u32 = 19_487_171;
const POW11_8: u32 = 214_358_881;

/// `++Ares-Core+release-china-13.05`
///
/// This regional transform was recovered from replay measurements. Four exact
/// first words at different states fixed the shortest six-operation family;
/// seven 47-bit and seven 9-bit ceremony blocks fixed the corresponding short
/// lanes. Five deterministic TimedBomb blocks supplied later-state relations,
/// and an exhaustive `u32` scan reduced the PRNG constants to one family.
/// Normal branch dispatch then walked all 276,631 ReplayData blocks in the
/// preserved replay with zero malformed framing, transform failures, RPC loss
/// or unread bytes. Export with checkpoints retained every unexplained bit as
/// 131 ReplayData and 20 checkpoint RepLayout-tail rows plus 1,416 opaque RPC
/// rows; typed state independently matched all ten players' final K/D and the
/// 5-3 score.
///
/// `tools/china_transform_oracle.py` is the independent implementation behind
/// eleven generated vectors at every 64/32/8/tail staging boundary.
///
/// The four middle rotations commute. The order below is the canonical
/// representative recorded in `tools/china_release/evidence/china_13_05.json`.
/// Subtracting `0x37` is wire-equivalent to adding `0x49`, because the seed-mix
/// offset is only observable modulo 128.
pub struct V13_05China;

impl SeededTransform for V13_05China {
    const BRANCH: &'static str = "++Ares-Core+release-china-13.05";
    const SEED_ADDEND: u32 = 0xf677_61c9;
    const INIT_A_OFFSET: u32 = 0x37;
    const TAIL_XOR: u8 = 0xc9;

    fn word64(mut value: u64, state: u32) -> u64 {
        value = value.wrapping_add(u64::from(state.rotate_right(8)));
        value = value.rotate_left((state.rotate_right(4) % 63) + 1);
        value = value.rotate_left((state.rotate_right(6) % 63) + 1);
        value = value.rotate_right((state.rotate_right(2) % 63) + 1);
        value = value.rotate_right((state.rotate_right(7) % 63) + 1);
        value.wrapping_sub(u64::from(state.rotate_right(1)))
    }

    fn word32(mut value: u32, state: u32) -> u32 {
        value = value.wrapping_add(state.rotate_left(8));
        value = value.rotate_left((state.rotate_left(4) % 31) + 1);
        value = value.rotate_left((state.rotate_left(6) % 31) + 1);
        value = value.rotate_right((state.rotate_left(2) % 31) + 1);
        value = value.rotate_right((state.rotate_left(7) % 31) + 1);
        value.wrapping_sub(state.rotate_left(1))
    }

    fn byte(mut value: u8, state: u32) -> u8 {
        let mix1 = state.wrapping_mul(POW11_1);
        let mix2 = state.wrapping_mul(POW11_2);
        let mix4 = state.wrapping_mul(POW11_4);
        let mix6 = state.wrapping_mul(POW11_6);
        let mix7 = state.wrapping_mul(POW11_7);
        let mix8 = state.wrapping_mul(POW11_8);

        value = value.wrapping_add(mix8 as u8);
        value = value.rotate_left((mix4 % 7) + 1);
        value = value.rotate_left((mix6 % 7) + 1);
        value = value.rotate_right((mix2 % 7) + 1);
        value = value.rotate_right((mix7 % 7) + 1);
        value.wrapping_sub(mix1 as u8)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn byte_lane_constants_match_the_word_rotations() {
        for (constant, exponent) in [
            (POW11_1, 1),
            (POW11_2, 2),
            (POW11_4, 4),
            (POW11_6, 6),
            (POW11_7, 7),
            (POW11_8, 8),
        ] {
            assert_eq!(constant, 11u32.pow(exponent));
        }
    }
}
