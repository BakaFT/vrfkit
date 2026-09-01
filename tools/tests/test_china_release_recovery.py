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
            sequence,
            ("REV", "XOR6", "ADD4", "ADD3", "ADD2", "XOR1"),
        )

    def test_a_wrong_second_word64_vector_is_rejected(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["word64"]["vectors"][1]["plain_le"] = "110ca261300f8120"
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(recover.RecoveryError):
                recover.recover_word64(evidence)

    def test_short_lanes_and_prng_have_one_solution(self):
        with contextlib.redirect_stdout(io.StringIO()):
            complements = recover.recover_short_lanes(self.evidence)
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
