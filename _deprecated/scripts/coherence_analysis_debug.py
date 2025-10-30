"""
脳波コヒーレンス分析スクリプト（デバッグ用）

ノートブックの内容をPythonスクリプトとして実行可能にしたバージョン
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mne

# MNEのバージョンに応じたインポート
try:
    from mne_connectivity import spectral_connectivity_epochs
    print("✓ mne_connectivity からインポート成功")
except ImportError:
    try:
        from mne.connectivity import spectral_connectivity_epochs
        print("✓ mne.connectivity からインポート成功")
    except ImportError:
        print("❌ 警告: mne-connectivity がインストールされていません")
        print("以下のコマンドでインストールしてください:")
        print("pip install mne-connectivity")
        exit(1)

import seaborn as sns

# 日本語フォント設定
plt.rcParams['font.family'] = 'Noto Sans CJK JP'
plt.rcParams['axes.unicode_minus'] = False

print("=" * 60)
print("1. データの読み込みと前処理")
print("=" * 60)

# データファイルのパス
DATA_PATH = Path('/home/tsu-nera/repo/titan2/data/samples/mindMonitor_2025-10-26--08-32-20_1403458594426768660.csv')
print(f'Loading: {DATA_PATH}')

# CSVを読み込み
df = pd.read_csv(DATA_PATH, low_memory=False)

# タイムスタンプを日時型に変換
df['TimeStamp'] = pd.to_datetime(df['TimeStamp'], errors='coerce')
df = df.dropna(subset=['TimeStamp']).sort_values('TimeStamp').reset_index(drop=True)

print(f'\nデータ形状: {df.shape[0]} 行 × {df.shape[1]} 列')
print(f'記録時間: {df["TimeStamp"].min()} ~ {df["TimeStamp"].max()}')
print(f'計測時間: {(df["TimeStamp"].max() - df["TimeStamp"].min()).total_seconds():.1f} 秒')

print("\n" + "=" * 60)
print("2. RAWデータの準備")
print("=" * 60)

# RAWチャネルの検出とMNE準備
raw_cols = [c for c in df.columns if c.startswith('RAW_')]

if not raw_cols:
    print('❌ RAWチャネルが見つかりません')
    exit(1)

# 数値変換と前処理
numeric = df[raw_cols].apply(pd.to_numeric, errors='coerce')
frame = pd.concat([df['TimeStamp'], numeric], axis=1)
frame = frame.set_index('TimeStamp')

# 重複タイムスタンプは平均化
frame = frame.groupby(level=0).mean()

# 時間補間で欠損値を埋める
frame = frame.interpolate(method='time').ffill().bfill()

# サンプリングレートの推定
diffs = frame.index.to_series().diff().dropna()
dt_seconds = diffs.median().total_seconds()
sfreq = 1.0 / dt_seconds if dt_seconds > 0 else 256.0

# MNE RawArrayの作成
ch_names = [name.replace('RAW_', '') for name in frame.columns]
ch_types = ['eeg'] * len(ch_names)
info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)

# μVスケールをVに変換
data = frame.to_numpy().T * 1e-6

raw = mne.io.RawArray(data, info, copy='auto', verbose=False)

# バンドパスフィルタ（1-50 Hz）
if sfreq > 2.0:
    raw = raw.filter(l_freq=1.0, h_freq=50.0, fir_design='firwin', verbose=False)

print(f'✓ 検出されたチャネル: {ch_names}')
print(f'✓ 推定サンプリングレート: {sfreq:.2f} Hz')
print(f'✓ サンプル数: {len(frame)}')
print(f'✓ 記録時間: {len(frame) / sfreq:.1f} 秒')

print("\n" + "=" * 60)
print("3. エポック分割")
print("=" * 60)

# 10秒エポックに分割
epoch_duration = 10.0  # 秒

# エポック作成用のイベント生成
n_samples = len(raw.times)
epoch_samples = int(epoch_duration * sfreq)
n_epochs = n_samples // epoch_samples

print(f'総サンプル数: {n_samples}')
print(f'エポックサンプル数: {epoch_samples}')
print(f'エポック数: {n_epochs}')

# イベント配列作成（各エポックの開始位置）
events = np.zeros((n_epochs, 3), dtype=int)
for i in range(n_epochs):
    events[i] = [i * epoch_samples, 0, 1]

print(f'✓ イベント配列作成完了: {events.shape}')

# エポック作成
epochs = mne.Epochs(
    raw,
    events,
    tmin=0,
    tmax=epoch_duration - 1/sfreq,
    baseline=None,
    preload=True,
    verbose=False
)

print(f'✓ エポック数: {len(epochs)}')
print(f'✓ エポック長: {epoch_duration} 秒')

print("\n" + "=" * 60)
print("4. コヒーレンス計算")
print("=" * 60)

print('コヒーレンスを計算中...')

# コヒーレンス計算
con = spectral_connectivity_epochs(
    epochs,
    method='coh',  # コヒーレンス
    mode='multitaper',
    fmin=1.0,
    fmax=50.0,
    faverage=False,
    verbose=False
)

print(f'✓ コヒーレンス計算完了')
print(f'  con オブジェクト型: {type(con)}')
print(f'  con の属性: {dir(con)}')

# 結果を取得（デバッグ情報付き）
print('\nデータ取得中...')
coherence = con.get_data(output='dense')
print(f'✓ coherence の型: {type(coherence)}')
print(f'✓ coherence の形状: {coherence.shape}')

# 周波数情報の取得（デバッグ）
print('\n周波数情報取得中...')
freqs = con.freqs
print(f'✓ freqs の型: {type(freqs)}')

# freqs がリストの場合は numpy array に変換
if isinstance(freqs, list):
    print('⚠️  freqs がリストなので numpy array に変換します')
    freqs = np.array(freqs)
    print(f'✓ 変換後の型: {type(freqs)}')

print(f'✓ freqs の形状: {freqs.shape if hasattr(freqs, "shape") else len(freqs)}')
print(f'✓ 周波数範囲: {freqs.min():.2f} - {freqs.max():.2f} Hz')
print(f'✓ 周波数点数: {len(freqs)}')

# エポック間で平均
print('\nエポック間で平均化中...')
coherence_avg = coherence.mean(axis=0)
print(f'✓ coherence_avg の形状: {coherence_avg.shape}')

print("\n" + "=" * 60)
print("5. 可視化準備完了")
print("=" * 60)

# バンド定義
band_ranges = {
    'Delta': (0.5, 4),
    'Theta': (4, 8),
    'Alpha': (8, 13),
    'Beta': (13, 30),
    'Gamma': (30, 50)
}

# チャネルペアの定義
channel_pairs = [
    ('TP9', 'TP10', '左右側頭部'),
    ('AF7', 'AF8', '左右前頭部'),
    ('TP9', 'AF7', '左側 側頭-前頭'),
    ('TP10', 'AF8', '右側 側頭-前頭'),
    ('TP9', 'AF8', '対角 左側頭-右前頭'),
    ('AF7', 'TP10', '対角 左前頭-右側頭'),
]

print(f'✓ チャネル数: {len(ch_names)}')
print(f'✓ チャネルペア数: {len(channel_pairs)}')
print(f'✓ バンド数: {len(band_ranges)}')

print("\n" + "=" * 60)
print("6. 簡単な統計サマリー")
print("=" * 60)

# 各バンドの平均コヒーレンスを計算
for band_name, (low, high) in band_ranges.items():
    mask = (freqs >= low) & (freqs <= high)
    if mask.any():
        # 全チャネルペアの平均
        band_coherence = coherence_avg[:, :, mask].mean(axis=2)

        # 対角線を除く（自己コヒーレンスを除外）
        off_diag_mask = ~np.eye(len(ch_names), dtype=bool)
        off_diag = band_coherence[off_diag_mask]

        print(f'\n{band_name} ({low}-{high} Hz):')
        print(f'  平均コヒーレンス: {off_diag.mean():.3f}')
        print(f'  最大: {off_diag.max():.3f}')
        print(f'  最小: {off_diag.min():.3f}')
        print(f'  標準偏差: {off_diag.std():.3f}')

print("\n" + "=" * 60)
print("✅ スクリプト実行完了")
print("=" * 60)
print("\n次のステップ:")
print("1. このスクリプトでエラーが出なければ、ノートブックを修正します")
print("2. 可視化コードを追加したい場合は追加できます")
