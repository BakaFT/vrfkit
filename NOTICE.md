# Third-party notices

## ValorantReplayParser

Parts of this project are derived from **ValorantReplayParser** by Michel Giehl,
used under the MIT License.

- Source: https://github.com/michel-giehl/ValorantReplayParser
- License: MIT

```
MIT License

Copyright (c) 2026 Michel Giehl

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### What is derived

| Area | Relationship |
|---|---|
| `crates/vrf-transform` | The five `release-*` per-build payload transforms and their constants are a port of `Replay.Encoding/PayloadEncryption`. The substitution tables and those builds' golden test vectors are extracted mechanically from that source (`tools/extract_sboxes.py`, `tools/extract_golden.py`). |
| `crates/vrf-bitio` | The Unreal wire primitives (`IntPacked`, bounded `SerializedInt`, `FString`, bit copying) follow the semantics implemented in `Replay.Encoding/Archives`. |

The reverse engineering of VALORANT's payload transformation originates with that
project; this repository reimplements the result rather than rediscovering it.

## ValorantReplayParser -- LeagueTavern fork

`versions::V13_02China`'s 64-bit lane and its three constants come from the
`china-server-support` branch of
[LeagueTavern/ValorantReplayParser](https://github.com/LeagueTavern/ValorantReplayParser),
also MIT. That branch documents them as recovered by decompiling a third party's
private build.

Its 32-bit and byte lanes are **not** derived from that source, which left both
zeroing their input, and are original to this repository -- see the type's doc
comment for how they were derived and what they were measured against.

## Prior art acknowledged upstream

ValorantReplayParser credits
[FortniteReplayDecompressor](https://github.com/Shiqan/FortniteReplayDecompressor)
for documenting the Unreal replay system. That documentation informs the
replication layer here as well.

## Disclaimer

This project is an independent, community-developed tool and is not affiliated
with, endorsed by, sponsored by, or approved by Riot Games. VALORANT, Riot Games,
and all related trademarks are the property of Riot Games, Inc.
