## 1.31.4 - 2026-01-24
### Extractors
#### Additions
- [kaliscan] add support ([#8917](https://github.com/mikf/gallery-dl/issues/8917))
- [turbo] add support - rewrite `saint` extractors ([#8893](https://github.com/mikf/gallery-dl/issues/8893) [#8896](https://github.com/mikf/gallery-dl/issues/8896))
- [xenforo] support `celebforum.to` ([#8902](https://github.com/mikf/gallery-dl/issues/8902))
- [xenforo] add `media-album` extractor ([#8902](https://github.com/mikf/gallery-dl/issues/8902))
#### Fixes
- [mangafire] fix extractors - generate `vrf` tokens ([#8400](https://github.com/mikf/gallery-dl/issues/8400) [#8906](https://github.com/mikf/gallery-dl/issues/8906))
- [nitter] use `gallery-dl/<version>` User-Agent ([#7045](https://github.com/mikf/gallery-dl/issues/7045) [#8130](https://github.com/mikf/gallery-dl/issues/8130) [#8409](https://github.com/mikf/gallery-dl/issues/8409))
- [tiktok] fix `following` extractor ([#8849](https://github.com/mikf/gallery-dl/issues/8849))
- [xenforo] fix using cookies for custom instances ([#8902](https://github.com/mikf/gallery-dl/issues/8902))
#### Improvements
- [imagebam] raise `NotFoundError` for deleted images & galleries ([#8890](https://github.com/mikf/gallery-dl/issues/8890))
- [kemono:discord] improve `filename` parsing
- [kemono:discord] support server URLs with trailing `/`
- [tiktok] download best quality videos ([#8846](https://github.com/mikf/gallery-dl/issues/8846))
- [tiktok] prefer `legacy` endpoint for user post extraction ([#8812](https://github.com/mikf/gallery-dl/issues/8812) [#8847](https://github.com/mikf/gallery-dl/issues/8847))
- [twitter] implement `"ratelimit": "abort:N"` ([#5251](https://github.com/mikf/gallery-dl/issues/5251) [#8864](https://github.com/mikf/gallery-dl/issues/8864))
- [weebdex] add `data-saver` option ([#8914](https://github.com/mikf/gallery-dl/issues/8914))
- [xenforo] ignore links starting with `#`
#### Metadata
- [kemono:discord] extract `archives` metadata ([#8898](https://github.com/mikf/gallery-dl/issues/8898))
- [xenforo:media-album] extract `album` metadata ([#8902](https://github.com/mikf/gallery-dl/issues/8902))
#### Removals
- [batoto] remove module ([#8834](https://github.com/mikf/gallery-dl/issues/8834) [#8908](https://github.com/mikf/gallery-dl/issues/8908))
### Miscellaneous
- [common] implement `parent-session` option
- [common] add `googlebot` User-Agent preset
- [docker] build from `python:3.14-alpine`
- [release] add more checks before committing a release
- [util] replace classes with functions for predicates, Popen, HTTPBasicAuth
