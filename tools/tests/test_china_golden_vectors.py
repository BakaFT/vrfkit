"""Keep every China boundary vector tied to the independent Python oracle."""
import re
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import china_transform_oracle as oracle


class ChinaGoldenTests(unittest.TestCase):
    def test_all_five_builds_have_the_independently_computed_boundaries(self):
        root = TOOLS.parent
        source = (root / "crates/vrf-transform/tests/data/golden_vectors.rs").read_text(encoding="utf-8")
        payload = bytes.fromhex(re.search(r'PAYLOAD_HEX: &str = "([0-9A-F]+)"', source)[1])
        actor = int(re.search(r'ACTOR_NET_GUID: u32 = (\d+)', source)[1])
        rows = re.findall(r'\("\+\+Ares-Core\+release-china-([0-9.]+)", (\d+), "([0-9A-F]*)"\)', source)
        classes = {
            "13.02": oracle.ChinaTransform,
            "13.04": oracle.China1304Transform,
            "13.05": oracle.China1305Transform,
            "13.08": oracle.China1308Transform,
            "13.09": oracle.China1309Transform,
        }
        self.assertEqual(len(rows), 55)
        self.assertEqual({version for version, _, _ in rows}, set(classes))
        for version, cls in classes.items():
            vectors = [(int(bits), expected) for v, bits, expected in rows if v == version]
            self.assertEqual([bits for bits, _ in vectors], [0, 1, 7, 8, 31, 32, 63, 64, 65, 287, 288])
            implementation = cls(root / "crates/vrf-transform/src/sbox.rs")
            for bits, expected in vectors:
                with self.subTest(version=version, bits=bits):
                    self.assertEqual(implementation.transform(payload, bits, bits ^ actor), bytes.fromhex(expected))


if __name__ == "__main__":
    unittest.main()
