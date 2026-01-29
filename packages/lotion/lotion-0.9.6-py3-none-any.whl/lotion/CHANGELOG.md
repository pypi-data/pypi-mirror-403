# Changelog

## [0.9.6](https://github.com/koboriakira/python-lotion/compare/v0.9.5...v0.9.6) (2026-01-24)


### Features

* add file upload functionality via Notion API ([#82](https://github.com/koboriakira/python-lotion/issues/82)) ([9b34dca](https://github.com/koboriakira/python-lotion/commit/9b34dca4452737601900b9def21d129728402d09))
* add py.typed marker for PEP 561 compliance ([#80](https://github.com/koboriakira/python-lotion/issues/80)) ([f2e7d0c](https://github.com/koboriakira/python-lotion/commit/f2e7d0c4d6e7b55f49d5c49dc7bfc33e8a5a40f1))


### Bug Fixes

* handle Union types (X | None) in [@notion](https://github.com/notion)_database decorator ([#85](https://github.com/koboriakira/python-lotion/issues/85)) ([53dcedb](https://github.com/koboriakira/python-lotion/commit/53dcedb4d46fa663d5a79177c34e43d9f937940b))
* support internal page links using link.page_id ([#84](https://github.com/koboriakira/python-lotion/issues/84)) ([5950036](https://github.com/koboriakira/python-lotion/commit/5950036f9dfc95b629511125f546409a1144e514)), closes [#83](https://github.com/koboriakira/python-lotion/issues/83)

## [0.9.5](https://github.com/koboriakira/python-lotion/compare/v0.9.4...v0.9.5) (2026-01-07)


### Features

* upgrade notion client ([#75](https://github.com/koboriakira/python-lotion/issues/75)) ([b88013d](https://github.com/koboriakira/python-lotion/commit/b88013dfe342a9cfdfa19f951e8eed56ee6e4c94))

## [0.9.4](https://github.com/koboriakira/python-lotion/compare/v0.9.3...v0.9.4) (2025-01-15)


### Features

* link_mentionのリッチテキストを扱う ([#74](https://github.com/koboriakira/python-lotion/issues/74)) ([31144b3](https://github.com/koboriakira/python-lotion/commit/31144b310b01c7d428e1ae2e518494a2d16c9dd8))
* SelectとMultiSelectについて全ページ検索せずに求められた結果を返却する ([#72](https://github.com/koboriakira/python-lotion/issues/72)) ([ba0cab5](https://github.com/koboriakira/python-lotion/commit/ba0cab501009d53278ff62cc6f611abbf8458b26))

## [0.9.3](https://github.com/koboriakira/python-lotion/compare/v0.9.2...v0.9.3) (2025-01-08)


### Features

* SelectとMultiSelectを取得する機能にキャッシュを追加 ([#69](https://github.com/koboriakira/python-lotion/issues/69)) ([07b11ed](https://github.com/koboriakira/python-lotion/commit/07b11ed4a712e4c499b19263c7548f4503027551))

## [0.9.2](https://github.com/koboriakira/python-lotion/compare/v0.9.1...v0.9.2) (2024-12-31)


### Features

* 作成時刻や更新時刻での簡単な検索用関数を用意 ([b021eec](https://github.com/koboriakira/python-lotion/commit/b021eec7090e7f849cdc667f0c8f0ffbdaa182ad))


### Bug Fixes

* Fix a typo ([2efa6eb](https://github.com/koboriakira/python-lotion/commit/2efa6eb997a849155c3e38f068c15d58d02d4423))

## [0.9.1](https://github.com/koboriakira/python-lotion/compare/v0.9.0...v0.9.1) (2024-12-31)


### Features

* 簡単な検索機能を実装 ([c19323f](https://github.com/koboriakira/python-lotion/commit/c19323f6bf02e79711626a937a932208bca6b6ae))

## [0.9.0](https://github.com/koboriakira/python-lotion/compare/v0.8.10...v0.9.0) (2024-12-30)


### ⚠ BREAKING CHANGES

* 独自プロパティの検索機能を実装 ([#65](https://github.com/koboriakira/python-lotion/issues/65))

### Features

* 独自プロパティの検索機能を実装 ([#65](https://github.com/koboriakira/python-lotion/issues/65)) ([f5ddd4f](https://github.com/koboriakira/python-lotion/commit/f5ddd4fefb02039e8dadf5f67100c8b9bd805669))

## [0.8.10](https://github.com/koboriakira/python-lotion/compare/v0.8.9...v0.8.10) (2024-12-30)


### Bug Fixes

* 独自のRelationの作成に失敗する事象を修正 ([d9820dc](https://github.com/koboriakira/python-lotion/commit/d9820dcf687b612ce6ab320b8ee63d3b31eb2177))

## [0.8.9](https://github.com/koboriakira/python-lotion/compare/v0.8.8...v0.8.9) (2024-12-30)


### Bug Fixes

* Relationに登録するページIDの重複を整理する ([9f6f3a6](https://github.com/koboriakira/python-lotion/commit/9f6f3a6ff5e68adcecb8b62d6d9aa565d33a75e9))

## [0.8.8](https://github.com/koboriakira/python-lotion/compare/v0.8.7...v0.8.8) (2024-12-29)


### Bug Fixes

* 日付の扱いを改善 ([1ea9bd0](https://github.com/koboriakira/python-lotion/commit/1ea9bd022b5eaefd72fe36fda3c6bb3c5d97338b))

## [0.8.7](https://github.com/koboriakira/python-lotion/compare/v0.8.6...v0.8.7) (2024-12-29)


### Bug Fixes

* 関数が意図通りにはたらくようにする ([e6b9846](https://github.com/koboriakira/python-lotion/commit/e6b9846d0756e52149572b8b7f6d1abd0c97e875))

## [0.8.6](https://github.com/koboriakira/python-lotion/compare/v0.8.5...v0.8.6) (2024-12-29)


### Bug Fixes

* 独自ページのプロパティを正しく取得する ([#58](https://github.com/koboriakira/python-lotion/issues/58)) ([5581b1f](https://github.com/koboriakira/python-lotion/commit/5581b1fcf8afd7e7c6a215d28f298c6d2e782e11))

## [0.8.5](https://github.com/koboriakira/python-lotion/compare/v0.8.4...v0.8.5) (2024-12-29)


### Bug Fixes

* Noneに対応 ([b2a8786](https://github.com/koboriakira/python-lotion/commit/b2a8786bc4442a4922f70caa27c1300f0823ee4b))

## [0.8.4](https://github.com/koboriakira/python-lotion/compare/v0.8.3...v0.8.4) (2024-12-29)


### Features

* SelectやMultiSelectの名前指定更新に対応する ([#54](https://github.com/koboriakira/python-lotion/issues/54)) ([38bcc63](https://github.com/koboriakira/python-lotion/commit/38bcc63321a63d5fcfff02d379999ee59ca69e90))

## [0.8.3](https://github.com/koboriakira/python-lotion/compare/v0.8.2...v0.8.3) (2024-12-28)


### Features

* append関数を作成 ([7c24814](https://github.com/koboriakira/python-lotion/commit/7c24814ef73d91d97a1c784dc1498ddeb1f442ee))
* find_page関数を実装 ([661169d](https://github.com/koboriakira/python-lotion/commit/661169dd848e2d36b5ce3818fad88a21c740e187))

## [0.8.2](https://github.com/koboriakira/python-lotion/compare/v0.8.1...v0.8.2) (2024-12-28)


### Features

* カバー画像とアイコンの指定を可能にする ([daab1af](https://github.com/koboriakira/python-lotion/commit/daab1af621dfb2deec3bd5ae4e7d4844368ea975))


### Bug Fixes

* 使わない関数を削除 ([c9dd4b2](https://github.com/koboriakira/python-lotion/commit/c9dd4b20e5f7cc6323639736d8a3b3fa3e29c189))

## [0.8.1](https://github.com/koboriakira/python-lotion/compare/v0.8.0...v0.8.1) (2024-12-27)


### Features

* fetch_multi_select関数を改善 ([729fa76](https://github.com/koboriakira/python-lotion/commit/729fa76f9f1cfb4f0fa734a19f19d638b572c649))
* fetch_select関数を改善 ([d1ce7a5](https://github.com/koboriakira/python-lotion/commit/d1ce7a527b137b8c6ec82f333884706cbf5dc60a))
* ページの作成状況によって関数を呼び出し分ける ([a3beedd](https://github.com/koboriakira/python-lotion/commit/a3beedd95da305d9ff11bf6fe44208f3232e3cba))

## [0.8.0](https://github.com/koboriakira/python-lotion/compare/v0.7.1...v0.8.0) (2024-12-27)


### ⚠ BREAKING CHANGES

* アノテーションを利用して独自プロパティ、ページを作成できるようにする ([#48](https://github.com/koboriakira/python-lotion/issues/48))

### Features

* アノテーションを利用して独自プロパティ、ページを作成できるようにする ([#48](https://github.com/koboriakira/python-lotion/issues/48)) ([64efa31](https://github.com/koboriakira/python-lotion/commit/64efa31c3cbd9f5287766b890529a63df9ffdd19))

## [0.7.1](https://github.com/koboriakira/python-lotion/compare/v0.7.0...v0.7.1) (2024-12-27)


### Features

* BasePageを継承可能なものにする ([#44](https://github.com/koboriakira/python-lotion/issues/44)) ([a327e56](https://github.com/koboriakira/python-lotion/commit/a327e56e7500e41d21d54e412550df4917f7a393))
* 各プロパティを継承可能にする ([#47](https://github.com/koboriakira/python-lotion/issues/47)) ([4659ad0](https://github.com/koboriakira/python-lotion/commit/4659ad03f0e2759724df28caec4523ef2e02ff9a))

## [0.7.0](https://github.com/koboriakira/python-lotion/compare/v0.6.4...v0.7.0) (2024-12-25)


### ⚠ BREAKING CHANGES

* Titleプロパティの扱いを改善 ([#40](https://github.com/koboriakira/python-lotion/issues/40))

### Features

* Titleプロパティの扱いを改善 ([#40](https://github.com/koboriakira/python-lotion/issues/40)) ([64dff55](https://github.com/koboriakira/python-lotion/commit/64dff55f4119b92db2a91ddec109089bcf29ca73))

## [0.6.4](https://github.com/koboriakira/python-lotion/compare/v0.6.3...v0.6.4) (2024-12-24)


### Features

* BasePageのコピー関数を追加 ([018a16c](https://github.com/koboriakira/python-lotion/commit/018a16c5a17c4adc134250ed7d142619bc48aa30))


### Bug Fixes

* ページ新規作成時にも使わないプロパティは取り除く ([cc18c8c](https://github.com/koboriakira/python-lotion/commit/cc18c8c5b206aa711254009c9210a0d2928b0c79))

## [0.6.3](https://github.com/koboriakira/python-lotion/compare/v0.6.2...v0.6.3) (2024-12-21)


### Features

* 見出しブロックにリッチテキストを指定可能にする ([97733e1](https://github.com/koboriakira/python-lotion/commit/97733e1eeee4c584782a32b4f7790141b3f2b166))

## [0.6.2](https://github.com/koboriakira/python-lotion/compare/v0.6.1...v0.6.2) (2024-12-21)


### Features

* 日付メンションに対応 ([8197bca](https://github.com/koboriakira/python-lotion/commit/8197bca585832a50cecec774a7f3913d1a8bc4fb))

## [0.6.1](https://github.com/koboriakira/python-lotion/compare/v0.6.0...v0.6.1) (2024-12-21)


### Features

* ファイルの操作に対応 ([3342cbf](https://github.com/koboriakira/python-lotion/commit/3342cbf15e3e9f682efab4dfdb7989c4a5a3a57d))
* 受け取ったページのデータからBasePageを作成できる ([f99009b](https://github.com/koboriakira/python-lotion/commit/f99009b0ccf97754fa3e7ac24b0978330c70002a))


### Bug Fixes

* IS_EMPTYのときは文字列チェックをしない ([1bc48e8](https://github.com/koboriakira/python-lotion/commit/1bc48e8830abeb286d1a4290733cc0c547d65f56))
* PageIdを隠蔽する ([#34](https://github.com/koboriakira/python-lotion/issues/34)) ([545ea62](https://github.com/koboriakira/python-lotion/commit/545ea624605c5ef42a3c15b83876c234211c788b))
* Titleインスタンスの生成でPageIdを利用しない ([c7bf7c6](https://github.com/koboriakira/python-lotion/commit/c7bf7c67f21c7246c57b0426787904f638d99be9))

## [0.5.0](https://github.com/koboriakira/lotion/compare/v0.4.0...v0.5.0) (2024-12-15)


### Features

* 作成日時などの更新に対応 ([#29](https://github.com/koboriakira/lotion/issues/29)) ([6daa2e9](https://github.com/koboriakira/lotion/commit/6daa2e97d134a807c69f24b30293e72c5a4b64ce))

## [0.4.0](https://github.com/koboriakira/lotion/compare/v0.3.0...v0.4.0) (2024-12-15)


### Features

* プロパティを空欄で更新できる ([#26](https://github.com/koboriakira/lotion/issues/26)) ([7f2f999](https://github.com/koboriakira/lotion/commit/7f2f9993a1ad4648ddeb102d3923963a1e3d0d8f))

## [0.3.0](https://github.com/koboriakira/lotion/compare/v0.2.0...v0.3.0) (2024-12-15)


### Features

* ユニークIDに対応 ([#23](https://github.com/koboriakira/lotion/issues/23)) ([566eae0](https://github.com/koboriakira/lotion/commit/566eae0461a9bde6542c9dbc6cdbf7a71dd58e74))
* ロールアップのあるページに対応 ([#22](https://github.com/koboriakira/lotion/issues/22)) ([ab0ce93](https://github.com/koboriakira/lotion/commit/ab0ce93422eb2d1a8cbc81a10ad333a9fd897ec3))
* 数式プロパティの入ったページを操作可能にする ([#20](https://github.com/koboriakira/lotion/issues/20)) ([d3709df](https://github.com/koboriakira/lotion/commit/d3709dfabc2bb6c1e085e8c6fb38390b78793ba4))

## [0.2.0](https://github.com/koboriakira/lotion/compare/v0.1.0...v0.2.0) (2024-12-14)


### Features

* マルチセレクトを指定できるようにする ([#16](https://github.com/koboriakira/lotion/issues/16)) ([312b39e](https://github.com/koboriakira/lotion/commit/312b39ee18730bb4a5e510f483c940316f8e09b2))
* 名前を指定してセレクトを取得して利用する ([#14](https://github.com/koboriakira/lotion/issues/14)) ([9a14d4c](https://github.com/koboriakira/lotion/commit/9a14d4cb1ff1135085e44df45b734af230ab80a8))

## 0.1.0 (2024-12-14)


### Bug Fixes

* 正しいキャメルケースに修正 ([#12](https://github.com/koboriakira/lotion/issues/12)) ([9ffbb91](https://github.com/koboriakira/lotion/commit/9ffbb91cfc0c22bdcecf607e5055b052b53e0e61))
