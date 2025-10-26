# Muse脳波データ分析ノートブック

このディレクトリには、Museヘッドバンドで取得した脳波データを分析するためのJupyter Notebookが含まれています。

## ノートブック一覧

### 1. 基本分析: [mind_monitor_basic_analysis.ipynb](mind_monitor_basic_analysis.ipynb)

**推奨実行順序: 最初**

Muse脳波データの基本的な分析を行います。すべての分析の起点となるノートブックです。

**内容:**
- データの読み込みと前処理
- 基本統計量の確認
- バンドパワー分析（Delta, Theta, Alpha, Beta, Gamma）
- 周波数解析（PSD、スペクトログラム）
- リラックス度・集中度のスコア化

**出力:**
- 各周波数バンドの時系列グラフ
- パワースペクトル密度（PSD）
- スペクトログラム
- 脳波指標の時間推移

---

### 2. 左右半球差分析: [laterality_analysis.ipynb](laterality_analysis.ipynb)

**推奨実行順序: 2番目**

脳の左右半球間の非対称性を詳細に分析します。感情状態や認知処理の傾向を評価します。

**内容:**
- 左右半球の非対称性指数（AI）の計算
- 左右差の時系列変化
- ヒートマップによる可視化
- 前頭部Alpha非対称性と感情状態の関連
- 前頭部Beta非対称性と認知処理の偏り

**主要な指標:**
- **前頭部Alpha非対称性**: 感情状態の評価（ポジティブ/ネガティブ傾向）
- **前頭部Beta非対称性**: 認知処理の傾向（言語処理/空間認識）

**出力:**
- 左右差の時系列グラフ
- バンド×領域のヒートマップ
- 感情状態の分布
- 解釈ガイド

---

### 3. fmシータ波分析: [fm_theta_analysis.ipynb](fm_theta_analysis.ipynb)

**推奨実行順序: 3番目**

サマタ瞑想中の前頭部ミッドラインシータ波（fmシータ）を分析し、瞑想の深さを定量的に評価します。

**内容:**
- 前頭部シータ波パワーの時間推移
- シータ/アルファ比による瞑想深度測定
- シータ波の周波数詳細分析
- 瞑想の深まりの評価（前半vs後半）

**fmシータ波とは:**
- **周波数**: 4-8 Hz
- **位置**: 前頭部正中線（Fz、FCz付近）
- **意味**: 集中的な注意、瞑想の深まりと相関

**主要な指標:**
- **シータ/アルファ比 > 1.0**: 深い瞑想状態
- **ピーク周波数 5.5-6.5 Hz**: fmシータの典型的範囲

**出力:**
- シータ波パワーの時系列グラフ
- シータ/アルファ比の推移
- 周波数スペクトル詳細
- 瞑想深度の統計サマリー

---

## 実行方法

### 1. 環境準備

```bash
# 必要なライブラリのインストール
pip install pandas numpy matplotlib mne scipy
```

### 2. ノートブックの実行順序

```bash
# Jupyter Notebookを起動
jupyter notebook

# 以下の順序で実行することを推奨：
1. mind_monitor_basic_analysis.ipynb  # 基本分析
2. laterality_analysis.ipynb          # 左右差分析
3. fm_theta_analysis.ipynb            # fmシータ波分析
```

各ノートブックは独立して実行可能ですが、基本分析を先に実行することで、全体像を把握してから詳細分析に進むことができます。

---

## データ形式

**入力データ:** Mind Monitor形式のCSVファイル

```
../data/samples/mindMonitor_YYYY-MM-DD--HH-MM-SS_*.csv
```

**必要なカラム:**
- `TimeStamp`: タイムスタンプ
- `Delta_TP9`, `Delta_AF7`, `Delta_AF8`, `Delta_TP10`: Deltaバンドパワー
- `Theta_*`, `Alpha_*`, `Beta_*`, `Gamma_*`: 各バンドパワー
- `RAW_TP9`, `RAW_AF7`, `RAW_AF8`, `RAW_TP10`: RAW脳波データ

---

## 出力ファイル

各ノートブックを実行すると、以下のような出力が得られます：

- **グラフ**: ノートブック内に埋め込まれた可視化
- **統計サマリー**: 数値による評価結果
- **解釈**: AIによる自動解釈とガイド

---

## 参考文献

- **fmシータ波と瞑想**: Aftanas & Golocheikine (2001)
- **前頭部Alpha非対称性**: Davidson (2004)
- **脳波バンドの意味**: Niedermeyer & da Silva (2005)

---

## トラブルシューティング

### フォントエラー

日本語フォントがない場合：

```python
# セルの先頭で以下を実行
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False
```

### MNEの警告

MNEライブラリの警告は無視しても問題ありません。重要なエラーが発生した場合は、MNEのバージョンを確認してください：

```bash
pip install --upgrade mne
```

---

## ライセンス

このノートブック群は、個人的な脳波データ分析と学習目的で使用できます。

---

## 更新履歴

- **2025-10-19**: 初版作成、単一ノートブックを3つに分割
