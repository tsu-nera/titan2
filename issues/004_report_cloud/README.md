# Issue 004: スマホから脳波分析レポート閲覧

スマホから直接、脳波分析レポートを閲覧できるようにするプロジェクト。

## クイックスタート

### 1. 概要を理解する
[ISSUE.md](ISSUE.md) を読んで、プロジェクトの全体像を把握してください。

### 2. 技術選定の背景を知る
[ARCHITECTURE.md](ARCHITECTURE.md) で、なぜGitHub Actionsを選んだのか、他の手段との比較を確認できます。

### 3. 実装を始める
[SETUP_GDRIVE.md](SETUP_GDRIVE.md) に従って、Google Drive APIの設定から始めてください。

## ドキュメント一覧

| ファイル | 内容 | 対象読者 |
|----------|------|----------|
| [ISSUE.md](ISSUE.md) | プロジェクト概要・実装計画 | 全員 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 技術選定・設計判断 | 開発者 |
| [SETUP_GDRIVE.md](SETUP_GDRIVE.md) | Google Drive API設定手順 | 初回セットアップ時 |

## アーキテクチャ概要

```
[Mind Monitor] → [Google Drive]
                       ↓
[スマホ: GitHub Mobile] 手動トリガー
                       ↓
[GitHub Actions] Drive APIでCSV取得 → 分析実行
                       ↓
[GitHub] レポート保存
                       ↓
[スマホ: ブラウザ] レポート閲覧
```

## 主な特徴

- ✅ **完全無料**: GitHub Actions無料枠（月2000分）で運用
- ✅ **メンテナンスフリー**: サーバー管理不要
- ✅ **モバイルファースト**: スマホから2タップで分析開始
- ✅ **履歴管理**: Gitで全レポート履歴が残る
- ✅ **既存資産活用**: issue 003のコードを100%再利用

## 実装ステータス

- [ ] Phase 1: Google Drive API セットアップ
- [ ] Phase 2: Drive連携スクリプト作成
- [ ] Phase 3: GitHub Actions ワークフロー作成
- [ ] Phase 4: ディレクトリ構造整備
- [ ] Phase 5: テスト実行
- [ ] Phase 6: ドキュメント作成

## 推定工数

合計: 5-7時間

## 次のステップ

1. [SETUP_GDRIVE.md](SETUP_GDRIVE.md) を開く
2. Google Cloudプロジェクトを作成
3. Phase 1から順に実装

## 関連Issue

- [Issue 003: 日次レポート改善](../003_improve_daily_report/ISSUE.md)

## 作成日

2025-11-04
