//! Exact, non-identifying observations from the preserved China 13.08 and 13.09 replays.
use vrf_transform::{TransformVersion, seed_for};

#[test]
fn china_1308_decodes_observed_ceremony_word() {
    let mut raw = [0xde, 0x8e, 0xd6, 0x08, 0xe3, 0x73, 0x0d, 0xce];
    TransformVersion::V1308China
        .apply(&mut raw, 64, seed_for(64, 538))
        .unwrap();
    assert_eq!(raw, [0x10, 0x0c, 0xa2, 0x61, 0x30, 0x0f, 0x81, 0x00]);
}

#[test]
fn china_1309_decodes_observed_ceremony_word() {
    let mut raw = [0x23, 0xf6, 0xcb, 0x85, 0xed, 0x75, 0xa4, 0x13];
    TransformVersion::V1309China
        .apply(&mut raw, 64, seed_for(64, 588))
        .unwrap();
    assert_eq!(raw, [0x10, 0x0c, 0xa2, 0x61, 0x30, 0x0f, 0x81, 0x00]);
}

#[test]
fn china_1309_decodes_observed_ceremony_block_with_tail() {
    // 32-bit lane, one byte, then a 7-bit tail: every stage and TAIL_XOR.
    let mut raw = [0xde, 0x8d, 0x80, 0x6a, 0x71, 0x28];
    TransformVersion::V1309China
        .apply(&mut raw, 47, seed_for(47, 588))
        .unwrap();
    assert_eq!(raw, [0x10, 0x0c, 0xa2, 0x61, 0x30, 0x00]);
}

#[test]
fn regional_branches_are_exact_and_do_not_alias_global() {
    assert_ne!(
        TransformVersion::require("++Ares-Core+release-china-13.08").unwrap(),
        TransformVersion::V1308
    );
    assert!(TransformVersion::require("++Ares-Core+release-china-13.07").is_err());
    assert_ne!(
        TransformVersion::require("++Ares-Core+release-china-13.09").unwrap(),
        TransformVersion::V1309
    );
    assert!(TransformVersion::require("++Ares-Core+release-china-13.10").is_err());
}
