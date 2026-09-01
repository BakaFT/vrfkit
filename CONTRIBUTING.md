# Contributing to vrfkit

Thanks for your interest. vrfkit is a reverse-engineered parser for a format
that changes every game build, so it has a few unusual rules. Please read these
before opening a PR.

## Build

```bash
cargo +1.86.0 build --release -p vrfkit --locked                       # inspect / validate / export
cargo +1.86.0 build --release -p vrfkit --no-default-features --locked # inspect / validate only
```

Edition 2024. `#![forbid(unsafe_code)]` is in every crate — do not add `unsafe`.

Python tooling under `tools/` needs `pip install -r requirements.txt`
(pyarrow, numpy) -- without it several checks below fail to import instead of
running.

**MSRV is 1.86, and CI pins exactly that.** A newer local toolchain accepts
syntax 1.86 rejects — `let` chains are the one that has already broken a build —
so a green `cargo test` on your machine is not evidence CI will pass. Install
the pinned toolchain once and run the sweep through it:

```bash
rustup toolchain install 1.86.0 --component clippy,rustfmt
cargo +1.86.0 clippy --workspace --all-targets --all-features --locked -- -D warnings
```

## Before you open a PR

Run the full sweep. Every one of these must be green:

```bash
cargo +1.86.0 fmt --check
cargo +1.86.0 clippy --workspace --all-targets --all-features --locked -- -D warnings
cargo +1.86.0 test --workspace --locked
cargo +1.86.0 check --workspace --all-targets --all-features --locked
RUSTDOCFLAGS="-D warnings" cargo +1.86.0 doc --workspace --all-features --no-deps --locked
cargo +1.86.0 check --manifest-path tools/probe_offset/Cargo.toml --locked
VRFKIT_INTEROP_DIR="<private-root>" cargo +1.86.0 test -p vrf-export --test roundtrip write_interop_files --locked -- --exact
python -W error crates/vrf-export/tests/python_interop.py "<private-root>/interop"
python -W error tools/check_ascii.py --check
python -W error tools/apply_type_corrections.py --check
python -W error tools/check_effect_decoder.py --check
python -W error tools/extract_checksum_types.py --export tools/fixtures/checksum_export --check
python -W error tools/check_baseline_schemas.py
python tools/check_docs.py            # not --fast: that skips the count check
python -W error -m unittest discover -s tools/tests -p "test_*.py"
```

For the interop lines, point `VRFKIT_INTEROP_DIR` at a private root; the Rust
test writes its files to that root's `interop` child, which is passed exactly
to Python. The script refuses to search the system temp directory, because
“newest” can be a stale fixture from another checkout.

Run every advertised core-only and singleton feature, not just the default
workspace. These are the commands CI executes; each singleton intentionally
starts from `--no-default-features`:

```bash
cargo +1.86.0 check -p vrfkit --no-default-features --locked
cargo +1.86.0 check -p vrfkit --no-default-features --features export --locked
cargo +1.86.0 check -p vrf-bitio --no-default-features --locked
cargo +1.86.0 check -p vrf-bitio --no-default-features --features alloc --locked
cargo +1.86.0 check -p vrf-container --no-default-features --locked
cargo +1.86.0 check -p vrf-container --no-default-features --features oodle --locked
cargo +1.86.0 check -p vrf-container --no-default-features --features event --locked
cargo +1.86.0 check -p vrf-container --no-default-features --features checkpoint --locked
cargo +1.86.0 check -p vrf-decode --no-default-features --locked
cargo +1.86.0 check -p vrf-decode --no-default-features --features array --locked
cargo +1.86.0 check -p vrf-decode --no-default-features --features effect --locked
cargo +1.86.0 check -p vrf-decode --no-default-features --features overlay --locked
cargo +1.86.0 check -p vrf-decode --no-default-features --features structs --locked
cargo +1.86.0 check -p vrf-export --no-default-features --locked
cargo +1.86.0 check -p vrf-export --no-default-features --features parquet --locked
cargo +1.86.0 check -p vrf-export --no-default-features --features fields --locked
cargo +1.86.0 check -p vrf-export --no-default-features --features movement --locked
cargo +1.86.0 check -p vrf-export --no-default-features --features actors --locked
cargo +1.86.0 check -p vrf-export --no-default-features --features net-guids --locked
cargo +1.86.0 check -p vrf-export --no-default-features --features events --locked
cargo +1.86.0 check -p vrf-export --no-default-features --features snappy --locked
cargo +1.86.0 check -p vrf-net --no-default-features --locked
cargo +1.86.0 check -p vrf-net --no-default-features --features diagnostics --locked
cargo +1.86.0 check -p vrf-schema --no-default-features --locked
cargo +1.86.0 check -p vrf-schema --no-default-features --features checkpoint --locked
```

`check_docs.py` without `--fast` runs the suites so it can compare the numbers
the docs quote against the real ones. CI runs `--fast` and cannot do otherwise —
the full mode shells out to `cargo test`, and the Python job is Ubuntu-only
because the Rust job needs Windows for the Oodle FFI. **That check is yours to
run, not CI's**, and it is the only thing that catches a stale count in prose.

If your change affects exported output, also run the regression guards in
[`docs/USAGE.md`](docs/USAGE.md) §6 (`check_export_baseline.py`,
`check_decode_errors_corpus.py`, `validate_corpus.py`) against a replay, and
update baselines with `--update` only after explaining each changed line. Those
need a corpus — see [Environment](#environment) below.

## Environment

The corpus guards read their inputs from environment variables rather than
hardcoded paths, so nothing in the tree points at one person's disk. None of
them are needed for the sweep above; all of them are needed for §6.

| Variable | What it points at | Read by |
|---|---|---|
| `VRFKIT_CORPUS_DIR` | Directory of `.vrf` replays; a bare filename in a baseline resolves against it | `check_export_baseline.py`, `check_corpus_baseline.py`, `check_metrics_baseline.py` |
| `VRFKIT_CSHARP_DIR` | Checkout root of the C# reference parser | `analyze_coverage.py`, `extract_equippables.py` |
| `VRFKIT_VALPLAY_DIR` | valplay checkout root | `check_metrics_baseline.py`, `validate_metrics_corpus.py`, `compare_combat_report.py`, `compare_rpc_params.py` |
| `VRFKIT_JOBS` | Worker count for the corpus sweeps; default is cores - 2, capped at 16 | `validate_corpus.py` |
| `VRFKIT_REQUIRE_CORPUS` | Set to anything to turn "corpus absent, skipping" into a failure | `crates/vrf-container/tests/corpus.rs`, `check_export_baseline.py`, `check_corpus_baseline.py` |

The `compare_*.py` scripts were listed against `VRFKIT_CSHARP_DIR` here, which
none of them reads. Two of them (`compare_combat_report.py`,
`compare_rpc_params.py`) read `VRFKIT_VALPLAY_DIR`, because what they compare
against is a valplay bundle. The third, `compare_with_csharp.py`, reads **no
environment variable at all** -- it takes the C# bundle directory and the vrfkit
output directory as its two positional arguments. Nothing checks this table, so
verify a row by grepping for the variable rather than by reading the name:

```bash
grep -rn "VRFKIT_" tools/*.py | grep environ
```

**`tests/corpus.rs` is a container-level smoke test, not a decode sweep.** It
parses each replay's header and decompresses its Oodle chunks; it never reaches
a field. A green `cargo test` with the corpus present therefore says nothing
about decoding. The sweeps that do are `validate_corpus.py` (RepLayout framing
on every content block) and `check_decode_errors_corpus.py` (the overlay), and
neither runs under `cargo test` or in CI. The names do not distinguish them, so
the distinction is written here.

```bash
export VRFKIT_CORPUS_DIR=/path/to/replays
python tools/check_decode_errors_corpus.py ./target/release/vrfkit "$VRFKIT_CORPUS_DIR"
```

**Without `VRFKIT_CORPUS_DIR` the guards skip and exit 0**, printing `SKIP:
replay not present`. That is deliberate — the corpus lives outside the repo, so
a contributor without one is not blocked — but it means an unset variable reads
as a pass at a glance. If you meant to run them, read the output and check it
says how many replays it walked.

## The load-bearing invariants (do not break)

These corrupt downstream consumers silently — no test fails when they break.

- **No skip path.** Every walkable field emits `raw_bits` even when its type is
  unknown or decoding fails. Typed `value_*` columns are an *additive* overlay;
  a decode failure leaves them null with the raw bits intact.
- **No silent success.** A block whose group cannot be resolved fails loudly
  (counted in `RPC stream failed`), never guessed.
- **Byte-identical output.** Exported Parquet is reproducible run to run. If you
  change row buffering, batch sizes, or iteration order, verify the output is
  byte-identical (the baselines pin this).
- **ASCII only** in Rust code and comments — the Windows cp949 console truncates
  output at the first non-ASCII byte in a format string.
- **No hardcoded names** in the parser. Display names live in the Python adapter
  (`tools/equippable_table.py`), never in a Rust crate.

## Bringing up a new game build

Riot rotates the payload transform every build. Across the seven in the tree no
two `word64` implementations are alike — the operator order, the `k` values it
rotates the state by, and whether the S-box stage runs at all have all changed
between consecutive releases. What has *never* changed is the skeleton: the
PRNG and its multiplier, `initial_prng_b`, the 64 → 32 → 8 → tail staging,
`seed_for`, and the S-box tables. So a new build is one `SeededTransform` impl,
and the rest of the workspace needs nothing: the container is version-pinned but
not build-pinned, field names come from the replay, handle layouts resolve by
name, and the checksum type table is content-addressed.

### 1. Check the container first

```bash
vrfkit inspect <new.vrf>
```

This works before any transform is registered. Confirm the branch string and
that `Network version` / `Engine net proto` still read 19 / 32. If either
moved, stop — that is a format change, and the pins in
`crates/vrf-container/src/limits.rs` are **not** a knob to turn to make a file
parse.

### 2. Ask whether the transform even changed

```bash
vrfkit validate <new.vrf> --transform release-<previous>
```

`--transform` forces a registered branch's transform onto the file. History says
it will not match — but confirming costs one command, and the same flag is the
measuring instrument for everything below. It always exits 3: a forced run
measures a hypothesis, not the file, and must never be mistakable for support.

### 3. Recover `word64` only

Register the new branch with a candidate `word64`, and leave the other two
lanes returning `0` for now. The oracle is near-binary and the staging gives a
graded signal, so you can confirm one lane at a time:

| lanes implemented | expected pass rate |
|---|---|
| nothing right | ~0% |
| `word64` right, 32/8 stubbed | ~99.6% |
| `word64` + `word32` | ~99.8% |
| all three | ~100% |

Those middle rows are what makes this tractable: **a correct `word64` is
visible on its own**, because only payloads whose length is not a multiple of
64 bits depend on the shorter lanes, and they are a small minority. You are
never guessing three functions at once.

`TAIL_XOR` is not an independent constant — it is the low byte of
`SEED_ADDEND` in all seven builds, and a test in `versions/mod.rs` enforces that.

### 4. Derive the other two lanes

Do not reverse them separately. Within one build the three word functions are
the same primitive sequence in three widths, differing only in how each derives
its per-word constant from `state`:

| lane | state derivation | modulus |
|---|---|---|
| 64-bit | `state.rotate_right(k)` | `% 63` |
| 32-bit | `state.rotate_left(k)` | `% 31` |
| byte | `state.wrapping_mul(11.pow(k))` | `% 7` |

Same `k` set, same operator order, same positions. The byte lane's magic
numbers are powers of eleven in disguise: `0x79` is `11^2`, `0x533` is `11^3`,
and `0x31`/`0x29` are `11^4`/`11^6` reduced mod 256. Expect one deliberate
asymmetry — several builds add or drop a complement in one lane — which shows up
as a pass rate that improves but stops short of 100%.

`versions/v13_02_china.rs` is the worked example: its 32-bit and byte lanes were
recovered this way after its source implementation had left both zeroing their
input.

### 5. Prove it twice

A replay validating is not enough on its own, and neither are golden vectors.

- **Golden vectors** catch a transcription slip between two implementations.
  They must come from somewhere other than the Rust you just wrote, or they
  prove nothing. `tools/extract_golden.py` lifts them from the C# fixture where
  one exists; `tools/china_transform_oracle.py` is the pattern to copy when one
  does not.
- **A real replay** catches the algorithm being wrong, which no vector taken
  from your own implementation ever will.
- **Values, not counters.** `Decode errors: 0` means nothing threw. Export and
  read something with a known shape — a scoreline that reaches 13, a
  half-time side switch at the right round — before believing it.

### 6. Register it everywhere

`ALL_VERSIONS` is `[TransformVersion; N]`; its *type* carries the count, so
adding a build touches `lib.rs` (import, variant, array, `branch()`, `apply()`),
`versions/mod.rs` (`mod`, `pub use`, the `build_table()` row), the golden
generator, and the build tables in `README.md` and `docs/USAGE.md`. The tests
that fail until you do are `every_registered_build_is_covered`,
`tail_xor_is_low_byte_of_seed_addend`, `build_constants_are_all_distinct`, and
`check_docs.py`. Let them.

## Generated files — never hand-edit

| File | Generator |
|---|---|
| `crates/vrf-decode/src/table.rs` | `tools/extract_descriptors.py` then `tools/apply_type_corrections.py` |
| `crates/vrf-decode/src/checksum_table.rs` | `tools/extract_checksum_types.py` against one or more fresh exports |
| `crates/vrf-transform/src/sbox.rs` | `tools/extract_sboxes.py` |
| `crates/vrf-transform/tests/data/golden_vectors.rs` | `tools/extract_golden.py` |
| `tools/equippable_table.py` | `tools/extract_equippables.py` |

Ordering for the overlay table is load-bearing:
`extract_descriptors.py` → `apply_type_corrections.py` → `cargo fmt` →
`extract_checksum_types.py` (against a **fresh** export).

The checksum step is last because it learns from what the overlay table
declares. Run it before the additions land and the new entries are not donors
yet -- the symptom is a field typed on the group you declared and still raw on
its siblings, which is easy to read as the propagation not working. Re-export
after rebuilding, then regenerate.

## Type corrections are conservative

`tools/apply_type_corrections.py` carries two kinds of entry:

- **Corrections** — the C# descriptor declares a type and the wire disagrees.
  Each has cited wire evidence.
- **ADDITIONS** — the C# descriptor is silent. These rest on unusually complete
  wire evidence (e.g. `Money` = 800 at pistol-round start across all actors). Do
  not widen the ADDITIONS list "by eye" — that undoes the reason it is allowed.
  Read the rationale block at the top of the script first.

## Commit style

Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `perf:`, `refactor:`,
`chore:`), lowercase, present tense. Keep the subject short; put the "why" in
the body.
