# China branches on upstream v0.4.0

This integration merges the complete yakisoba0728/vrfkit v0.4.0 history
(`b9ba3f70735c7219fef41ba61a80626a4bb88757`) into the BakaFT China branch,
including the 13.08/13.09 work from PR #1. It keeps the upstream decoder,
export formats, diagnostics, tools, fixes and tests. The regional transforms
use the upstream `transforms!` registry instead of the old per-version files.
There are 26 global branches and five additional China branches; the same
numeric version in another region is never an alias.

## Registered regional transforms

| Branch suffix | Seed addend | Subtracted initial offset | Tail XOR |
| --- | --- | --- | --- |
| china-13.02 | 0x9e70cf19 | 0x67 | 0x19 |
| china-13.04 | 0xe92064a1 | 0x5f | 0xa1 |
| china-13.05 | 0xf67761c9 | 0x37 | 0xc9 |
| china-13.08 | 0x4a67f535 | 0x4b | 0x35 |
| china-13.09 | 0x350f7d3f | 0x41 | 0x3f |

All names have the exact prefix `++Ares-Core+release-`. Unknown branches
are refused. Provenance and retained MIT terms are in [NOTICE](../NOTICE.md)
and [CHINA_LICENSE.txt](../CHINA_LICENSE.txt).

The 13.04 short-lane XOR convention differs from the global convention;
the registry's `xorc` operation makes that difference explicit. The 13.08
and 13.09 transforms are recovered from replay measurements. Their algorithms
are pinned by real observed blocks, partial-bit tails and an independent
Python implementation, not by aliasing the same-numbered global version.

## Evidence and its limits

The committed recovery records are under `tools/china_release/evidence/`
for 13.04, 13.05, 13.08 and 13.09. Each contains seeds, ciphertext,
plaintext assumptions and intermediate candidates, without replay files or
player identities. The helper under `tools/china_release/` accepts an
evidence JSON path and reconstructs the word sequence, short lanes and PRNG
constants. `--rescan-mixed-a` repeats the full 32-bit scan with NumPy instead
of using the committed exhaustive-scan results.

For example, from the repository root:

```bash
python tools/china_release/recover.py tools/china_release/evidence/china_13_09.json
```

13.09's four 64-bit observations admit two inequivalent sequence families.
Ceremony 32-bit and byte observations reject one. The remaining sequence is
`NOT, SUB6, REV, ADD4, REV, SBOX`. TimedBomb relations and successor bytes
constrain the PRNG constants. Blocks not used by those constraints, including
the 7-bit ceremony tail, are checked against the previous version's plaintext.
The equality of these plaintexts across versions is a supported assumption,
not an independent game-format specification.

`tools/china_transform_oracle.py` supplies separate Python implementations
for all five branches. Its outputs pin 55 regional golden vectors at the
0/1/7/8/31/32/63/64/65/287/288-bit boundaries. The tools tests recompute all
55 and compare them to the committed Rust fixture. The existing global and
native vectors remain unchanged.

The historical upstream global audit remains in its original fixture and
scope. China measurements for this merge are recorded separately in
[CHINA_SYNC_VALIDATION.md](CHINA_SYNC_VALIDATION.md); they must not be counted
as additional replays in that historical audit. A branch with no locally
available replay can have transform vectors without a new full-match claim.

## Probe an unregistered build

BakaFT's validation-only transform override is retained on the new shared
decode pass:

```bash
vrfkit validate candidate.vrf --transform release-china-13.09
vrfkit validate candidate.vrf --transform ++Ares-Core+release-china-13.09
```

The output identifies the actual header and forced transform. Every completed
forced run exits **3**, even when using the file's own transform or when every
block passes. Read and parse errors still fail. Normal validation retains
upstream's 0/1/2 verdict codes. Neither `export` nor `diag` accepts this option.
The command never edits the replay or exports results under a guessed transform.

## Add the next regional version

1. Copy representative replays to a private corpus. Inspect the header and
   include competitive and Swiftplay samples when available. Keep the game
   installation and original files read-only.
2. Recover the word operation sequence from known plaintext. Check every
   candidate family against the short lanes before deriving PRNG constants.
   Search from the shortest sequence; a plausible first word alone is not
   sufficient evidence.
3. Constrain the PRNG with independent seeds and verify unused whole blocks,
   including trailing bits. Commit a reproducible, non-identifying evidence
   record and independently implement the algorithm in the Python oracle.
4. Add a `transforms!` row in `crates/vrf-transform/src/lib.rs`, regional
   vectors and observed-block tests. Extend the pinned route registry with
   no routes initially. Transform support is not proof of structured-array
   layouts; admission requires separate measurements.
5. Run `validate`, `export --checkpoints` and independent semantic comparisons
   on the affected replays. Compare per-player statistics to death events and
   winners to per-team results. Check the counters, positive decoded rows,
   source hashes and previously supported branches, then run the full sweep
   in [CONTRIBUTING](../CONTRIBUTING.md).

The upstream 13.09 round decoder handles `WinningTeamMode` as a raw byte and
`TeamResults` by declared member names. There is no regional skip arm.
The measured 13.09 replays have mode 1; its enum name is not asserted.
Preserved unknown RPC payloads are not decoded semantics. A zero-loss report
does not establish complete ability or rendering fidelity.
