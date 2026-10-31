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

The three existing China builds do not have the same provenance:

- China 13.02's 64-bit lane and PRNG constants came from the public port of a
  third-party decompilation. This repository derived only its missing 32-bit
  and byte lanes.
- China 13.04 and China 13.05 had no usable external implementation. Their
  three word functions and PRNG constants were recovered independently from
  replay measurements in this repository.

See [`NOTICE.md`](../NOTICE.md#china-1304-replay-recovery),
[`NOTICE.md`](../NOTICE.md#china-1305-replay-recovery), and the doc comments on
[`V13_02China`](../crates/vrf-transform/src/versions/v13_02_china.rs),
[`V13_04China`](../crates/vrf-transform/src/versions/v13_04_china.rs), and
[`V13_05China`](../crates/vrf-transform/src/versions/v13_05_china.rs).

"Original to this repository" does not mean "derived from no prior knowledge."
China 13.04 and 13.05 reused the already measured transform skeleton,
historical primitive vocabulary, Unreal RepLayout grammar and supported older
replays as known-plaintext references. Those are constraints, not the answer
for either new branch.

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

The recovery helper and the replay-recovered evidence fixtures are:

```text
tools/china_release/recover.py
tools/china_release/evidence/china_13_04.json
tools/china_release/evidence/china_13_05.json
tools/china_release/evidence/china_13_08.json
tools/china_release/evidence/china_13_09.json
```

No evidence file contains a replay or account identifier. Each records the
preserved replay's label, size and SHA-256; exact little-endian plaintext and
ciphertext observations with their state/seed; a historical China 13.02
calibration; full-scan intermediates; and the expected final constants.
China 13.04 additionally records two target word64 states, fourteen short-lane
observations, Ace-derived PlayerState candidates and seven `state1` low bytes.
China 13.05 records four target word64 states, fourteen short-lane observations,
three TimedBomb-derived full-state candidates, and five independent word32 plus
seven byte constraints on the successor state. China 13.08 records four word64
states, fourteen short-lane observations, one TimedBomb full-state candidate and
twelve word32 plus seven byte successor constraints. China 13.09 records the
same four word64 classes, fourteen short-lane observations, 32 TimedBomb
full-state candidates and three word32 plus seven byte successor constraints.

Run the fast, committed-evidence reproductions from the repository root. The
13.04 fixture remains the default for compatibility:

```bash
python -W error tools/china_release/recover.py
python -W error tools/china_release/recover.py \
  tools/china_release/evidence/china_13_05.json
```

The 13.08 and 13.09 fixtures replay the same way:

```bash
python -W error tools/china_release/recover.py   tools/china_release/evidence/china_13_08.json
python -W error tools/china_release/recover.py   tools/china_release/evidence/china_13_09.json
```

Run phases separately while investigating; insert an evidence path after the
script name to select another build:

```bash
python -W error tools/china_release/recover.py --phase word64
python -W error tools/china_release/recover.py --phase short-lanes
python -W error tools/china_release/recover.py --phase prng
```

The PRNG phase normally verifies the committed result of the full `u32` scan.
To repeat the China 13.05 scan rather than trust those intermediates:

```bash
python -W error tools/china_release/recover.py \
  tools/china_release/evidence/china_13_05.json \
  --phase prng --rescan-mixed-a --scan-bits 32
```

The rescan uses NumPy from `requirements.txt`, scans in bounded chunks and
prints progress. `--scan-bits N` exists only for tool development. A result
from less than 32 bits is not evidence for a release transform. The final
13.05 acceptance run enumerated all 4,294,967,296 values, reproduced five
inverses across three candidate states and returned the one committed constant
family. The 13.09 rescan enumerated all 4,294,967,296 values in 108.6 s on one machine and
reproduced 34 inverses across 32 candidate states.

The helper deliberately reads the repository's generated S-boxes rather than a
game executable. China 13.04 and 13.05 do not use an S-box; 13.08 and 13.09 do,
and the China 13.02 calibration does. No private binary is needed to reproduce
any committed search.

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

For China 13.05 the separately preserved evidence is:

```text
label:   c6a882f3
size:    19,764,252 bytes
SHA-256: 4a54d799e278a2bc123ac2fda558a8ee93dafc504d423f254123b1d4c9f1cdf9
branch:  ++Ares-Core+release-china-13.05
```

Both files were copied into private scratch space before analysis; the game
installation remained read-only. Nothing in the repository resolves either
label to a personal filesystem path.

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

China 13.05 was probed against all eight transforms then registered. They passed
between 27.931071% and 32.215478% under the current consumed-or-preserved block
metric, with global 13.04 lowest and global 12.11 highest. None approached the
new transform's 276,631/276,631 result. Record the exact metric being compared:
preservation-aware pass rates are not directly comparable to older strict
framing percentages.

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

Ceremony actors met those conditions in all three China builds. Never copy a
handle number forward without checking the target replay: China 13.05 itself
redeclared handles 3, 12 and 14 before they were used. Supported older exports
established their initial payloads as 3, 3 and 1 bits with values 1, 3 and true.

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

China 13.05 used four states instead of relying on a two-vector collision:

| Anchor | State | Cipher, little endian | Plain, little endian |
|---|---:|---|---|
| DefaultCeremony exact 64-bit block | 528 | `16 0d a2 51 30 0f 81 00` | `10 0c a2 61 30 0f 81 00` |
| BaseReplayPlayerState first word | 92 | `d0 30 18 c3 05 c1 80 20` | `10 0c 82 01 41 a0 61 30` |
| AresWorldSettings first word | 2,276 | `08 20 00 9e 0f a2 61 30` | `10 0c a2 61 30 10 20 00` |
| BaseReplayController first word | 285 | `e0 30 0f eb 03 9e 0c a4` | `10 0c a4 61 30 0f 08 04` |

The three non-ceremony plaintext words repeat byte-for-byte in the same
actor-open classes across three supported China 13.02/13.04 replays. The target
replay supplied the ciphertext, declared bit length and actor NetGUID used to
recompute every state.

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

It uses meet-in-the-middle: evaluate half-sequences forward from every
ciphertext and backward from every plaintext, then join on the tuple of all
intermediate words. The multi-state key matters. Prefixes can collide at one
state and diverge at another; the old single-vector key discarded the actual
China 13.05 prefix. A representative is merged only when its joint signature
matches at every evidence state. This bounds memory without making one state a
lossy deduplication key; it is still not a count of every possible textual
spelling.

One China 13.04 vector admitted accidental shorter spellings. Applying the
second state removed all lengths below six and left representative forms that
reduce to one semantic transform:

```text
REV -> XOR6 -> ADD4 -> ADD3 -> ADD2 -> XOR1
```

The ADD operations commute. The apparent alternative using `XORNOT` and `SUB`
is universally equivalent because `~x - s == ~(x + s)` and the two complemented
XORs cancel the representation change.

For China 13.05 all four states rejected every sequence shorter than six. At
length six the joint search retained 12 representatives, all differing only in
the order of four commuting rotations. The committed canonical spelling is:

```text
ADD8 -> ROL4 -> ROL6 -> ROR2 -> ROR7 -> SUB1
```

The ambiguity is explicit: the evidence fixes the semantic transform, not one
unique source-code order for operations that commute on every input.

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

China 13.05 projects the same six operations directly: `rotate_right(k)` state
operands become `rotate_left(k)` in word32 and `state * 11^k` in byte. Seven
independent 32-bit ceremony words and seven bytes all matched. Because this
sequence has no XOR primitive, its complement-toggle space contains exactly the
empty tuple; the helper still evaluates both short lanes through the same
general 52-primitive interpreter rather than a 13.05-specific formula.

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

China 13.05 contained no Ace event, so it used a different full-state anchor.
The initial 127-bit `/Game/GameModes/Bomb/TimedBomb` plaintext was byte-for-byte
identical in 17 instances across three already supported replays:

```text
10 0c a2 61 30 10 40 00 00 00 00 00 40 23 20 00
```

Five independently seeded target instances had the same shape. Inverting the
known second word32, whose plaintext is zero, produced exactly three possible
`state1` values for anchor seed 4,909:

```text
0x27f93a29  0x43744ab6  0x6ce1103c
```

This is a full 32-bit relation. The other four TimedBomb words and seven
ceremony successor bytes remained independent filters; none was used to invent
the three anchor candidates.

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

For China 13.05, scanning all `u32` mixed-A values against all three TimedBomb
states yielded five inverses: two, one and two per state respectively. Applying
the other four TimedBomb word32 constraints and all seven ceremony byte
constraints left one result:

```text
state1 at seed 4909       0x6ce1103c
SEED_ADDEND               0xf67761c9
subtract INIT_A_OFFSET    0x37
equivalent add offset     0x49
TAIL_XOR                  0xc9
```

The checked `--rescan-mixed-a --scan-bits 32` run enumerated the full
4,294,967,296-value domain and reproduced those five committed inverses before
selecting this family.

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

China 13.05 used a prefix census instead of claiming unmeasured intermediate
pass rates:

| Candidate state | China 13.05 observation |
|---|---:|
| Each of eight prior transforms | 27.931071% to 32.215478% consumed or preserved |
| Recovered `word64` | 61,440/61,440 eligible RepLayout first words valid |
| Prefix classification | 61,363 ordinary records + 77 valid early-terminator tails + 0 malformed |
| Recovered full transform | 276,631/276,631 content blocks consumed or preserved |

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

China 13.05 retained 131 ReplayData tails (131,001 bits), 1,416 unresolved RPC
payloads and 20 checkpoint tails (4,742 bits); exact byte lengths and zero high
padding were checked for every row. Its 54 ReplayData partial-bunch errors and
293 checkpoint partial-bunch errors all carried zero captured fragments and
left zero unfinished partials, the signature of independently entered streams
that start after those fragment sequences; supported 13.02 and 13.04 replays
show the same condition. They are surfaced, not relabelled as successful
reassembly.

One value-level audit also caught 3,064 reported RPC suffix bits from four
799-bit `AresAbilitySystemComponent:ActiveGameplayEffects` calls. The same
shape occurred in 20 calls across two supported China 13.02 replays, ruling out
a China 13.05 transform residual. The generic FunctionParameters walker had
fabricated one zero-bit `_h0` child before stopping, even though the complete
parent raw payload was preserved. The observed payload does not follow the
generic FunctionParameters grammar. A regression now routes that exact
class/function pair to one whole raw row: all 24 parents remain, no fabricated
children remain, and both ReplayData and checkpoint RPC suffix counters are
zero.

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
The replay-recovered implementations are
[`v13_04_china.rs`](../crates/vrf-transform/src/versions/v13_04_china.rs),
[`v13_05_china.rs`](../crates/vrf-transform/src/versions/v13_05_china.rs),
[`v13_08_china.rs`](../crates/vrf-transform/src/versions/v13_08_china.rs) and
[`v13_09_china.rs`](../crates/vrf-transform/src/versions/v13_09_china.rs).

Registration must use the exact branch string read from the target replay. For
13.05 that is:

```text
++Ares-Core+release-china-13.05
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

China 13.04 walked 285,488 of 285,488 ReplayData blocks. China 13.05 walked
276,631 of 276,631, then decoded 8/8 checkpoints and 6,949 checkpoint content
blocks without transform, framing, field or RPC loss. Both used normal branch
dispatch.

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

The China 13.05 cross-check used the same independent views:

- 59 `characterDeath` events mapped through `manifest.players`;
- one self-kill excluded from credited kills;
- 58 credited kills and 59 deaths matched all ten final scoreboards exactly;
- one missing assist remained visibly absent rather than becoming zero;
- `roundStarted` produced rounds 0 through 7 and `switchTeams` occurred after
  round 3;
- the final typed score was Red 5 / Blue 3;
- overlay, struct, array, movement, RPC-suffix and checkpoint errors were zero.

The reproducible filters and totals are recorded in
[`USAGE.md`](USAGE.md#supported-builds).

### 14.4 More than one replay

One replay gives strong evidence, not complete corpus coverage. Acquire a
second replay from the same branch, preferably a different mode and map. Until
then, documentation must continue to say "one preserved replay" rather than
implying a regional corpus.

## 15. Acceptance checklist

The checked state below is the China 13.05 acceptance record. Reset the boxes
when using this section as the gate for a later branch.

- [x] Replay copied out of the game directory; size and SHA-256 recorded.
- [x] Exact branch and protocol values inspected.
- [x] Prior transforms probed and rejected or one explicitly confirmed.
- [x] At least two exact 64-bit vectors use different states.
- [x] Search implementation recovers a known historical calibration vector.
- [x] `word64` candidate is the shortest measured family or ambiguity is stated.
- [x] 32-bit and byte lanes each match several independent observations.
- [x] PRNG constants satisfy a full-state relation, not low bytes alone.
- [x] Every solver/enumeration candidate is tested against the whole replay.
- [x] Every residual failure is explained, preserved or left as a failure.
- [x] Final validation uses normal branch dispatch and exits zero.
- [x] Python/Rust boundary vectors agree.
- [x] Export plus checkpoints has no decode/struct/array loss.
- [x] At least one value-level semantic cross-check agrees.
- [x] Temporary probes and private paths are absent from the repository.
- [x] Full `CONTRIBUTING.md` sweep passes on Rust 1.86.
- [x] Verification scope and replay count are documented without inflation.

The 12 word64 spellings count as one semantic candidate because their middle
rotations commute for every input. Known-plaintext successor-state constraints
eliminated the incomplete PRNG possibilities before one full transform
remained; that transform was then tested against every replay block.

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
| Several families pass the word64 vectors at the shortest length | The four first words under-constrain the order | Score every family on the short lanes before choosing; 13.09 left two |
| Transform passes, a struct blob fails on a new member | Game-side schema change, not a transform residual | Surface the error; decode or skip the member explicitly by declared name |

Static binary analysis remains an optional source of new primitives or direct
constants, not a prerequisite. In the 13.04 investigation the copied game image
was protected/high entropy and did not yield the transform implementation. An
independent 13.05 lane reached the same evidence limit: the copied executable's
on-disk code was protected and the relevant Base DLL ordinal entered a
virtualized section, so there was no trustworthy code cross-reference or
constant extraction. That lane stopped instead of inferring an algorithm from
missing data. The successful path remained replay-driven. Never attach to or
modify a running game process merely because replay recovery is difficult.

## 17. What is now reproducible

From the committed replay-recovery fixtures, another contributor can
reproduce:

- the China 13.02 calibration of the MITM implementation;
- the shortest China 13.04 sequence and its equivalent representatives;
- the China 13.04 unique short-lane complement choice across fourteen vectors;
- the China 13.04 twelve recorded `mixed_a` inverses and final constants;
- the China 13.05 shortest six-operation family jointly across four states;
- its 12 retained representatives, differing only by commuting rotate order;
- its seven word32 and seven byte observations with no complement toggle;
- its three TimedBomb state candidates, five recorded `mixed_a` inverses and
  unique final constants after four more word32 plus seven byte constraints;
- the China 13.08 six-operation sequence, its single short-lane complement
  toggle and its unique constants;
- the China 13.09 sequence, the second length-six family the short lanes
  reject, and its unique constants from 32 TimedBomb state candidates;
- any full `mixed_a` scan by opting into `--rescan-mixed-a`.

The fixtures do not reproduce extraction of those observations from private
replays. That still requires a suitable replay, temporary measurement code or a
future structured known-plaintext extractor. Keep this distinction explicit:
reproducing a derivation from evidence is not the same as independently
collecting the evidence.
