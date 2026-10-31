# vrfkit

Copyright 2026 vrfkit contributors

Licensed under the Apache License, Version 2.0; see [`LICENSE`](LICENSE).

## Earlier MIT-licensed releases

Releases up to and including v0.2.0 were published under the MIT License, and
contributions made before the change to Apache-2.0 were made under it. The MIT
License allows that code to be distributed under other terms as long as its
notice stays with it, so the notice is kept here:

```
MIT License

Copyright (c) 2026 vrfkit contributors

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

# Third-party notices

Parts of vrfkit are derived from ValorantReplayParser, used under the MIT
License:

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

# Disclaimer

This project is an independent, community-developed tool and is not affiliated
with, endorsed by, sponsored by, or approved by Riot Games. VALORANT, Riot Games,
and all related trademarks are the property of Riot Games, Inc.


## BakaFT China regional contributions

The China 13.02, 13.04 and 13.05 transforms, the independent Python oracle,
recovery helper and validation-only transform probe derive from
[BakaFT/vrfkit](https://github.com/BakaFT/vrfkit), including commit
`36c0bcfd0393f8831cc879bfb671503b287bd127`, under MIT terms preserved in
[CHINA_LICENSE.txt](CHINA_LICENSE.txt). They have been adapted to the v0.4.0
registry and shared decode pass; the main upstream Apache-2.0 license is
unchanged.

China 13.02's 64-bit lane and constants trace to the MIT-licensed
[LeagueTavern/ValorantReplayParser](https://github.com/LeagueTavern/ValorantReplayParser)
China branch. BakaFT supplied the working 32-bit and byte lanes. China 13.04
and 13.05 were recovered from replay evidence, not copied from that parser.
China 13.08 and 13.09 derive from the replay recovery contributed in
[BakaFT/vrfkit#1](https://github.com/BakaFT/vrfkit/pull/1); their evidence and
independent oracle are retained. See
[regional bring-up](docs/CHINA_RELEASE_BRINGUP.md) for scope and method.

The regional contribution license is reproduced here so binary archives
(which include this notice) retain its terms:

```text
MIT License

Copyright (c) 2026 vrfkit contributors

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
