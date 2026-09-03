import contextlib
import copy
import io
import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / "china_release"))
import recover  # noqa: E402


class ChinaReleaseRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = recover.load_evidence(recover.DEFAULT_EVIDENCE)

    def test_word64_search_recovers_the_shortest_measured_sequence(self):
        with contextlib.redirect_stdout(io.StringIO()):
            sequence = recover.recover_word64(self.evidence)
        self.assertEqual(
            recover.sequence_names(sequence),
            ("REV", "XOR6", "ADD4", "ADD3", "ADD2", "XOR1"),
        )

    def test_word64_search_keeps_distinct_multi_state_prefixes(self):
        rows = [
            {
                "state": 528,
                "cipher_le": "160da251300f8100",
                "plain_le": "100ca261300f8100",
            },
            {
                "state": 92,
                "cipher_le": "d03018c305c18020",
                "plain_le": "100c820141a06130",
            },
            {
                "state": 2276,
                "cipher_le": "0820009e0fa26130",
                "plain_le": "100ca26130102000",
            },
            {
                "state": 285,
                "cipher_le": "e0300feb039e0ca4",
                "plain_le": "100ca461300f0804",
            },
        ]
        sbox = recover.load_sbox(recover.REPO / "crates/vrf-transform/src/sbox.rs")
        with contextlib.redirect_stdout(io.StringIO()):
            matches = recover.search_word64_representatives(rows, 6, sbox)
        names = {recover.sequence_names(match) for match in matches}
        self.assertIn(
            ("ADD8", "ROL4", "ROL6", "ROR2", "ROR7", "SUB1"),
            names,
        )

    def test_china_1305_committed_evidence_recovers_every_unknown(self):
        evidence_path = (
            recover.REPO / "tools/china_release/evidence/china_13_05.json"
        )
        evidence = recover.load_evidence(evidence_path)
        with contextlib.redirect_stdout(io.StringIO()):
            sequence = recover.recover_word64(evidence)
            complements = recover.recover_short_lanes(evidence, sequence)
            candidate = recover.recover_prng(evidence, sequence, complements)

        self.assertEqual(
            recover.sequence_names(sequence),
            ("ADD8", "ROL4", "ROL6", "ROR2", "ROR7", "SUB1"),
        )
        self.assertEqual(complements, ())
        self.assertEqual(candidate["state"], 0x6CE1_103C)
        self.assertEqual(candidate["seed_addend"], 0xF677_61C9)
        self.assertEqual(candidate["subtract_offset"], 0x37)
        self.assertEqual(candidate["tail_xor"], 0xC9)

    def test_a_wrong_second_word64_vector_is_rejected(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["word64"]["vectors"][1]["plain_le"] = "110ca261300f8120"
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(recover.RecoveryError):
                recover.recover_word64(evidence)

    def test_short_lanes_and_prng_have_one_solution(self):
        with contextlib.redirect_stdout(io.StringIO()):
            sequence = recover.recover_word64(self.evidence)
            complements = recover.recover_short_lanes(self.evidence, sequence)
            candidate = recover.recover_prng(self.evidence)
        self.assertEqual(complements, (True, True))
        self.assertEqual(candidate["seed_addend"], 0xE920_64A1)
        self.assertEqual(candidate["subtract_offset"], 0x5F)
        self.assertEqual(candidate["tail_xor"], 0xA1)

    def test_small_vectorized_scan_finds_a_constructed_preimage(self):
        config = copy.deepcopy(self.evidence["prng"])
        mixed_a = 1234
        seed = config["seed"]
        state = (
            ((mixed_a + recover.mixed_b(seed)) * recover.MULTIPLIER)
            & recover.MASK64
        ) >> 32
        config["state_candidates"] = [
            {"identity": "constructed", "state": hex(state)}
        ]
        with contextlib.redirect_stderr(io.StringIO()):
            found = recover.scan_mixed_a(config, bits=12, chunk_bits=10)
        self.assertIn(mixed_a, found[state])


if __name__ == "__main__":
    unittest.main()
