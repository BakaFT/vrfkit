"""Extract payload-transform golden vectors from the upstream C# test suite
and the independent regional Python oracles, then emit a Rust data module.

The upstream fixture supplies 66 vectors for six global builds; the Python
oracles supply 33 more for release-china-13.02, release-china-13.04 and
release-china-13.05. Together these 99 vectors cover all nine transforms at
every staging boundary.

Usage:
    python tools/extract_golden.py <ValorantSeededTransformTests.cs> <out.rs>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

if __package__:
    from .atomic_io import atomic_write_text
    from .china_transform_oracle import (
        BRANCH as CHINA_1302_BRANCH,
        CHINA_1304_BRANCH,
        CHINA_1305_BRANCH,
        China1304Transform,
        China1305Transform,
        ChinaTransform,
    )
else:  # direct script execution
    from atomic_io import atomic_write_text
    from china_transform_oracle import (
        BRANCH as CHINA_1302_BRANCH,
        CHINA_1304_BRANCH,
        CHINA_1305_BRANCH,
        China1304Transform,
        China1305Transform,
        ChinaTransform,
    )

# Builds whose vectors are lifted from the C# fixture -- an implementation
# written by someone else, which is what makes them an independent check.
EXPECTED_BRANCHES = (
    "++Ares-Core+release-12.10",
    "++Ares-Core+release-12.11",
    "++Ares-Core+release-13.00",
    "++Ares-Core+release-13.01",
    "++Ares-Core+release-13.02",
    "++Ares-Core+release-13.04",
)

# Historical China fixtures carried release-china-13.02 vectors from an
# implementation whose 32-bit and byte lanes zeroed their input. Current global
# fixtures omit all regional branches. If regional rows are encountered they
# are discarded; the three China builds below always come from the independent
# Python oracle.
ORACLE_TRANSFORMS = (
    (CHINA_1302_BRANCH, ChinaTransform),
    (CHINA_1304_BRANCH, China1304Transform),
    (CHINA_1305_BRANCH, China1305Transform),
)
ORACLE_BRANCHES = tuple(branch for branch, _ in ORACLE_TRANSFORMS)
SUPERSEDED_FIXTURE_BRANCHES = ORACLE_BRANCHES

SBOX_RS = Path(__file__).resolve().parent.parent / "crates/vrf-transform/src/sbox.rs"
EXPECTED_BOUNDARIES = (0, 1, 7, 8, 31, 32, 63, 64, 65, 287, 288)
EXPECTED_CASE_COUNT = len(EXPECTED_BRANCHES) * len(EXPECTED_BOUNDARIES)

# Vectors are written either with an inline hex literal or with a reference to a
# `private const string` declared at the top of the fixture.
CONST_RE = re.compile(r'private\s+const\s+string\s+(\w+)\s*=\s*"([0-9A-Fa-f]*)"\s*;')
INT_CONST_RE = re.compile(r"private\s+const\s+(?:int|uint)\s+(\w+)\s*=\s*(\d+)\s*;")
CASE_RE = re.compile(
    r'new\(\s*"(?P<branch>[^"]+)"\s*,\s*(?P<bits>\d+)\s*,\s*(?P<hex>"[0-9A-Fa-f]*"|\w+)\s*\)'
)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        raise SystemExit(__doc__)
    src = Path(argv[1]).read_text(encoding="utf-8-sig")

    strings = {m.group(1): m.group(2) for m in CONST_RE.finditer(src)}
    ints = {m.group(1): int(m.group(2)) for m in INT_CONST_RE.finditer(src)}
    for required in ("PayloadHex",):
        if required not in strings:
            raise SystemExit(f"missing `{required}` constant in fixture")
    if "ActorNetGuid" not in ints:
        raise SystemExit("missing `ActorNetGuid` constant in fixture")

    cases = []
    for m in CASE_RE.finditer(src):
        raw = m.group("hex")
        if raw.startswith('"'):
            hexstr = raw.strip('"')
        elif raw in strings:
            hexstr = strings[raw]
        else:
            raise SystemExit(f"vector references unknown constant `{raw}`")
        bits = int(m.group("bits"))
        expected_bytes = (bits + 7) // 8
        if len(hexstr) // 2 != expected_bytes:
            raise SystemExit(
                f"{m.group('branch')} @ {bits} bits: expected {expected_bytes} bytes, "
                f"hex carries {len(hexstr) // 2}"
            )
        branch = m.group("branch")
        if branch in SUPERSEDED_FIXTURE_BRANCHES:
            continue
        cases.append((branch, bits, hexstr.upper()))

    if len(cases) != EXPECTED_CASE_COUNT:
        raise SystemExit(
            f"expected exactly {EXPECTED_CASE_COUNT} golden vectors from the fixture, "
            f"found {len(cases)}"
        )

    # Compute the oracle-backed regional builds over the same payload and seed
    # rule as the fixture.
    payload = bytes.fromhex(strings["PayloadHex"])
    for branch, oracle_type in ORACLE_TRANSFORMS:
        oracle = oracle_type(SBOX_RS)
        for bits in EXPECTED_BOUNDARIES:
            seed = bits ^ ints["ActorNetGuid"]
            out = oracle.transform(payload, bits, seed)
            cases.append((branch, bits, out.hex().upper()))

    pairs = {(branch, bits) for branch, bits, _ in cases}
    expected_pairs = {
        (branch, bits)
        for branch in EXPECTED_BRANCHES + ORACLE_BRANCHES
        for bits in EXPECTED_BOUNDARIES
    }
    if pairs != expected_pairs or len(pairs) != len(cases):
        missing = sorted(expected_pairs - pairs)
        unexpected = sorted(pairs - expected_pairs)
        duplicate_count = len(cases) - len(pairs)
        details = []
        if missing:
            details.append("missing " + ", ".join(f"{b} @ {n}" for b, n in missing))
        if unexpected:
            details.append(
                "unexpected " + ", ".join(f"{b} @ {n}" for b, n in unexpected)
            )
        if duplicate_count:
            details.append(f"{duplicate_count} duplicate vector(s)")
        raise SystemExit("invalid golden oracle: " + "; ".join(details))

    branches = sorted({c[0] for c in cases})
    # Regular `//` comments, not `//!`: this file is pulled in with `include!`,
    # and an inner doc comment is only legal at the top of a module.
    lines = [
        "// Golden payload-transform vectors.",
        "//",
        "// GENERATED by tools/extract_golden.py -- do not edit by hand.",
        "//",
        "// Provenance differs by build, and it matters:",
        "//   - the six release-* builds are lifted from the upstream C# fixture,",
        "//     an implementation written by someone else;",
        "//   - release-china-13.02, release-china-13.04 and",
        "//     release-china-13.05 are computed by",
        "//     tools/china_transform_oracle.py; the first replaces known-wrong",
        "//     fixture stubs and the latter two are absent from that fixture.",
        "//",
        f"// {len(cases)} vectors across {len(branches)} builds. Bit counts are chosen to",
        "// exercise every staging boundary of the transform: 0, 1, 7 (tail only),",
        "// 8 (one byte), 31/32 (32-bit word edge), 63/64/65 (64-bit word edge) and",
        "// 287/288 (multi-word with and without a partial tail).",
        "",
        "/// The shared plaintext payload every vector transforms.",
        f'pub const PAYLOAD_HEX: &str = "{strings["PayloadHex"].upper()}";',
        "",
        "/// Actor net GUID used to derive the seed in the reference fixture.",
        f"pub const ACTOR_NET_GUID: u32 = {ints['ActorNetGuid']};",
        "",
        "/// `(branch, bit_count, expected_output_hex)`",
        f"pub const VECTORS: [(&str, usize, &str); {len(cases)}] = [",
    ]
    for branch, bits, hexstr in cases:
        lines.append(f'    ("{branch}", {bits}, "{hexstr}"),')
    lines.append("];")
    lines.append("")

    atomic_write_text(Path(argv[2]), "\n".join(lines))
    per_branch = {b: sum(1 for c in cases if c[0] == b) for b in branches}
    for b in branches:
        print(f"  {b}: {per_branch[b]} vectors")
    print(f"wrote {argv[2]} ({len(cases)} vectors total)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
