# Upstream and China merge validation

The tested code is merge commit
`7ae62c452c388cab4c65812adb3fd6255b222d05`, whose parents are the China PR #1
head `4412b80611b101c06e3a479c12c713ffa997c81b` and upstream v0.4.0
`b9ba3f70735c7219fef41ba61a80626a4bb88757`. This is a complete history merge,
not a cherry-pick of selected upstream fixes. The subsequent validation
documentation commit does not change the parser or verification tools.

The tested release binary's SHA-256 is
`fd56aa69ef1e764f46e6299d559529c6602a98ba79dbd5ab77667a7c19a4eca7`.
The [machine-readable report](china-sync-validation.json) records the input
hashes, parser-source digest, verifier digest, binary digest, every failure
counter and positive decoded-value counts. No replay or player identity is
included.

## Replay validation

| Branch | Replays | Strict passes | Checkpoint decoding |
| --- | ---: | ---: | --- |
| release-12.10 | 1 public | 1 | observed |
| release-12.11 | 1 public | 1 | observed |
| release-13.00 | 1 public | 1 | observed |
| release-china-13.02 | 4 private | 4 | observed |
| release-china-13.05 | 5 private | 5 | observed |
| release-china-13.08 | 2 private | 2 | observed |
| release-china-13.09 | 5 private | 5 | observed |

All 19 unique inputs passed normal branch dispatch, full checkpoint export,
the upstream strict counters, GUID reconciliation and independent raw/typed
value checks. All input hashes remained unchanged. The three public fixtures
also match the unchanged upstream corpus baselines. This is a new 19-replay
measurement; the larger historical upstream audit is not claimed as rerun.

The release binary was built with Rust 1.86.0. Commands, with corpus and work
directories supplied by the operator:

```bash
cargo +1.86.0 build --release -p vrfkit --locked
python -W error tools/verify_build_corpus.py --exe <vrfkit.exe> --corpus <china-corpus> --corpus <public-corpus> --work-dir <new-work-dir> --output <report.json> --jobs 2
python -W error tools/check_corpus_baseline.py --baseline tools/baselines/build_1210.json --corpus <12.10-corpus> --exe <vrfkit.exe> --require-input
```

The last command was also run for `build_1211.json` and `build_1300.json`.
Public inputs are the three SHA-256-pinned fixtures in `.github/workflows/ci.yml`.
The Windows release packaging helper also created and verified a local ZIP,
including its extracted-executable smoke check.

## Before and after semantic comparison

The existing pre-sync China binary (SHA-256
`b37e0ee04a9735b325ff5b03df2ad086c8dadc1f4111232b73c016c3c7c5717d`)
and the new release binary each exported the same 16 private inputs with
checkpoints. The [aggregate comparison](china-sync-semantic-comparison.json)
records the sample hashes and results.

For each export, fields are sorted by time and the last observed
`AggregateKills` and `AggregateDeaths` are compared for every player actor.
All final `RoundResults[index]` fields, including nested team members, are
compared by index. Every one of those values is unchanged across the merge.
Independently encoded `characterDeath` events agree with the statistics,
accounting for self-kills and players owning multiple characters.

| China build | Round results | Death events | Players with aggregate statistics |
| --- | ---: | ---: | ---: |
| 13.02, four replays | 93 | 710 | 39 |
| 13.05, five replays | 100 | 763 | 50 |
| 13.08, two replays | 41 | 237 | 20 |
| 13.09, five replays | 76 | 587 | 50 |

One 13.02 replay has ten players but only nine with aggregate statistics;
that measured absence is unchanged, not silently filled with zero. The 13.08
surrender replay has 19 round results, 12 start events and eight awarded
surrender rounds. All 152 team rows across the 76 China 13.09 rounds agree
with the winning team and its role; `WinningTeamMode` is raw value 1 throughout.

Full export bytes and total content-block counts are not claimed identical
to the old BakaFT parser: upstream has changed framing/accounting and added
diagnostic and checkpoint tables. The old counters are not substituted for
the new strict measurement.

## Code and tools checks

On Windows, Rust 1.86.0 and Python 3.12:

- fmt, all-target/all-feature clippy with warnings denied, and all-feature check;
- 746 Rust tests and 1,084 Python tests, measured by the full documentation guard;
- 27 metadata-derived core/single-feature checks;
- core-only CLI and container runtime tests, and strict rustdoc;
- Rust-to-PyArrow Parquet interoperability;
- ASCII, overlay generation, checksum generation, scoped-type generation and baseline-schema guards;
- negative mutation checks for the 13.09 transform constant and the probe exit code, followed by restored passing tests.

The actual release binary was also run on a real 13.09 replay with its own
transform forced: the oracle still scored 100%, but the command returned 3
and printed PROBE. A forced measurement cannot be mistaken for normal support.

CI now covers PRs targeting `china-13.05-support`, as well as `main`, and
pushes to the integration branches. Local results above do not assert that
every remote OS/Python matrix job has already run.

## Limits

- No local 13.04 replay was available. Its existing transform, independent
  boundary vectors and recovery evidence pass; no new full-match claim is made.
- China structured-array child routes remain unadmitted without their own
  route-specific evidence. This merge does not import application-specific
  route admissions or host commands.
- Unknown RPC payloads remain preserved, not semantically decoded. Successful
  checks do not establish complete ability semantics or rendering fidelity.
- The upstream historical audit fixture and all three public baselines are
  unchanged. This contribution does not widen their claimed coverage.
