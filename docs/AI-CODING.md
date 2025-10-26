# AI Coding Guidelines

このドキュメントは、Codex CLI、Claude Code、およびその他のAIコーディングツールが共通で参照するプロジェクトガイドラインです。

---

## プロジェクト概要

Muse Headband（脳波測定デバイス）から取得したデータの解析プロジェクトです。

---

## Python 仮想環境

### 環境名
- `titan`

### セットアップ手順
```bash
# 環境の作成
python3 -m venv titan

# 有効化 (WSL/Linux)
source titan/bin/activate

# パッケージインストール
pip install -r requirements.txt
```

### インストール済みパッケージ
- `numpy`
- `pandas`
- `matplotlib`
- `seaborn`
- `jupyterlab`
- `scipy`

---

## 開発環境

### Jupyter Lab
分析用ノートブックは以下で起動します：
```bash
jupyter lab
```

### WSL2 環境
Google Drive (Windows側 `G:`) をWSL2から扱う場合：
```bash
sudo mount -t drvfs G: /mnt/g
```
マウント後は `/mnt/g/マイドライブ/` 以下のデータを参照できます。

---

## データ仕様

### Mind Monitor CSV Data

Mind Monitor (Muse Headband用アプリ) のCSVデータを扱う場合は、以下のドキュメントを参照してください：

**仕様書**: [docs/MIND_MONITOR_CSV_SPECIFICATION.md](MIND_MONITOR_CSV_SPECIFICATION.md)

#### 含まれる情報
- 全カラムの詳細仕様（単位、範囲、説明）
- センサー位置と脳波周波数帯域の説明
- データ品質管理の方法
- サンプリングレートと欠損値の扱い

---

## コーディング規約

### Python コードスタイル
- PEP 8に準拠
- 関数・クラスには必ずdocstringを記述
- 型ヒントを推奨

### ファイル構成
```
titan2/
├── data/              # データファイル
│   └── samples/       # サンプルCSVデータ
├── docs/              # ドキュメント
├── notebooks/         # Jupyter notebooks
├── scripts/           # Python スクリプト
└── titan/             # Python 仮想環境
```

### 命名規則
- スクリプト名: `snake_case.py`
- クラス名: `PascalCase`
- 関数・変数名: `snake_case`

---

## テスト

### 実行方法
```bash
# 全テスト実行（将来的に追加予定）
pytest

# 特定テスト実行
pytest tests/test_specific.py
```

---

## コミットメッセージ

### フォーマット
```
<type>: <subject>

<body>
```

### Type
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメントのみの変更
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: ビルド、設定変更

---

## 解析関連

### 実装済み機能
- **呼吸数推定**: `scripts/respiratory_rate_estimation.py`
  - 心拍変動（HRV）からRSA解析により呼吸数を推定
  - FFTおよびWelch法による周波数解析

### データ品質管理
Mind Monitorデータのフィルタリング例：
```python
# 良質なデータのみを抽出
df_quality = df[
    (df['HeadBandOn'] == 1) &  # 装着中
    (df['HSI_TP9'] == 1) &      # 全センサー良好
    (df['HSI_AF7'] == 1) &
    (df['HSI_AF8'] == 1) &
    (df['HSI_TP10'] == 1)
]
```

---

## 参考資料

### 外部ドキュメント
- [Mind Monitor FAQ](https://mind-monitor.com/FAQ.php)
- [Muse Developer Docs](https://choosemuse.com/pages/developers)
- [EEG Wikipedia](https://en.wikipedia.org/wiki/Electroencephalography)

---

**最終更新**: 2025-10-26
**バージョン**: 1.0
