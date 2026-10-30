# Upstream delta audit — 2026-10-30

This is a bounded cross-project review, **not** a claim that C# upstream and Rust vrfkit have identical semantics or that all upstream behavior was ported.

- Upstream: [michel-giehl/ValorantReplayParser](https://github.com/michel-giehl/ValorantReplayParser)
- Previous referenced revision: [`2e4d3aded2e892cda21e0a66c4b55c73b3b7a07f`](https://github.com/michel-giehl/ValorantReplayParser/commit/2e4d3aded2e892cda21e0a66c4b55c73b3b7a07f) (2026-09-30)
- Audited upstream revision: [`09a8e1e1d81c48840b8810f523f1595e539b7d55`](https://github.com/michel-giehl/ValorantReplayParser/commit/09a8e1e1d81c48840b8810f523f1595e539b7d55) (2026-10-27)
- **56 commits**, **377 net changed paths**: 169 added, 183 modified, 25 removed.
- Method: enumerate all commit messages with the GitHub compare endpoint, then compare the two complete Git trees by blob SHA. GitHub's compare endpoint exposes only the first 300 changed paths for this range; its truncated path list is **not** the complete inventory. Both recursive Git tree responses reported `truncated=false`. Paths changed and later reverted are visible in history but not in this final-state inventory.
- No downstream source files are modified by the inventory itself. Each entry below is a path-level change, not proof of line-by-line behavioral equivalence.

## Semantic triage (Rust vrfkit versus C# upstream)

| Upstream delta | Current vrfkit state / decision |
|---|---|
| Global transforms 11.06–13.09 | Already registered in `vrf-transform`, including 13.08 and 13.09; keep native-vector checks. |
| Separate China 13.05 transform | **Not ported.** Needs verified China-native arithmetic vectors and full replay, not a global-branch alias. |
| 13.09 `RoundResults.WinningTeamMode` | Already exposed as raw byte in `RoundResults` before this audit. |
| 13.09 nested `RoundResults.TeamResults` | **Ported in PR #39**: sparse team name/number/role/outcome fields, declared-name routing, strict bounded windows, raw parent preservation. |
| 13.09 17th inventory `ItemSlots` and shifted handles | `AresInventory.ItemSlots` remains raw intentionally. `fields.parquet` retains the actual handles and bits. Do not assign slot identities without replay observations. |
| 13.09 `RoundParticipantsInfos` handle shift | Parent is currently raw; dynamic array typing requires concrete corpus fixtures, especially across old build layouts. |
| BombPlayerState Ping u16 | Already typed as `SerializedInt { max: 65536 }` in the overlay table. |
| Gun actor ownership, skin/chroma/charm ObjectNetGuid | Already typed in vrfkit's corresponding actor overlay groups. Verify per-build population and lifetimes before presenting a semantic owner/purchaser view. |
| Hush/Paprika agent and ability actors, Iso/Waylay/Cypher/Breach/Sage/Viper abilities | Some fields stay raw or unnamed in vrfkit; C# actor catalog entries are hypotheses, not sufficient new decoding evidence. Measure wire declaration, checksums, decoded non-null values and raw retention before typing. |
| Enriched footsteps, jump landing/launch, pickup and comm ping | C# produces derived events; vrfkit primarily produces native fields/RPC plus Python analysis views. Adding equivalent joins needs replay fixtures, actor lifetime and source attribution controls. |
| Spike plant/defuse signals and state | vrfkit already exports several typed fields and RPCs and has `extract_spike_carrier.py`; compare distinct semantics (start/cancel/stop/checkpoint) before introducing new event labels. |
| Gun zoom state, location effects and map doors | Not claimed as implemented solely from the upstream catalog. Keep raw observations until widths, object identity and timing can be demonstrated. |
| NetGUID export notifications and fully resolved object paths | vrfkit emits `net_guids.parquet` and checkpoint GUID tables. C# event timing/API contracts are different; explicit per-packet export-event parity remains separate work. |
| C# event-enricher extraction, thread-safe descriptor locking and field-binding compiler | Architecture-specific C# changes. vrfkit uses its own Rust decoding/sink layers; do not transplant mechanically. |
| .NET/NuGet packaging, Sonar/assembly changes | Not applicable to Rust Cargo/Windows ZIP publishing; existing Rust CI remains the acceptance gate. |
| New upstream tests and private/pinned fixture files | Descriptive reference and regression ideas; no private fixtures or game binaries are copied into vrfkit. |

## Revalidation needed before expanding the port

1. Run the 13.09 replay corpus on this patch and compare exact main/checkpoint outputs: expect **new typed child rows** for TeamResults, *not* byte-for-byte identical field tables. Require zero new framing/array/struct-blob failures, zero unexplained data loss and correct per-team values; distinguish old historical baselines from measurements on this code.
2. Pilot 13.09 AresInventory slot identity and RoundParticipantsInfos framing against source bytes. Preserve absent fields, zero object references and sparse update indices.
3. Sample raw Hush/Paprika and additional agent ability paths against measured replay declarations and independently validate new type assumptions. Prioritize one small verified route at a time.
4. Footstep/zoom/spike event enrichment needs source attribution, ordering and explicit negative controls rather than guessing from an RPC label.
5. Treat C#-specific API changes as non-portable unless an equivalent bug is reproduced in Rust.

## Complete commit ledger (56)

| # | Commit | Subject | Author date (UTC) |
|---:|---|---|---|
| 1 | [`8e539660d`](https://github.com/michel-giehl/ValorantReplayParser/commit/8e539660d758adb907b5f28eef10032254d7190b) | feat: inventory and economy | 2026-10-01 |
| 2 | [`4326635f1`](https://github.com/michel-giehl/ValorantReplayParser/commit/4326635f1250b4c2654318de77345c034e8c292b) | feat: add missing transforms | 2026-10-03 |
| 3 | [`d05038eef`](https://github.com/michel-giehl/ValorantReplayParser/commit/d05038eef424a943b8da3cf9c8b9db49e032dd86) | feat!: prepare 0.1.0-alpha.2 | 2026-10-08 |
| 4 | [`32aee2353`](https://github.com/michel-giehl/ValorantReplayParser/commit/32aee2353252aeb025245c7168240f47db39da63) | fix: sonarcube issues | 2026-10-09 |
| 5 | [`673d52621`](https://github.com/michel-giehl/ValorantReplayParser/commit/673d52621fb97ffc3c022a8390b4a88f07706eaa) | feat: more descriptors | 2026-10-09 |
| 6 | [`95d318ae7`](https://github.com/michel-giehl/ValorantReplayParser/commit/95d318ae77932864bdfcff53dafbcb59fac13e4f) | feat: sage slow patches | 2026-10-09 |
| 7 | [`baa4e1f00`](https://github.com/michel-giehl/ValorantReplayParser/commit/baa4e1f00f5fba37fd2c7f839cdad41b7816c668) | add missing owner/instigator fields | 2026-10-09 |
| 8 | [`68a248da8`](https://github.com/michel-giehl/ValorantReplayParser/commit/68a248da82c5e33f887149f4684bfc1368c5af3c) | feat: viper snakebite and life state | 2026-10-10 |
| 9 | [`e86ec408f`](https://github.com/michel-giehl/ValorantReplayParser/commit/e86ec408f2b89ea7ddca88ffae03113781d7c482) | feat: 13.08 transform | 2026-10-14 |
| 10 | [`774933340`](https://github.com/michel-giehl/ValorantReplayParser/commit/774933340649fa37fabb39f56e57e565f269e217) | feat: add Iso and remaining agent ability descriptors | 2026-10-15 |
| 11 | [`e028d95d7`](https://github.com/michel-giehl/ValorantReplayParser/commit/e028d95d7e7803646ba9bec6b5c3b59efb02ba6a) | feat: add more descriptors | 2026-10-15 |
| 12 | [`8ec6f1fef`](https://github.com/michel-giehl/ValorantReplayParser/commit/8ec6f1fef9947c571d57527d0e1cbc81a325f70d) | refactor: centralize field binding compilation | 2026-10-15 |
| 13 | [`041dd35b9`](https://github.com/michel-giehl/ValorantReplayParser/commit/041dd35b93462e7003a3f2071dc24cd3ab850fe7) | Merge pull request #10 from michel-giehl/codex/field-binding-compilation | 2026-10-15 |
| 14 | [`756e8af5e`](https://github.com/michel-giehl/ValorantReplayParser/commit/756e8af5ee7d7b07277a571da37940116268892a) | chore: code quality fixes | 2026-10-15 |
| 15 | [`3188fbb3d`](https://github.com/michel-giehl/ValorantReplayParser/commit/3188fbb3db978492ff2d882b11691763b6ede691) | Merge branch 'feat/ability-descriptor-coverage' | 2026-10-15 |
| 16 | [`0d6ed7704`](https://github.com/michel-giehl/ValorantReplayParser/commit/0d6ed7704e7945cd83a1b92831b0f61d114f0341) | quality: remove unused usings | 2026-10-15 |
| 17 | [`71e90cd7b`](https://github.com/michel-giehl/ValorantReplayParser/commit/71e90cd7baec043eb529d1ba00e5a6ab39b954f6) | code quality: fix namespaces | 2026-10-15 |
| 18 | [`9f2bfcc2f`](https://github.com/michel-giehl/ValorantReplayParser/commit/9f2bfcc2f8e50b366fbfb1ca575e56f1cb7d431e) | fix: fix imports in NetGuidCacheReader | 2026-10-15 |
| 19 | [`2b5959215`](https://github.com/michel-giehl/ValorantReplayParser/commit/2b5959215119533e61975f4b566c0ed52dc718cc) | code quality: remove redundant code | 2026-10-15 |
| 20 | [`234f2917d`](https://github.com/michel-giehl/ValorantReplayParser/commit/234f2917d7cf9ae4341adff385119b78872f1c04) | fix: fix disposable scopes, remove unused tests | 2026-10-15 |
| 21 | [`b77b0ab66`](https://github.com/michel-giehl/ValorantReplayParser/commit/b77b0ab66e78e2fe68495d95e4c6da4ad25f2447) | feat: add missing property to ChildDamageSectionComponent | 2026-10-15 |
| 22 | [`486603e88`](https://github.com/michel-giehl/ValorantReplayParser/commit/486603e88e58439e74c6bb06a4b2014bc1afe043) | fix: fix types not being nullable and readd null check | 2026-10-15 |
| 23 | [`d2bb59e22`](https://github.com/michel-giehl/ValorantReplayParser/commit/d2bb59e2265ec0d48a20271704ccc1d5f9ece84f) | feat: register state machine subobjects | 2026-10-15 |
| 24 | [`f3c8e15a5`](https://github.com/michel-giehl/ValorantReplayParser/commit/f3c8e15a541fd0c7fc6d9d15f1a3d15d0136d54c) | feat: add effect container to shots | 2026-10-15 |
| 25 | [`b8f85ce08`](https://github.com/michel-giehl/ValorantReplayParser/commit/b8f85ce083b517034b9ebff8564e8be6682fd945) | Merge pull request #12 from Ka1serM/feat/shot-effect-container | 2026-10-16 |
| 26 | [`272517e14`](https://github.com/michel-giehl/ValorantReplayParser/commit/272517e145f9cc4bc4000b9a42fbf8129f8d92aa) | Merge pull request #11 from Ka1serM/feat/state-machine-subobjects | 2026-10-16 |
| 27 | [`ef3500630`](https://github.com/michel-giehl/ValorantReplayParser/commit/ef3500630c8e33a38472cadfe4eac91c422cbbc6) | chore: delete useless docs | 2026-10-16 |
| 28 | [`685e0d897`](https://github.com/michel-giehl/ValorantReplayParser/commit/685e0d8970a34b12535661dc48f4aaa42bbabf02) | feat: add missing ability descriptors | 2026-10-16 |
| 29 | [`17884cde7`](https://github.com/michel-giehl/ValorantReplayParser/commit/17884cde7aa3aa547e0a05cf33ce2a31435cf235) | feat: resolve object references to full paths | 2026-10-16 |
| 30 | [`68c2bdd44`](https://github.com/michel-giehl/ValorantReplayParser/commit/68c2bdd44274c9890fa34e388fb5ab46074a3a3a) | feat: decode Fade trails and Breach Fault Line | 2026-10-16 |
| 31 | [`2a96cad2f`](https://github.com/michel-giehl/ValorantReplayParser/commit/2a96cad2f312692e77da27310dcf5b8d072ca95f) | feat: emit native net GUID export events | 2026-10-16 |
| 32 | [`c4dd1d650`](https://github.com/michel-giehl/ValorantReplayParser/commit/c4dd1d650654de99000f931c126b47b26976ebed) | refactor!: separate gameplay event enrichment from the parser | 2026-10-16 |
| 33 | [`2839b3a9d`](https://github.com/michel-giehl/ValorantReplayParser/commit/2839b3a9dbecfac970074f7337d52d95ac977c0c) | Merge main and address object-reference review findings | 2026-10-16 |
| 34 | [`28e24af44`](https://github.com/michel-giehl/ValorantReplayParser/commit/28e24af44f5d2e2444fb679f500b6ec04ab60672) | Merge pull request #14 from Ka1serM/feat/net-object-reference | 2026-10-16 |
| 35 | [`c30718160`](https://github.com/michel-giehl/ValorantReplayParser/commit/c30718160cca7cec84dd28717bbbe87752a661c9) | feat: add waylay descriptors | 2026-10-16 |
| 36 | [`4ee26a3ed`](https://github.com/michel-giehl/ValorantReplayParser/commit/4ee26a3ed6bfabf03d78b4c454e5e81e89c17939) | feat: ground volume stuff for brim molly | 2026-10-17 |
| 37 | [`285636774`](https://github.com/michel-giehl/ValorantReplayParser/commit/285636774ed7727d590f3f6e3b0741946dbc9642) | feat: decode locational one-shot effects | 2026-10-20 |
| 38 | [`bb02014fb`](https://github.com/michel-giehl/ValorantReplayParser/commit/bb02014fbcdbb94d21e69b6577b38d34c715fb6c) | feat: emit footstep and jump events | 2026-10-21 |
| 39 | [`1134bf977`](https://github.com/michel-giehl/ValorantReplayParser/commit/1134bf9775dae5502f9fe23a6fa2fd54208d4765) | feat: decode spike state and plant and defuse attempts | 2026-10-21 |
| 40 | [`90d75dec9`](https://github.com/michel-giehl/ValorantReplayParser/commit/90d75dec9d41033d276915808999bab61c796d04) | Merge pull request #15 from 33k0/feat/locational-effects | 2026-10-21 |
| 41 | [`0b9b828e3`](https://github.com/michel-giehl/ValorantReplayParser/commit/0b9b828e3cc42a8e79749fc2ce937d6727aa287c) | Merge pull request #16 from 33k0/feat/spike-state | 2026-10-21 |
| 42 | [`ebef830d6`](https://github.com/michel-giehl/ValorantReplayParser/commit/ebef830d6b0e30b078c3ee70cfc269f9fc65ed8e) | Merge pull request #17 from 33k0/feat/footstep-events | 2026-10-21 |
| 43 | [`95f3268fd`](https://github.com/michel-giehl/ValorantReplayParser/commit/95f3268fd0c3c097bd858aee458a316164496e01) | feat: decode zoom state | 2026-10-21 |
| 44 | [`d1f642cc0`](https://github.com/michel-giehl/ValorantReplayParser/commit/d1f642cc0348bd269e0aaed75fd5a511accd2eba) | feat: decode item pickups and comm pings on agent caches | 2026-10-21 |
| 45 | [`7234e6a26`](https://github.com/michel-giehl/ValorantReplayParser/commit/7234e6a26cae35f7410e5f66cfce9ae70e4f627a) | Merge pull request #18 from 33k0/feat/zoom-state | 2026-10-23 |
| 46 | [`78e264bcb`](https://github.com/michel-giehl/ValorantReplayParser/commit/78e264bcb63898b5a444cbe4bdd6e8ac3205f30d) | Merge pull request #19 from 33k0/feat/agent-pickups-and-pings | 2026-10-23 |
| 47 | [`85df154a7`](https://github.com/michel-giehl/ValorantReplayParser/commit/85df154a78b17a2ac53e614fcd7d46c2718675bf) | feat: decode BombPlayerState ping | 2026-10-24 |
| 48 | [`7f8cf5939`](https://github.com/michel-giehl/ValorantReplayParser/commit/7f8cf593944a741f9868777906aa6ba1fa7b9c33) | quality: remove unnecessary comment | 2026-10-24 |
| 49 | [`d6649b0df`](https://github.com/michel-giehl/ValorantReplayParser/commit/d6649b0df26c965ce514e12450f67f77925a0a27) | Merge remote-tracking branch 'origin/main' | 2026-10-24 |
| 50 | [`cb5a33bf1`](https://github.com/michel-giehl/ValorantReplayParser/commit/cb5a33bf129743d1cd08507b4c6b48a511ab1f4f) | fix: name the Bandit and match the Guardian's wire class path | 2026-10-26 |
| 51 | [`266c2986a`](https://github.com/michel-giehl/ValorantReplayParser/commit/266c2986a4287ed31f0535706da2d8b98329fae6) | feat: decode gun actor cosmetics | 2026-10-26 |
| 52 | [`e169d746e`](https://github.com/michel-giehl/ValorantReplayParser/commit/e169d746ec9f24ba6ec63bad0ffbc469ac31db5c) | feat: name Neon's Overdrive gun | 2026-10-26 |
| 53 | [`f7f048360`](https://github.com/michel-giehl/ValorantReplayParser/commit/f7f048360fc3ba8f9ea06b63f0cb9a0681150b91) | fix: configure shared descriptors under a lock | 2026-10-26 |
| 54 | [`fe99a6f1d`](https://github.com/michel-giehl/ValorantReplayParser/commit/fe99a6f1dc4047e3cef2878fe53f9668d1c8f850) | Merge pull request #20 from michel-giehl/viewer-completion | 2026-10-26 |
| 55 | [`d20afc6fa`](https://github.com/michel-giehl/ValorantReplayParser/commit/d20afc6fae16faa24ace85d21eacc0d0445153f4) | feat: support release 13.09 and decode Hush | 2026-10-27 |
| 56 | [`09a8e1e1d`](https://github.com/michel-giehl/ValorantReplayParser/commit/09a8e1e1d81c48840b8810f523f1595e539b7d55) | Merge pull request #21 from michel-giehl/release-13.09-hush | 2026-10-27 |

## Complete final-state changed-path inventory (377)

`A` = added, `M` = modified, `D` = removed relative to the previous reference. Git blob-tree hashes, not API compare's 300-file listing, were used.

```text
M  .github/workflows/build.yml
M  .github/workflows/release-candidate.yml
A  .sonarcloud.properties
A  CHANGELOG.md
M  README.md
A  THIRD-PARTY-NOTICES.md
M  ValorantReplayParser.sln
M  build/LibraryPackage.props
M  build/Test-Packages.ps1
D  docs/public-nuget-release-plan.md
D  docs/sonar-triage.md
M  src/CliReader/ActorEventLogger.cs
M  src/CliReader/CliApplication.cs
M  src/CliReader/CliReader.csproj
M  src/CliReader/JsonExport/ReplayEventJsonWriter.cs
M  src/CliReader/JsonExport/ReplayExportManifestWriter.cs
M  src/CliReader/JsonExport/ReplayExportRunner.cs
M  src/CliReader/JsonExport/ReplayExportSink.cs
M  src/CliReader/JsonExport/ReplayExportStatistics.cs
M  src/CliReader/JsonExport/ReplayJsonNormalizer.cs
D  src/CliReader/Logging/SerilogLoggerProvider.cs
M  src/CliReader/Properties/AssemblyInfo.cs
M  src/CliReader/ReplayLogRunner.cs
D  src/NetGuidCacheReader/Logging/SerilogLoggerProvider.cs
M  src/NetGuidCacheReader/NetGuidCacheReader.csproj
M  src/NetGuidCacheReader/Program.cs
M  src/Replay.Encoding/Archives/ArchiveErrorCode.cs
M  src/Replay.Encoding/Archives/ByteArchiveReader.cs
M  src/Replay.Encoding/Net/NetGuidCache.cs
M  src/Replay.Encoding/PayloadEncryption/PayloadTransformRegistry.cs
M  src/Replay.Encoding/PayloadEncryption/ValorantSeededTransformHelpers.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform11_06.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform11_07.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform11_08.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform11_09.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform11_10.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform11_11.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform12_00.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform12_01.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform12_02.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform12_03.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform12_04.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform12_05.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform12_06.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform12_07.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform12_08.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform12_09.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform13_08.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransform13_09.cs
A  src/Replay.Encoding/PayloadEncryption/VersionedTransforms/ValorantSeededTransformChina13_05.cs
M  src/Replay.Encoding/Replay.Encoding.csproj
M  src/Replay.Models/Descriptors/DecodedFieldValue.cs
M  src/Replay.Models/Descriptors/DecodedFieldValueKind.cs
M  src/Replay.Models/Descriptors/DescriptorConfiguration.cs
A  src/Replay.Models/Events/NetGuidExported.cs
A  src/Replay.Models/Net/NetObjectReference.cs
A  src/Replay.Models/Unreal/FHitResult.cs
M  src/Replay.Models/Unreal/FQuat.cs
M  src/Replay.Unreal/Bunches/Payload/BunchPayloadPipeline.cs
M  src/Replay.Unreal/Exports/ExportDataReader.cs
M  src/Replay.Unreal/PackageMap/NetGuidObjectReader.cs
M  src/Replay.Unreal/PackageMap/PackageMapReader.cs
M  src/Replay.Unreal/Packets/PlaybackPacketReader.cs
M  src/Replay.Unreal/Packets/RawPacketReader.cs
M  src/Replay.Unreal/Parsing/DecodedValueAssigner.cs
M  src/Replay.Unreal/Parsing/DescriptorBuilderDecoderExtensions.cs
A  src/Replay.Unreal/Parsing/FieldBindingCompiler.cs
M  src/Replay.Unreal/Parsing/FieldPayloadParser.cs
A  src/Replay.Unreal/Parsing/IRepLayoutCustomDeltaPayload.cs
M  src/Replay.Unreal/Parsing/PrimitiveDecoders.cs
M  src/Replay.Unreal/Parsing/RepLayoutArrayDecoders.cs
M  src/Replay.Unreal/Parsing/ReplayExportBinder.cs
M  src/Replay.Unreal/Readers/ReplayReaderContext.cs
A  src/Replay.Valorant.Events/Combat/ValorantEquippable.cs
A  src/Replay.Valorant.Events/Combat/ValorantEquippableCategory.cs
A  src/Replay.Valorant.Events/Combat/ValorantEquippableResolver.cs
A  src/Replay.Valorant.Events/Combat/ValorantShot.cs
A  src/Replay.Valorant.Events/Combat/ValorantShotEventEnricher.cs
A  src/Replay.Valorant.Events/Combat/ValorantShotFactory.cs
A  src/Replay.Valorant.Events/Combat/ValorantShotReceived.cs
A  src/Replay.Valorant.Events/Flashes/ValorantFlashEventEnricher.cs
A  src/Replay.Valorant.Events/Flashes/ValorantFlashEvents.cs
A  src/Replay.Valorant.Events/Footsteps/ValorantFootstepEventEnricher.cs
A  src/Replay.Valorant.Events/Footsteps/ValorantFootstepEvents.cs
A  src/Replay.Valorant.Events/Movement/RemoteCharacterMovementReceived.cs
A  src/Replay.Valorant.Events/Movement/ValorantMovementEventEnricher.cs
A  src/Replay.Valorant.Events/Nearsights/ValorantNearsightEventEnricher.cs
A  src/Replay.Valorant.Events/Nearsights/ValorantNearsightEvents.cs
A  src/Replay.Valorant.Events/PlayerIdentityTracker.cs
A  src/Replay.Valorant.Events/Replay.Valorant.Events.csproj
A  src/Replay.Valorant.Events/ValorantEventEnricher.cs
A  src/Replay.Valorant.Events/Walls/ValorantWallEventEnricher.cs
A  src/Replay.Valorant.Events/Walls/ValorantWallEvents.cs
A  src/Replay.Valorant/Combat/DamageAssist.cs
A  src/Replay.Valorant/Combat/DamageLifeChangeEvent.cs
M  src/Replay.Valorant/Combat/DamageParameters.cs
M  src/Replay.Valorant/Combat/DamageableComponentClassNetCacheDescriptor.cs
A  src/Replay.Valorant/Combat/LifeChangeRpcParameters.cs
M  src/Replay.Valorant/Combat/MulticastNotifyDamageBaseParameters.cs
M  src/Replay.Valorant/Combat/MulticastNotifyDamagePointParameters.cs
M  src/Replay.Valorant/Combat/MulticastNotifyKilledEnemyParameters.cs
A  src/Replay.Valorant/Combat/PointDamageParameters.cs
D  src/Replay.Valorant/Combat/ValorantEquippable.cs
D  src/Replay.Valorant/Combat/ValorantEquippableCategory.cs
D  src/Replay.Valorant/Combat/ValorantEquippableResolver.cs
D  src/Replay.Valorant/Combat/ValorantShot.cs
D  src/Replay.Valorant/Combat/ValorantShotEventEnricher.cs
D  src/Replay.Valorant/Combat/ValorantShotReceived.cs
A  src/Replay.Valorant/Descriptors/Agents/AbilityActorDescriptor.cs
A  src/Replay.Valorant/Descriptors/Agents/AbilityDescriptorRegistration.cs
A  src/Replay.Valorant/Descriptors/Agents/AbilityObjectParameters.cs
A  src/Replay.Valorant/Descriptors/Agents/AbilityProjectileDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/AgentClassNetCacheDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Aggrobot/AggrobotAgentDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Aggrobot/AggrobotDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/BountyHunter/BountyHunterDescriptors.cs
A  src/Replay.Valorant/Descriptors/Agents/BountyHunter/FadeTrailDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Breach/BreachDescriptors.cs
A  src/Replay.Valorant/Descriptors/Agents/Breach/BreachFaultLineChargeParameters.cs
A  src/Replay.Valorant/Descriptors/Agents/Breach/BreachFaultLineDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Cable/CableDescriptors.cs
A  src/Replay.Valorant/Descriptors/Agents/Cable/CableGeometryParameters.cs
M  src/Replay.Valorant/Descriptors/Agents/Cashew/CashewDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Clay/ClayAbilityDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Clay/ClayAgentDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Clay/RazeForceParameters.cs
A  src/Replay.Valorant/Descriptors/Agents/Deadeye/ChamberPresenceDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Deadeye/DeadeyeDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/GenericAgentDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Grenadier/GrenadierDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Guide/GuideDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Gumshoe/CageTrapAbilityDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Gumshoe/CageTrapProjectileDescriptor.cs
A  src/Replay.Valorant/Descriptors/Agents/Gumshoe/GumshoeAbilityDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Gumshoe/GumshoeDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Gumshoe/SecondTripWireGameObjectDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Gumshoe/TripWireAbilityDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Gumshoe/TripWireGameObjectDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Hunter/HunterDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Iris/IrisDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Killjoy/KilljoyDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Mage/CoveAbilityDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Mage/MageDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Mage/MageWallDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Mage/TidalWave/TidalWaveExportDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Mage/TidalWave/TidalWaveRpcParameters.cs
M  src/Replay.Valorant/Descriptors/Agents/Nox/NoxDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Pandemic/PandemicDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Pandemic/SmokeScreen/MulticastAddSmokeScreenPointParameters.cs
M  src/Replay.Valorant/Descriptors/Agents/Pandemic/SmokeScreen/ProjectileSmokeScreenDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Pandemic/SmokeScreen/SmokeScreenManagerDescriptor.cs
A  src/Replay.Valorant/Descriptors/Agents/Pandemic/SnakeBiteDescriptors.cs
A  src/Replay.Valorant/Descriptors/Agents/Pandemic/ViperPitDescriptors.cs
A  src/Replay.Valorant/Descriptors/Agents/Paprika/PaprikaAgentDescriptor.cs
A  src/Replay.Valorant/Descriptors/Agents/Paprika/PaprikaComponentDescriptors.cs
A  src/Replay.Valorant/Descriptors/Agents/Paprika/PaprikaDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Phoenix/FlameWallDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Phoenix/PhoenixDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Pine/PineDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Rift/RiftDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Sarge/SargeDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Sequoia/SequoiaDescriptors.cs
A  src/Replay.Valorant/Descriptors/Agents/Sequoia/SequoiaTeleportContextDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Smonk/SmonkDescriptors.cs
A  src/Replay.Valorant/Descriptors/Agents/SparseAbilityProjectileDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Sprinter/NeonTunnelDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Sprinter/SprinterDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Stealth/StealthDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Terra/TerraDescriptors.cs
A  src/Replay.Valorant/Descriptors/Agents/Terra/WaylayRewindPathPointDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Thorne/ThorneDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Vampire/VampireDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Wraith/DarkCoverAbilityDescriptor.cs
M  src/Replay.Valorant/Descriptors/Agents/Wraith/WraithDescriptors.cs
M  src/Replay.Valorant/Descriptors/Agents/Wushu/WushuDescriptors.cs
M  src/Replay.Valorant/Descriptors/AresAbilitySystemComponentDescriptor.cs
M  src/Replay.Valorant/Descriptors/BaseReplayControllerDescriptor.cs
M  src/Replay.Valorant/Descriptors/BaseReplayPlayerState.cs
A  src/Replay.Valorant/Descriptors/ControllablePawnDescriptor.cs
A  src/Replay.Valorant/Descriptors/DynamicVolume/GroundVolumeClassNetCacheDescriptor.cs
A  src/Replay.Valorant/Descriptors/DynamicVolume/GroundVolumeComponentDescriptor.cs
A  src/Replay.Valorant/Descriptors/Effects/Locational/LocationalEffectDescriptors.cs
M  src/Replay.Valorant/Descriptors/Effects/Replay/EffectDataObject.cs
M  src/Replay.Valorant/Descriptors/Effects/Replay/ReplayPlayContinuousEffectAtLocationParameters.cs
A  src/Replay.Valorant/Descriptors/ObfuscatedPlayerInformation.cs
M  src/Replay.Valorant/Descriptors/OwnerExclusivePlayerInfoDescriptor.cs
A  src/Replay.Valorant/Descriptors/Patches/CellularPatchNodeGridParameters.cs
A  src/Replay.Valorant/Descriptors/PhoenixPresenceDescriptor.cs
M  src/Replay.Valorant/Descriptors/RemoteCharacterUpdateDescriptor.cs
A  src/Replay.Valorant/Descriptors/ReplicatedObjectReference.cs
A  src/Replay.Valorant/Descriptors/RiotUniqueNetId.cs
M  src/Replay.Valorant/Descriptors/SmokeAbilityDescriptor.cs
M  src/Replay.Valorant/Descriptors/ValorantDescriptors.cs
M  src/Replay.Valorant/Descriptors/ValorantPathAliasProvider.cs
M  src/Replay.Valorant/Descriptors/ValorantPayloadDecoders.cs
A  src/Replay.Valorant/Economy/GunRequestDescriptors.cs
A  src/Replay.Valorant/Economy/MoneyManagementComponentDescriptor.cs
M  src/Replay.Valorant/Flashes/Descriptors/BlindManagerComponentDescriptor.cs
D  src/Replay.Valorant/Flashes/Descriptors/BreachFlashExitLocationDecoder.cs
A  src/Replay.Valorant/Flashes/Descriptors/BreachFlashHitResultDecoder.cs
M  src/Replay.Valorant/Flashes/Descriptors/EffectManagerComponentDescriptors.cs
M  src/Replay.Valorant/Flashes/Descriptors/EffectManagerRpcDescriptors.cs
M  src/Replay.Valorant/Flashes/Descriptors/EffectManagerValueDescriptors.cs
M  src/Replay.Valorant/Flashes/Descriptors/FlashPaths.cs
M  src/Replay.Valorant/Flashes/Descriptors/FlashProjectileDescriptors.cs
M  src/Replay.Valorant/Flashes/Descriptors/SkyeFlashSourceDescriptors.cs
D  src/Replay.Valorant/Flashes/ValorantFlashEventEnricher.cs
D  src/Replay.Valorant/Flashes/ValorantFlashEvents.cs
M  src/Replay.Valorant/GameState/AbilityCooldownComponentDescriptor.cs
M  src/Replay.Valorant/GameState/AresInventoryDescriptor.cs
M  src/Replay.Valorant/GameState/AresPlayerRoundInfo.cs
M  src/Replay.Valorant/GameState/AresRoundResults.cs
M  src/Replay.Valorant/GameState/AresTeamEconomy.cs
A  src/Replay.Valorant/GameState/AresTeamRoundResult.cs
M  src/Replay.Valorant/GameState/ArmorItemDescriptor.cs
M  src/Replay.Valorant/GameState/BombCombatReportComponentDescriptor.cs
M  src/Replay.Valorant/GameState/BombGameStateDescriptor.cs
M  src/Replay.Valorant/GameState/BombObjectiveDescriptors.cs
M  src/Replay.Valorant/GameState/BombPlayerStateDescriptor.cs
M  src/Replay.Valorant/GameState/ChildDamageSectionComponentDescriptor.cs
M  src/Replay.Valorant/GameState/CombatRoundReports.cs
M  src/Replay.Valorant/GameState/DamageClassNetCacheDescriptors.cs
M  src/Replay.Valorant/GameState/EquippableStateMachineComponentDescriptor.cs
A  src/Replay.Valorant/GameState/GameplayResourceDescriptors.cs
M  src/Replay.Valorant/GameState/MulticastEndRoundParameters.cs
M  src/Replay.Valorant/GameState/MulticastEnterPlayspaceParameters.cs
M  src/Replay.Valorant/GameState/MulticastReceivePlayerResurrectEventParameters.cs
M  src/Replay.Valorant/GameState/MulticastReceivePlayerTemporaryDeathEventBaseParameters.cs
M  src/Replay.Valorant/GameState/MulticastReceivePlayerTemporaryDeathEventPointParameters.cs
M  src/Replay.Valorant/GameState/MulticastResetForRespawnParameters.cs
M  src/Replay.Valorant/GameState/OrbPickedUpRpcParameters.cs
A  src/Replay.Valorant/GameState/RoundParticipantsInfo.cs
A  src/Replay.Valorant/GameState/SpikePickupDescriptors.cs
A  src/Replay.Valorant/GameState/TimedBombDescriptor.cs
A  src/Replay.Valorant/GameState/UpdateHalosEventParameters.cs
M  src/Replay.Valorant/GameState/WingmanDescriptor.cs
A  src/Replay.Valorant/GameState/ZoomMultiplierComponentDescriptor.cs
A  src/Replay.Valorant/Inventory/EAresItemSlot.cs
A  src/Replay.Valorant/Inventory/EInventoryTransaction.cs
A  src/Replay.Valorant/Inventory/GunActorDescriptor.cs
A  src/Replay.Valorant/Inventory/ItemSlotContentsUpdate.cs
A  src/Replay.Valorant/Inventory/ItemSlotDescriptors.cs
A  src/Replay.Valorant/Inventory/MulticastItemPickedUpParameters.cs
A  src/Replay.Valorant/Inventory/PurchasedItemComponentDescriptor.cs
A  src/Replay.Valorant/MapDoors/MapDoorDescriptors.cs
M  src/Replay.Valorant/Movement/ComponentDataStream.cs
D  src/Replay.Valorant/Movement/RemoteCharacterMovementReceived.cs
M  src/Replay.Valorant/Movement/RemoteCharacterUpdateBatch.cs
M  src/Replay.Valorant/Movement/RemoteCharacterUpdatesRpcDecoder.cs
M  src/Replay.Valorant/Nearsights/Descriptors/NearsightDescriptors.cs
D  src/Replay.Valorant/Nearsights/ValorantNearsightEventEnricher.cs
D  src/Replay.Valorant/Nearsights/ValorantNearsightEvents.cs
M  src/Replay.Valorant/Replay.Valorant.csproj
M  src/Replay.Valorant/Reveals/Descriptors/RevealDescriptors.cs
M  src/Replay.Valorant/Smokes/Descriptors/SmokeDescriptors.cs
M  src/Replay.Valorant/ValorantReleaseVersionParser.cs
M  src/Replay.Valorant/ValorantReplayReader.cs
M  src/Replay.Valorant/Walls/Descriptors/WallDescriptors.cs
D  src/Replay.Valorant/Walls/ValorantWallEventEnricher.cs
D  src/Replay.Valorant/Walls/ValorantWallEvents.cs
A  src/Tools.Shared/Logging/SerilogLoggerProvider.cs
M  tests/PackageConsumerSmoke/PackageConsumerSmoke.csproj
M  tests/PackageConsumerSmoke/Program.cs
M  tests/Replay.Encoding.Tests/Net/NetGuidCacheTests.cs
A  tests/Replay.Encoding.Tests/PayloadEncryption/ValorantLegacyTransformTests.Vectors.cs
A  tests/Replay.Encoding.Tests/PayloadEncryption/ValorantLegacyTransformTests.cs
A  tests/Replay.Encoding.Tests/PayloadEncryption/ValorantSeededTransform13_08Tests.cs
M  tests/Replay.Encoding.Tests/PayloadEncryption/ValorantSeededTransformTests.cs
M  tests/Replay.Unreal.Tests/Bunches/BunchPayloadErrorLoggingTests.cs
M  tests/Replay.Unreal.Tests/Bunches/BunchPayloadPipelineTests.cs
M  tests/Replay.Unreal.Tests/Bunches/PartialBunchAccumulatorTests.cs
M  tests/Replay.Unreal.Tests/Exports/ExportDataReaderTests.cs
A  tests/Replay.Unreal.Tests/Fixtures/ViperPit/README.md
A  tests/Replay.Unreal.Tests/Fixtures/ViperPit/packet-2069.bin
A  tests/Replay.Unreal.Tests/Fixtures/ViperPit/packet-2070.bin
A  tests/Replay.Unreal.Tests/Fixtures/ViperPit/packet-2071.bin
A  tests/Replay.Unreal.Tests/Fixtures/ViperPit/packet-2072.bin
A  tests/Replay.Unreal.Tests/Fixtures/ViperPit/packet-2073.bin
A  tests/Replay.Unreal.Tests/Fixtures/ViperPit/packet-2074.bin
A  tests/Replay.Unreal.Tests/Fixtures/ViperPit/packet-2075.bin
A  tests/Replay.Unreal.Tests/Fixtures/ViperPit/packet-2076.bin
A  tests/Replay.Unreal.Tests/Fixtures/ViperPit/packet-2077.bin
A  tests/Replay.Unreal.Tests/Fixtures/ViperPit/packet-2078.bin
M  tests/Replay.Unreal.Tests/Packets/RawPacketReaderTests.cs
A  tests/Replay.Unreal.Tests/Packets/ViperPitPacketTests.cs
M  tests/Replay.Unreal.Tests/Parsing/FieldPayloadParserTests.cs
M  tests/Replay.Unreal.Tests/Parsing/PrimitiveDecodersScalarTests.cs
M  tests/Replay.Unreal.Tests/Parsing/PrimitiveDecodersVectorTests.cs
M  tests/Replay.Unreal.Tests/Parsing/ReleaseAwareDescriptorTests.cs
M  tests/Replay.Unreal.Tests/Parsing/RepLayoutArrayDecodersTests.cs
M  tests/Replay.Unreal.Tests/Replay.Unreal.Tests.csproj
A  tests/Replay.Valorant.Events.Tests/Combat/ValorantEquippableTests.cs
A  tests/Replay.Valorant.Events.Tests/Combat/ValorantShotEventEnricherTests.cs
A  tests/Replay.Valorant.Events.Tests/Combat/ValorantShotFactoryTests.cs
A  tests/Replay.Valorant.Events.Tests/Export/CliCommandTests.cs
A  tests/Replay.Valorant.Events.Tests/Export/ReplayExportTests.cs
A  tests/Replay.Valorant.Events.Tests/Flashes/ValorantFlashEventEnricherTests.cs
A  tests/Replay.Valorant.Events.Tests/Footsteps/ValorantFootstepEventEnricherTests.cs
A  tests/Replay.Valorant.Events.Tests/Nearsights/ValorantNearsightEventEnricherTests.cs
A  tests/Replay.Valorant.Events.Tests/Replay.Valorant.Events.Tests.csproj
A  tests/Replay.Valorant.Events.Tests/ValorantEventEnricherTests.cs
A  tests/Replay.Valorant.Events.Tests/Walls/ValorantWallEventEnricherTests.cs
A  tests/Replay.Valorant.Tests/Combat/DamageEquippableTests.cs
A  tests/Replay.Valorant.Tests/Combat/DamageLifeChangeEventTests.cs
A  tests/Replay.Valorant.Tests/Combat/LifeChangeRpcDecodingTests.cs
D  tests/Replay.Valorant.Tests/Combat/ValorantEquippableTests.cs
D  tests/Replay.Valorant.Tests/Combat/ValorantShotEventEnricherTests.cs
M  tests/Replay.Valorant.Tests/Combat/ValorantShotTests.cs
A  tests/Replay.Valorant.Tests/Descriptors/AbilityDescriptorCoverageTests.cs
A  tests/Replay.Valorant.Tests/Descriptors/AbilityProjectileDescriptorTests.cs
A  tests/Replay.Valorant.Tests/Descriptors/AgentPickupAndCommDescriptorTests.cs
A  tests/Replay.Valorant.Tests/Descriptors/BreachChargeDescriptorTests.cs
A  tests/Replay.Valorant.Tests/Descriptors/BrimstoneGroundVolumeDescriptorTests.cs
A  tests/Replay.Valorant.Tests/Descriptors/CellularPatchDescriptorTests.cs
M  tests/Replay.Valorant.Tests/Descriptors/ClayDescriptorTests.cs
A  tests/Replay.Valorant.Tests/Descriptors/DescriptorCoveragePayloadTests.cs
A  tests/Replay.Valorant.Tests/Descriptors/FadeTrailDescriptorTests.cs
A  tests/Replay.Valorant.Tests/Descriptors/GroundVolumeDescriptorTests.cs
A  tests/Replay.Valorant.Tests/Descriptors/GumshoeDescriptorTests.cs
A  tests/Replay.Valorant.Tests/Descriptors/IsoDescriptorTests.cs
A  tests/Replay.Valorant.Tests/Descriptors/LocationalEffectDescriptorTests.cs
A  tests/Replay.Valorant.Tests/Descriptors/PaprikaDescriptorTests.cs
M  tests/Replay.Valorant.Tests/Descriptors/RpcExportBindingRegressionTests.cs
A  tests/Replay.Valorant.Tests/Descriptors/SentinelDescriptorTests.cs
A  tests/Replay.Valorant.Tests/Descriptors/SnakeBiteDescriptorTests.cs
A  tests/Replay.Valorant.Tests/Descriptors/TerraDescriptorTests.cs
M  tests/Replay.Valorant.Tests/Descriptors/ValorantDescriptorsTests.cs
A  tests/Replay.Valorant.Tests/Descriptors/ZoneOwnershipDescriptorTests.cs
A  tests/Replay.Valorant.Tests/Economy/EconomyDescriptorTests.cs
D  tests/Replay.Valorant.Tests/Export/CliCommandTests.cs
D  tests/Replay.Valorant.Tests/Export/ReplayExportTests.cs
A  tests/Replay.Valorant.Tests/Fixtures/Brimstone/fragment-0.bin
A  tests/Replay.Valorant.Tests/Fixtures/Brimstone/fragment-1.bin
A  tests/Replay.Valorant.Tests/Fixtures/CellularPatch/sage-node-grids.json
A  tests/Replay.Valorant.Tests/Fixtures/DescriptorCoverage/components.json
A  tests/Replay.Valorant.Tests/Fixtures/DescriptorCoverage/fields.json
A  tests/Replay.Valorant.Tests/Fixtures/ViperPit/cast-1.bin
A  tests/Replay.Valorant.Tests/Fixtures/ViperPit/cast-2.bin
A  tests/Replay.Valorant.Tests/Fixtures/ViperPit/cast-3.bin
A  tests/Replay.Valorant.Tests/Fixtures/ViperPit/cast-4.bin
A  tests/Replay.Valorant.Tests/Fixtures/ViperPit/cast-5.bin
A  tests/Replay.Valorant.Tests/Fixtures/ViperPit/cast-6.bin
A  tests/Replay.Valorant.Tests/Fixtures/ViperPit/cast-7.bin
A  tests/Replay.Valorant.Tests/Fixtures/ViperPit/cast-8.bin
M  tests/Replay.Valorant.Tests/Flashes/BreachFlashExitLocationDecoderTests.cs
D  tests/Replay.Valorant.Tests/Flashes/ValorantFlashEventEnricherTests.cs
M  tests/Replay.Valorant.Tests/GameState/AresPlayerRoundInfoDecoderTests.cs
M  tests/Replay.Valorant.Tests/GameState/AresRoundResultsDecoderTests.cs
M  tests/Replay.Valorant.Tests/GameState/BombPlayerStateUltimateTests.cs
M  tests/Replay.Valorant.Tests/GameState/CombatRoundReportsDecoderTests.cs
A  tests/Replay.Valorant.Tests/GameState/DamageSectionDescriptorTests.cs
A  tests/Replay.Valorant.Tests/GameState/SpikeDescriptorTests.cs
A  tests/Replay.Valorant.Tests/GameState/TimedBombDescriptorTests.cs
M  tests/Replay.Valorant.Tests/GameState/UltimateObjectiveDescriptorTests.cs
M  tests/Replay.Valorant.Tests/GameState/WingmanDescriptorTests.cs
A  tests/Replay.Valorant.Tests/GameState/ZoomMultiplierComponentDescriptorTests.cs
A  tests/Replay.Valorant.Tests/Inventory/GameplayResourceDescriptorTests.cs
A  tests/Replay.Valorant.Tests/Inventory/GunActorDescriptorTests.cs
A  tests/Replay.Valorant.Tests/Inventory/InventoryDescriptorTests.cs
A  tests/Replay.Valorant.Tests/MapDoors/MapDoorDescriptorTests.cs
M  tests/Replay.Valorant.Tests/Movement/RemoteCharacterMovementTests.cs
D  tests/Replay.Valorant.Tests/Nearsights/ValorantNearsightEventEnricherTests.cs
M  tests/Replay.Valorant.Tests/Replay.Valorant.Tests.csproj
A  tests/Replay.Valorant.Tests/TestReleases.cs
M  tests/Replay.Valorant.Tests/ValorantReleaseVersionParserTests.cs
M  tests/Replay.Valorant.Tests/ValorantReplayReaderTests.cs
D  tests/Replay.Valorant.Tests/Walls/ValorantWallEventEnricherTests.cs
M  tests/Test.Integration/FlashLifecycleIntegrationTests.cs
M  tests/Test.Integration/HarborAbilityTests.cs
A  tests/Test.Integration/InventoryEconomyIntegrationTests.cs
M  tests/Test.Integration/NearsightLifecycleIntegrationTests.cs
M  tests/Test.Integration/OmenAbilityTests.cs
M  tests/Test.Integration/ReplayReaderIntegrationTests.cs
M  tests/Test.Integration/Test.Integration.csproj
M  tests/Test.Integration/WallLifecycleIntegrationTests.cs
A  third-party/ValCoach-LICENSE
A  third-party/vrfkit-LICENSE
```
