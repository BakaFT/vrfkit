//! Run the real CLI: a forced transform is a measurement, never file support.
mod common;

use common::*;

fn replay(dir: &std::path::Path, branch: &str) -> std::path::PathBuf {
    let mut data = replay_info(&Info::default());
    data.extend(chunk(
        0,
        &header_payload_for_branch(branch, 0, &[3, 0, 0, 0, 49, 56, 0]),
    ));
    let path = dir.join("probe.vrf");
    std::fs::write(&path, data).unwrap();
    path
}

#[test]
fn probe_accepts_an_unknown_header_without_claiming_support_or_changing_it() {
    let dir = scratch("transform_probe", "unknown");
    let branch = "++Ares-Core+release-china-99.99";
    let path = replay(&dir, branch);
    let original = std::fs::read(&path).unwrap();
    let normal = vrfkit(&["validate", path_arg(&path)]);
    assert_eq!(normal.code, Some(1), "{}", normal.stderr);
    for forced in ["release-china-13.09", "++Ares-Core+release-china-13.09"] {
        let run = vrfkit(&["validate", path_arg(&path), "--transform", forced]);
        assert_eq!(run.code, Some(3), "{}\n{}", run.stdout, run.stderr);
        assert_eq!(line_value(&run.stdout, "Branch:"), branch);
        assert!(line_value(&run.stdout, "VERDICT:").starts_with("PROBE"));
        assert!(run.stderr.contains("++Ares-Core+release-china-13.09"));
        assert_eq!(std::fs::read(&path).unwrap(), original);
    }
    std::fs::remove_dir_all(dir).unwrap();
}

#[test]
fn forcing_the_files_own_transform_still_returns_probe() {
    let dir = scratch("transform_probe", "same");
    let path = replay(&dir, "++Ares-Core+release-12.10");
    assert_eq!(vrfkit(&["validate", path_arg(&path)]).code, Some(2));
    let run = vrfkit(&["validate", path_arg(&path), "--transform", "release-12.10"]);
    assert_eq!(run.code, Some(3), "{}\n{}", run.stdout, run.stderr);
    assert!(line_value(&run.stdout, "VERDICT:").starts_with("PROBE"));
    std::fs::remove_dir_all(dir).unwrap();
}
