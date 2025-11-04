# 使い方ガイド: スマホから脳波分析を実行

このガイドでは、スマホからGitHub Actionsを使って脳波分析を実行し、レポートを閲覧する方法を説明します。

---

## 前提条件

- [SETUP_GDRIVE.md](SETUP_GDRIVE.md) の手順を完了していること
- GitHub Secretsが設定されていること:
  - `GDRIVE_CREDENTIALS`: サービスアカウントJSON
  - `GDRIVE_FOLDER_ID`: Google DriveフォルダID

---

## 方法1: GitHub Mobile アプリ（推奨）

### 1. GitHub Mobile をインストール

- iOS: [App Store](https://apps.apple.com/app/github/id1477376905)
- Android: [Google Play](https://play.google.com/store/apps/details?id=com.github.android)

### 2. リポジトリを開く

1. アプリを開いてログイン
2. 「Repositories」→ `titan2` を選択

### 3. Actionsを実行

1. 下部タブの「Actions」をタップ
2. 「EEG Analysis」ワークフローを選択
3. 右上の「⋯」（三点リーダー）→「Run workflow」をタップ
4. ブランチ選択（通常は `main` または `issue-004`）
5. **日付指定（オプション）**:
   - 空欄 or `latest`: 最新ファイルを分析
   - `2025-11-04`: 特定日付のファイルを分析
6. 「Run workflow」ボタンをタップ

### 4. 実行状況の確認

1. ワークフロー実行一覧に戻る
2. 最新の実行（黄色い点＝実行中）をタップ
3. 「analyze」ジョブをタップして詳細ログを確認
4. 実行時間: 約4-7分

### 5. レポートを閲覧

1. 実行完了後（緑色のチェックマーク）
2. 「Code」タブに戻る
3. `reports/` フォルダを開く
4. 最新のタイムスタンプフォルダ（例: `20251104_153000`）を開く
5. `REPORT.md` をタップして閲覧

---

## 方法2: Webブラウザ（PC/スマホ両対応）

### 1. リポジトリにアクセス

ブラウザで以下にアクセス:
```
https://github.com/<your-username>/titan2
```

### 2. Actionsタブを開く

1. 上部タブの「Actions」をクリック
2. 左サイドバーから「EEG Analysis」を選択

### 3. ワークフローを実行

1. 右上の「Run workflow」ボタンをクリック
2. ドロップダウンが表示される:
   - **Branch**: `main` または `issue-004`
   - **日付指定**: 空欄 or `latest` or `2025-11-04`
3. 緑色の「Run workflow」ボタンをクリック

### 4. 実行状況の確認

1. ワークフロー実行一覧に新しい実行が表示される
2. クリックして詳細画面へ
3. 「analyze」ジョブをクリックして各ステップの進捗を確認

### 5. レポートを閲覧

実行完了後:
1. 「Code」タブに戻る
2. `reports/` → タイムスタンプフォルダ → `REPORT.md` を開く

---

## レポートの見方

### REPORT.md の構成

1. **セッション基本情報**
   - 記録時間、計測時間
   - データ品質評価

2. **データ品質**
   - HSI接続品質（各電極の信号品質）

3. **基本周波数バンド統計**
   - Delta, Theta, Alpha, Beta, Gamma の平均値

4. **パワースペクトル密度（PSD）**
   - 各周波数帯のパワー分布グラフ

5. **スペクトログラム**
   - 時間経過による周波数パワーの変化

6. **高度な指標**
   - **Frontal Midline Theta (Fmθ)**: 瞑想深度
     - 高いほど深い瞑想状態
   - **Peak Alpha Frequency (PAF)**: 個人アルファ周波数
     - 8-13Hz の範囲で最もパワーが強い周波数
   - **Frontal Alpha Asymmetry (FAA)**: 左右半球バランス
     - 正の値: 左半球優位（ポジティブ感情）
     - 負の値: 右半球優位（ネガティブ感情）
   - **Spectral Entropy (SE)**: 注意集中度
     - 低いほど集中している
   - **Band Ratios**:
     - Theta/Beta 比: 瞑想深度
     - Alpha/Theta 比: リラックス度

7. **時間経過分析**
   - 5分毎のセグメント比較
   - ピークパフォーマンスの検出

8. **fNIRS分析**
   - 脳血流（HbO, HbR）の測定

9. **総合スコア（0-100点）**
   - 5つの指標を統合したスコア

### 画像の確認

`img/` フォルダには以下の画像が保存されています:

- `band_power_time_series.png`: バンドパワーの時間推移
- `psd.png`: パワースペクトル密度
- `spectrogram.png`: スペクトログラム
- `frontal_midline_theta.png`: Fmθの時間推移
- `paf.png`: PAF分布
- `frontal_alpha_asymmetry.png`: FAA時間推移
- `spectral_entropy.png`: SE時間推移
- `band_ratios.png`: バンド比率
- `time_segment_metrics.png`: セグメント別比較（重要！）
- その他

---

## トラブルシューティング

### ワークフローが失敗する

#### エラー: "CSVファイルが見つかりません"

**原因**: Google Driveにファイルがない、またはフォルダIDが間違っている

**対処法**:
1. Google Driveにファイルがアップロードされているか確認
2. GitHub Secretsの `GDRIVE_FOLDER_ID` が正しいか確認
3. サービスアカウントにフォルダ共有されているか確認

#### エラー: "認証失敗"

**原因**: GitHub Secretsの設定ミス

**対処法**:
1. [SETUP_GDRIVE.md](SETUP_GDRIVE.md) の Step 6 を再確認
2. `GDRIVE_CREDENTIALS` に正しいJSON全文がコピーされているか確認

#### エラー: "メモリ不足"

**原因**: 超長時間セッション（2時間以上）でメモリ不足

**対処法**:
- セッションを30分以内に分割する
- ローカルPCで分析する（GitHub Actions回避）

### "Run workflow" ボタンが表示されない

**原因**: ブランチにワークフローファイルがpushされていない

**対処法**:
1. `.github/workflows/eeg_analysis.yml` がリポジトリに存在するか確認
2. 最新のコミットがpushされているか確認
3. 正しいブランチを選択しているか確認

### レポートが生成されない

**原因**: 分析中にエラーが発生

**対処法**:
1. Actions の実行ログを確認
2. 「analyze」ジョブ → 「脳波分析を実行」ステップのログを読む
3. エラーメッセージを確認

---

## よくある質問

### Q: 複数のCSVファイルがある場合、どれが選ばれる？

**A**: 日付を指定しない場合、更新日時が最新のファイルが選ばれます。

### Q: 古いレポートは自動削除される？

**A**: いいえ、手動で削除する必要があります。90日以上経過したレポートは定期的に削除することを推奨します。

### Q: privateリポジトリでも使える？

**A**: はい。GitHub Actions無料枠は月2,000分（privateリポジトリ）です。

### Q: 1ヶ月に何回分析できる？

**A**: 1回の分析が5分の場合、月に約400回可能です（無料枠内）。

### Q: スマホから直接CSVをアップロードできる？

**A**: 現在はGoogle Drive経由のみです。将来的にWebフォームからのアップロード機能を追加予定（Phase 7）。

### Q: リアルタイムで実行できる？

**A**: 手動トリガーのみです。自動実行（例: CSV更新時）は技術的に可能ですが、現在は未実装です。

---

## 次のステップ

### GitHub Pagesでレポートを見やすくする

HTMLベースのダッシュボードを作成して、より見やすいUIでレポートを閲覧できます。

詳細: [ARCHITECTURE.md - Phase 7拡張案](ARCHITECTURE.md#phase-7以降オプション)

### Slack/LINE通知

分析完了時に通知を送信する機能を追加できます。

### データベース統合

過去のスコアを蓄積して、進捗グラフを生成できます。

---

## 参考リンク

- [GitHub Actions ドキュメント](https://docs.github.com/ja/actions)
- [GitHub Mobile ヘルプ](https://docs.github.com/ja/get-started/using-github/github-mobile)
- [Issue 003: 日次レポート改善](../003_improve_daily_report/ISSUE.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)

---

**作成日**: 2025-11-04
**最終更新**: 2025-11-04
