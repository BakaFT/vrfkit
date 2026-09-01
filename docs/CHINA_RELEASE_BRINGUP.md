# China Release Transform Bring-up

Status: live procedure. This is the repository's reproducible method for
recovering a Tencent-published `release-china-*` payload transform when no
usable implementation exists.

This document is about **China release recovery**, not the global release port.
The integration steps shared by every build remain in
[`CONTRIBUTING.md`](../CONTRIBUTING.md#bringing-up-a-new-game-build). This file
covers the harder question that guide previously left open: how to recover the
per-build word functions and PRNG constants from replay evidence.

## 1. Scope and claim

A new build is cheap to *integrate* after its transform is known: one
`SeededTransform` implementation, registry entries, vectors and documentation.
Recovering that implementation can be the expensive part. Do not confuse those
two costs.

The method here applies while these measured invariants still hold:

- the branch is `++Ares-Core+release-china-*`;
- network version and engine net protocol remain 19 and 32;
- content-block headers and declared bit lengths remain plaintext;
- `seed_for`, the PRNG multiplier, `initial_prng_b`, PRNG advance and
  64 -> 32 -> 8 -> tail staging remain unchanged;
- each word function is a short sequence drawn mostly from the historical
  primitive vocabulary;
- the 32-bit and byte lanes continue to correspond to the 64-bit lane.

If a protocol number or one of those structural invariants changes, stop. That
is a format investigation, not a transform rotation, and this procedure must
not be used to force a plausible parse.

## 2. Provenance matters

The two existing China builds do not have the same provenance:

- China 13.02's 64-bit lane and PRNG constants came from the public port of a
  third-party decompilation. This repository derived only its missing 32-bit
  and byte lanes.
- China 13.04 had no usable external implementation. Its three word functions
  and PRNG constants were recovered from replay measurements in this
  repository.

See [`NOTICE.md`](../NOTICE.md#china-1304-replay-recovery) and the doc comments
on [`V13_02China`](../crates/vrf-transform/src/versions/v13_02_china.rs) and
[`V13_04China`](../crates/vrf-transform/src/versions/v13_04_china.rs).

"Original to this repository" does not mean "derived from no prior knowledge."
China 13.04 reused the already measured transform skeleton, historical
primitive vocabulary, Unreal RepLayout grammar and a supported China 13.02
replay as a known-plaintext reference. Those are constraints, not a 13.04
answer.

## 3. Evidence hierarchy

Treat every candidate as a hypothesis. Evidence has different strengths:

| Evidence | What it proves | What it does not prove |
|---|---|---|
| One plaintext/ciphertext word | A sequence fits one state | The sequence is unique or works on a replay |
| Two words with different seeds | Accidental short sequences are strongly reduced | PRNG constants or later states are correct |
| Lane vectors at 32 and 8 bits | The short-lane spelling matches observed bytes | Later PRNG states are correct |
| Independent-language vectors | Two implementations agree byte-for-byte | The shared recovered hypothesis is true |
| Whole-replay grammar | The transform produces structurally valid streams broadly | Typed values are semantically correct |
| Event vs replicated-value cross-check | Two independently encoded game views agree | Every unknown raw payload is understood |
| A second replay | The result is not peculiar to one match | Every possible class or mode is covered |

The Python oracle in [`tools/china_transform_oracle.py`](../tools/china_transform_oracle.py)
is independent **implementation evidence**, not an independent source for the
algorithm. Its own module comment states this limitation. A vector generated
from the recovered algorithm cannot, by itself, prove that algorithm correct.

## 4. Reproducible artifacts

The recovery helper and the committed China 13.04 evidence are:

```text
tools/china_release/recover.py
tools/china_release/evidence/china_13_04.json
```

The evidence file contains no replay and no account identifier. It records:

- the preserved replay's label, size and SHA-256;
- exact little-endian plaintext/ciphertext word pairs;
- the state/seed attached to each pair;
- seven 32-bit and seven byte-lane observations;
- candidate first PRNG states from the Ace payload;
- seven independently observed `state1` low bytes;
- the complete `mixed_a` scan result and expected final constants.

Run the fast, committed-evidence reproduction from the repository root:

```bash
python -W error tools/china_release/recover.py
```

Run phases separately while investigating:

```bash
python -W error tools/china_release/recover.py --phase word64
python -W error tools/china_release/recover.py --phase short-lanes
python -W error tools/china_release/recover.py --phase prng
```

The default PRNG phase uses the committed result of the full `u32` scan. To
repeat that scan rather than trust the recorded intermediates:

```bash
python -W error tools/china_release/recover.py \
  --phase prng --rescan-mixed-a --scan-bits 32
```

The rescan uses NumPy from `requirements.txt`, scans in bounded chunks and
prints progress. `--scan-bits N` exists only for tool development. A result
from less than 32 bits is not evidence for a release transform.

The helper deliberately reads the repository's generated `SBOX_64` rather than
a game executable. China 13.04 ultimately does not use an S-box, but the search
vocabulary includes it and the China 13.02 calibration does use it. No private
binary is needed to reproduce the committed search.

## 5. Preserve the input first

Game-owned demo directories rotate. Before treating a replay as evidence:

1. Copy it to a private, non-game-owned corpus directory.
2. Record byte size and SHA-256.
3. Keep the game installation read-only.
4. Do not commit the replay or identifiers derived from player accounts.
5. Record mode and any visible semantic anchors, such as a known Ace or final
   score, without depending on display names.

For China 13.04 the preserved replay evidence is:

```text
label:   4bf66d93
size:    21,190,421 bytes
SHA-256: 661f1e4689c06c992915cb87236eb822329d0d62b5b55bc0992eb84a499fc1d9
branch:  ++Ares-Core+release-china-13.04
```

Nothing in the repository resolves that label to a personal filesystem path.

## 6. Establish the failure baseline

Inspect the container before modifying transform code:

```bash
vrfkit inspect new.vrf --redact-identifiers
```

Confirm the exact branch and protocol values. Then force every plausible prior
transform with `validate --transform`. A forced run always exits 3; read the
pass rate and counters.

China 13.04 measured between 0.72% and 0.90% with all seven transforms known at
the time. Global 13.04 scored 0.733481%; China 13.02 scored 0.904416%. That is
random-error scale and rejects both "regional branch reuses global" and
"regional routine did not rotate".

Record rejected candidates. Repeating a failed family later wastes time and
makes a lucky near-match look novel.

## 7. Construct exact known plaintext

Grammar scoring is useful for direction, but exact plaintext is the leverage
that makes program search decisive.

### 7.1 Choose a deterministic small block

Good anchors have all of these properties:

- a replay-declared class and field layout;
- deterministic initial values;
- a length that isolates one staging lane;
- at least two actor GUIDs or block lengths, producing different seeds;
- a supported older replay carrying the same semantic object, when available.

Ceremony actors met those conditions in both China 13.02 and China 13.04.
`DefaultCeremony_C` declared handles 3, 12 and 14. A supported China 13.02
export established their initial payloads as 3, 3 and 1 bits with values 1, 3
and true.

### 7.2 Rebuild the framing, not a byte guess

RepLayout is:

```text
checksum_bit
repeat {
    IntPacked(handle + 1)       # zero terminates the stream
    IntPacked(payload_bit_count)
    payload bits
}
```

Encoding the measured handles, lengths and values produced the exact 64-bit
plaintext:

```text
10 0c a2 61 30 0f 81 00
```

It ends with the zero-handle terminator exactly at bit 64. This matters: a
"plausible prefix" is not an exact vector.

The two China 13.04 vectors committed in the evidence fixture are:

| Anchor | State | Cipher, little endian | Plain, little endian |
|---|---:|---|---|
| DefaultCeremony, actor 28, 64 bits | 92 | `f0 f4 00 81 30 68 8a 45` | `10 0c a2 61 30 0f 81 00` |
| AceCeremony, actor 30, first word of 96 bits | 126 | `f0 74 04 81 d0 df 9d 45` | `10 0c a2 61 30 0f 81 20` |

The second plaintext ends immediately after handle 15. Its unknown payload
length and player value start in the next word, so they cannot contaminate this
64-bit constraint.

## 8. Recover `word64`

### 8.1 Calibrate the search implementation

Before searching an unknown build, require the same implementation to recover a
known build. The fixture includes a China 13.02 ceremony vector and requires the
search to find:

```text
ROL7 -> ROR8 -> SBOX -> SWAP -> REV -> ADD1
```

That calibration catches wrong endianness, the unusual 64-bit reverse variant,
S-box direction, rotate semantics and inverse operations. A search that cannot
recover the known transform has no standing to propose a new one.

### 8.2 Search a constrained vocabulary

The helper's 52 operations are the historical reversible primitives:

```text
NOT, SWAP, REV, SBOX
ROL(k), ROR(k), ADD(k), SUB(k), XOR(k), XORNOT(k), k=1..8
```

It uses meet-in-the-middle: evaluate half-sequences forward from ciphertext and
half-sequences backward from plaintext, then join on the intermediate word.
Only representative prefixes are retained when algebraically equivalent paths
converge; this bounds memory and is sufficient to recover a candidate. It is
not a count of every possible textual spelling.

One China 13.04 vector admitted accidental shorter spellings. Applying the
second state removed all lengths below six and left representative forms that
reduce to one semantic transform:

```text
REV -> XOR6 -> ADD4 -> ADD3 -> ADD2 -> XOR1
```

The ADD operations commute. The apparent alternative using `XORNOT` and `SUB`
is universally equivalent because `~x - s == ~(x + s)` and the two complemented
XORs cancel the representation change.

### 8.3 Broad brute force is a rejection tool

Before exact plaintext and MITM were available, the investigation enumerated
203,212,800 assignments of the global 13.04 operation family and found zero
matches. Smaller China/global 13.02 permutation families also found zero.

That work was real brute force, but it did not recover the answer. Its value was
negative evidence: the new function was not a simple permutation of any one
neighbour's complete template. Do not repeat those searches for 13.04.

## 9. Recover the short lanes

Do not search `word32` and `byte` from the full vocabulary independently. Across
all measured builds, one build's three lanes preserve operation order and the
same exponent set:

| 64-bit expression | 32-bit expression | Byte expression |
|---|---|---|
| `state.rotate_right(k)` | `state.rotate_left(k)` | `state * 11^k` |
| word modulus 63 | word modulus 31 | rotate modulus 7 |

China 13.04 had seven 47-bit ceremony blocks whose first 32 bits were known and
seven 9-bit ceremony blocks whose first plaintext byte was the zero terminator.
At the first lane, `state == seed`; unknown PRNG constants therefore do not
participate.

Keep the recovered operation order and test explicit asymmetries. For 13.04 the
only variable was whether the first and last XOR operands were complemented.
Of the four combinations, only "both complemented" matched all fourteen
observations:

```text
word32:
    REV32
    XOR !state.rol(6)
    ADD  state.rol(4)
    ADD  state.rol(3)
    ADD  state.rol(2)
    XOR !state.rol(1)

byte:
    REV8
    XOR !(state * 11^6)
    ADD  (state * 11^4)
    ADD  (state * 11^3)
    ADD  (state * 11^2)
    XOR !(state * 11^1)
```

The committed recovery helper reruns all four combinations. It fails unless
exactly one passes both lane sets.

## 10. Recover the PRNG constants

A correct first word does not determine the two per-build PRNG constants. It
uses the raw seed as state; the constants only affect state after the first
advance.

This is why the generic pass-rate ladder in `CONTRIBUTING.md` is conditional.
With correct PRNG constants and only short lanes missing, a correct `word64` is
near 99.6%. During source-free China 13.04 recovery, correct `word64` plus wrong
constants reached only 56.386608%, although 222,692 of 222,757 first-word grammar
prefixes passed. The prefix measurement, not total pass rate alone, isolated the
correct first-word function.

### 10.1 Collect low-byte observations

The fifth plaintext byte of each 47-bit ceremony block is fixed. Once the byte
lane is known, it determines the low byte of `state1`. Seven seeds yielded:

```text
seed:        51  49  429 447 445 443 441
state1 low:  92  f0  cf  0c  cf  e6  44
```

Low bytes alone are insufficient. A Z3 model satisfying all seven produced
`SEED_ADDEND=0x6a716262`, add-offset `0x32`; the whole replay rejected it at
59.505829%. Keep this as the canonical warning against accepting solver
satisfiability as transform evidence.

### 10.2 Obtain one full-state relation

The Ace ceremony's second word contains a fixed payload-length byte, a
PlayerState ObjectNetGuid and a terminator. Event chunks are independent of the
content transform. Parsing `characterDeath` events established that character
684 completed five kills immediately before the Ace event.

The ten live PlayerState GUIDs reduced the unknown payload to ten semantic
possibilities. Inverting the recovered `word32` over them yielded eleven exact
`state1` candidates. The fixture commits those states without any account name.

Do not guess a GUID relation from numerical proximity. It must come from Event,
actor-open or replay-declared relation evidence.

### 10.3 Split the multiplication from the xor-shift

For anchor seed 126:

```text
state1 = high32((mixed_a * M) + (mixed_b(seed) * M))
M      = 0x2545f4914f6cdd1d
```

A direct bit-vector solve over constants was slow. The successful route split
the problem:

1. Scan every `mixed_a: u32` once and retain values whose high product word is
   one of the eleven target states.
2. Invert the triangular xor-shift
   `g(x) = x ^ (x >> 12) ^ (x >> 27)` exactly.
3. Enumerate only the 128 possible high seven bits hidden by the offset term.
4. Reconstruct `SEED_ADDEND` and the offset residue.
5. Filter with all seven independently observed low-byte pairs.

The full `u32` scan produced twelve `mixed_a` inverses. The remaining algebra
produced one constant family:

```text
SEED_ADDEND              0xe92064a1
subtract INIT_A_OFFSET   0x5f
equivalent add offset    0x21
TAIL_XOR                 0xa1
```

The add and subtract offset spellings are wire-equivalent because the offset
term multiplies by `0x02000000`; only the offset modulo 128 is observable. Use
the canonical subtract spelling for consistency with other builds.

The scan is exhaustive only when `--scan-bits 32` is used. A smaller scan is a
tool self-check, not evidence.

## 11. Validate progressively

Instrument one hypothesis at a time and record the movement of counters:

| Candidate state | China 13.04 observation |
|---|---:|
| Any registered transform | 0.72% to 0.90% |
| Correct `word64`, wrong PRNG/short lanes | 56.386608% |
| False low-byte Z3 constants | 59.505829% |
| Recovered lanes and constants, old tail accounting | 99.968475% |
| Recovered transform, every suffix consumed or preserved | 100.000000% |

A graded improvement is evidence about which stage is right; it is not an
acceptance threshold. The false Z3 model improved the pass rate and was still
wrong.

After permanent registration, run the replay without `--transform`. A forced
probe can never establish support because it exits 3 by design and bypasses
normal branch dispatch.

## 12. Investigate every residual

China 13.04 initially stopped at 99.968475% with 90 field-stream failures. Do
not suppress a counter or declare "close enough."

All 90 failures:

- were `AresAbilitySystemComponent` RepLayout blocks;
- consumed a coherent 185-bit prefix;
- had the same fields and prefix bytes as a supported China 13.02 replay;
- matched 286 equivalent suffixes in that supported replay.

The parser understood the prefix but not the suffix after the terminator. The
correct fix was not an exemption. The exact suffix bits are now emitted as a
distinguished preservation row, counted as both `field_stream_failures` and
`rep_layout_tails_preserved`, and excluded from ordinary downstream fields.

Consequently, 100% means "every present content block was consumed or
preserved," not "every bit was semantically decoded." The nonzero tail counter
must remain visible. See the measured wording in [`USAGE.md`](USAGE.md#supported-builds).

A residual may be netted from *loss* only when all of these hold:

- the exact undecoded bit window is copied;
- byte length and final-byte padding are checked;
- a unique marker prevents it from masquerading as a field;
- the raw failure counter still increments;
- the manifest and summary publish both failure and preservation counts;
- downstream adapters explicitly exclude the marker;
- a regression comparison proves ordinary rows are unchanged.

Otherwise it remains a failed block.

## 13. Implement the permanent transform

Only after the measured hypothesis closes should it become a dedicated file.
For China 13.04 the final implementation is
[`v13_04_china.rs`](../crates/vrf-transform/src/versions/v13_04_china.rs).

Registration must use the exact branch string:

```text
++Ares-Core+release-china-13.04
```

Never alias a China branch to the global branch with the same version number.
They report the same container/protocol versions but use different transforms.

Remove all runtime environment probes, packet limits and debug counters before
final verification. Search for the tags used by the investigation and require
zero results.

## 14. Prove implementation and hypothesis separately

### 14.1 Independent implementation

Add a Python implementation written from the measured description, not copied
line-for-line from Rust. Generate vectors at all staging boundaries:

```text
0, 1, 7, 8, 31, 32, 63, 64, 65, 287, 288 bits
```

These vectors catch transcription, masking, padding and endian errors between
the Python and Rust implementations. They do not independently prove the
recovered algorithm.

### 14.2 Real replay grammar

The final release binary must dispatch from the replay's own branch and report:

- zero malformed packet or content-block framing failures;
- zero transform failures;
- zero unread ReplayData bytes;
- zero genuinely lost content blocks;
- explicit nonzero preservation counts where applicable;
- a passing process exit code.

China 13.04 walked 285,488 of 285,488 ReplayData blocks.

### 14.3 Values, not counters

Export with checkpoints and compare independent game views. The China 13.04
cross-check used Event chunks against typed replicated state:

- 54 `characterDeath` events mapped through `manifest.players`;
- one self-kill excluded from credited kills;
- 53 credited kills and 54 deaths matched all ten final scoreboards exactly;
- the first-round five-kill sequence ended at 122,503 ms;
- typed `RoundResults` produced rounds 0 through 6, one side switch and a 5-2
  final score;
- overlay, struct, array and checkpoint error counters were zero.

The reproducible filters and totals are recorded in
[`USAGE.md`](USAGE.md#supported-builds).

### 14.4 More than one replay

One replay gives strong evidence, not complete corpus coverage. Acquire a
second replay from the same branch, preferably a different mode and map. Until
then, documentation must continue to say "one preserved replay" rather than
implying a regional corpus.

## 15. Acceptance checklist

Do not mark a China release supported until every applicable item is checked:

- [ ] Replay copied out of the game directory; size and SHA-256 recorded.
- [ ] Exact branch and protocol values inspected.
- [ ] Prior transforms probed and rejected or one explicitly confirmed.
- [ ] At least two exact 64-bit vectors use different states.
- [ ] Search implementation recovers a known historical calibration vector.
- [ ] `word64` candidate is the shortest measured family or ambiguity is stated.
- [ ] 32-bit and byte lanes each match several independent observations.
- [ ] PRNG constants satisfy a full-state relation, not low bytes alone.
- [ ] Every solver/enumeration candidate is tested against the whole replay.
- [ ] Every residual failure is explained, preserved or left as a failure.
- [ ] Final validation uses normal branch dispatch and exits zero.
- [ ] Python/Rust boundary vectors agree.
- [ ] Export plus checkpoints has no decode/struct/array loss.
- [ ] At least one value-level semantic cross-check agrees.
- [ ] Temporary probes and private paths are absent from the repository.
- [ ] Full `CONTRIBUTING.md` sweep passes on Rust 1.86.
- [ ] Verification scope and replay count are documented without inflation.

## 16. Failure conditions and next moves

| Observation | Interpretation | Next move |
|---|---|---|
| Protocol 19/32 changed | Container/network format may have moved | Stop transform work; investigate framing |
| All old transforms near random scale | Per-build transform changed | Construct exact plaintext |
| No deterministic block in the replay | Insufficient known plaintext | Acquire another replay or independent source |
| Calibrated MITM finds no short sequence | Primitive vocabulary or sequence length changed | Add only primitives justified by binary/history; do not expand blindly |
| First-word prefixes pass, total remains low | `word64` likely right; PRNG constants wrong | Recover a full later state |
| Low-byte solver improves but does not close | Underconstrained false model | Add full-state relation; reject it |
| Candidate reaches almost 100% | Could be parser coverage or a subtle transform error | Classify every residual against a known build |
| Grammar passes but values disagree | Plausible wrong transform or decode schema | Reject support; investigate value evidence |
| Python vectors agree, replay fails | Both implementations share a wrong hypothesis | Trust the replay failure |

Static binary analysis remains an optional source of new primitives or direct
constants, not a prerequisite. In the 13.04 investigation the copied game image
was protected/high entropy and did not yield the transform implementation. The
successful path remained replay-driven. Never attach to or modify a running
game process merely because replay recovery is difficult.

## 17. What is now reproducible

From the committed fixture alone, another contributor can reproduce:

- the China 13.02 calibration of the MITM implementation;
- the shortest China 13.04 64-bit representative sequence;
- the unique short-lane complement choice across fourteen vectors;
- the twelve recorded `mixed_a` inverses;
- the algebraic reduction to one PRNG constant family;
- the full `mixed_a` scan by opting into `--rescan-mixed-a`.

The fixture does not reproduce extraction of those observations from a private
replay. That still requires a suitable replay, temporary measurement code or a
future structured event/known-plaintext extractor. Keep this distinction
explicit: reproducing a derivation from evidence is not the same as independently
collecting the evidence.
