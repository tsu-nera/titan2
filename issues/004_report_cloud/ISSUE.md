# Issue 004: スマホから脳波分析レポート閲覧

## 背景と課題

### 現状のワークフロー

```
Mind Monitor（スマホ）でデータ計測
    ↓
Google Drive にアップロード
    ↓
ローカルPCにダウンロード
    ↓
WSL/Linux環境で分析実行
    ↓
レポート閲覧
```

### 課題

1. **PCでの分析が必須**: 脳波計測のたびにPCを使う必要がある
2. **手動オペレーション**: ダウンロード、コマンド実行が煩雑
3. **モビリティの欠如**: 外出先で分析結果を確認できない

## 目標

**スマホから直接、脳波分析レポートを閲覧できるようにする**

要件:
- 全15指標 + グラフ（issue 003と同等の機能）
- 2-5分の処理時間は許容
- 完全無料で実現
- Webブラウザで閲覧
- CSVデータはGitHubにcommitしない（サイズ対策）

## アーキテクチャ

### 選定: GitHub Actions + Google Drive 連携

```
[Mind Monitor]
    ↓ CSV保存
[Google Drive]
    ↓ 手動トリガー
[スマホ: GitHub Mobile]
    ↓ workflow_dispatch
[GitHub Actions]
    ├─ Google Drive APIで最新CSV取得
    ├─ generate_report.py 実行
    └─ レポートのみGitにcommit
    ↓
[スマホ: GitHub]
    └─ REPORT.md + 画像閲覧
```

### 技術スタック

**実行環境**
- GitHub Actions (Ubuntu runner)
  - メモリ: 7GB
  - 無料枠: 月2,000分（約400回分析）

**分析エンジン**
- Python 3.11
- MNE-Python（脳波専門ライブラリ）
- generate_report.py（issue 003の既存実装）

**データ連携**
- Google Drive API（サービスアカウント認証）
- GitHub Secrets（認証情報保管）

**閲覧インターフェース**
- GitHub Web UI / GitHub Mobile
- Markdown + 画像レンダリング

### アーキテクチャ判断の根拠

他の手段と比較した結果（詳細は [ARCHITECTURE.md](ARCHITECTURE.md) 参照）:

| 手段 | 無料 | 自動化 | メモリ | MNE対応 | 判定 |
|------|------|--------|--------|---------|------|
| **GitHub Actions** | ✅ | ✅ | 7GB | ✅ | ⭐⭐⭐⭐⭐ |
| Google Colab | ✅ | ❌ | 12GB | ✅ | ⭐⭐⭐ |
| Cloud Functions | ⚠️ | ✅ | 設定次第 | ✅ | ⭐⭐⭐⭐ |
| Streamlit Cloud | ✅ | ✅ | 1GB | ❌ | ⭐⭐ |

## 実装計画

### Phase 1: Google Drive API セットアップ（1時間）

**作業内容:**

1. **Google Cloud プロジェクト作成**
   - https://console.cloud.google.com
   - プロジェクト名: `titan-eeg-analysis` (例)

2. **Drive API 有効化 + サービスアカウント作成**
   - IAMでサービスアカウント作成
   - JSONキーダウンロード

3. **Drive フォルダ共有**
   - Mind Monitor用フォルダIDを取得
   - サービスアカウントに閲覧権限付与

4. **GitHub Secrets 設定**
   - `GDRIVE_CREDENTIALS`: JSONキー全文
   - `GDRIVE_FOLDER_ID`: フォルダID

**成果物:**
- サービスアカウント認証情報
- 設定済みGitHub Secrets

**詳細手順:**
[SETUP_GDRIVE.md](SETUP_GDRIVE.md) 参照

---

### Phase 2: Google Drive連携スクリプト作成（1-1.5時間）

**作業内容:**

1. **`scripts/fetch_from_gdrive.py` 新規作成**
   ```python
   機能:
   - Google Drive API認証
   - 指定フォルダから最新CSVファイル検索
     - ファイル名パターン（日付含む）でフィルタ
     - 更新日時で降順ソート
   - ファイルダウンロード
   - エラーハンドリング
   ```

2. **依存関係追加**
   - `requirements.txt` に追加:
     ```
     google-auth>=2.23.0
     google-api-python-client>=2.100.0
     ```

**成果物:**
- `scripts/fetch_from_gdrive.py`
- 更新された `requirements.txt`

---

### Phase 3: GitHub Actions ワークフロー作成（1時間）

**作業内容:**

1. **`.github/workflows/eeg_analysis.yml` 作成**
   ```yaml
   トリガー: workflow_dispatch（手動実行）

   入力パラメータ:
   - date: 分析する日付（省略時は最新）

   ジョブ:
   1. リポジトリチェックアウト
   2. Python 3.11 セットアップ
   3. 依存関係インストール
   4. Google Drive から最新CSV取得
   5. generate_report.py 実行
   6. レポート結果を自動commit & push
   ```

2. **`.gitignore` 更新**
   ```
   # CSVファイルを明示的に除外
   data/**/*.csv
   *.csv

   # 一時ダウンロードファイル
   /tmp_data/
   ```

**成果物:**
- `.github/workflows/eeg_analysis.yml`
- 更新された `.gitignore`

---

### Phase 4: ディレクトリ構造整備（30分）

**ディレクトリレイアウト:**

```
titan2/
  .github/
    workflows/
      eeg_analysis.yml           # 新規作成

  scripts/
    fetch_from_gdrive.py         # 新規作成

  issues/
    003_improve_daily_report/
      generate_report.py         # 既存（再利用）

    004_report_cloud/            # 新規ディレクトリ
      ISSUE.md                   # このファイル
      SETUP_GDRIVE.md            # API設定手順
      ARCHITECTURE.md            # 技術判断記録
      USAGE.md                   # スマホ操作手順

  reports/                       # 新規（分析結果格納先）
    20251104_153000/             # タイムスタンプ付きディレクトリ
      REPORT.md
      img/
        *.png
    20251105_090000/
      REPORT.md
      img/
        *.png

  data/                          # .gitignore対象
    (CSVファイルはコミットしない)
```

**作業内容:**
- ディレクトリ作成
- README追加（各ディレクトリの説明）

**成果物:**
- 整備されたディレクトリ構造

---

### Phase 5: テスト実行（30分-1時間）

**5.1 ローカルテスト**

```bash
# 認証テスト
python scripts/fetch_from_gdrive.py --folder-id <FOLDER_ID> --list

# ダウンロードテスト
python scripts/fetch_from_gdrive.py --folder-id <FOLDER_ID> --download latest --output /tmp
```

**5.2 GitHub Actions テスト**

1. GitHub Web UIでワークフロー手動実行
2. Actions タブでログ確認
3. レポート生成確認
4. エラーハンドリング検証

**成果物:**
- 動作確認済みワークフロー

---

### Phase 6: ドキュメント作成（1時間）

**作業内容:**

1. **SETUP_GDRIVE.md**（Google Drive API設定）
   - GCP画面のスクリーンショット指示
   - フォルダID取得方法
   - GitHub Secrets設定手順

2. **USAGE.md**（スマホ操作手順）
   - GitHub Mobileでのワークフロー起動方法
   - レポート閲覧方法
   - トラブルシューティング

3. **ARCHITECTURE.md**（技術判断記録）
   - 手段比較表
   - コスト分析
   - セキュリティ考慮事項

**成果物:**
- 完全なドキュメントセット

---

## 推定工数

| Phase | 作業内容 | 時間 |
|-------|----------|------|
| 1 | Google Drive API セットアップ | 1h |
| 2 | Drive連携スクリプト作成 | 1-1.5h |
| 3 | GitHub Actions ワークフロー | 1h |
| 4 | ディレクトリ整備 | 0.5h |
| 5 | テスト実行 | 0.5-1h |
| 6 | ドキュメント作成 | 1h |
| **合計** | | **5-7時間** |

## コスト分析

### GitHub Actions 無料枠

```
無料枠: 月2,000分（privateリポジトリ）
1回の分析: 約5分
月間可能回数: 400回

想定利用: 1日2回 × 30日 = 60回/月
使用時間: 60 × 5 = 300分/月（15%使用）

コスト: 0円
```

### Google Cloud Platform

```
Google Drive API:
- 無料枠: 1,000,000リクエスト/日
- 今回の使用: 2リクエスト/分析（ファイル検索 + ダウンロード）

コスト: 0円
```

### 総コスト

**完全無料**（想定使用量では無料枠内）

## セキュリティ考慮事項

### 認証情報管理

1. **GitHub Secrets使用**
   - サービスアカウントJSONをSecretsに保存
   - リポジトリログには表示されない
   - Actions実行時のみ環境変数として利用

2. **最小権限原則**
   - サービスアカウントはDrive読み取り権限のみ
   - 特定フォルダのみアクセス可能

3. **privateリポジトリ推奨**
   - publicの場合、レポート内容が公開される
   - 個人データを含む場合はprivate必須

### データ管理

1. **CSVファイルをGitに含めない**
   - `.gitignore`で明示的に除外
   - git historyに残らない

2. **Google Drive上の削除**
   - 定期的に手動削除（ユーザー管理）
   - Actions実行後、Driveからファイル削除も可能（オプション）

## メリット

### ユーザーエクスペリエンス

1. **モバイルファースト**
   - スマホから2タップで分析開始
   - 外出先で結果確認可能

2. **自動化**
   - CSV取得からレポート生成まで自動
   - PCを開く必要なし

3. **履歴管理**
   - Gitで全レポート履歴が残る
   - 日付別比較が容易

### 技術的メリット

1. **インフラ管理不要**
   - サーバー運用なし
   - スケーリング自動

2. **既存コード再利用**
   - `generate_report.py`をそのまま使用
   - issue 003の成果を100%活用

3. **コスト0円**
   - 無料枠で十分
   - 運用コストなし

## 制約事項

### 技術的制約

1. **実行時間**
   - 起動〜完了まで4-7分
   - リアルタイム性は低い
   - （許容済み）

2. **手動トリガー**
   - 自動実行はスケジュールのみ
   - ファイルアップロード検知は不可
   - （要件として手動トリガー希望）

3. **GitHub Actions制限**
   - 1ジョブ最大6時間
   - 30分セッション（5分処理）には十分

### 運用制約

1. **Google Drive手動管理**
   - CSVファイルの定期削除が必要
   - ストレージ容量管理

2. **GitHub Secrets更新**
   - サービスアカウントキー更新時
   - 手動で再設定必要

## トラブルシューティング

### 想定される問題

1. **Drive API認証失敗**
   - 原因: Secrets設定ミス
   - 対処: JSONキー再確認

2. **CSVファイルが見つからない**
   - 原因: フォルダID間違い
   - 対処: DriveのURL確認

3. **メモリ不足**
   - 原因: 超長時間セッション（2時間以上）
   - 対処: セッション分割

4. **Actions実行失敗**
   - 原因: 依存関係インストールエラー
   - 対処: requirements.txt確認

## 今後の拡張案

### Phase 7以降（オプション）

1. **GitHub Pages化**
   - 静的サイト生成
   - より見やすいUI

2. **Slack/LINE通知**
   - 分析完了時に通知
   - レポートURLを送信

3. **データベース統合**
   - 過去データ集計
   - 進捗グラフ生成

4. **複数ファイル一括分析**
   - 週次まとめレポート
   - 統計比較

## 次のステップ

### 実装開始時

1. [SETUP_GDRIVE.md](SETUP_GDRIVE.md) に従ってGoogle Cloud設定
2. Phase 1から順に実装
3. 各Phaseでコミット

### 質問・課題

- GitHub Actionsの実行履歴を何日保持するか？
- レポート古いものを自動削除するか？（git history管理）
- 複数デバイス（家族共有）対応は必要か？

---

**作成日**: 2025-11-04
**ブランチ**: issue-004
**関連Issue**: [Issue 003](../003_improve_daily_report/ISSUE.md)
