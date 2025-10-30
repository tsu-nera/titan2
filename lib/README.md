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

### 5. EEG解析 (`eeg.py`)
- 周波数バンド統計（Delta, Theta, Alpha, Beta, Gamma）
- MNE-Pythonによるパワースペクトル密度（PSD）計算
- スペクトログラム（Time-Frequency Representation）
- Peak Alpha Frequency（PAF）分析
- バンド比率計算（リラックス度、集中度、瞑想深度）
- PAF時間推移の追跡
- EEG可視化機能（時系列、PSD、スペクトログラム、PAF）

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

### EEG解析の使用例

```python
from lib import (
    load_mind_monitor_csv,
    calculate_band_statistics,
    prepare_mne_raw,
    calculate_psd,
    calculate_paf,
    plot_psd,
    plot_paf
)
import matplotlib.pyplot as plt

# データ読み込み
df = load_mind_monitor_csv("data.csv", quality_filter=False)

# バンド統計
band_stats = calculate_band_statistics(df)
print(band_stats['statistics'])

# MNE RawArray準備
mne_dict = prepare_mne_raw(df)
raw = mne_dict['raw']

# PSD計算
psd_dict = calculate_psd(raw)

# PAF分析
paf_dict = calculate_paf(psd_dict)
print(f"IAF: {paf_dict['iaf']:.2f} Hz")

# 可視化
plot_psd(psd_dict, img_path='psd.png')
plot_paf(paf_dict, img_path='paf.png')
```

### Jupyter Notebookでの使用

詳細な解析例は以下を参照してください：
- [`notebooks/integrated_physiological_analysis.ipynb`](../notebooks/integrated_physiological_analysis.ipynb) - fNIRS・呼吸数解析
- [`issues/001_basic_analysis/`](../issues/001_basic_analysis/) - EEG基本解析の実装例

## インストール

必要なライブラリ:
```bash
pip install pandas numpy matplotlib scipy mne
```

## ライブラリ構成

```
lib/
├── __init__.py          # パッケージ初期化
├── data_loader.py       # データ読み込み・前処理
├── fnirs.py             # fNIRS解析
├── respiratory.py       # 呼吸数推定
├── eeg.py               # EEG解析（NEW）
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

### eeg

#### `calculate_band_statistics(df, bands=None)`
各周波数バンドの基本統計を計算します。

**Parameters:**
- `df` (pd.DataFrame): Mind Monitorデータフレーム
- `bands` (list, optional): バンド名リスト

**Returns:**
- `dict`: `{'statistics': pd.DataFrame, 'bands': list}`

#### `prepare_mne_raw(df, sfreq=None)`
MNE RawArrayを準備します。

**Parameters:**
- `df` (pd.DataFrame): Mind Monitorデータフレーム
- `sfreq` (float, optional): サンプリングレート

**Returns:**
- `dict`: `{'raw': mne.io.RawArray, 'channels': list, 'sfreq': float, 'n_samples': int}`

#### `calculate_psd(raw, fmin=0.5, fmax=50.0, n_fft=512)`
パワースペクトル密度を計算します。

**Parameters:**
- `raw` (mne.io.RawArray): MNE RawArray
- `fmin`, `fmax` (float): 周波数範囲
- `n_fft` (int): FFTウィンドウサイズ

**Returns:**
- `dict`: `{'freqs': np.ndarray, 'psds': np.ndarray, 'channels': list, 'spectrum': mne.Spectrum}`

#### `calculate_paf(psd_dict, alpha_range=(8.0, 13.0))`
Peak Alpha Frequencyを計算します。

**Parameters:**
- `psd_dict` (dict): `calculate_psd()`の戻り値
- `alpha_range` (tuple): Alpha帯域範囲

**Returns:**
- `dict`: `{'paf_by_channel': dict, 'iaf': float, 'iaf_std': float, 'alpha_range': tuple}`

#### `plot_band_power_time_series(df, bands=None, img_path=None, rolling_window=50)`
バンドパワーの時系列をプロットします。

**Parameters:**
- `df` (pd.DataFrame): Mind Monitorデータフレーム
- `bands` (list, optional): バンド名リスト
- `img_path` (str or Path, optional): 保存先パス
- `rolling_window` (int): 移動平均ウィンドウサイズ

**Returns:**
- `fig`: Matplotlib figure

#### `plot_psd(psd_dict, bands=None, img_path=None)`
PSDをプロットします。

**Parameters:**
- `psd_dict` (dict): `calculate_psd()`の戻り値
- `bands` (dict, optional): バンド定義辞書
- `img_path` (str or Path, optional): 保存先パス

**Returns:**
- `fig`: Matplotlib figure

詳細は [`lib/eeg.py`](eeg.py) のdocstringを参照してください。

## テスト

動作確認スクリプト:
```bash
python test_lib.py
```

## ライセンス

MIT License

## 更新履歴

- **2025-10-30**: `eeg.py` 追加 - EEG周波数バンド解析、PSD、PAF、スペクトログラム機能を実装
- **2025-10-26**: 初版作成 - fNIRS、呼吸数推定、可視化機能
