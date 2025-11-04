# 脳波分析レポート

このディレクトリには、GitHub Actionsで自動生成された脳波分析レポートが保存されます。

## ディレクトリ構造

```
reports/
  20251104_153000/          # タイムスタンプ付きディレクトリ
    REPORT.md               # 分析レポート（Markdown）
    img/                    # グラフ画像（15枚）
      band_power_time_series.png
      psd.png
      spectrogram.png
      frontal_midline_theta.png
      paf.png
      ...
  20251105_090000/
    REPORT.md
    img/
      ...
```

## レポートの見方

各ディレクトリ内の `REPORT.md` を開くと、以下の内容が表示されます：

1. **データ品質評価**: HSI接続品質、信号品質
2. **基本統計**: バンドパワー（Delta, Theta, Alpha, Beta, Gamma）
3. **高度な指標**:
   - Frontal Midline Theta (Fmθ): 瞑想深度
   - Peak Alpha Frequency (PAF): 個人アルファ周波数
   - Frontal Alpha Asymmetry (FAA): 左右半球バランス
   - Spectral Entropy (SE): 注意集中度
   - Band Ratios: リラックス度、集中度
4. **時間経過分析**: セグメント別、前半・後半比較
5. **総合スコア**: 0-100点（5指標統合）

## レポート生成方法

### GitHub Actionsで自動生成（推奨）

1. GitHubリポジトリの「Actions」タブを開く
2. 「EEG Analysis」ワークフローを選択
3. 「Run workflow」ボタンをクリック
4. 日付指定（オプション）して実行
5. 4-7分後、このディレクトリに新しいレポートが追加される

### ローカルで手動生成

```bash
# 仮想環境アクティベート
source titan/bin/activate

# 分析実行
python issues/003_improve_daily_report/generate_report.py \
  --data data/your_csv_file.csv \
  --output reports/$(date +%Y%m%d_%H%M%S)
```

## 履歴管理

- すべてのレポートはGit管理下にあります
- 過去のレポートを比較して進捗確認が可能
- 古いレポートは手動で削除してください（90日以上経過したものを推奨）

## 関連ドキュメント

- [Issue 003: 日次レポート改善](../issues/003_improve_daily_report/ISSUE.md)
- [Issue 004: スマホから分析](../issues/004_report_cloud/ISSUE.md)
