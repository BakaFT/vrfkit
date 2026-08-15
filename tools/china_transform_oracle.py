"""Independent Python implementation of the `release-china-13.02` payload transform.

Every other build's golden vectors are lifted from the upstream C# fixture,
which is an implementation written by someone else and therefore an independent
check on our port. For this build that is not available: the C# fixture's
China vectors encode a routine whose 32-bit and byte lanes were never
recovered and were left zeroing their input, so six of its eleven vectors
disagree with the real client. Lifting them would pin our port to a known-wrong
oracle.

This module supplies the missing second implementation. It is written against
the algorithm description rather than transliterated from the Rust, so it
catches the failure this file exists to catch -- a transcription, masking or
endianness slip in one of the two ports. It cannot, on its own, catch "the
algorithm is wrong"; that is what validating against real replays does, and
`versions::V13_02China` records the result (100.000000% of 893,665 content
blocks framed across two replays).

The S-boxes are read from the generated Rust table rather than re-embedded: they
are shared with the global builds, whose vectors DO come from the C# fixture, so
a corrupt table would already be failing those.

Usage:
    from china_transform_oracle import ChinaTransform
    ChinaTransform(sbox_path).transform(payload_bytes, bit_count, seed)
"""

from __future__ import annotations

import re
from pathlib import Path

BRANCH = "++Ares-Core+release-china-13.02"

MASK8 = 0xFF
MASK32 = 0xFFFF_FFFF
MASK64 = 0xFFFF_FFFF_FFFF_FFFF

MULTIPLIER = 0x2545_F491_4F6C_DD1D
SEED_ADDEND = 0x9E70_CF19
INIT_A_OFFSET = 0x67
TAIL_XOR = 0x19

SBOX_RE = re.compile(r"(SBOX_\w+)\s*:\s*\[u8;\s*256\]\s*=\s*\[(.*?)\];", re.S)
BYTE_RE = re.compile(r"0x([0-9a-fA-F]{2})\b")


def load_sboxes(sbox_rs: Path) -> dict[str, list[int]]:
    """Parse `SBOX_8`, `SBOX_32` and `SBOX_64` out of the generated Rust table."""
    text = sbox_rs.read_text(encoding="utf-8")
    tables: dict[str, list[int]] = {}
    for match in SBOX_RE.finditer(text):
        values = [int(b, 16) for b in BYTE_RE.findall(match.group(2))]
        if len(values) != 256:
            raise SystemExit(f"{match.group(1)}: expected 256 entries, parsed {len(values)}")
        tables[match.group(1)] = values
    for required in ("SBOX_8", "SBOX_32", "SBOX_64"):
        if required not in tables:
            raise SystemExit(f"missing `{required}` in {sbox_rs}")
    return tables


def rotl(value: int, count: int, width: int, mask: int) -> int:
    count %= width
    return ((value << count) | (value >> (width - count))) & mask if count else value


def rotr(value: int, count: int, width: int, mask: int) -> int:
    count %= width
    return ((value >> count) | (value << (width - count))) & mask if count else value


def swap_adjacent(value: int, mask: int) -> int:
    pattern = 0x5555_5555_5555_5555 & mask
    return (((value & pattern) << 1) | ((value >> 1) & pattern)) & mask


def reverse_bits(value: int, width: int) -> int:
    """Reverse `width` bits, EXCEPT the final half-swap stage is kept.

    For 32 and 8 bits this is a plain reversal. For 64 bits the engine omits the
    16-bit stage, so it is not a reversal at all -- see `reverse64_no_16`.
    """
    out = 0
    for i in range(width):
        if value & (1 << i):
            out |= 1 << (width - 1 - i)
    return out


def reverse64_no_16(value: int) -> int:
    """The 1/2/4/8-bit swaps and the 32-bit halves exchange, with no 16-bit stage."""
    v = value
    v = ((v & 0x5555_5555_5555_5555) << 1) | ((v >> 1) & 0x5555_5555_5555_5555)
    v = ((v & 0x3333_3333_3333_3333) << 2) | ((v >> 2) & 0x3333_3333_3333_3333)
    v = ((v & 0x0F0F_0F0F_0F0F_0F0F) << 4) | ((v >> 4) & 0x0F0F_0F0F_0F0F_0F0F)
    v = ((v & 0x00FF_00FF_00FF_00FF) << 8) | ((v >> 8) & 0x00FF_00FF_00FF_00FF)
    v &= MASK64
    return ((v << 32) | (v >> 32)) & MASK64


def substitute(value: int, table: list[int], byte_count: int) -> int:
    out = 0
    for i in range(byte_count):
        out |= table[(value >> (8 * i)) & MASK8] << (8 * i)
    return out


class ChinaTransform:
    """The `release-china-13.02` transform, staged 64 -> 32 -> 8 -> tail."""

    def __init__(self, sbox_rs: Path) -> None:
        tables = load_sboxes(sbox_rs)
        self.sbox8 = tables["SBOX_8"]
        self.sbox32 = tables["SBOX_32"]
        self.sbox64 = tables["SBOX_64"]

    # -- PRNG -------------------------------------------------------------

    @staticmethod
    def initial_prng_a(seed: int) -> int:
        seed_plus = (seed + SEED_ADDEND) & MASK32
        offset_term = ((seed - INIT_A_OFFSET) & MASK32) * 0x0200_0000 & MASK32
        mixed = ((((seed_plus >> 15) ^ seed_plus) >> 12) ^ offset_term ^ seed_plus) & MASK32
        return (mixed * MULTIPLIER) & MASK64

    @staticmethod
    def initial_prng_b(seed: int) -> int:
        mixed = ((((seed >> 15) ^ seed) >> 12) ^ ((seed << 25) & MASK32) ^ seed) & MASK32
        return (mixed * MULTIPLIER) & MASK64

    @staticmethod
    def advance(state: int, prng_a: int, prng_b: int) -> tuple[int, int, int, int]:
        total = (prng_b + prng_a) & MASK64
        prng_b ^= prng_a
        prng_a = (rotr(prng_a, 9, 64, MASK64) ^ ((prng_b << 14) & MASK64) ^ prng_b) & MASK64
        prng_b = rotl(prng_b, 36, 64, MASK64)
        state = (total >> 32) & MASK32
        return state, prng_a, prng_b, state & MASK8

    # -- Lanes ------------------------------------------------------------

    def word64(self, v: int, state: int) -> int:
        ror1 = rotr(state, 1, 32, MASK32)
        ror7 = rotr(state, 7, 32, MASK32)
        ror8 = rotr(state, 8, 32, MASK32)
        v = rotl(v, (ror7 % 63) + 1, 64, MASK64)
        v = rotr(v, (ror8 % 63) + 1, 64, MASK64)
        v = substitute(v, self.sbox64, 8)
        v = swap_adjacent(v, MASK64)
        v = reverse64_no_16(v)
        return (v + ror1) & MASK64

    def word32(self, v: int, state: int) -> int:
        rol1 = rotl(state, 1, 32, MASK32)
        rol7 = rotl(state, 7, 32, MASK32)
        rol8 = rotl(state, 8, 32, MASK32)
        v = rotl(v, (rol7 % 31) + 1, 32, MASK32)
        v = rotr(v, (rol8 % 31) + 1, 32, MASK32)
        v = substitute(v, self.sbox32, 4)
        v = swap_adjacent(v, MASK32)
        v = reverse_bits(v, 32)
        return (v + rol1) & MASK32

    def byte(self, v: int, state: int) -> int:
        mix1 = (state * 11) & MASK32
        mix7 = (state * 19_487_171) & MASK32
        mix8 = (state * 214_358_881) & MASK32
        v = rotl(v, (mix7 % 7) + 1, 8, MASK8)
        v = rotr(v, (mix8 % 7) + 1, 8, MASK8)
        v = self.sbox8[v]
        v = swap_adjacent(v, MASK8)
        v = reverse_bits(v, 8)
        return (v + (mix1 & MASK8)) & MASK8

    # -- Driver -----------------------------------------------------------

    def transform(self, payload: bytes, bit_count: int, seed: int) -> bytes:
        """Take `bit_count` bits of `payload` and return the decoded bytes.

        Padding in the final byte is zeroed before transforming, exactly as
        `BitReader::copy_bits_to` guarantees on the Rust side; stale padding
        would be folded into the tail byte.
        """
        byte_count = (bit_count + 7) // 8
        buf = bytearray(payload[:byte_count].ljust(byte_count, b"\x00"))
        if bit_count == 0:
            return bytes(buf)
        used = bit_count & 7
        if used:
            buf[-1] &= (1 << used) - 1

        state = seed
        stream_byte = seed & MASK8
        prng_a = self.initial_prng_a(seed)
        prng_b = self.initial_prng_b(seed)
        offset = 0
        left = bit_count

        while left > 63:
            word = int.from_bytes(buf[offset : offset + 8], "little")
            buf[offset : offset + 8] = self.word64(word, state).to_bytes(8, "little")
            state, prng_a, prng_b, stream_byte = self.advance(state, prng_a, prng_b)
            offset += 8
            left -= 64
        while left > 31:
            word = int.from_bytes(buf[offset : offset + 4], "little")
            buf[offset : offset + 4] = self.word32(word, state).to_bytes(4, "little")
            state, prng_a, prng_b, stream_byte = self.advance(state, prng_a, prng_b)
            offset += 4
            left -= 32
        while left > 7:
            buf[offset] = self.byte(buf[offset], state)
            state, prng_a, prng_b, stream_byte = self.advance(state, prng_a, prng_b)
            offset += 1
            left -= 8
        if left:
            mask = 0xFF >> (7 - ((bit_count - 1) & 7))
            buf[offset] ^= mask & (stream_byte ^ TAIL_XOR)

        return bytes(buf)
