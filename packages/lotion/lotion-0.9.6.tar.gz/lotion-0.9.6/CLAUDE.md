# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

Lotion は Notion API の Python ラッパーライブラリです。`notion-client` をベースに、より Pythonic でクラスベースのインターフェースを提供します。

## 開発コマンド

### ビルドとインストール
```bash
# 開発用インストール
make install

# パッケージビルド
make build

# PyPI へのリリース（要認証）
make release
```

### テスト実行
```bash
# ユニットテストのみ（API・学習テストを除く）
make test

# すべてのテストを並列実行
make test-all

# 最小限のテストのみ実行
make test-min

# 特定のテスト実行
make test-current  # @pytest.mark.current でマークされたテスト
make test-learning  # 学習用テスト（@pytest.mark.learning）
make test-api      # API統合テスト（@pytest.mark.api）

# 単一テストの実行
pytest test/test_lotion/test_rich_text.py::TestRichText::test_リンクを含むリッチテキストを作成する -v
```

### コード品質
```bash
# Ruff でのリント・フォーマット
make lint

# タイプチェック（現在未設定）
# プロジェクトにタイプチェッカーがない場合は導入を検討してください
```

## アーキテクチャ概要

### 中核となるデザインパターン

1. **Facade パターン**: `Lotion` クラスが Notion API への統一インターフェースを提供
2. **Decorator パターン**: `@notion_database` と `@notion_prop` でメタデータを注入
3. **Factory パターン**: `BlockFactory` と `PropertyTranslator` でオブジェクト生成
4. **Builder パターン**: `Builder` クラスでフィルタ条件を構築

### 主要コンポーネント

1. **ページシステム**
   - `BasePage`: すべてのページクラスの基底クラス
   - `@notion_database`: データベースIDを設定し、プロパティを自動生成
   - 例:
     ```python
     @notion_database("database-id")
     class MyPage(BasePage):
         title: Title
         status: Select
     ```

2. **プロパティシステム**
   - `Property`: 抽象基底クラス
   - 各種プロパティ: Title, Text, Select, MultiSelect, Checkbox, Date など
   - `PropertyTranslator`: 型に応じて適切なプロパティインスタンスを生成

3. **ブロックシステム**
   - `Block`: 抽象基底クラス
   - 各種ブロック: Paragraph, Heading, Quote, Code, Image など
   - `RichText` と `RichTextBuilder` でリッチテキストをサポート

4. **キャッシング**
   - `SelectCache` と `MultiSelectCache` で Select/MultiSelect のオプションをキャッシュ
   - 不要な API 呼び出しを削減

### データフロー

1. デコレーターでページクラスを定義
2. プロパティへのアクセスは生成されたゲッター/セッターを通じて行う
3. 変更は Properties コレクションで追跡
4. 更新時にシリアライズして Notion API へ送信
5. レスポンスを型付きオブジェクトにデシリアライズ

## 重要な実装上の注意点

1. **エラーハンドリング**
   - 502 Bad Gateway エラーは自動リトライ
   - カスタム例外: `NotionApiError`, `AppendBlockError`, `NotCreatedError`

2. **新機能の追加**
   - 新しいプロパティ型: `properties/` ディレクトリに実装を追加
   - 新しいブロック型: `block/` ディレクトリに実装を追加
   - `PropertyTranslator` や `BlockFactory` の更新も忘れずに

3. **テスト駆動開発**
   - 新機能は必ずテストを先に書く
   - API テストは `@pytest.mark.api` でマーク
   - 学習用テストは `@pytest.mark.learning` でマーク

4. **最近の変更（v0.9.4）**
   - link_mention のリッチテキストサポートを追加
   - Select/MultiSelect の取得を最適化（全ページ検索を回避）
   - Select/MultiSelect プロパティのキャッシュ機能を追加