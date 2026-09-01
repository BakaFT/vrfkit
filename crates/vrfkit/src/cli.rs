//! Argument parsing -- hand-rolled, no external dependencies.
//!
//! Three subcommands:
//!   inspect `<file>`
//!   validate `<file>`
//!   export `<file>` --out `<dir>`      (feature `export`)

use crate::error::CliError;
use crate::inspect;
use crate::oracle;

/// The part of a replay branch string that has never differed between builds.
///
/// Only `--transform` uses this, to let a human type `release-13.02` instead of
/// the full header string. It deliberately does **not** live in
/// `vrf_transform::TransformVersion::from_branch`: that function matches the
/// string a replay header actually carries, and a prefix-tolerant lookup there
/// would let a file whose branch merely resembles a known one resolve to the
/// wrong transform -- which produces plausible garbage rather than an error.
///
/// `branch_prefix_holds_for_every_registered_build` pins the assumption, so a
/// build that arrives under a different prefix fails a test instead of having
/// its name silently mangled.
const BRANCH_PREFIX: &str = "++Ares-Core+";

/// Expand a `--transform` argument to a full branch string.
///
/// Anything already starting with `+` is taken as written, so a full header
/// string pasted from `inspect` still works and a typo in the prefix reaches
/// the lookup intact instead of being prepended onto.
fn resolve_transform_branch(arg: &str) -> String {
    if arg.starts_with('+') {
        arg.to_owned()
    } else {
        format!("{BRANCH_PREFIX}{arg}")
    }
}

const USAGE: &str = "\
vrfkit -- VALORANT replay (.vrf) toolkit

USAGE:
    vrfkit inspect  <file.vrf> [--redact-identifiers]
    vrfkit validate <file.vrf> [--diagnostics] [--transform <branch>]
    vrfkit export   <file.vrf> --out <dir> [--checkpoints]

SUBCOMMANDS:
    inspect   Print replay info, header, branch, and chunk summary
              --redact-identifiers  Suppress the replay's friendly name
    validate  Run the RepLayout grammar oracle on every ReplayData content
              block. Exits 0 when all present content was consumed or preserved,
              1 when validation found loss, 2 when the file carried no content
              blocks to check, and 3 when --transform made the run a probe
              rather than a verdict.
              --diagnostics  Print full context for every malformed/skipped event
              --transform <branch>
                             Force a registered branch's transform onto this
                             file instead of the one its header asks for. Takes
                             either a bare `release-13.02` or the full
                             `++Ares-Core+release-13.02`. For bringing up an
                             unsupported build: implement a candidate, point
                             this at a real replay, and read the pass rate (a
                             correct transform frames ~100%, a wrong one ~0%).
                             Always exits 3 -- a forced run measures a
                             hypothesis, not the file, and must not be
                             mistakable for support.
    export    Write five Parquet tables (fields, movement, actors,
              net_guids, events) + manifest.json
              --checkpoints  Also parse Checkpoint chunks into
                             checkpoint_fields.parquet. Off by default: the
                             snapshots are ~10% of the file and a separate
                             read, and the five other tables are unaffected
                             either way.
";

/// Dispatch one command line and report the process exit code it earns.
///
/// `Ok(0)` for every subcommand that has nothing to conclude. `validate` is the
/// exception: it is an oracle, so it returns its own code and `Ok` no longer
/// means "clean". See [`oracle::Verdict`].
pub fn run(args: &[String]) -> Result<u8, CliError> {
    // args[0] = binary name
    if args.len() < 2 {
        return Err(CliError::Usage(USAGE.to_string()));
    }

    match args[1].as_str() {
        "inspect" => {
            let file = args
                .get(2)
                .ok_or_else(|| CliError::Usage("inspect requires <file.vrf>".to_string()))?;
            let mut redact_identifiers = false;
            for arg in args.iter().skip(3) {
                match arg.as_str() {
                    "--redact-identifiers" if !redact_identifiers => {
                        redact_identifiers = true;
                    }
                    "--redact-identifiers" => {
                        return Err(CliError::Usage(
                            "duplicate option: --redact-identifiers".to_string(),
                        ));
                    }
                    other => {
                        return Err(CliError::Usage(format!(
                            "unknown inspect option or surplus argument: {other}"
                        )));
                    }
                }
            }
            inspect::run(file, redact_identifiers).map(|()| 0)
        }
        "validate" => {
            let file = args
                .get(2)
                .ok_or_else(|| CliError::Usage("validate requires <file.vrf>".to_string()))?;
            let mut diagnostics = false;
            let mut transform: Option<String> = None;
            let mut i = 3;
            while i < args.len() {
                match args[i].as_str() {
                    "--diagnostics" if !diagnostics => diagnostics = true,
                    "--diagnostics" => {
                        return Err(CliError::Usage(
                            "duplicate option: --diagnostics".to_string(),
                        ));
                    }
                    "--transform" if transform.is_some() => {
                        return Err(CliError::Usage("duplicate option: --transform".to_string()));
                    }
                    "--transform" => {
                        i += 1;
                        let arg = args.get(i).map(String::as_str).ok_or_else(|| {
                            CliError::Usage("--transform requires a branch string".to_string())
                        })?;
                        transform = Some(resolve_transform_branch(arg));
                    }
                    other => {
                        return Err(CliError::Usage(format!(
                            "unknown validate option or surplus argument: {other}"
                        )));
                    }
                }
                i += 1;
            }
            oracle::run(file, diagnostics, transform.as_deref()).map(oracle::Verdict::exit_code)
        }
        "export" => export(args).map(|()| 0),
        "help" | "--help" | "-h" => {
            println!("{USAGE}");
            Ok(0)
        }
        other => Err(CliError::Usage(format!(
            "unknown subcommand: {other}\n{USAGE}"
        ))),
    }
}

#[cfg(feature = "export")]
fn export(args: &[String]) -> Result<(), CliError> {
    let file = args
        .get(2)
        .ok_or_else(|| CliError::Usage("export requires <file.vrf>".to_string()))?;
    let mut out_dir: Option<&str> = None;
    let mut with_checkpoints = false;
    let mut i = 3;
    while i < args.len() {
        if args[i] == "--out" {
            if out_dir.is_some() {
                return Err(CliError::Usage("duplicate option: --out".to_string()));
            }
            i += 1;
            out_dir =
                Some(args.get(i).map(String::as_str).ok_or_else(|| {
                    CliError::Usage("--out requires a directory path".to_string())
                })?);
        } else if args[i] == "--checkpoints" {
            if with_checkpoints {
                return Err(CliError::Usage(
                    "duplicate option: --checkpoints".to_string(),
                ));
            }
            with_checkpoints = true;
        } else {
            return Err(CliError::Usage(format!("unknown option: {}", args[i])));
        }
        i += 1;
    }
    let out_dir =
        out_dir.ok_or_else(|| CliError::Usage("export requires --out <dir>".to_string()))?;
    crate::driver::run(file, out_dir, with_checkpoints)
}

/// Refusal, not silence. A build without the `export` feature has no Parquet
/// writers at all, and a subcommand that printed nothing and exited 0 would be
/// indistinguishable from one that wrote the files.
#[cfg(not(feature = "export"))]
fn export(_args: &[String]) -> Result<(), CliError> {
    Err(CliError::Usage(
        "export is not available: this binary was built without the `export` feature".to_string(),
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn owned(args: &[&str]) -> Vec<String> {
        args.iter().map(|arg| (*arg).to_owned()).collect()
    }

    #[test]
    fn inspect_rejects_surplus_arguments_before_opening_the_file() {
        let err = run(&owned(&["vrfkit", "inspect", "missing.vrf", "extra"]))
            .expect_err("inspect must not ignore a surplus positional argument");
        assert!(matches!(err, CliError::Usage(_)), "got {err:?}");
    }

    #[test]
    fn inspect_accepts_identifier_redaction_before_opening_the_file() {
        let err = run(&owned(&[
            "vrfkit",
            "inspect",
            "missing.vrf",
            "--redact-identifiers",
        ]))
        .expect_err("the missing input should still be opened after parsing");
        assert!(matches!(err, CliError::Io(_)), "got {err:?}");
    }

    #[test]
    fn inspect_rejects_duplicate_identifier_redaction() {
        let err = run(&owned(&[
            "vrfkit",
            "inspect",
            "missing.vrf",
            "--redact-identifiers",
            "--redact-identifiers",
        ]))
        .expect_err("duplicate privacy options must not be ignored");
        assert!(matches!(err, CliError::Usage(_)), "got {err:?}");
    }

    #[test]
    fn validate_rejects_unknown_options_before_opening_the_file() {
        let err = run(&owned(&["vrfkit", "validate", "missing.vrf", "--unknown"]))
            .expect_err("validate must not ignore an unknown option");
        assert!(matches!(err, CliError::Usage(_)), "got {err:?}");
    }

    #[test]
    fn validate_rejects_surplus_positional_arguments() {
        let err = run(&owned(&["vrfkit", "validate", "missing.vrf", "other.vrf"]))
            .expect_err("validate must not ignore another input path");
        assert!(matches!(err, CliError::Usage(_)), "got {err:?}");
    }

    #[test]
    fn validate_rejects_transform_without_a_branch() {
        let err = run(&owned(&[
            "vrfkit",
            "validate",
            "missing.vrf",
            "--transform",
        ]))
        .expect_err("--transform must not silently mean 'no override'");
        assert!(matches!(err, CliError::Usage(_)), "got {err:?}");
    }

    #[test]
    fn validate_rejects_duplicate_transform() {
        let err = run(&owned(&[
            "vrfkit",
            "validate",
            "missing.vrf",
            "--transform",
            "++Ares-Core+release-13.02",
            "--transform",
            "++Ares-Core+release-13.01",
        ]))
        .expect_err("validate must reject a duplicate --transform");
        assert!(matches!(err, CliError::Usage(_)), "got {err:?}");
    }

    /// The shorthand is only safe while every build shares the prefix.
    ///
    /// If a future build arrives under a different one, `release-<x>` would be
    /// expanded into a branch that does not exist while the real branch became
    /// untypeable in short form. Fail here instead.
    #[test]
    fn branch_prefix_holds_for_every_registered_build() {
        for version in vrf_transform::ALL_VERSIONS {
            assert!(
                version.branch().starts_with(BRANCH_PREFIX),
                "{} does not start with {BRANCH_PREFIX}; the --transform shorthand cannot expand it",
                version.branch()
            );
        }
    }

    #[test]
    fn transform_shorthand_expands_to_the_full_branch() {
        for version in vrf_transform::ALL_VERSIONS {
            let full = version.branch();
            let short = full
                .strip_prefix(BRANCH_PREFIX)
                .expect("prefix checked above");
            assert_eq!(resolve_transform_branch(short), full);
            // A full string pasted from `inspect` must survive unchanged.
            assert_eq!(resolve_transform_branch(full), full);
        }
    }

    /// A mistyped prefix reaches the lookup as written, so the error names what
    /// was actually asked for rather than a doubly-prefixed mangling of it.
    #[test]
    fn a_leading_plus_is_never_prefixed_again() {
        assert_eq!(
            resolve_transform_branch("++Ares-Kore+release-13.02"),
            "++Ares-Kore+release-13.02"
        );
    }

    /// `--transform` takes the NEXT argument as its value, so a branch string
    /// must not be re-parsed as an option or as a surplus input path.
    #[test]
    fn validate_accepts_transform_with_diagnostics_and_reaches_the_file() {
        let err = run(&owned(&[
            "vrfkit",
            "validate",
            "missing.vrf",
            "--transform",
            "++Ares-Core+release-13.02",
            "--diagnostics",
        ]))
        .expect_err("the file does not exist, so this must fail at open time");
        // Io, not Usage: argument parsing accepted the pair and got as far as
        // opening the replay.
        assert!(matches!(err, CliError::Io(_)), "got {err:?}");
    }

    #[cfg(feature = "export")]
    #[test]
    fn export_rejects_duplicate_out_before_opening_the_file() {
        let err = run(&owned(&[
            "vrfkit",
            "export",
            "missing.vrf",
            "--out",
            "first",
            "--out",
            "second",
        ]))
        .expect_err("export must reject a duplicate --out");
        assert!(matches!(err, CliError::Usage(_)), "got {err:?}");
    }

    #[cfg(feature = "export")]
    #[test]
    fn export_rejects_duplicate_checkpoints_before_opening_the_file() {
        let err = run(&owned(&[
            "vrfkit",
            "export",
            "missing.vrf",
            "--out",
            "out",
            "--checkpoints",
            "--checkpoints",
        ]))
        .expect_err("export must reject a duplicate --checkpoints");
        assert!(matches!(err, CliError::Usage(_)), "got {err:?}");
    }
}
