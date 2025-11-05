# Issue 004 進捗記録

## 作業日: 2025-11-04

---

## ✅ 完了した作業

### Phase 1: Google Drive API セットアップ

- [x] Google Cloud プロジェクト作成: `titan2-477209`
- [x] Google Drive API 有効化
- [x] サービスアカウント作成: `github-actions-drive-reader@titan2-477209.iam.gserviceaccount.com`
- [x] JSONキーダウンロード: `private/titan2-477209-d26f6c208011.json`
- [x] DriveフォルダID取得: `1Yo4QRa8sP16zRJ9ky-vPHzJ8zEBQ85C5`
- [x] サービスアカウントにフォルダ共有（閲覧者権限）
- [x] GitHub Secrets設定:
  - `GDRIVE_CREDENTIALS`: サービスアカウントJSON全文
  - `GDRIVE_FOLDER_ID`: フォルダID

**成果物:**
- ドキュメント: [SETUP_GDRIVE.md](SETUP_GDRIVE.md)

---

### Phase 2: Google Drive連携スクリプト作成

- [x] `scripts/fetch_from_gdrive.py` 作成
  - Google Drive API認証
  - ZIPファイル自動検出（CSVもサポート）
  - 最新ファイル取得
  - 日付指定ダウンロード
  - ZIP自動解凍
- [x] `requirements.txt` 更新
  - `google-auth>=2.23.0`
  - `google-api-python-client>=2.100.0`
- [x] ローカルテスト成功
  - ZIPダウンロード: 14.9 MB
  - CSV解凍: 176 MB
  - Mind Monitor CSV形式確認済み

**成果物:**
- スクリプト: [scripts/fetch_from_gdrive.py](../../scripts/fetch_from_gdrive.py)
- 依存関係: [requirements.txt](../../requirements.txt)

---

### Phase 3: GitHub Actions ワークフロー作成

- [x] `.github/workflows/eeg_analysis.yml` 作成
  - `workflow_dispatch` 手動トリガー
  - 日付パラメータ（latest / YYYY-MM-DD）
  - Google Drive連携
  - `generate_report.py` 実行
  - レポート自動commit
- [x] `.gitignore` 更新
  - `*.csv`, `*.zip`, `data/`, `private/` 除外
- [x] `reports/` ディレクトリ作成
  - README.md（レポートの見方）
- [x] YAML構文チェック: OK
- [x] ローカルでレポート生成テスト: 成功（12枚画像生成）
- [x] mainブランチにマージ完了

**成果物:**
- ワークフロー: [.github/workflows/eeg_analysis.yml](../../.github/workflows/eeg_analysis.yml)
- ディレクトリ: [reports/](../../reports/)
- ドキュメント: [USAGE.md](USAGE.md)

---

### ドキュメント作成

- [x] [ISSUE.md](ISSUE.md): プロジェクト概要・実装計画
- [x] [ARCHITECTURE.md](ARCHITECTURE.md): 技術選定・設計判断
- [x] [SETUP_GDRIVE.md](SETUP_GDRIVE.md): Google Drive API設定手順
- [x] [USAGE.md](USAGE.md): スマホ操作手順
- [x] [README.md](README.md): プロジェクト全体ガイド

---

## ⚠️ 発生した問題

### 問題1: GitHub Actions push権限エラー (403)

**エラー内容:**
```
remote: Permission to tsu-nera/titan2.git denied to github-actions[bot].
fatal: unable to access 'https://github.com/tsu-nera/titan2/': The requested URL returned error: 403
Error: Process completed with exit code 128.
```

**原因:**
- GitHub Actionsにリポジトリへの書き込み権限（`contents: write`）が付与されていない

**解決策（未実装）:**
ワークフローファイルに以下を追加：
```yaml
permissions:
  contents: write
```

---

### 問題2: 設計上の課題

**課題:**
- 現在の設計では、Actionsが実行されるたびにレポートをコミット
- 開発コミットとデータ分析結果が混在
- リポジトリサイズ肥大化（画像が蓄積）
- コミット履歴が汚れる

**決定した解決策:**
**別リポジトリ方式を採用**

```
titan2/ (開発リポジトリ)
  └─ コード、ドキュメント、ワークフロー

titan2-reports/ (データリポジトリ - 新規作成)
  └─ reports/YYYYMMDD/ (分析結果のみ)
```

---

## 📋 明日の作業（Phase 4）

### 4.1 新規リポジトリ作成

- [ ] GitHubで `titan2-reports` リポジトリ作成
  - 公開/非公開の選択
  - README.md初期化
  - ディレクトリ構造準備

### 4.2 ワークフロー修正

**変更点:**

1. **push権限追加**
   ```yaml
   permissions:
     contents: write  # titan2への書き込み（不要になる可能性）
   ```

2. **レポート保存先変更**
   - 現在: `reports/` (titan2内)
   - 変更後: titan2-reports リポジトリにpush

3. **認証設定**
   - GitHub Token (GITHUB_TOKEN) 使用
   - または Personal Access Token (PAT) 作成

4. **コミット削除 または 別リポジトリへのpush**
   ```yaml
   - name: レポートをtitan2-reportsにpush
     run: |
       git clone https://github.com/tsu-nera/titan2-reports.git
       cp -r $OUTPUT_DIR titan2-reports/reports/
       cd titan2-reports
       git add reports/
       git commit -m "Add report $(date)"
       git push
   ```

### 4.3 ドキュメント更新

- [ ] ARCHITECTURE.md: 新しい設計を反映
- [ ] USAGE.md: レポート閲覧方法を更新（titan2-reports参照）
- [ ] README.md: リポジトリ構成を更新

### 4.4 動作確認

- [ ] GitHub Actionsで実際に実行
- [ ] レポートがtitan2-reportsに正しくpushされるか確認
- [ ] スマホからレポート閲覧確認

---

## 🔧 技術メモ

### GitHub Actionsで別リポジトリにpushする方法

#### 方法1: Personal Access Token (PAT) 使用

**手順:**
1. GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token" (classic)
3. スコープ選択: `repo` (全権限)
4. トークン生成 → コピー
5. titan2リポジトリのSecrets追加: `PAT_TOKEN`

**ワークフロー例:**
```yaml
- name: Clone reports repository
  run: |
    git clone https://${{ secrets.PAT_TOKEN }}@github.com/tsu-nera/titan2-reports.git

- name: Commit and push to reports repo
  working-directory: titan2-reports
  run: |
    git config user.name "GitHub Actions"
    git config user.email "actions@github.com"
    cp -r ../$OUTPUT_DIR reports/
    git add reports/
    git commit -m "Add EEG analysis report $(date)"
    git push
```

#### 方法2: GitHub App Token（推奨・セキュア）

より細かい権限管理が可能。設定が複雑だが、長期運用には推奨。

#### 方法3: Deploy Keys（リポジトリ単位）

各リポジトリに専用のSSHキーを設定。最もセキュア。

---

## 📂 ディレクトリ構成（計画）

### titan2/ (開発リポジトリ)

```
titan2/
  .github/
    workflows/
      eeg_analysis.yml          # 修正予定
  scripts/
    fetch_from_gdrive.py
  issues/
    004_report_cloud/
      ISSUE.md
      ARCHITECTURE.md           # 更新予定
      SETUP_GDRIVE.md
      USAGE.md                  # 更新予定
      PROGRESS.md               # このファイル
  private/
    titan2-477209-d26f6c208011.json
  requirements.txt
  README.md
```

### titan2-reports/ (データリポジトリ - 新規作成)

```
titan2-reports/
  reports/
    20251104_103220/
      REPORT.md
      img/
        *.png (12枚)
    20251105_090000/
      REPORT.md
      img/
        *.png
  README.md                     # レポート閲覧ガイド
```

---

## 参考資料

### GitHub Actions

- [Manually running a workflow](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/manually-running-a-workflow)
- [workflow_dispatch event](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_dispatch)
- [Using secrets in GitHub Actions](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)

### 別リポジトリへのpush

- [GitHub Actions: Pushing to another repository](https://github.com/marketplace/actions/github-push)
- Stack Overflow: [How to push to another repository in GitHub Actions](https://stackoverflow.com/questions/57921401)

---

## チェックリスト（明日）

### 準備

- [ ] `titan2-reports` リポジトリ作成
- [ ] Personal Access Token 生成
- [ ] GitHub Secretsに `PAT_TOKEN` 追加

### 実装

- [ ] `eeg_analysis.yml` 修正
  - [ ] permissions追加
  - [ ] titan2-reportsへのpush処理追加
  - [ ] titan2へのcommit削除
- [ ] ローカルでYAML構文チェック
- [ ] コミット＆プッシュ

### テスト

- [ ] GitHub Actionsでワークフロー実行
- [ ] エラーログ確認
- [ ] titan2-reportsにレポートが生成されているか確認
- [ ] スマホからレポート閲覧テスト

### ドキュメント

- [ ] ARCHITECTURE.md更新
- [ ] USAGE.md更新
- [ ] PROGRESS.md更新

---

## コスト見積もり（再評価）

### titan2 (開発リポジトリ)

- サイズ: ~10MB（コードのみ）
- 更新頻度: 開発時のみ

### titan2-reports (データリポジトリ)

- 1レポート: ~10MB（画像12枚 + REPORT.md）
- 月30回分析: 300MB/月
- 年間: 3.6GB

**GitHub無料プラン:**
- リポジトリサイズ制限: なし（推奨 1GB以下）
- ⚠️ 3.6GB/年 → 3年で10GB超

**対策:**
- 古いレポート（90日以上）を定期削除
- または有料プラン（Pro: $4/月）
- またはGitHub Releasesに圧縮保存

---

**最終更新: 2025-11-04 19:45**
**次回作業: 2025-11-05**
**担当: tsu-nera + Claude**
