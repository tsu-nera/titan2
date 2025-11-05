# 明日の作業: Phase 4 実装ガイド

**作業日**: 2025-11-05（予定）

---

## 概要

開発リポジトリ（titan2）とデータリポジトリ（titan2-reports）を分離する。

```
titan2/ (開発)          titan2-reports/ (データ)
     ↓ Actions実行            ↑
     └─────────────────────→  レポートpush
```

---

## ステップ1: titan2-reports リポジトリ作成（5分）

### 1.1 GitHubでリポジトリ作成

**ブラウザで操作:**
```
https://github.com/new
```

**設定:**
- Repository name: `titan2-reports`
- Description: `Brain wave analysis reports generated from titan2`
- 公開設定: **Private** 推奨（個人データ含む）
- Initialize:
  - ✅ Add a README file
  - ❌ Add .gitignore
  - ❌ Choose a license

「Create repository」をクリック

### 1.2 初期ディレクトリ構造作成

**ローカルでクローン:**
```bash
cd /home/tsu-nera/repo/
git clone https://github.com/tsu-nera/titan2-reports.git
cd titan2-reports
```

**ディレクトリ作成:**
```bash
mkdir -p reports
echo "# titan2-reports" > README.md
```

**README.md編集:**
```markdown
# titan2-reports

Muse脳波データの自動分析レポート保管リポジトリ

## 概要

このリポジトリには、[titan2](https://github.com/tsu-nera/titan2)のGitHub Actionsで生成された
脳波分析レポートが自動的に保存されます。

## ディレクトリ構成

```
reports/
  20251104_103220/
    REPORT.md           # 分析レポート（Markdown）
    img/
      *.png             # グラフ画像（12枚）
  20251105_090000/
    REPORT.md
    img/
      *.png
```

## レポートの見方

各レポートには以下が含まれます：

1. **データ品質評価**: HSI接続品質
2. **基本周波数バンド**: Delta, Theta, Alpha, Beta, Gamma
3. **高度な指標**:
   - Frontal Midline Theta (Fmθ): 瞑想深度
   - Peak Alpha Frequency (PAF): 個人アルファ周波数
   - Frontal Alpha Asymmetry (FAA): 左右半球バランス
   - Spectral Entropy (SE): 注意集中度
4. **時間経過分析**: セグメント別比較
5. **総合スコア**: 0-100点

## 分析方法

レポートは以下の方法で生成されます：

1. Mind Monitor（スマホアプリ）でEEGデータ計測
2. Google Driveに自動アップロード
3. [titan2](https://github.com/tsu-nera/titan2)のGitHub Actionsを手動実行
4. このリポジトリに自動保存

## 関連リンク

- [titan2リポジトリ](https://github.com/tsu-nera/titan2)
- [実装詳細（ISSUE.md）](https://github.com/tsu-nera/titan2/blob/main/issues/004_report_cloud/ISSUE.md)
```

**コミット＆プッシュ:**
```bash
git add README.md reports/
git commit -m "Initial commit: Setup repository structure"
git push origin main
```

---

## ステップ2: Personal Access Token (PAT) 作成（5分）

### 2.1 トークン生成

**ブラウザで操作:**
```
https://github.com/settings/tokens
```

1. 「Tokens (classic)」を選択
2. 「Generate new token」→「Generate new token (classic)」
3. 設定:
   - **Note**: `titan2-actions-to-reports`
   - **Expiration**: `90 days` または `No expiration`（推奨: 90日）
   - **Select scopes**:
     - ✅ `repo` (Full control of private repositories)
4. 「Generate token」をクリック
5. **トークンをコピー**（表示は一度だけ！）
   - 例: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 2.2 GitHub Secretsに保存

**titan2リポジトリで操作:**
```
https://github.com/tsu-nera/titan2/settings/secrets/actions
```

1. 「New repository secret」をクリック
2. 設定:
   - **Name**: `PAT_TOKEN`
   - **Secret**: 先ほどコピーしたトークンを貼り付け
3. 「Add secret」をクリック

**確認:**
- Secrets一覧に `PAT_TOKEN` が表示される
- 既存の `GDRIVE_CREDENTIALS`, `GDRIVE_FOLDER_ID` と並んで表示

---

## ステップ3: ワークフロー修正（15分）

### 3.1 現在のワークフローをバックアップ

```bash
cd /home/tsu-nera/repo/titan2
cp .github/workflows/eeg_analysis.yml .github/workflows/eeg_analysis.yml.bak
```

### 3.2 ワークフロー修正

**ファイル:** `.github/workflows/eeg_analysis.yml`

**修正内容:**

#### 1. permissions追加（ファイル先頭付近）

```yaml
name: EEG Analysis

on:
  workflow_dispatch:
    inputs:
      date:
        description: '分析する日付（例: 2025-11-04）省略時は最新ファイル'
        required: false
        default: 'latest'
        type: string

permissions:
  contents: read  # titan2への読み取り権限

jobs:
  analyze:
    runs-on: ubuntu-latest
    timeout-minutes: 30
```

#### 2. レポートコミット処理を削除 → 別リポジトリへのpushに変更

**削除する部分:**
```yaml
      - name: レポートをGitにコミット
        run: |
          git config --local user.name "GitHub Actions"
          git config --local user.email "actions@github.com"
          git add "$OUTPUT_DIR"
          CSV_NAME=$(basename "$CSV_PATH")
          COMMIT_DATE=$(date +'%Y-%m-%d %H:%M:%S')
          git commit -m "Add EEG analysis report - ${COMMIT_DATE}" \
            -m "" \
            -m "Generated from workflow run: ${{ github.run_number }}" \
            -m "Input CSV: ${CSV_NAME}" \
            -m "Output: ${OUTPUT_DIR}" \
            -m "" \
            -m "Generated with GitHub Actions"
          git push
```

**新しい処理に置き換え:**
```yaml
      - name: titan2-reportsリポジトリにレポートをpush
        env:
          PAT_TOKEN: ${{ secrets.PAT_TOKEN }}
        run: |
          # titan2-reportsをクローン
          git clone https://${PAT_TOKEN}@github.com/tsu-nera/titan2-reports.git /tmp/titan2-reports

          # レポートをコピー
          cp -r "$OUTPUT_DIR" /tmp/titan2-reports/reports/

          # Git設定
          cd /tmp/titan2-reports
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"

          # コミット情報準備
          CSV_NAME=$(basename "$CSV_PATH")
          COMMIT_DATE=$(date +'%Y-%m-%d %H:%M:%S')
          REPORT_DIR=$(basename "$OUTPUT_DIR")

          # コミット
          git add "reports/${REPORT_DIR}"
          git commit -m "Add EEG analysis report - ${COMMIT_DATE}" \
            -m "" \
            -m "Generated from: github.com/${{ github.repository }}/actions/runs/${{ github.run_id }}" \
            -m "Input CSV: ${CSV_NAME}" \
            -m "Report directory: reports/${REPORT_DIR}" \
            -m "" \
            -m "🤖 Generated with GitHub Actions"

          # プッシュ
          git push origin main

          echo "✅ レポートをtitan2-reportsにpushしました"
          echo "📊 https://github.com/tsu-nera/titan2-reports/tree/main/reports/${REPORT_DIR}"
```

#### 3. クリーンアップ処理更新

```yaml
      - name: クリーンアップ
        if: always()
        run: |
          # 一時ファイル削除
          rm -rf /tmp/data
          rm -rf /tmp/credentials
          rm -rf /tmp/titan2-reports  # 追加
```

#### 4. サマリー更新

```yaml
      - name: 分析結果サマリー
        if: success()
        run: |
          REPORT_DIR=$(basename "$OUTPUT_DIR")

          echo "✅ 脳波分析が完了しました"
          echo ""
          echo "📊 レポート: reports/${REPORT_DIR}/REPORT.md"
          echo "📁 画像: reports/${REPORT_DIR}/img/"
          echo ""
          echo "🔗 titan2-reportsでレポートを閲覧:"
          echo "   https://github.com/tsu-nera/titan2-reports/blob/main/reports/${REPORT_DIR}/REPORT.md"
```

### 3.3 修正後の完全版ワークフロー

<details>
<summary>完全版YAML（クリックして展開）</summary>

```yaml
name: EEG Analysis

on:
  workflow_dispatch:
    inputs:
      date:
        description: '分析する日付（例: 2025-11-04）省略時は最新ファイル'
        required: false
        default: 'latest'
        type: string

permissions:
  contents: read

jobs:
  analyze:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: リポジトリをチェックアウト
        uses: actions/checkout@v4

      - name: Python環境セットアップ
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: 依存関係インストール
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Google Drive認証情報を設定
        env:
          GDRIVE_CREDENTIALS: ${{ secrets.GDRIVE_CREDENTIALS }}
        run: |
          mkdir -p /tmp/credentials
          echo "$GDRIVE_CREDENTIALS" > /tmp/credentials/gdrive.json
          echo "GOOGLE_APPLICATION_CREDENTIALS=/tmp/credentials/gdrive.json" >> $GITHUB_ENV

      - name: Google DriveからCSVファイルを取得
        env:
          FOLDER_ID: ${{ secrets.GDRIVE_FOLDER_ID }}
        run: |
          mkdir -p /tmp/data

          if [ "${{ github.event.inputs.date }}" = "latest" ]; then
            echo "最新ファイルをダウンロード中..."
            python scripts/fetch_from_gdrive.py \
              --folder-id "$FOLDER_ID" \
              --download latest \
              --output /tmp/data
          else
            echo "日付指定でダウンロード中: ${{ github.event.inputs.date }}"
            python scripts/fetch_from_gdrive.py \
              --folder-id "$FOLDER_ID" \
              --download "${{ github.event.inputs.date }}" \
              --output /tmp/data
          fi

          CSV_FILE=$(ls /tmp/data/*.csv | head -n 1)
          echo "CSV_PATH=$CSV_FILE" >> $GITHUB_ENV
          echo "ダウンロード完了: $CSV_FILE"

      - name: 脳波分析を実行
        run: |
          TIMESTAMP=$(date +%Y%m%d_%H%M%S)
          OUTPUT_DIR="/tmp/report_${TIMESTAMP}"

          echo "分析開始..."
          echo "  入力CSV: $CSV_PATH"
          echo "  出力先: $OUTPUT_DIR"

          python issues/003_improve_daily_report/generate_report.py \
            --data "$CSV_PATH" \
            --output "$OUTPUT_DIR"

          echo "OUTPUT_DIR=$OUTPUT_DIR" >> $GITHUB_ENV
          echo "分析完了: $OUTPUT_DIR"

      - name: titan2-reportsリポジトリにレポートをpush
        env:
          PAT_TOKEN: ${{ secrets.PAT_TOKEN }}
        run: |
          git clone https://${PAT_TOKEN}@github.com/tsu-nera/titan2-reports.git /tmp/titan2-reports

          REPORT_DIR=$(basename "$OUTPUT_DIR")
          cp -r "$OUTPUT_DIR" "/tmp/titan2-reports/reports/${REPORT_DIR}"

          cd /tmp/titan2-reports
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"

          CSV_NAME=$(basename "$CSV_PATH")
          COMMIT_DATE=$(date +'%Y-%m-%d %H:%M:%S')

          git add "reports/${REPORT_DIR}"
          git commit -m "Add EEG analysis report - ${COMMIT_DATE}" \
            -m "" \
            -m "Generated from: github.com/${{ github.repository }}/actions/runs/${{ github.run_id }}" \
            -m "Input CSV: ${CSV_NAME}" \
            -m "Report directory: reports/${REPORT_DIR}" \
            -m "" \
            -m "🤖 Generated with GitHub Actions"

          git push origin main

          echo "✅ レポートをtitan2-reportsにpushしました"
          echo "REPORT_DIR=${REPORT_DIR}" >> $GITHUB_ENV

      - name: クリーンアップ
        if: always()
        run: |
          rm -rf /tmp/data
          rm -rf /tmp/credentials
          rm -rf /tmp/titan2-reports

      - name: 分析結果サマリー
        if: success()
        run: |
          echo "✅ 脳波分析が完了しました"
          echo ""
          echo "📊 レポート: reports/${REPORT_DIR}/REPORT.md"
          echo "📁 画像: reports/${REPORT_DIR}/img/"
          echo ""
          echo "🔗 titan2-reportsでレポートを閲覧:"
          echo "   https://github.com/tsu-nera/titan2-reports/blob/main/reports/${REPORT_DIR}/REPORT.md"
```

</details>

---

## ステップ4: コミット＆プッシュ（5分）

```bash
cd /home/tsu-nera/repo/titan2

# 変更確認
git diff .github/workflows/eeg_analysis.yml

# ステージング
git add .github/workflows/eeg_analysis.yml
git add issues/004_report_cloud/PROGRESS.md
git add issues/004_report_cloud/NEXT_STEPS.md

# コミット
git commit -m "Modify workflow to push reports to separate repository (Issue 004 Phase 4)

Changes:
- Push reports to titan2-reports instead of titan2
- Remove git commit to development repository
- Add PAT_TOKEN authentication
- Update cleanup and summary steps

Related: #004"

# プッシュ
git push origin main
```

---

## ステップ5: テスト実行（10分）

### 5.1 GitHub Actionsで実行

**ブラウザで操作:**
```
https://github.com/tsu-nera/titan2/actions
```

1. 「EEG Analysis」ワークフローをクリック
2. 「Run workflow」ボタンをクリック
3. Branch: `main`
4. 日付: `latest`
5. 「Run workflow」（緑ボタン）をクリック

### 5.2 実行状況確認

- 実行一覧に新しいワークフローが表示される
- クリックして詳細ログを確認
- 各ステップが緑色✅になることを確認

**チェックポイント:**
- ✅ Google Driveからダウンロード成功
- ✅ 分析実行成功
- ✅ titan2-reportsへのpush成功
- ❌ 403エラーが出ないこと

### 5.3 レポート確認

**titan2-reportsリポジトリを開く:**
```
https://github.com/tsu-nera/titan2-reports
```

- `reports/` ディレクトリに新しいフォルダが追加されている
- フォルダを開いて `REPORT.md` を確認
- 画像が正しく表示されるか確認

---

## ステップ6: ドキュメント更新（15分）

### 6.1 ARCHITECTURE.md更新

**追記内容:**

```markdown
## 最終設計: 別リポジトリ方式（採用）

### アーキテクチャ図

```
[Mind Monitor] → [Google Drive]
       ↓
[GitHub Actions: titan2]
  ├─ CSV取得
  ├─ 分析実行
  └─ レポートpush
       ↓
[titan2-reports (別リポジトリ)]
  └─ reports/YYYYMMDD_HHMMSS/
       ├─ REPORT.md
       └─ img/*.png
       ↓
[スマホブラウザ] 閲覧
```

### メリット

1. **開発とデータの完全分離**
   - titan2: コード・ドキュメントのみ
   - titan2-reports: 分析結果のみ

2. **コミット履歴のクリーン化**
   - 開発履歴とデータ生成履歴が混在しない
   - git blameが正確

3. **リポジトリサイズ管理**
   - titan2は小さく保てる（10MB程度）
   - titan2-reportsは必要に応じて削除・アーカイブ可能

4. **権限管理**
   - titan2: 開発者に編集権限
   - titan2-reports: Actions専用（人間は閲覧のみ）

### デメリットと対策

**デメリット:**
- Personal Access Token (PAT)の管理が必要
- 90日毎にトークン更新（expiration設定による）

**対策:**
- GitHub App認証への移行検討（長期運用時）
- または "No expiration" に設定（セキュリティリスク考慮）
```

### 6.2 USAGE.md更新

**修正箇所: レポート閲覧方法**

```markdown
### 5. レポートを閲覧

実行完了後（緑色のチェックマーク）:

**新しいリポジトリで閲覧:**
1. **titan2-reportsリポジトリ**を開く
   ```
   https://github.com/tsu-nera/titan2-reports
   ```
2. `reports/` フォルダを開く
3. 最新のタイムスタンプフォルダ（例: `20251104_153000`）を開く
4. `REPORT.md` をタップして閲覧

**または、Actions実行ログから直接アクセス:**
- Actionsの「分析結果サマリー」ステップにリンクが表示されます
```

### 6.3 README.md更新

```markdown
## リポジトリ構成

- **titan2** (このリポジトリ): 開発コード・ドキュメント
- **[titan2-reports](https://github.com/tsu-nera/titan2-reports)**: 分析レポート保管
```

---

## トラブルシューティング

### エラー1: PAT_TOKENが見つからない

**エラー:**
```
fatal: could not read Username for 'https://github.com': No such device or address
```

**原因:** `PAT_TOKEN` がSecretsに登録されていない

**対処:**
- ステップ2.2を再確認
- Secretsに `PAT_TOKEN` が存在するか確認

### エラー2: 403 Forbidden (再発)

**エラー:**
```
remote: Permission to tsu-nera/titan2-reports.git denied
```

**原因:** PATのスコープが不足

**対処:**
- PATの `repo` スコープが有効か確認
- 新しいトークンを生成してSecrets更新

### エラー3: titan2-reportsが見つからない

**エラー:**
```
fatal: repository 'https://github.com/tsu-nera/titan2-reports.git' not found
```

**原因:** リポジトリが作成されていない、またはprivate

**対処:**
- ステップ1を完了させる
- リポジトリ名のスペルミスを確認

---

## 所要時間見積もり

| ステップ | 内容 | 所要時間 |
|---------|------|---------|
| 1 | titan2-reports作成 | 5分 |
| 2 | PAT作成・設定 | 5分 |
| 3 | ワークフロー修正 | 15分 |
| 4 | コミット＆プッシュ | 5分 |
| 5 | テスト実行 | 10分 |
| 6 | ドキュメント更新 | 15分 |
| **合計** | | **約55分** |

---

## チェックリスト

### 準備
- [ ] titan2-reportsリポジトリが作成済み
- [ ] READMEが初期化済み
- [ ] PAT_TOKENが生成済み
- [ ] GitHub SecretsにPAT_TOKENが登録済み

### 実装
- [ ] eeg_analysis.yml修正完了
- [ ] バックアップファイル作成済み
- [ ] YAML構文チェック（ローカル）
- [ ] コミット＆プッシュ完了

### テスト
- [ ] GitHub Actionsでワークフロー実行
- [ ] エラーなく完了
- [ ] titan2-reportsにレポート生成確認
- [ ] REPORT.mdが正しく表示される
- [ ] 画像が正しく表示される

### ドキュメント
- [ ] ARCHITECTURE.md更新
- [ ] USAGE.md更新
- [ ] README.md更新
- [ ] PROGRESS.md更新

---

**準備完了！明日の作業を開始できます 🚀**
