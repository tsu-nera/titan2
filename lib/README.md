# Mind Monitor Analysis Library

Mind Monitor (Muse S) のデータから生理学的指標を解析するためのPythonライブラリです。

## 機能

### 1. データローダー (`data_loader.py`)
- Mind Monitor CSVファイルの読み込み
- 品質フィルタリング（HeadBandOn=1）
- Opticsデータ・心拍数データの抽出
- データ概要統計の取得

### 2. fNIRS解析 (`fnirs.py`)
- Modified Beer-Lambert LawによるHbO/HbR計算
- 730nm/850nmの2波長データを使用
- 左右前頭葉の脳活動解析
- Muse App準拠のスケール調整

### 3. 呼吸数推定 (`respiratory.py`)
- 心拍変動（HRV）からの呼吸数推定
- RRインターバル計算
- FFT法・Welch法による周波数解析
- RSA (Respiratory Sinus Arrhythmia) 利用

### 4. 可視化 (`visualization.py`)
- fNIRS時系列プロット（HbO/HbR）
- 心拍数・呼吸数の時系列プロット
- 周波数スペクトル表示
- 統合ダッシュボード

## 使用例

### 基本的な使用方法

```python
from lib import (
    load_mind_monitor_csv,
    get_optics_data,
    get_heart_rate_data,
    analyze_fnirs,
    analyze_respiratory,
    plot_integrated_dashboard
)
import matplotlib.pyplot as plt

# データ読み込み
df = load_mind_monitor_csv("data.csv", quality_filter=True)

# fNIRS解析
optics_data = get_optics_data(df)
fnirs_results = analyze_fnirs(optics_data)

# 呼吸数推定
hr_data = get_heart_rate_data(df)
respiratory_results = analyze_respiratory(hr_data)

# 統合ダッシュボード
fig, gs = plot_integrated_dashboard(fnirs_results, hr_data, respiratory_results)
plt.show()
```

### Jupyter Notebookでの使用

詳細な解析例は [`notebooks/integrated_physiological_analysis.ipynb`](../notebooks/integrated_physiological_analysis.ipynb) を参照してください。

## インストール

必要なライブラリ:
```bash
pip install pandas numpy matplotlib scipy
```

## ライブラリ構成

```
lib/
├── __init__.py          # パッケージ初期化
├── data_loader.py       # データ読み込み・前処理
├── fnirs.py             # fNIRS解析
├── respiratory.py       # 呼吸数推定
├── visualization.py     # 可視化関数
└── README.md            # このファイル
```

## API リファレンス

### data_loader

#### `load_mind_monitor_csv(csv_path, quality_filter=True)`
CSVファイルを読み込み、前処理を実行します。

**Parameters:**
- `csv_path` (str): CSVファイルのパス
- `quality_filter` (bool): HeadBandOn=1でフィルタリングするか

**Returns:**
- `df` (pd.DataFrame): 読み込んだデータフレーム

#### `get_optics_data(df)`
Opticsデータを抽出します。

**Returns:**
- `dict`: `{'left_730', 'left_850', 'right_730', 'right_850', 'time'}`

#### `get_heart_rate_data(df)`
心拍数データを抽出します（Heart_Rate > 0）。

**Returns:**
- `dict`: `{'heart_rate', 'time', 'timestamps'}`

### fnirs

#### `analyze_fnirs(optics_data)`
fNIRS解析を実行します。

**Parameters:**
- `optics_data` (dict): `get_optics_data()`の戻り値

**Returns:**
- `dict`: `{'left_hbo', 'left_hbr', 'right_hbo', 'right_hbr', 'time', 'stats'}`

### respiratory

#### `analyze_respiratory(hr_data)`
呼吸数推定を実行します。

**Parameters:**
- `hr_data` (dict): `get_heart_rate_data()`の戻り値

**Returns:**
- `dict`: `{'rr_intervals', 'respiratory_rate_welch', 'respiratory_rates_fft', ...}`

### visualization

#### `plot_integrated_dashboard(fnirs_results, hr_data, respiratory_results)`
統合ダッシュボードを生成します。

**Parameters:**
- `fnirs_results` (dict): `analyze_fnirs()`の戻り値
- `hr_data` (dict): `get_heart_rate_data()`の戻り値
- `respiratory_results` (dict): `analyze_respiratory()`の戻り値

**Returns:**
- `fig`, `gs`: Matplotlib figure と GridSpec

## テスト

動作確認スクリプト:
```bash
python test_lib.py
```

## ライセンス

MIT License

## 作成日

2025-10-26
