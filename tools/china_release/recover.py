#!/usr/bin/env python3
"""Reproduce the replay-driven recovery steps for a China release transform.

The evidence file contains only deterministic wire observations: seeds,
plaintext/ciphertext pairs, state candidates and low-byte constraints. The
default run verifies the committed observations quickly. Pass
`--rescan-mixed-a` to repeat the full u32 intermediate-state scan with NumPy.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
import time
from pathlib import Path


MASK8 = 0xFF
MASK32 = 0xFFFF_FFFF
MASK64 = 0xFFFF_FFFF_FFFF_FFFF
MULTIPLIER = 0x2545_F491_4F6C_DD1D
OPERATION_COUNT = 52
REPO = Path(__file__).resolve().parents[2]
DEFAULT_EVIDENCE = Path(__file__).resolve().parent / "evidence" / "china_13_04.json"
BYTE_RE = re.compile(r"0x([0-9a-fA-F]{2})\b")


class RecoveryError(RuntimeError):
    pass


def parse_int(value: int | str) -> int:
    return value if isinstance(value, int) else int(value, 0)


def le_word(value: str) -> int:
    raw = bytes.fromhex(value)
    if not raw:
        raise RecoveryError("an evidence word cannot be empty")
    return int.from_bytes(raw, "little")


def rotl(value: int, count: int, width: int, mask: int) -> int:
    count %= width
    if count == 0:
        return value & mask
    return ((value << count) | (value >> (width - count))) & mask


def rotr(value: int, count: int, width: int, mask: int) -> int:
    count %= width
    if count == 0:
        return value & mask
    return ((value >> count) | (value << (width - count))) & mask


def swap_adjacent(value: int, mask: int) -> int:
    pattern = 0x5555_5555_5555_5555 & mask
    return (((value & pattern) << 1) | ((value >> 1) & pattern)) & mask


def reverse_bits(value: int, width: int) -> int:
    output = 0
    for bit in range(width):
        if value & (1 << bit):
            output |= 1 << (width - 1 - bit)
    return output


def reverse64_without_final_16bit_swap(value: int) -> int:
    value = swap_adjacent(value, MASK64)
    value = ((value & 0x3333_3333_3333_3333) << 2) | (
        (value >> 2) & 0x3333_3333_3333_3333
    )
    value = ((value & 0x0F0F_0F0F_0F0F_0F0F) << 4) | (
        (value >> 4) & 0x0F0F_0F0F_0F0F_0F0F
    )
    value = ((value & 0x00FF_00FF_00FF_00FF) << 8) | (
        (value >> 8) & 0x00FF_00FF_00FF_00FF
    )
    return rotl(value & MASK64, 32, 64, MASK64)


def load_sbox(path: Path, name: str = "SBOX_64") -> tuple[int, ...]:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        rf"pub static {re.escape(name)}:\s*\[u8;\s*256\]\s*=\s*\[(.*?)\];",
        text,
        re.S,
    )
    if match is None:
        raise RecoveryError(f"cannot find {name} in {path}")
    values = tuple(int(byte, 16) for byte in BYTE_RE.findall(match.group(1)))
    if len(values) != 256 or set(values) != set(range(256)):
        raise RecoveryError(f"{name} is not a 256-byte permutation")
    return values


def substitute64(value: int, table: tuple[int, ...]) -> int:
    output = 0
    for index in range(8):
        output |= table[(value >> (index * 8)) & MASK8] << (index * 8)
    return output


def state_operand(state: int, operation: int) -> int:
    exponent = (operation - 4) % 8 + 1
    return rotr(state, exponent, 32, MASK32)


def apply_operation(
    value: int, state: int, operation: int, sbox: tuple[int, ...]
) -> int:
    operand = state_operand(state, operation) if operation >= 4 else 0
    if operation == 0:
        return (~value) & MASK64
    if operation == 1:
        return swap_adjacent(value, MASK64)
    if operation == 2:
        return reverse64_without_final_16bit_swap(value)
    if operation == 3:
        return substitute64(value, sbox)
    if 4 <= operation <= 11:
        return rotl(value, (operand % 63) + 1, 64, MASK64)
    if 12 <= operation <= 19:
        return rotr(value, (operand % 63) + 1, 64, MASK64)
    if 20 <= operation <= 27:
        return (value + operand) & MASK64
    if 28 <= operation <= 35:
        return (value - operand) & MASK64
    if 36 <= operation <= 43:
        return value ^ operand
    if 44 <= operation <= 51:
        return value ^ ((~operand) & MASK64)
    raise RecoveryError(f"unknown operation {operation}")


def apply_inverse(
    value: int,
    state: int,
    operation: int,
    sbox: tuple[int, ...],
    inverse_sbox: tuple[int, ...],
) -> int:
    if operation <= 2 or 36 <= operation <= 51:
        return apply_operation(value, state, operation, sbox)
    if operation == 3:
        return substitute64(value, inverse_sbox)
    operand = state_operand(state, operation)
    if 4 <= operation <= 11:
        return rotr(value, (operand % 63) + 1, 64, MASK64)
    if 12 <= operation <= 19:
        return rotl(value, (operand % 63) + 1, 64, MASK64)
    if 20 <= operation <= 27:
        return (value - operand) & MASK64
    if 28 <= operation <= 35:
        return (value + operand) & MASK64
    raise RecoveryError(f"unknown inverse operation {operation}")


def operation_name(operation: int) -> str:
    if operation == 0:
        return "NOT"
    if operation == 1:
        return "SWAP"
    if operation == 2:
        return "REV"
    if operation == 3:
        return "SBOX"
    families = (
        (4, 11, "ROL"),
        (12, 19, "ROR"),
        (20, 27, "ADD"),
        (28, 35, "SUB"),
        (36, 43, "XOR"),
        (44, 51, "XORNOT"),
    )
    for first, last, label in families:
        if first <= operation <= last:
            return f"{label}{operation - first + 1}"
    raise RecoveryError(f"unknown operation {operation}")


def sequence_names(sequence: tuple[int, ...]) -> tuple[str, ...]:
    return tuple(operation_name(operation) for operation in sequence)


def evaluate_sequence(
    value: int, state: int, sequence: tuple[int, ...], sbox: tuple[int, ...]
) -> int:
    for operation in sequence:
        value = apply_operation(value, state, operation, sbox)
    return value


def vector(row: dict) -> tuple[int, int, int]:
    return le_word(row["cipher_le"]), le_word(row["plain_le"]), parse_int(row["state"])


def search_word64_representatives(
    row: dict, length: int, sbox: tuple[int, ...]
) -> list[tuple[int, ...]]:
    """Return one representative for each meet-in-the-middle state.

    Algebraically equivalent prefixes can converge on the same intermediate
    value. Keeping the first one matches the calibrated investigation tool and
    keeps memory bounded; this is a recovery search, not a proof that every
    possible spelling has been enumerated.
    """
    cipher, plain, state = vector(row)
    inverse = [0] * 256
    for source, target in enumerate(sbox):
        inverse[target] = source
    inverse_sbox = tuple(inverse)

    left_depth = length // 2
    right_depth = length - left_depth
    forward: dict[int, tuple[int, ...]] = {}
    for sequence in itertools.product(range(OPERATION_COUNT), repeat=left_depth):
        value = evaluate_sequence(cipher, state, sequence, sbox)
        forward.setdefault(value, sequence)

    matches: set[tuple[int, ...]] = set()
    for reverse_sequence in itertools.product(
        range(OPERATION_COUNT), repeat=right_depth
    ):
        value = plain
        for operation in reverse_sequence:
            value = apply_inverse(value, state, operation, sbox, inverse_sbox)
        prefix = forward.get(value)
        if prefix is not None:
            matches.add(prefix + tuple(reversed(reverse_sequence)))
    return sorted(matches)


def filter_vectors(
    candidates: list[tuple[int, ...]], rows: list[dict], sbox: tuple[int, ...]
) -> list[tuple[int, ...]]:
    return [
        candidate
        for candidate in candidates
        if all(
            evaluate_sequence(cipher, state, candidate, sbox) == plain
            for cipher, plain, state in map(vector, rows)
        )
    ]


def recover_word64(evidence: dict) -> tuple[str, ...]:
    config = evidence["word64"]
    sbox = load_sbox(REPO / config["sbox_path"])

    calibration = config["calibration"]
    calibration_length = len(calibration["expected_sequence"])
    calibration_matches = search_word64_representatives(
        calibration, calibration_length, sbox
    )
    calibration_names = {sequence_names(match) for match in calibration_matches}
    expected_calibration = tuple(calibration["expected_sequence"])
    if expected_calibration not in calibration_names:
        raise RecoveryError("word64 search failed its China 13.02 calibration")
    print(
        f"word64 calibration: {len(calibration_matches)} representative "
        f"match(es), expected sequence recovered"
    )

    rows = config["vectors"]
    matches: list[tuple[int, ...]] = []
    shortest = 0
    for length in range(1, int(config["max_sequence_length"]) + 1):
        candidates = search_word64_representatives(rows[0], length, sbox)
        matches = filter_vectors(candidates, rows[1:], sbox)
        print(f"word64 target: length={length} representatives={len(matches)}")
        if matches:
            shortest = length
            break
    if not matches:
        raise RecoveryError("no word64 sequence satisfies every evidence vector")

    expected = tuple(config["expected_sequence"])
    names = {sequence_names(match) for match in matches}
    if expected not in names:
        raise RecoveryError("the expected word64 sequence was not recovered")
    print(f"word64 recovered at shortest length {shortest}: {' -> '.join(expected)}")
    return expected


def decode_word32(cipher: int, state: int, first_not: bool, last_not: bool) -> int:
    value = reverse_bits(cipher, 32)
    first = rotl(state, 6, 32, MASK32)
    value ^= ((~first) & MASK32) if first_not else first
    for exponent in (4, 3, 2):
        value = (value + rotl(state, exponent, 32, MASK32)) & MASK32
    last = rotl(state, 1, 32, MASK32)
    value ^= ((~last) & MASK32) if last_not else last
    return value


def decode_byte(cipher: int, state: int, first_not: bool, last_not: bool) -> int:
    value = reverse_bits(cipher, 8)
    mixes = {
        exponent: (state * (11**exponent)) & MASK32
        for exponent in (1, 2, 3, 4, 6)
    }
    first = mixes[6] & MASK8
    value ^= ((~first) & MASK8) if first_not else first
    for exponent in (4, 3, 2):
        value = (value + (mixes[exponent] & MASK8)) & MASK8
    last = mixes[1] & MASK8
    value ^= ((~last) & MASK8) if last_not else last
    return value


def recover_short_lanes(evidence: dict) -> tuple[bool, bool]:
    config = evidence["short_lanes"]
    passing = []
    for first_not, last_not in itertools.product((False, True), repeat=2):
        word32_ok = all(
            decode_word32(
                le_word(row["cipher_le"]), row["state"], first_not, last_not
            )
            == le_word(row["plain_le"])
            for row in config["word32"]
        )
        byte_ok = all(
            decode_byte(
                parse_int(row["cipher"]), row["state"], first_not, last_not
            )
            == parse_int(row["plain"])
            for row in config["byte"]
        )
        if word32_ok and byte_ok:
            passing.append((first_not, last_not))

    expected = config["expected_complements"]
    expected_pair = (expected["first_xor"], expected["last_xor"])
    if passing != [expected_pair]:
        raise RecoveryError(
            f"short-lane complement search returned {passing}, expected {expected_pair}"
        )
    print(
        "short lanes: unique complement pair first_xor=true last_xor=true "
        f"({len(config['word32'])} word32 and {len(config['byte'])} byte vectors)"
    )
    return expected_pair


def g(value: int) -> int:
    value &= MASK32
    return (value ^ (value >> 12) ^ (value >> 27)) & MASK32


def invert_g(value: int) -> int:
    value &= MASK32
    after_first = value ^ (value >> 27)
    return (after_first ^ (after_first >> 12) ^ (after_first >> 24)) & MASK32


def mixed_b(seed: int) -> int:
    return g(seed) ^ ((seed & 0x7F) << 25)


def state1(seed: int, addend: int, q_at_anchor_seed: int, anchor_seed: int) -> int:
    offset_bits = (q_at_anchor_seed + seed - anchor_seed) & 0x7F
    mixed_a = g((seed + addend) & MASK32) ^ (offset_bits << 25)
    total = ((mixed_a * MULTIPLIER) + (mixed_b(seed) * MULTIPLIER)) & MASK64
    return total >> 32


def recorded_mixed_a(config: dict) -> dict[int, list[int]]:
    return {
        parse_int(state): [parse_int(value) for value in values]
        for state, values in config["mixed_a_solutions"].items()
    }


def scan_mixed_a(
    config: dict, *, bits: int = 32, chunk_bits: int = 22
) -> dict[int, list[int]]:
    try:
        import numpy as np
    except ImportError as error:
        raise RecoveryError(
            "--rescan-mixed-a requires NumPy; install requirements.txt"
        ) from error

    if not 1 <= bits <= 32:
        raise RecoveryError("scan bits must be in 1..=32")
    if not 10 <= chunk_bits <= 26:
        raise RecoveryError("chunk bits must be in 10..=26")

    targets = sorted(
        {parse_int(candidate["state"]) for candidate in config["state_candidates"]}
    )
    found = {target: [] for target in targets}
    limit = 1 << bits
    chunk_size = 1 << min(bits, chunk_bits)
    multiplier = np.uint64(MULTIPLIER)
    base = np.uint64(mixed_b(parse_int(config["seed"])))
    started = time.perf_counter()
    next_report = max(chunk_size, limit // 8)

    for start in range(0, limit, chunk_size):
        end = min(start + chunk_size, limit)
        candidates = np.arange(start, end, dtype=np.uint64)
        with np.errstate(over="ignore"):
            states = ((candidates + base) * multiplier) >> np.uint64(32)
        for target in targets:
            indexes = np.flatnonzero(states == np.uint64(target))
            if indexes.size:
                found[target].extend(int(candidates[index]) for index in indexes)
        if end >= next_report or end == limit:
            elapsed = time.perf_counter() - started
            print(
                f"mixed_a scan: {end}/{limit} ({end / limit:.0%}) "
                f"elapsed={elapsed:.1f}s",
                file=sys.stderr,
            )
            next_report += max(chunk_size, limit // 8)

    for values in found.values():
        values.sort()
    return found


def derive_prng_candidates(
    config: dict, mixed_values: dict[int, list[int]]
) -> list[dict[str, int | str]]:
    anchor_seed = parse_int(config["seed"])
    low_pairs = [
        (parse_int(row["seed"]), parse_int(row["value"]))
        for row in config["state1_low_bytes"]
    ]
    identities: dict[int, list[str]] = {}
    for candidate in config["state_candidates"]:
        identities.setdefault(parse_int(candidate["state"]), []).append(
            candidate["identity"]
        )

    results = []
    seen = set()
    for target_state, names in identities.items():
        for mixed_a in mixed_values.get(target_state, []):
            for high7 in range(128):
                unmixed = (high7 << 25) | (mixed_a & ((1 << 25) - 1))
                seed_plus = invert_g(unmixed)
                addend = (seed_plus - anchor_seed) & MASK32
                q_at_anchor = high7 ^ (mixed_a >> 25)
                if state1(anchor_seed, addend, q_at_anchor, anchor_seed) != target_state:
                    raise RecoveryError("derived PRNG candidate failed to round-trip")
                if not all(
                    (state1(seed, addend, q_at_anchor, anchor_seed) & MASK8) == low
                    for seed, low in low_pairs
                ):
                    continue
                subtract_offset = (anchor_seed - q_at_anchor) & 0x7F
                key = (target_state, addend, q_at_anchor, subtract_offset)
                if key in seen:
                    continue
                seen.add(key)
                for identity in names:
                    results.append(
                        {
                            "identity": identity,
                            "state": target_state,
                            "seed_addend": addend,
                            "q_at_anchor": q_at_anchor,
                            "subtract_offset": subtract_offset,
                            "equivalent_add_offset": (-subtract_offset) & 0x7F,
                            "tail_xor": addend & MASK8,
                        }
                    )
    return results


def recover_prng(
    evidence: dict, *, rescan: bool = False, scan_bits: int = 32, chunk_bits: int = 22
) -> dict[str, int | str]:
    config = evidence["prng"]
    committed = recorded_mixed_a(config)
    if rescan:
        mixed_values = scan_mixed_a(config, bits=scan_bits, chunk_bits=chunk_bits)
        if scan_bits == 32 and mixed_values != committed:
            raise RecoveryError("full mixed_a rescan disagrees with committed evidence")
    else:
        mixed_values = committed
        print("mixed_a scan: using committed full-u32 results (pass --rescan-mixed-a to repeat)")

    inverse_count = sum(len(values) for values in mixed_values.values())
    print(
        f"mixed_a inverses: {inverse_count} across "
        f"{len(mixed_values)} target state(s)"
    )
    candidates = derive_prng_candidates(config, mixed_values)
    if len(candidates) != 1:
        raise RecoveryError(f"PRNG derivation produced {len(candidates)} candidates")
    candidate = candidates[0]
    expected = config["expected"]
    expected_values = {
        "identity": expected["identity"],
        "state": parse_int(expected["state"]),
        "seed_addend": parse_int(expected["seed_addend"]),
        "subtract_offset": parse_int(expected["subtract_offset"]),
        "equivalent_add_offset": parse_int(expected["equivalent_add_offset"]),
        "tail_xor": parse_int(expected["tail_xor"]),
    }
    for key, value in expected_values.items():
        if candidate[key] != value:
            raise RecoveryError(
                f"PRNG candidate {key}={candidate[key]!r}, expected {value!r}"
            )
    print(
        "prng recovered: "
        f"seed_addend=0x{candidate['seed_addend']:08x} "
        f"subtract_offset=0x{candidate['subtract_offset']:02x} "
        f"tail_xor=0x{candidate['tail_xor']:02x} "
        f"identity={candidate['identity']}"
    )
    return candidate


def load_evidence(path: Path) -> dict:
    evidence = json.loads(path.read_text(encoding="utf-8"))
    if evidence.get("schema_version") != 1:
        raise RecoveryError("unsupported evidence schema_version")
    for section in ("branch", "word64", "short_lanes", "prng"):
        if section not in evidence:
            raise RecoveryError(f"evidence is missing {section}")
    return evidence


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "evidence",
        nargs="?",
        type=Path,
        default=DEFAULT_EVIDENCE,
        help="recovery evidence JSON (default: committed China 13.04 fixture)",
    )
    parser.add_argument(
        "--phase",
        choices=("all", "word64", "short-lanes", "prng"),
        default="all",
        help="run one recovery phase instead of all phases",
    )
    parser.add_argument(
        "--rescan-mixed-a",
        action="store_true",
        help="repeat the PRNG intermediate-state scan instead of using recorded results",
    )
    parser.add_argument(
        "--scan-bits",
        type=int,
        default=32,
        help="candidate width for the optional scan; 32 is the evidentiary run",
    )
    parser.add_argument(
        "--chunk-bits",
        type=int,
        default=22,
        help="NumPy scan chunk size as a power of two (10..26)",
    )
    args = parser.parse_args(argv)
    if args.rescan_mixed_a and args.phase not in ("all", "prng"):
        parser.error("--rescan-mixed-a requires --phase all or --phase prng")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        evidence = load_evidence(args.evidence)
        if args.phase in ("all", "word64"):
            recover_word64(evidence)
        if args.phase in ("all", "short-lanes"):
            recover_short_lanes(evidence)
        if args.phase in ("all", "prng"):
            recover_prng(
                evidence,
                rescan=args.rescan_mixed_a,
                scan_bits=args.scan_bits,
                chunk_bits=args.chunk_bits,
            )
        print(f"PASS: recovered evidence for {evidence['branch']}")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError, RecoveryError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
